import json,re
from itpm.core.errors import require
from itpm.core.json_fields import object_field,list_field
from .rules import progress,classification,image_descriptors,phase_payload,log_payload,TERMINAL,LIST_FIELDS

class Work:
    def __init__(self,repo,clock,ids,vocabulary,base):self.repo,self.clock,self.ids,self.v,self.base=repo,clock,ids,vocabulary,base
    def requirement(self,u,rid,lock=False):return self.repo.get(u,'requirements',rid,True,lock)
    def raw_requirement(self,u,rid):return self.repo.get(u,'requirements',rid)
    def recycle_rows(self,u):return [x for x in self.repo.find(u,'requirements') if x.get('deletedAt')]
    def recycle_restore(self,u,identifier):self.repo.change(u,'requirements',identifier,dict(deletedAt='',deletedByUserId='',deletedByName=''))
    def raw_project_children(self,u,identifier):return self.repo.find(u,'requirements',{'projectId':identifier})
    def recycle_purge(self,u,identifier):
        for row in self.repo.find(u,'changelogs',{'requirementId':identifier}):self.repo.remove(u,'changelogs',row['id'])
        self.repo.remove(u,'requirements',identifier)
    def purge_project_sprints(self,u,identifier):
        for row in self.repo.find(u,'sprints',{'projectId':identifier}):self.repo.remove(u,'sprints',row['id'])
    def sync_create(self,u,p,item,project):
        now=self.clock.now();row={k:item.get(k) or '' for k in 'title type itemKind parentRequirementId versionTarget priority status assignee requester department description acceptanceCriteria expectedDeliveryTime labels changeObject impactLevel workloadLevel'.split()}
        row.update(id=self.ids.new('r',8),flowMode='quick_iteration',lifecycleVersion=2,reportingEligible=1,registeredAt=now,relatedRequirementId='',
            projectId=project['id'],projectName=project.get('name') or '',sprintId='',storyPoints=item.get('storyPoints') or 0,
            completedAt=item['workDate']+' 00:00:00' if item['status'] in {'已交付','已关闭'} else '',priorityEvaluation='{}',images='[]',
            createdByUserId=p.userId,createdByName=p.devOwnerName or p.name,createdAt=now,updatedAt=now)
        self.repo.add(u,'requirements',row);self.seed_phases(u,p,row,project,item.get('phaseTemplateKeys'))
        self.change_log(u,p,row['id'],'状态流转','status','无',item['status'],'通用开发工作同步写入');return self.requirement(u,row['id'])
    def sync_log(self,u,p,rid,log,bid,skip_duplicate=False):
        if skip_duplicate and any(x.get('content')==log.get('content') and x.get('occurredAt')==log.get('occurredAt') and x.get('sourceBatchId')!=bid for x in self.log_sources(u,rid)):return False
        now=self.clock.now();occurred=log.get('occurredAt') or now;req=self.raw_requirement(u,rid) or {}
        self.repo.add(u,'requirement_work_logs',dict(id=self.ids.new('wl'),requirementId=rid,logType=log.get('logType') or '工作进展',content=log.get('content') or '',
            operatorUserId=p.userId,operatorName=p.devOwnerName or p.name,createdAt=now,occurredAt=occurred,sourceBatchId=bid,workDate=occurred[:10],
            visibility='it_private',sourceType='work_sync',sourceRef=bid,reportingEligible=int(bool(req.get('reportingEligible'))),updatedAt=now))
        return True
    def sync_rollback(self,u,p,rids,bid):
        removed=0
        for rid in rids:
            row=self.requirement(u,rid)
            if row:self.repo.change(u,'requirements',rid,dict(deletedAt=self.clock.now(),deletedByUserId=p.userId,deletedByName=p.devOwnerName or p.name));removed+=1
            for row in self.repo.find(u,'changelogs',{'requirementId':rid}):self.repo.remove(u,'changelogs',row['id'])
        logs=self.repo.find(u,'requirement_work_logs',{'sourceBatchId':bid})
        for row in logs:self.repo.remove(u,'requirement_work_logs',row['id'])
        return removed,len(logs)
    def sync_correct(self,u,p,row,developer,business,reason):
        for field,value in [('assignee',developer),('requester',business)]:
            if row.get(field)!=value:self.change_log(u,p,row['id'],'负责人修正',field,row.get(field) or '空',value,reason)
        self.repo.change(u,'requirements',row['id'],{'assignee':developer,'requester':business,'updatedAt':self.clock.now()})
    def requirements(self,u,filters=None,project_id=None,include_deleted=False):return self.repo.requirements(u,filters,project_id,include_deleted)
    def progress(self,u,pid):return progress(self.requirements(u,project_id=pid))
    def list_rows(self,u,filters):return self.repo.list_requirements(u,filters)
    def progress_many(self,u,ids):
        grouped={pid:[] for pid in ids}
        for row in self.repo.progress_rows(u,ids):grouped[row['projectId']].append(row)
        return {pid:progress(rows) for pid,rows in grouped.items()}
    def templates(self,u,st):return [{**x,'required':bool(x.get('required')),'enabled':bool(x.get('enabled',1))} for x in self.repo.templates(u,st)]
    def phases(self,u,rid):return [phase_payload(x,self.v) for x in self.repo.phases(u,rid)]
    def detail(self,u,row):
        images=list_field(row.get('images'));k=row.get('itemKind') or 'feature'
        return {**row,'images':image_descriptors(row['id'],images,self.base),'imageCount':len(images),'priorityEvaluation':object_field(row.get('priorityEvaluation')),
            'itemKind':k,'itemKindLabel':next((x['label'] for x in self.v['L3_ITEM_KINDS'] if x['key']==k),k),
            'parentRequirementId':row.get('parentRequirementId') or '','versionTarget':row.get('versionTarget') or '','phaseCount':len(self.repo.phases(u,row['id']))}
    def list_payload(self,row,project):
        return {**{k:row.get(k) for k in LIST_FIELDS},'imageCount':row['imageCount'],'pname':(project or {}).get('name'),'projectDepartment':(project or {}).get('department')}
    def change_log(self,u,p,rid,kind,field,before,after,reason=''):
        row=self.requirement(u,rid)
        self.repo.add(u,'changelogs',{'id':self.ids.new('cl',6),'requirementId':rid,'requirementTitle':row.get('title') if row else rid,'changeType':kind,'fieldName':field,'oldValue':str(before),'newValue':str(after),'reason':reason or '', 'operator':p.name,'createdAt':self.clock.now()})
    def shared_phase_log(self,u,p,row,content,activity_id):
        now=self.clock.now()
        self.repo.add(u,'requirement_work_logs',{'id':self.ids.new('wl'),'requirementId':row['id'],'logType':'工作进展','content':content,'operatorUserId':p.userId,'operatorName':p.name,'createdAt':now,'occurredAt':now,'sourceBatchId':activity_id})
    def log(self,u,p,req,d):
        content=str(d.get('content') or '').strip();require(content,'工作动态不能为空');require(len(content)<=5000,'工作动态最多5000字')
        date=str(d.get('workDate') or self.clock.now()[:10]).strip()[:10];require(re.fullmatch(r'\d{4}-\d{2}-\d{2}',date),'工作日期格式不正确')
        kind=str(d.get('logType') or '工作进展').strip();kind=kind if kind in {'工作进展','遇到问题','交付说明','下一步'} else '工作进展'
        vis=str(d.get('visibility') or 'it_private').strip();vis=vis if vis in {'it_private','business_shared'} else 'it_private';now=self.clock.now()
        row={'id':self.ids.new('wl'),'requirementId':req['id'],'logType':kind,'content':content,'operatorUserId':p.userId,'operatorName':p.name,'createdAt':now,'occurredAt':now,
            'workDate':date,'visibility':vis,'sourceType':str(d.get('sourceType') or 'manual').strip()[:40],'sourceRef':str(d.get('sourceRef') or '').strip()[:200],
            'reportingEligible':1 if req.get('reportingEligible') else 0,'updatedAt':now}
        self.repo.add(u,'requirement_work_logs',row);return log_payload(self.repo.get(u,'requirement_work_logs',row['id']))
    def logs(self,u,rid):return [log_payload(x) for x in self.repo.linked(u,'requirement_work_logs','requirementId',rid)]
    def log_source(self,u,identifier):return self.repo.get(u,'requirement_work_logs',identifier)
    def log_sources(self,u,rid):return self.repo.linked(u,'requirement_work_logs','requirementId',rid)
    def projection_scopes(self,u):return self.repo.projection_scopes(u)
    def collaboration_log(self,u,p,rid,kind,content,source=''):
        now=self.clock.now()
        self.repo.add(u,'requirement_work_logs',{'id':self.ids.new('wl'),'requirementId':rid,'logType':kind,'content':content,
            'operatorUserId':p.userId,'operatorName':p.name,'createdAt':now,'occurredAt':now,'sourceBatchId':source})
    def legacy_intake(self,u,p,d,project):
        now=self.clock.now();kind=d['kind'];item='initial_build' if kind=='new_requirement' else 'bugfix' if kind=='issue' else 'feature'
        row={'id':self.ids.new('r',8),'title':d['title'],'type':self.v['BUSINESS_INTAKE_REQUIREMENT_TYPE'].get(kind,'业务确认'),
            'itemKind':item,'parentRequirementId':'','versionTarget':'','priority':d['priority'],'status':'待处理',
            'projectId':(project or {}).get('id') or '','projectName':(project or {}).get('name') or '','sprintId':'','assignee':d['assignee'],
            'requester':p.name,'department':d['department'],'description':d['originalFeedback'],'acceptanceCriteria':'',
            'expectedDeliveryTime':d['expectedDeliveryTime'],'completedAt':'','storyPoints':3 if kind=='new_requirement' else 1,
            'labels':'','priorityEvaluation':'{}','images':'[]','changeObject':'模块' if kind=='new_requirement' else '功能',
            'impactLevel':'重要' if kind=='new_requirement' else '常规','workloadLevel':'中','createdByUserId':p.userId,
            'createdByName':p.name,'createdAt':now,'updatedAt':now}
        self.repo.add(u,'requirements',row)
        self.seed_phases(u,p,row,project or {})
        self.change_log(u,p,row['id'],'状态流转','status','无','待处理','业务协作提交')
        self.collaboration_log(u,p,row['id'],'工作进展','业务协作提交：'+d['originalFeedback'])
        return self.requirement(u,row['id'])
    def formal(self,u,p,d,project,historical=False):
        values=classification(d,self.v,True);now=self.clock.now();rid=self.ids.new('r',8)
        row={'id':rid,'title':d['title'],'type':values['type'],'itemKind':d.get('itemKind') or 'feature','parentRequirementId':'','demandId':d['demandId'],
            'versionTarget':d.get('versionTarget') or project.get('currentVersion') or '','priority':d.get('priority') or 'P2','status':values['status'],
            'projectId':project['id'],'projectName':project['name'],'sprintId':'','assignee':d['assignee'],'requester':d.get('requester') or '',
            'department':d['department'],'description':d.get('description') or '','acceptanceCriteria':d.get('acceptanceCriteria') or '',
            'expectedDeliveryTime':d['expectedDeliveryTime'],'completedAt':'','storyPoints':d.get('storyPoints') or 3,'labels':d.get('labels') or '',
            'priorityEvaluation':'{}','images':'[]','changeObject':values['changeObject'],'impactLevel':values['impactLevel'],'workloadLevel':values['workloadLevel'],
            'createdByUserId':p.userId,'createdByName':p.name,'createdAt':now,'updatedAt':now}
        if not historical:row.update(flowMode='full_demand',lifecycleVersion=2,reportingEligible=1,registeredAt=now,relatedRequirementId='')
        self.repo.add(u,'requirements',row);self.seed_phases(u,p,row,project,[] if historical else d.get('phaseTemplateKeys'))
        self.change_log(u,p,rid,'状态流转','status','无','待处理','已完成需求历史补录独立 L3 工作项' if historical else '需求池综合决策后正式立项')
        if not historical:self.log(u,p,row,{'content':'需求池综合决策完成，正式创建 L3：'+d.get('demandTitle',''),'sourceType':'system_event','sourceRef':'requirement-created:'+rid})
        return self.requirement(u,rid)
    def internal_change(self,u,rid,values):self.repo.change(u,'requirements',rid,values);return self.requirement(u,rid)
    def mark_initial_reporting(self,u,rid):
        for log in self.log_sources(u,rid):self.repo.change(u,'requirement_work_logs',log['id'],{'reportingEligible':1})
    def feedback_requirement(self,u,p,source,project,kind,content,title):
        now=self.clock.now();restructure=kind=='requirement_change';rid=self.ids.new('r',8)
        row={'id':rid,'title':title or ('需求重构' if restructure else '新增功能')+'：'+(source.get('title') or '未命名需求'),
            'type':'需求重构' if restructure else '新增功能','itemKind':'enhancement' if restructure else 'feature','parentRequirementId':source['id'],
            'versionTarget':source.get('versionTarget') or project.get('currentVersion') or '','priority':source.get('priority') or 'P2','status':'待处理',
            'projectId':source.get('projectId') or '','projectName':project.get('name') or source.get('projectName') or '','sprintId':'',
            'assignee':source.get('assignee') or project.get('devOwner') or '待分配','requester':source.get('requester') or project.get('businessOwner') or '',
            'department':source.get('department') or project.get('department') or '',
            'description':f"由交付反馈分流创建。来源 L3：{source.get('title') or source['id']}（{source['id']}）。\n业务反馈：{content[:8000]}",
            'acceptanceCriteria':'','expectedDeliveryTime':source.get('expectedDeliveryTime') or project.get('targetEndDate') or '',
            'completedAt':'','storyPoints':0,'labels':f"feedback_route:{kind},source_l3:{source['id']}",'priorityEvaluation':'{}','images':'[]',
            'changeObject':source.get('changeObject') or '功能','impactLevel':source.get('impactLevel') or '常规','workloadLevel':source.get('workloadLevel') or '中',
            'createdByUserId':p.userId,'createdByName':p.name,'createdAt':now,'updatedAt':now}
        self.repo.add(u,'requirements',row);self.change_log(u,p,rid,'状态流转','status','无','待处理','由交付反馈分流创建新 L3')
        self.collaboration_log(u,p,rid,'工作进展',f"由 L3「{source.get('title') or source['id']}」的业务反馈分流创建。")
        self.seed_phases(u,p,row,project);return self.requirement(u,rid)
    def seed_phases(self,u,p,req,project,keys=None):
        requested={str(k).strip() for k in (keys or []) if str(k).strip()}
        if not requested and req['itemKind']!='initial_build':return
        for t in self.templates(u,project.get('solutionType') or 'unknown'):
            if requested and t['phaseKey'] not in requested:continue
            self.phase(u,p,req['id'],{'phaseKey':t['phaseKey'],'phaseLabel':t['phaseLabel'],'description':t.get('description') or '',
                'required':t['required'],'sortOrder':t.get('sortOrder') or 0})
    def create(self,u,p,d,project):
        d={**d,**classification(d,self.v,True)};now=self.clock.now()
        kind=str(d.get('itemKind') or 'feature').strip()
        if kind not in {x['key'] for x in self.v['L3_ITEM_KINDS']}:kind='feature'
        mode=str(d.get('flowMode') or ('full_demand' if d.get('demandId') else 'legacy')).strip()
        if mode not in {'full_demand','quick_iteration','legacy'}:mode='legacy'
        eligible=1 if d.get('reportingEligible') or mode in {'full_demand','quick_iteration'} else 0
        if mode=='quick_iteration':require(str(d.get('acceptanceCriteria') or '').strip(),'快速迭代 L3 必须填写一句验收标准')
        row={'id':self.ids.new('r',8),'title':d['title'],'type':d['type'],'itemKind':kind,'parentRequirementId':str(d.get('parentRequirementId') or '').strip()[:120],
            'demandId':d.get('demandId',''),'flowMode':mode,'lifecycleVersion':2 if eligible else 1,'reportingEligible':eligible,'registeredAt':now,
            'relatedRequirementId':str(d.get('relatedRequirementId') or '').strip()[:120],'versionTarget':str(d.get('versionTarget') or '').strip()[:120],
            'priority':d.get('priority','P2'),'status':d['status'],'projectId':d['projectId'],'projectName':project['name'],'sprintId':d.get('sprintId',''),
            'assignee':d['assignee'],'requester':d.get('requester',''),'department':d['department'],'description':d.get('description',''),'acceptanceCriteria':d.get('acceptanceCriteria',''),
            'expectedDeliveryTime':d['expectedDeliveryTime'],'completedAt':now if d['status'] in TERMINAL else '','storyPoints':d.get('storyPoints',0),'labels':d.get('labels',''),
            'priorityEvaluation':json.dumps(d.get('priorityEvaluation',{}),ensure_ascii=False),'images':json.dumps(d.get('images',[]),ensure_ascii=False),
            'changeObject':d['changeObject'],'impactLevel':d['impactLevel'],'workloadLevel':d['workloadLevel'],'createdByUserId':p.userId,'createdByName':p.name,'createdAt':now,'updatedAt':now}
        self.repo.add(u,'requirements',row)
        self.change_log(u,p,row['id'],'状态流转','status','无',d.get('status','待评估'),'新建需求')
        self.log(u,p,row,{'content':f"已登记工作，当前状态：{d['status']}",'sourceType':'system_event','sourceRef':f"requirement-created:{row['id']}"})
        self.seed_phases(u,p,row,project,d.get('phaseTemplateKeys'))
        return self.requirement(u,row['id'])
    def initial(self,u,p,project,keys=None):
        existing=next((x for x in reversed(self.requirements(u,project_id=project['id'])) if x.get('itemKind')=='initial_build'),None)
        if existing:return existing
        now=self.clock.now();row={'id':self.ids.new('r',8),'title':'初始建设','type':'技术建设','itemKind':'initial_build','parentRequirementId':'','demandId':'','flowMode':'legacy','lifecycleVersion':1,'reportingEligible':0,'registeredAt':now,'relatedRequirementId':'','versionTarget':project.get('currentVersion') or 'v1.0.0','priority':project.get('priority') or 'P2','status':'待处理','projectId':project['id'],'projectName':project.get('name') or '','sprintId':'','assignee':project.get('devOwner') or '待分配','requester':project.get('businessOwner') or '','department':project.get('department') or '','description':'L2 项目的初始建设工作，阶段卡按项目类型生成，可按需调整。','acceptanceCriteria':'','expectedDeliveryTime':project.get('targetEndDate') or '','completedAt':'','storyPoints':0,'labels':'initial_build','priorityEvaluation':'{}','images':'[]','changeObject':'模块','impactLevel':'重要','workloadLevel':'大','createdByUserId':p.userId,'createdByName':p.name,'createdAt':now,'updatedAt':now}
        self.repo.add(u,'requirements',row);self.change_log(u,p,row['id'],'状态流转','status','无','待处理','创建 L2 时生成初始建设 L3')
        self.log(u,p,row,{'content':'创建初始建设 L3，可按项目类型调整阶段卡。','sourceType':'system_event','sourceRef':f"requirement-created:{row['id']}"});self.seed_phases(u,p,row,project,keys)
        return self.requirement(u,row['id'])
    def update(self,u,p,old,d):
        rid=old['id'];now=self.clock.now();values={k:v for k,v in d.items() if k in 'title type itemKind parentRequirementId versionTarget projectId assignee requester department acceptanceCriteria expectedDeliveryTime labels changeObject impactLevel workloadLevel storyPoints'.split()}
        if 'itemKind' in values:require(str(values['itemKind'] or '') in {x['key'] for x in self.v['L3_ITEM_KINDS']},'不支持的 L3 类型')
        for k in ['itemKind','parentRequirementId','versionTarget']:
            if k in values:values[k]=str(values[k] or '').strip()
        if 'priorityEvaluation' in d:values['priorityEvaluation']=json.dumps(d['priorityEvaluation'],ensure_ascii=False) if isinstance(d['priorityEvaluation'],dict) else d['priorityEvaluation']
        for key,kind,default in [('description','范围变更','更新描述'),('priority','优先级调整',''),('status','状态流转',''),('sprintId','重新排期','重新排期')]:
            if key in d and d[key]!=old.get(key):
                self.change_log(u,p,rid,kind,key,old.get(key) or ('未排期' if key=='sprintId' else ''),d[key] or ('未排期' if key=='sprintId' else ''),d.get('reason',default));values[key]=d[key]
        if 'status' in values:
            if values['status'] in TERMINAL:values['completedAt']=now
            elif old.get('status') in TERMINAL:values['completedAt']=''
            self.log(u,p,old,{'content':f"状态更新为：{values['status']}。{d.get('reason') or ''}".strip(),'logType':'交付说明' if values['status'] in {'待交付','已交付','已关闭'} else '工作进展','sourceType':'status_change','sourceRef':rid})
        if 'images' in d:
            images=d['images'];oldimages=list_field(old.get('images'))
            if isinstance(images,list):
                images=[oldimages[x['existingIndex']] if isinstance(x,dict) and isinstance(x.get('existingIndex'),int) and 0<=x['existingIndex']<len(oldimages) else x for x in images]
            values['images']=json.dumps(images,ensure_ascii=False) if isinstance(images,list) else images
        if values:values['updatedAt']=now
        self.repo.change(u,'requirements',rid,values);return self.requirement(u,rid),bool(values)
    def delete(self,u,p,rid):self.repo.change(u,'requirements',rid,{'deletedAt':self.clock.now(),'deletedByUserId':p.userId,'deletedByName':p.name})
    def phase(self,u,p,rid,d):
        key=str(d.get('phaseKey') or '').strip()[:120];label=str(d.get('phaseLabel') or d.get('title') or '').strip()[:200]
        require(key and label,'阶段编号和阶段名称不能为空');status=str(d.get('status') or 'todo').strip();require(status in {x['key'] for x in self.v['PHASE_STATUS_OPTIONS']},'不支持的阶段状态')
        old=self.repo.phase(u,rid,key) or {};now=self.clock.now();identifier=old.get('id') or self.ids.new('rph',18)
        values={'phaseLabel':label,'description':str(d.get('description') or old.get('description') or '').strip()[:2000],'status':status,
            'ownerUserId':str(d.get('ownerUserId') or old.get('ownerUserId') or '').strip()[:120],'ownerName':str(d.get('ownerName') or old.get('ownerName') or '').strip()[:120],
            'required':1 if d.get('required',old.get('required')) else 0,'sortOrder':int(d.get('sortOrder') if d.get('sortOrder') is not None else old.get('sortOrder') or 0),
            'plannedAt':str(d.get('plannedAt') or old.get('plannedAt') or '').strip()[:40],'startedAt':old.get('startedAt') or (now if status=='in_progress' else ''),'completedAt':now if status in {'done','skipped'} else '',
            'evidence':json.dumps(d['evidence'] if isinstance(d.get('evidence'),dict) else object_field(old.get('evidence')),ensure_ascii=False),'note':str(d.get('note') or old.get('note') or '').strip()[:5000],'updatedAt':now}
        if old:self.repo.change(u,'requirement_phases',identifier,values)
        else:self.repo.add(u,'requirement_phases',{'id':identifier,'requirementId':rid,'phaseKey':key,**values,'createdByUserId':p.userId,'createdByName':p.name,'createdAt':now})
        return phase_payload(self.repo.get(u,'requirement_phases',identifier),self.v),old
    def phase_by_id(self,u,rid,identifier):
        row=self.repo.get(u,'requirement_phases',identifier);return row if row and row['requirementId']==rid else None
    def changelogs(self,u,project=None,rid=None):return self.repo.changelogs(u,project,rid)
    def sprints(self,u):return self.repo.list_table(u,'sprints','startdate')
    def sprint(self,u,sid):return self.repo.get(u,'sprints',sid)
    def create_sprint(self,u,d):
        require(d.get('name') and d.get('projectId'),'name+projectId required');sid=self.ids.new('s',8)
        self.repo.add(u,'sprints',{'id':sid,'name':d['name'],'projectId':d['projectId'],'startDate':d.get('startDate',''),'endDate':d.get('endDate',''),'status':'规划中','releaseNotes':'','totalTasks':0,'completedTasks':0});return {'id':sid,'name':d['name']}
    def update_sprint(self,u,sid,d):
        require(self.sprint(u,sid),'迭代不存在',404,'NOT_FOUND');v={k:d[k] for k in ['name','startDate','endDate','releaseNotes'] if k in d}
        if d.get('status') in ['规划中','进行中','已发布','已取消']:
            v['status']=d['status']
            if d['status']=='已发布':
                reqs=[x for x in self.requirements(u,include_deleted=True) if x.get('sprintId')==sid];v.update(completedTasks=len(reqs),totalTasks=len(reqs))
        self.repo.change(u,'sprints',sid,v);return self.sprint(u,sid)
    def delete_sprint(self,u,sid):require(self.sprint(u,sid),'迭代不存在',404,'NOT_FOUND');self.repo.remove(u,'sprints',sid);return {'ok':1}
    def releases(self,u,pid=''):return [x for x in self.repo.list_table(u,'releases','releasedate') if not pid or x['projectId']==pid]
    def release(self,u,rid):return self.repo.get(u,'releases',rid)
    def create_release(self,u,d):
        require(d.get('projectId') and d.get('version'),'projectId+version required');rid=self.ids.new('rel',8)
        self.repo.add(u,'releases',{'id':rid,'projectId':d['projectId'],'version':d['version'],'releaseDate':d.get('releaseDate',self.clock.now()[:10]),'summary':json.dumps(d.get('summary',[]),ensure_ascii=False),'type':d.get('type','minor')});return {'id':rid}
    def bulk_classify(self,u,row,changes):
        values=dict(changes)
        if 'status' in values:
            if values['status'] in {'已交付','已关闭'}:values['completedAt']=row.get('completedAt') or self.clock.now()
            elif row.get('status') in {'已交付','已关闭'}:values['completedAt']=''
        values['updatedAt']=self.clock.now();self.repo.change(u,'requirements',row['id'],values);return self.requirement(u,row['id'])
