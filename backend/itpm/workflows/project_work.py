"""Cross-domain orchestration. Rules and persistence stay in their domains."""
from itpm.core.errors import require
from itpm.core.events import Event,DeferredEvent,AfterCommitAction,legacy_dedupe_key
from itpm.core.json_fields import list_field,object_field
from itpm.modules.work.public import classification,transition,TERMINAL
from itpm.modules.identity.public import split_people,same_name
from itpm.modules.portfolio.public import solution_type,validate_project
from itpm.core.ports import Principal
import json,hashlib


class ProjectWork:
    def __init__(self,identity,portfolio,work,audit,inbox,delivery,postlaunch,value,collaboration,clock,ids,vocabulary,notices,uow_factory):
        self.identity,self.portfolio,self.work,self.audit,self.inbox=identity,portfolio,work,audit,inbox
        self.delivery,self.postlaunch,self.value,self.collaboration=delivery,postlaunch,value,collaboration
        self.clock,self.ids,self.v=clock,ids,vocabulary
        self.notices,self.uow_factory=notices,uow_factory

    def emit(self,u,p,name,row,aggregate):
        identifier=row.get('id') or row.get('requirementId') or ''
        key=legacy_dedupe_key(name,row);fact=row.get('activityId') or row.get('commentId') or identifier
        u.events.append(Event(name,'evt'+hashlib.sha256(key.encode()).hexdigest()[:24],f'{name}:{fact}',self.clock.now(),p.dto(),aggregate,identifier,row,
            correlation_id=getattr(u,'correlation_id',''),dedupe_key=key))

    def project_payload(self,u,row,rich=True,progress=False,phase_templates=None,progress_value=None):
        row={**row,'images':list_field(row.get('images'))}
        if rich:
            st=solution_type(row.get('solutionType'),self.v);row.update(solutionType=st,solutionTypeLabel=next(x['label'] for x in self.v['PROJECT_SOLUTION_TYPES'] if x['key']==st),
                lifecycleTemplate=row.get('lifecycleTemplate') or st,phaseTemplates=self.work.templates(u,st) if phase_templates is None else phase_templates)
        if progress:row['progress']=self.work.progress(u,row['id']) if progress_value is None else progress_value
        return row

    def list_projects(self,u,category=None,identifier=None):
        rows=self.portfolio.projects(u,category,identifier)
        if identifier:require(rows,'项目不存在',404,'NOT_FOUND')
        progress_values=self.work.progress_many(u,[x['id'] for x in rows]);templates={}
        if category is None:
            for x in rows:
                st=solution_type(x.get('solutionType'),self.v)
                if st not in templates:templates[st]=self.work.templates(u,st)
        result=[self.project_payload(u,x,category is None,True,templates.get(solution_type(x.get('solutionType'),self.v)),progress_values[x['id']]) for x in rows]
        return result[0] if identifier else result

    def category(self,u,identifier):
        row=self.portfolio.category(u,identifier);require(row,'大类不存在',404,'NOT_FOUND');return row

    def create_category(self,u,p,d):
        self.identity.action(u,p,'category.manage');require(d.get('name'),'name required');row=self.portfolio.create_category(u,p,d)
        self.audit.record(u,p,'L1',row['id'],row['name'],'create','新增大类',after=row);return {'id':row['id'],'name':row['name']}

    def update_category(self,u,p,cid,d):
        self.identity.action(u,p,'category.manage');old=self.category(u,cid);row=self.portfolio.update_category(u,cid,d)
        before={**old,'owner':json.dumps(old['owner'],ensure_ascii=False)}
        self.audit.record(u,p,'L1',cid,row.get('name',cid),'update','修改大类',before=before,after=row);return row

    def delete_category(self,u,p,cid):
        self.identity.action(u,p,'category.manage');old=self.category(u,cid);count=self.portfolio.category_count(u,cid)
        require(not count,f'该大类下有 {count} 个项目，请先删除项目');self.portfolio.delete(u,p,'category',cid)
        before={**old,'owner':json.dumps(old['owner'],ensure_ascii=False)}
        self.audit.record(u,p,'L1',cid,old['name'],'delete','移入回收站',before=before);return {'ok':1}

    def create_project(self,u,p,d):
        self.identity.action(u,p,'project.create');row=self.portfolio.create_project(u,p,d);result=self.project_payload(u,row)
        self.audit.record(u,p,'L2',row['id'],row['name'],'create','新增项目',after=result);self.emit(u,p,'project_created',result,'project')
        initial=''
        if d.get('createInitialL3') and row['solutionType']!='unknown':
            req=self.work.initial(u,p,row,d.get('phaseTemplateKeys'));initial=req['id']
            self.audit.record(u,p,'L3',initial,'初始建设','create','创建 L2 时生成初始建设 L3',after={'projectId':row['id'],'itemKind':'initial_build'})
        return {'id':row['id'],'name':row['name'],'solutionType':result['solutionType'],'solutionTypeLabel':result['solutionTypeLabel'],'initialRequirementId':initial}

    def update_project(self,u,p,pid,d):
        self.identity.authenticated(p);old=self.portfolio.project(u,pid,True);require(old,'项目不存在',404,'NOT_FOUND')
        require(self.identity.can_edit(u,p,old,'project'),'普通编辑者只能修改自己创建、负责或被分配的项目',403,'FORBIDDEN')
        if any(k in d and str(d[k] or '')!=str(old.get(k) or '') for k in ['businessOwner','devOwner']):require(self.identity.has(u,p,'assignment.manage'),'只有管理员可以修改项目负责人',403,'FORBIDDEN')
        validate_project({**old,**d});row,changed=self.portfolio.update_project(u,pid,d);result=self.project_payload(u,row)
        if changed:
            self.audit.record(u,p,'L2',pid,row.get('name',pid),'update','修改项目',old,result)
            if d.get('status') in {'已上线','已交付'} and old.get('status') not in {'已上线','已交付'}:
                for req in self.work.requirements(u,project_id=pid,include_deleted=True):self.close_todos(u,req['id'])
                self.start_operation(u,p,row,'project')
            self.emit(u,p,'project_updated',result,'project')
        return result

    def delete_project(self,u,p,pid,summary='移入回收站'):
        old=self.portfolio.project(u,pid,True);require(old,'项目不存在',404,'NOT_FOUND');self.identity.delete_permission(u,p,old,'project')
        count=len(self.work.requirements(u,project_id=pid));require(not count,f'该项目下有 {count} 个需求，请先逐个删除需求')
        self.portfolio.delete(u,p,'project',pid);self.audit.record(u,p,'L2',pid,old.get('name',pid),'delete',summary,before=old);return {'ok':1}

    def bulk_projects(self,u,p,ids):
        self.identity.action(u,p,'project.delete');require(ids,'ids required');deleted=[];skipped=[]
        for pid in ids[:200]:
            old=self.portfolio.project(u,pid,True)
            if not old:skipped.append({'id':pid,'reason':'项目不存在'});continue
            count=len(self.work.requirements(u,project_id=pid))
            if count:skipped.append({'id':pid,'name':old.get('name'),'reason':f'仍有 {count} 个需求'});continue
            self.delete_project(u,p,pid,'批量移入回收站');deleted.append(pid)
        return {'ok':1,'deleted':deleted,'skipped':skipped}

    def requirement_payload(self,u,row,complete_join=False):
        project=self.portfolio.project(u,row.get('projectId'))
        result={**row,'pname':(project or {}).get('name')}
        if complete_join:
            category=self.portfolio.category(u,(project or {}).get('categoryId'))
            result.update(categoryId=(project or {}).get('categoryId'),projectDepartment=(project or {}).get('department'),cname=(category or {}).get('name'))
        return self.work.detail(u,result)

    def requirement(self,u,rid):
        row=self.work.requirement(u,rid);require(row,'需求不存在',404,'NOT_FOUND')
        # Missing historical project is legal; an explicitly deleted project is not.
        project=self.portfolio.project(u,row.get('projectId'))
        raw=self.portfolio.raw_project(u,row.get('projectId'))
        require(not raw or not raw.get('deletedAt'),'需求不存在',404,'NOT_FOUND')
        return self.requirement_payload(u,row,True)

    def list_requirements(self,u,filters):
        result=[];projects=self.portfolio.project_map(u)
        for row in self.work.list_rows(u,filters):
            project=projects.get(row.get('projectId'))
            if project and project.get('deletedAt'):continue
            if filters.get('categoryId') and (project or {}).get('categoryId')!=filters['categoryId']:continue
            result.append(self.work.list_payload(row,project))
        return result

    def editable_requirement(self,u,p,rid,message='普通编辑者只能修改自己创建、负责或被分配的需求'):
        self.identity.authenticated(p);row=self.work.requirement(u,rid,True);require(row,'需求不存在',404,'NOT_FOUND')
        project=self.portfolio.project(u,row.get('projectId'));require(self.identity.can_edit(u,p,row,'requirement',project),message,403,'FORBIDDEN');return row,project

    def assign_todos(self,u,p,row,message):
        recipients=split_people(row.get('assignee'))
        # Preserve canonical aliases from configured developers.
        developers=self.identity.options(u)['developers'];recipients=[next((d['name'] for d in developers if same_name(d['name'],n,self.v['DEVELOPERS'])),n) for n in recipients]
        for todo in self.inbox.assign(u,p,row,message,recipients,self.identity.policy(u)):
            self.emit(u,p,'todo_created',{**row,**todo},'todo')
            u.events[-1]=DeferredEvent(u.events[-1],self.finish_todo_notice)

    def finish_todo_notice(self,payload):
        try:sent=self.notices.todo(payload)
        except Exception:
            sent=False
            with self.uow_factory() as u:self.audit.log(u,{'source':'todo-robot','level':'error','message':'待办机器人通知失败','detail':'INTEGRATION_UNAVAILABLE','userName':payload.get('recipientName') or ''})
        if sent:
            with self.uow_factory() as u:self.inbox.mark_sent(u,payload['id'])
            payload['dingTalkSent']=True
        return payload

    def close_todos(self,u,rid):
        for todo in self.inbox.close(u,rid):
            if todo.get('dingTalkTaskId'):u.events.append(AfterCommitAction(lambda todo=todo:self.finish_native_todo(todo)))

    def finish_native_todo(self,todo):
        try:self.notices.complete_native(todo)
        except Exception:
            with self.uow_factory() as u:
                self.inbox.mark_error(u,todo['id'],'INTEGRATION_UNAVAILABLE')
                self.audit.log(u,{'source':'dingtalk-todo','level':'error','message':'Native DingTalk todo complete failed','detail':'INTEGRATION_UNAVAILABLE','userName':todo.get('recipientName') or ''})

    def completion_notice(self,u,p,row):
        if not self.identity.policy(u)['notifyRequesterOnOnline']:return
        uid=row.get('createdByUserId') or '';name=row.get('createdByName') or ''
        if not uid:
            hint=self.inbox.creator_hint(u,row['id']) or {};uid=hint.get('sourceUserId') or '';name=hint.get('sourceName') or name
        if not uid and (row.get('requester') or name):name=name or row.get('requester') or '';uid=self.identity.person_id(u,name)
        if not uid:
            self.audit.log(u,{'source':'dingtalk-work-notice','level':'warning','message':'Completion notice skipped','detail':'creator userid not found','userName':name});return
        notice={'userId':uid,'title':row.get('title') or row.get('requirementTitle') or '',
            'project':row.get('pname') or row.get('projectName') or '', 'actor':p.name,
            'url':self.delivery.public_link(u,row['id'],uid,name,self.clock.now(),self.notices.base,self.v),'recipientName':name}
        u.events.append(AfterCommitAction(lambda:self.finish_completion_notice(notice)))

    def finish_completion_notice(self,notice):
        try:self.notices.completion(notice)
        except Exception:
            with self.uow_factory() as u:self.audit.log(u,{'source':'todo-robot','level':'error','message':'Completion notice failed','detail':'INTEGRATION_UNAVAILABLE','userName':notice.get('recipientName') or ''})

    def create_requirement(self,u,p,d):
        self.identity.action(u,p,'requirement.create');require(d.get('title') and d.get('projectId'),'title+projectId required')
        d={**d,**classification(d,self.v,True)}
        for field,label in [('department','归属部门'),('assignee','开发负责人'),('expectedDeliveryTime','预计交付时间')]:require(d.get(field),label+'必填')
        project=self.portfolio.project(u,d['projectId'],True);require(project,'所属项目不存在或已在回收站')
        row=self.work.create(u,p,d,project);eventrow={**row,'pname':project['name'],'images':list_field(row.get('images')),'priorityEvaluation':object_field(row.get('priorityEvaluation'))}
        self.audit.record(u,p,'L3',row['id'],row['title'],'create','新增需求',after=eventrow)
        self.assign_todos(u,p,eventrow,'新建需求并指派给你，请确认处理');self.emit(u,p,'requirement_created',eventrow,'requirement')
        if eventrow.get('assignee') and eventrow['assignee']!='待分配':self.emit(u,p,'requirement_assigned',eventrow,'requirement')
        if row['status']=='已交付':self.start_operation(u,p,row,'requirement')
        return {'id':row['id'],'title':row['title']}

    def update_requirement(self,u,p,rid,d):
        old,project=self.editable_requirement(u,p,rid);d={**d,**classification(d,self.v)}
        if any(k in d and str(d[k] or '')!=str(old.get(k) or '') for k in ['assignee','requester']):require(self.identity.has(u,p,'assignment.manage'),'只有管理员可以修改需求负责人或提出方',403,'FORBIDDEN')
        changed_status='status' in d and d['status']!=old.get('status');status_only=set(d)<= {'status','reason','operator'} and changed_status
        if not status_only:
            merged={**old,**d}
            for field,label in [('department','归属部门'),('assignee','开发负责人'),('expectedDeliveryTime','预计交付时间')]:require(merged.get(field),label+'必填')
        if changed_status:transition(old['status'],d['status'],d.get('reason'),self.v,self.delivery.pending_verification(u,rid),self.postlaunch.delivered(u,rid))
        row,changed=self.work.update(u,p,old,d);result=self.requirement_payload(u,row)
        if changed:
            self.audit.record(u,p,'L3',rid,row.get('title',rid),'update','修改需求',old,result)
            if 'assignee' in d and d['assignee']!=old.get('assignee'):
                self.assign_todos(u,p,result,'需求负责人已改派给你，请确认处理');self.emit(u,p,'requirement_assigned',result,'requirement')
            if changed_status and d['status'] in TERMINAL:self.close_todos(u,rid)
            if changed_status and d['status']=='已交付':self.completion_notice(u,p,result);self.start_operation(u,p,row,'requirement')
            if changed_status and d['status'] in TERMINAL:self.emit(u,p,'requirement_delivered',result,'requirement')
            self.emit(u,p,'requirement_updated',result,'requirement')
        return result

    def delete_requirement(self,u,p,rid,summary='移入回收站'):
        row=self.work.requirement(u,rid,True);require(row,'需求不存在',404,'NOT_FOUND');self.identity.delete_permission(u,p,row,'requirement')
        self.work.delete(u,p,rid);self.close_todos(u,rid);self.audit.record(u,p,'L3',rid,row.get('title',rid),'delete',summary,before=row);return {'ok':1}

    def bulk_requirements(self,u,p,ids):
        self.identity.action(u,p,'requirement.delete');require(ids,'ids required');deleted=[];skipped=[]
        for rid in ids[:500]:
            row=self.work.requirement(u,rid,True)
            if not row:skipped.append({'id':rid,'reason':'需求不存在'});continue
            self.delete_requirement(u,p,rid,'批量移入回收站');deleted.append(rid)
        return {'ok':1,'deleted':deleted,'skipped':skipped}

    def bulk_classification(self,u,p,d):
        self.identity.action(u,p,'requirement.update');ids=list(dict.fromkeys(str(x) for x in d.get('ids',[]) if x));require(ids,'ids required');require(len(ids)<=500,'一次最多补录500条需求')
        values=classification(d,self.v);require(values,'至少选择一个需要补录的字段');updated=[];skipped=[]
        for rid in ids:
            old=self.work.requirement(u,rid,True)
            if not old:skipped.append({'id':rid,'reason':'需求不存在'});continue
            if not self.identity.can_edit(u,p,old,'requirement',self.portfolio.project(u,old.get('projectId'))):skipped.append({'id':rid,'reason':'当前角色不能编辑此需求'});continue
            changes={k:v for k,v in values.items() if str(old.get(k) or '')!=str(v)}
            if not changes:skipped.append({'id':rid,'reason':'字段值无需修改'});continue
            if 'status' in changes and old.get('status') not in self.v['REQUIREMENT_STATUS_OPTIONS'] and old.get('status') not in self.v['REQUIREMENT_STATUS_MAP']:
                skipped.append({'id':rid,'reason':f"不允许从{old.get('status') or '未设置'}变更为{changes['status']}"});continue
            row=self.work.bulk_classify(u,old,changes)
            if changes.get('status') in {'已交付','已关闭'}:self.close_todos(u,rid)
            self.audit.record(u,p,'L3',rid,row.get('title',rid),'update',str(d.get('reason') or '批量补录/校正L3字段').strip()[:200],old,self.requirement_payload(u,row));updated.append(rid)
        return {'ok':1,'updated':updated,'skipped':skipped}

    def log(self,u,p,rid,d):
        row,_=self.editable_requirement(u,p,rid,'当前角色不能记录此需求的工作动态');log=self.work.log(u,p,row,d)
        after={k:v for k,v in log.items() if k!='sourceBatchId'};after['reportingEligible']=1 if log['reportingEligible'] else 0
        self.audit.record(u,p,'L3',rid,row.get('title') or rid,'work_log',f"追加{log['logType']}",after=after);return log

    def phase(self,u,p,rid,d,phase_id=None):
        row,project=self.editable_requirement(u,p,rid,'当前角色不能维护阶段卡')
        if phase_id:
            old=self.work.phase_by_id(u,rid,phase_id);require(old,'阶段卡不存在',404,'NOT_FOUND');d={**old,**d,'phaseKey':old['phaseKey'],'phaseLabel':d.get('phaseLabel') or old['phaseLabel']}
        saved,old=self.work.phase(u,p,rid,d);action='update' if old else 'create'
        self.audit.record(u,p,'L3',rid,row.get('title') or rid,'phase_'+action,('更新' if old else '新增')+'阶段：'+saved['phaseLabel'],after=saved)
        if old and old['status']!=saved['status']:
            labels={x['key']:x['label'] for x in self.v['PHASE_STATUS_OPTIONS']};content=f"阶段「{saved['phaseLabel']}」：{labels.get(old['status'],old['status'] or '待开始')} → {labels[saved['status']]}"
            activity=self.collaboration.phase_progress(u,p,row,content)
            # V1 phase sharing produces an additional log without manual-log defaults.
            self.work.shared_phase_log(u,p,row,content,activity['id'])
            recipient=(project or {}).get('businessOwner') or row.get('requester') or ''
            recipient_uid=self.identity.person_id(u,recipient)
            same_actor=recipient==p.name or bool(p.userId and recipient_uid and p.userId==recipient_uid)
            if recipient and not same_actor:self.inbox.assign(u,p,row,f'{p.name}发布了工作进展',[recipient],{},'shared_activity')
            self.audit.record(u,p,'L3',rid,row.get('title') or rid,'shared_activity','发布工作进展',after={'activityId':activity['id'],'activityType':'work_progress'})
            record={**(project or {}),**row,'pname':(project or {}).get('name'),'projectBusinessOwner':(project or {}).get('businessOwner'),'projectDevOwner':(project or {}).get('devOwner'),
                'projectId':row.get('projectId') or '','projectName':(project or {}).get('name') or '',
                'scopeType':'requirement','scopeId':rid,'activityId':activity['id'],'activityTypeLabel':'工作进展','content':content,'actorName':p.name}
            self.emit(u,p,'shared_activity_created',record,'requirement')
        return saved

    def start_operation(self,u,p,target,kind):
        if kind=='requirement':
            project=self.portfolio.project(u,target.get('projectId')) or {}
            target={**target,'requester':target.get('requester') or project.get('businessOwner') or '',
                'targetEndDate':project.get('targetEndDate') or ''}
        name=target.get('requester') if kind=='requirement' else target.get('businessOwner')
        operation,created=self.postlaunch.start(u,p,target,kind,self.identity.person_id(u,name))
        if created:
            requests=self.value.schedule(u,p,operation,self.value.eligible(u,target) if kind=='requirement' else False)
            if requests:self.postlaunch.attach_requests(u,operation['id'],requests);operation.update(day7RequestId=requests.get('day7',''),day30RequestId=requests.get('day30',''))
            self.audit.record(u,p,'L3' if kind=='requirement' else 'L2',target['id'],target.get('title') or target.get('name') or '',
                'postlaunch_start','建立交付后运营记录',after=operation)
