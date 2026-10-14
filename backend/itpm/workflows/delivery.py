import hashlib
import json
import secrets
from datetime import datetime,timedelta
from dataclasses import replace
from itpm.core.errors import AppError
from itpm.core.ports import Principal
from itpm.core.json_fields import object_field
from itpm.core.events import AfterCommitAction
from itpm.modules.delivery.public import KINDS,OUTCOMES,FEEDBACK_TYPES,FEEDBACK_ROUTES,DEFAULT_ROUTES


def need(condition,message,status=400):
    if not condition:raise AppError(message,status,'LIFECYCLE_ERROR',field='detail')


class DeliveryWorkflow:
    def __init__(self,delivery,flow,shared,demand,files):
        self.delivery,self.flow,self.shared,self.demand,self.files=delivery,flow,shared,demand,files
        self.operation_payload=None
    def resource(self,u,p,rid,edit=False):
        need(p.authenticated,'请先登录',401);project,req=self.shared.scope(u,'requirement',rid);need(req,'L3 不存在或已归档',404)
        need(self.flow.identity.can_edit(u,p,req,'requirement',project) if edit else self.shared.visible(u,p,'requirement',rid),'无权操作此 L3',403)
        self.flow.work.requirement(u,rid,True)
        return req,project
    def token_link(self,u,token,pending=False,lock=False):
        row=self.delivery.link(u,token=token,lock=lock);need(row and row['status']!='revoked' and row['expiresAt']>self.flow.clock.now(),'链接已失效，请联系 IT 重新生成',410)
        need(self.shared.scope(u,'requirement',row['requirementId'])[1],'关联 L3 已归档',410)
        need(not pending or row['status']=='pending','本轮已提交，请联系 IT 发起下一轮',409);return row
    def evidence(self,u,rid):
        owners=self.shared.owners_for_requirement(u,rid)+self.demand.evidence_owners(u,rid)
        files=[file for kind,identifier in owners for file in self.files.list(u,kind,identifier)]
        return sorted(files,key=lambda x:(x['createdAt'],x['id']),reverse=True)
    def history(self,u,p,rid):
        project,req=self.shared.scope(u,'requirement',rid)
        history=[]
        for activity in reversed(self.shared.historical(u,'requirement',rid)):
            if self.shared.private(u,activity):continue
            payload=self.shared.activity_payload(u,activity);comments=[]
            for c in payload['comments']:
                if str(c.get('content') or '').strip():comments.append({'commenterName':str(c.get('commenterName') or '协作方')[:80],'content':str(c['content']).strip()[:4000],'createdAt':str(c.get('createdAt') or '')[:40]})
            content=str(payload.get('content') or '').strip()
            if content or comments:history.append({'activityTypeLabel':str(payload.get('activityTypeLabel') or '产品动态')[:40],
                'title':str(payload.get('title') or payload.get('activityTypeLabel') or '产品动态').strip()[:160],
                'content':content[:4000],'actorName':str(payload.get('actorName') or '系统')[:80],'createdAt':str(payload.get('createdAt') or '')[:40],'comments':comments[:20]})
        return history[-50:]
    def public_payload(self,u,row):
        full=object_field(row['snapshot']);keys=['requirementTitle','title','content','recipientName','attachments']
        if row['kind'] in {'baseline','verification'}:keys+=['description','acceptanceCriteria']
        snapshot={k:full.get(k) or ([] if k=='attachments' else '') for k in keys}
        if row['kind']=='baseline' and full.get('deliveryBaseline'):snapshot['deliveryBaseline']=full['deliveryBaseline']
        response=self.shared.message(u,row.get('responseMessageId') or '')
        return {'id':row['id'],'kind':row['kind'],'kindLabel':KINDS[row['kind']],'status':row['status'],'expiresAt':row['expiresAt'],'snapshot':snapshot,
            'outcome':row.get('outcome') or '','outcomeLabel':OUTCOMES.get(row.get('outcome'),''),'submittedAt':row.get('submittedAt') or '',
            'response':{'content':response['content'],'attachments':self.files.list(u,'collaboration_message',response['id'])} if response else None,
            'draftAttachments':self.files.list(u,'collaboration_link',row['id'])}
    def internal_payload(self,u,row,edit=False):
        result=self.public_payload(u,row);result['snapshot']=object_field(row['snapshot']);result.update({k:row.get(k) for k in ['collaborationId','createdAt','createdByName','responseMessageId']})
        if row['status']=='pending' and row['expiresAt']<=self.flow.clock.now():result['status']='expired'
        if edit and result['status']=='pending':result['link']=self.flow.notices.base+'/#/entry/collaboration?token='+row['token']
        if row['kind']=='verification':
            feedback=self.delivery.feedback(u,round_id=row['id'])
            if feedback:result['feedback']=self.delivery.feedback_payload(feedback)
        return result
    def template(self,u,req,project):
        sources=self.demand.source_demands(u,req['id']);key=(sources[-1].get('solutionType') if sources else '') or (project or {}).get('solutionType') or 'custom'
        # Lifecycle uses its historical aliases (custom remains custom).
        aliases={**self.flow.v['DELIVERY_STANDARD_TEMPLATE_ALIASES'],'custom':'custom'};key=aliases.get(key,key)
        return key if key in self.flow.v['DELIVERY_STANDARD_TEMPLATE_LABELS'] else 'custom'
    def list_baselines(self,u,p,rid):
        req,project=self.resource(u,p,rid);template=self.template(u,req,project)
        return {'canEdit':self.flow.identity.can_edit(u,p,req,'requirement'),'templateType':template,
            'templateLabel':self.flow.v['DELIVERY_STANDARD_TEMPLATE_LABELS'].get(template,'通用交付标准'),'items':[self.delivery.baseline_payload(x) for x in self.delivery.baselines(u,rid)]}
    def create_baseline(self,u,p,rid,data):
        req,project=self.resource(u,p,rid,True);content={str(k):str(v or '').strip()[:10000] for k,v in (data.get('content') or {}).items()} if isinstance(data.get('content'),dict) else {}
        need(all(content.get(k) for k in ['scope','scenarios','expected']),'请至少填写交付范围、验证场景和预期结果')
        template=str(data.get('templateType') or self.template(u,req,project)).strip();template=template if template in self.flow.v['DELIVERY_STANDARD_TEMPLATE_LABELS'] else 'custom'
        recipient=str(data.get('recipientName') or req.get('requester') or '').strip();need(recipient and len(recipient)<=120,'请填写业务确认人')
        old=self.delivery.baselines(u,rid);latest=old[0] if old else None;version=int((latest or {}).get('version') or 0)+1;now=self.flow.clock.now()
        summary='交付范围：'+content['scope']+'\n验证场景：'+content['scenarios']+'\n预期结果：'+content['expected']
        row={'id':self.flow.ids.new('rdb',18),'requirementId':rid,'version':version,'templateType':template,'content':json.dumps(content,ensure_ascii=False),
            'status':'pending_confirmation' if data.get('send') else 'draft','recipientUserId':str(data.get('recipientUserId') or '').strip(),'recipientName':recipient,
            'confirmationLinkId':'','supersedesId':(latest or {}).get('id') or '','createdByUserId':p.userId,'createdByName':p.name,'createdAt':now,'updatedAt':now,'confirmedAt':''}
        if latest and latest['status'] in {'draft','pending_confirmation','confirmed','changes_requested'}:self.delivery.change_baseline(u,latest['id'],{'status':'superseded','updatedAt':now})
        self.delivery.add_baseline(u,row);self.flow.work.internal_change(u,rid,{'acceptanceCriteria':summary[:10000],'updatedAt':now});link=None
        if data.get('send'):
            link=self.create_link(u,p,rid,{'clientKey':'baseline-'+row['id'],'kind':'baseline','title':f"上线前交付标准 V{version}：{req.get('title') or rid}",
                'content':summary,'recipientName':recipient,'validDays':data.get('validDays',14),'attachmentIds':data.get('attachmentIds') or [],'baselineId':row['id']})
            self.delivery.change_baseline(u,row['id'],{'confirmationLinkId':link['id'],'updatedAt':self.flow.clock.now()})
        self.flow.audit.record(u,p,'L3',rid,req['title'],'delivery_baseline_create',f'创建上线前交付标准 V{version}'+('并发起业务确认' if link else ''),after={'baselineId':row['id'],'version':version,'templateType':template})
        return {**self.delivery.baseline_payload(self.delivery.baseline(u,row['id'])),'link':(link or {}).get('link') if link else '','requestId':(link or {}).get('id') if link else ''}
    def set_status(self,u,p,req,status,reason):
        if req['status']==status:return
        self.flow.work.change_log(u,p,req['id'],'状态流转','status',req['status'],status,reason)
        self.flow.work.internal_change(u,req['id'],{'status':status,'updatedAt':self.flow.clock.now(),'completedAt':self.flow.clock.now() if status=='已交付' else ''})
    def sync_todo(self,u,p,row,req,replied=False,send=False):
        f=self.flow;f.inbox.close_lifecycle(u,thread_id=row['collaborationId']);thread=self.shared.source(u,'business_collaboration_items',row['collaborationId'])
        if replied:thread={**thread,'recipientUserId':row['createdByUserId'],'recipientName':row['createdByName'],'content':KINDS[row['kind']]+'已回复，请查看结果并继续处理'}
        todo=f.inbox.collaboration_todo(u,p,thread,req)
        if send and todo and todo.get('recipientUserId'):
            notice={'action':{'materials':'请补充资料','baseline':'请确认交付范围','verification':'请完成业务验证'}[row['kind']],
                'url':f.notices.base+'/#/entry/collaboration?token='+row['token'],'topic':object_field(row['snapshot']).get('title') or thread['title'],
                'content':thread.get('content') or todo['message'],'public':True}
            def after():
                try:sent=f.notices.collaboration(todo,notice)
                except Exception:sent=False
                if sent:
                    with f.uow_factory() as write:f.inbox.mark_sent(write,todo['id'])
            u.events.append(AfterCommitAction(after))
    def create_link(self,u,p,rid,data):
        f=self.flow;req,project=self.resource(u,p,rid,True);key=str(data.get('clientKey') or '').strip();need(key and len(key)<=120,'请求编号必填，最多 120 字')
        previous=self.delivery.previous_key(u,rid,key)
        if previous:return self.internal_payload(u,previous,True)
        kind=str(data.get('kind') or '');need(kind in KINDS,'请选择资料请求、范围确认或业务验证')
        title=str(data.get('title') or '').strip();content=str(data.get('content') or '').strip();need(title and len(title)<=300,'主题必填，最多 300 字');need(content and len(content)<=10000,'本轮说明必填，最多 10000 字')
        recipient=str(data.get('recipientName') or req.get('requester') or '').strip();need(recipient and len(recipient)<=120,'请填写业务确认人')
        bid=str(data.get('baselineId') or '').strip();baseline=self.delivery.baseline(u,bid) if bid else None
        if baseline and baseline['requirementId']!=rid:baseline=None
        need(kind!='baseline' or baseline,'请先保存上线前交付标准')
        need(kind!='verification' or not baseline or baseline['status']=='confirmed','请先完成业务对上线前交付标准的确认')
        need(kind!='verification' or req.get('acceptanceCriteria') or baseline,'请先在 L3 详情补充验收标准')
        available={x['id']:x for x in self.evidence(u,rid)};attachment_ids=data.get('attachmentIds') or []
        need(isinstance(attachment_ids,list) and len(attachment_ids)<=30 and all(isinstance(x,str) and x in available for x in attachment_ids),'分享材料必须来自当前 L3，最多 30 个附件',403)
        try:days=int(data.get('validDays',14))
        except (ValueError,TypeError):days=0
        need(1<=days<=90,'有效天数应为 1 至 90')
        tid=str(data.get('collaborationId') or '');thread=self.shared.source(u,'business_collaboration_items',tid) if tid else None
        need(not tid or thread and thread['requirementId']==rid and thread['direction']=='it_to_business','请选择当前 L3 的 IT 发起协作主题')
        need(not thread or self.shared.can_handle(u,p,thread),'无权继续该协作',403)
        history=self.history(u,p,rid);links=self.delivery.links(u,rid)
        if kind=='verification':
            for old in self.delivery.revoke(u,[x for x in links if x['kind']=='verification']):f.inbox.close_lifecycle(u,thread_id=old['collaborationId'])
        if thread:
            self.delivery.revoke(u,[x for x in links if x['collaborationId']==tid]);message=self.shared.insert_message(u,thread,p,'it',content,'delivery' if kind=='verification' else 'message')
            self.shared.change_thread(u,tid,{'status':'waiting_business','recipientName':recipient,'recipientUserId':'','updatedAt':f.clock.now(),'closedAt':''})
        else:
            thread=self.shared.insert_thread(u,p,req,{'kind':'resource_request' if kind=='materials' else 'acceptance','title':title,'content':content,'status':'waiting_business','sourceType':'lifecycle'},'it_to_business',recipient,'')
            tid=thread['id'];message=self.shared.projected_messages(u,thread)[0]
        snapshot={'requirementTitle':req['title'],'description':req.get('description') or '','acceptanceCriteria':req.get('acceptanceCriteria') or '',
            'workType':req.get('type') or '','assignee':req.get('assignee') or '','expectedDeliveryTime':req.get('expectedDeliveryTime') or '',
            'title':title,'content':content,'recipientName':recipient,'attachments':[self.files.meta(available[x]) for x in dict.fromkeys(attachment_ids)],'history':history}
        if baseline:snapshot.update(baselineId=baseline['id'],baselineVersion=baseline['version'],deliveryBaseline=self.delivery.baseline_payload(baseline))
        now=f.clock.now();expires=(datetime.strptime(now,'%Y-%m-%d %H:%M:%S')+timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        row=self.delivery.add_link(u,{'id':f.ids.new('clr',32),'requirementId':rid,'collaborationId':tid,'requestMessageId':message['id'],
            'kind':kind,'token':secrets.token_urlsafe(32),'clientKey':key,'snapshot':json.dumps(snapshot,ensure_ascii=False),'status':'pending','expiresAt':expires,
            'createdByUserId':p.userId,'createdByName':p.name,'createdAt':now})
        self.sync_todo(u,p,row,req,send=True)
        if kind=='verification' and req['status'] not in {'已交付','已关闭'}:self.set_status(u,p,req,'待交付','已生成业务验证链接')
        f.audit.record(u,p,'L3',rid,req['title'],'collaboration_link_create','生成'+KINDS[kind],after={'requestId':row['id'],'collaborationId':tid})
        return self.internal_payload(u,row,True)
    def submit(self,u,token,data):
        f=self.flow;row=self.token_link(u,token,lock=True)
        if row['status']=='submitted':return self.public_payload(u,row)
        outcome=str(data.get('outcome') or '');need(outcome in {'materials':{'provided'},'baseline':{'confirmed','changes'},'verification':{'passed','changes'}}[row['kind']],'请选择本轮确认结果')
        content=str(data.get('content') or '').strip();feedback_type=str(data.get('feedbackType') or '').strip();requested=str(data.get('requestedTitle') or '').strip()[:180]
        if outcome=='changes' and row['kind']=='verification':need(feedback_type in FEEDBACK_TYPES,'请选择本次修改的类型')
        attachments=self.files.list(u,'collaboration_link',row['id']);need(len(content)<=10000 and (outcome!='changes' or content) and (outcome!='provided' or content or attachments),'请补充资料或修改说明，文字最多 10000 字')
        snapshot=object_field(row['snapshot']);p=Principal(name=snapshot['recipientName']);message_content=OUTCOMES[outcome]+('：'+content if content else '')
        if outcome=='changes' and row['kind']=='verification':message_content='修改类型：'+FEEDBACK_TYPES[feedback_type]+'\n'+message_content+('\n新需求标题：'+requested if requested else '')
        thread=self.shared.source(u,'business_collaboration_items',row['collaborationId']);message=self.shared.insert_message(u,thread,p,'business',message_content,'issue' if outcome=='changes' else 'acceptance')
        self.files.move_owner(u,'collaboration_link',row['id'],'collaboration_message',message['id']);now=f.clock.now()
        self.delivery.change_link(u,row['id'],{'status':'submitted','outcome':outcome,'responseMessageId':message['id'],'submittedAt':now})
        self.shared.change_thread(u,thread['id'],{'status':'waiting_it','response':message_content,'respondedAt':now,'updatedAt':now})
        req=f.work.requirement(u,row['requirementId'],True);bid=snapshot.get('baselineId') or ''
        if bid and row['kind']=='baseline':self.delivery.change_baseline(u,bid,{'status':'confirmed' if outcome=='confirmed' else 'changes_requested','confirmedAt':now if outcome=='confirmed' else '','updatedAt':now})
        route,routed='',''
        if outcome=='changes' and row['kind']=='verification':
            route=DEFAULT_ROUTES[feedback_type];routed=req['id'];status='pending'
            if req['status']=='待交付':self.set_status(u,p,req,'进行中','业务交付反馈：'+FEEDBACK_TYPES[feedback_type])
            if route in {'new_l3_feature','new_l3_restructure'}:routed=self.followup(u,p,req,feedback_type,content,requested);status='created'
            elif route in {'same_l3_rework','same_l3_improvement'}:status='routed'
            self.delivery.add_feedback(u,{'id':f.ids.new('rdf',18),'requirementId':req['id'],'deliveryRoundId':row['id'],'baselineId':bid,
                'feedbackType':feedback_type,'routeType':route,'content':content,'requestedTitle':requested,'routedRequirementId':routed,'status':status,
                'submittedByUserId':'','submittedByName':p.name,'createdAt':now,'updatedAt':now,'resolvedAt':''})
        self.sync_todo(u,p,row,req,True)
        f.audit.record(u,p,'L3',req['id'],req['title'],'collaboration_link_submit',OUTCOMES[outcome]+('，分流：'+FEEDBACK_ROUTES[route] if route else ''),after={'requestId':row['id'],'messageId':message['id'],'feedbackType':feedback_type,'routeType':route,'routedRequirementId':routed})
        return self.public_payload(u,self.delivery.link(u,row['id']))
    def deliver(self,u,p,rid,data):
        f=self.flow;req,project=self.resource(u,p,rid,True);key=str(data.get('clientKey') or '').strip();need(key and len(key)<=120,'交付编号必填，最多 120 字')
        previous=next((x for x in f.postlaunch.operations(u,rid) if x.get('deliveryRoundId')==key),None)
        if previous:return self.operation_payload(u,previous)
        aid=str(data.get('acceptanceRequestId') or '');exemption=str(data.get('verificationExemption') or '').strip();snapshot={k:req.get(k) or '' for k in ['description','acceptanceCriteria','title','type']}
        if aid:
            accepted=self.delivery.link(u,aid);need(accepted and accepted['requirementId']==rid and accepted['kind']=='verification' and accepted['status']=='submitted' and accepted['outcome']=='passed','请选择本 L3 已通过的业务验证')
            need(not f.postlaunch.acceptance_used(u,aid),'这次业务验证已用于交付，请为新交付发起新一轮验证',409);snapshot=object_field(accepted['snapshot'])
            need(all(snapshot.get(k,'')==(req.get(k) or '') for k in ['description','acceptanceCriteria']),'范围或验收标准已变更，请重新验证',409)
            latest=next((x for x in self.delivery.links(u,rid) if x['kind']=='verification' and x['status']!='revoked'),None)
            need(latest and latest['id']==aid,'已有后续验证轮次，请使用最新验证结果',409)
        else:need(exemption and len(exemption)<=2000,'本次无需业务验证时，请说明交付依据（最多 2000 字）')
        date=str(data.get('deliveryDate') or f.clock.now()[:10]);use=str(data.get('useStartDate') or date)
        try:datetime.strptime(date,'%Y-%m-%d');datetime.strptime(use,'%Y-%m-%d')
        except ValueError:need(False,'请填写有效的交付和使用开始日期')
        owner=str(data.get('businessOwnerName') or req.get('requester') or (project or {}).get('businessOwner') or '').strip()[:120]
        target={**req,'requester':owner,'projectTargetEndDate':(project or {}).get('targetEndDate') or ''}
        operation,new=f.postlaunch.create(u,p,target,'requirement',{**data,'deliveryRoundId':key,'deliveryDate':date,'useStartDate':use,'businessOwnerName':owner},
            str(data.get('businessOwnerUserId') or '').strip()[:120] or f.identity.person_id(u,owner))
        if new:
            f.postlaunch.attach_requests(u,operation['id'],f.value.schedule(u,p,operation,f.value.eligible(u,req)))
            f.audit.record(u,p,'L3',rid,req['title'],'postlaunch_start','建立交付后运营记录',after=f.postlaunch.get(u,operation['id']))
        operation=f.postlaunch.change(u,operation['id'],{'acceptanceRequestId':aid,'acceptanceSnapshot':json.dumps(snapshot,ensure_ascii=False),'verificationExemption':exemption})
        self.set_status(u,p,req,'已交付','IT 完成交付：'+str(data.get('notes') or exemption or '业务验证通过'))
        if aid:
            self.shared.change_thread(u,accepted['collaborationId'],{'status':'resolved','closedAt':f.clock.now(),'updatedAt':f.clock.now()});f.inbox.close_lifecycle(u,thread_id=accepted['collaborationId'])
        f.inbox.close_lifecycle(u,rid=rid,assigned_only=True)
        f.audit.record(u,p,'L3',rid,req['title'],'lifecycle_delivery','IT 完成交付',after={'operationId':operation['id'],'acceptanceRequestId':aid,'exemption':exemption})
        return self.operation_payload(u,operation)
    def followup(self,u,p,req,feedback_type,content,title):
        project=self.flow.portfolio.project(u,req.get('projectId') or '') or {}
        actor=Principal(userId=req.get('createdByUserId') or p.userId,name=req.get('createdByName') or req.get('assignee') or p.name or '系统')
        created=self.flow.work.feedback_requirement(u,actor,req,project,feedback_type,content,title)
        self.flow.audit.record(u,actor,'L3',created['id'],created['title'],'create_from_delivery_feedback','由交付反馈创建'+FEEDBACK_TYPES.get(feedback_type,'新需求')+' L3',after={'sourceRequirementId':req['id'],'feedbackType':feedback_type})
        self.flow.assign_todos(u,actor,{**created,'pname':project.get('name')},'交付反馈已分流为新的 L3，请确认范围和验收标准');return created['id']
    def route_feedback(self,u,p,identifier,data):
        feedback=self.delivery.feedback(u,identifier);need(feedback,'交付反馈不存在',404);req,_=self.resource(u,p,feedback['requirementId'],True)
        route=str(data.get('routeType') or '').strip();need(route in {'same_l3_rework','same_l3_improvement','new_l3_feature','new_l3_restructure'},'请选择有效的反馈处理路由')
        if feedback.get('status') not in {'pending',''}:return self.delivery.feedback_payload(feedback)
        kind='new_feature' if route=='new_l3_feature' else 'requirement_change' if route=='new_l3_restructure' else feedback.get('feedbackType') or 'other'
        rid=req['id']
        if req['status']=='待交付' or route in {'same_l3_rework','same_l3_improvement'} and req['status'] in {'已交付','已上线'}:self.set_status(u,p,req,'进行中','IT 确认交付反馈处理路由')
        if route.startswith('new_l3_'):rid=self.followup(u,p,req,kind,feedback.get('content') or '',feedback.get('requestedTitle') or '')
        result=self.delivery.route_feedback(u,identifier,route,rid);row=self.delivery.link(u,feedback.get('deliveryRoundId') or '')
        if row:self.sync_todo(u,p,row,req,True)
        self.flow.audit.record(u,p,'L3',req['id'],req['title'],'delivery_feedback_route','IT 确认交付反馈分流：'+FEEDBACK_ROUTES[route],after={'feedbackId':identifier,'routeType':route,'routedRequirementId':rid})
        return self.delivery.feedback_payload(result)
    def revoke(self,u,p,identifier):
        row=self.delivery.link(u,identifier);need(row,'链接不存在',404);req,_=self.resource(u,p,row['requirementId'],True)
        if self.delivery.revoke(u,[row]):
            self.flow.inbox.close_lifecycle(u,thread_id=row['collaborationId']);self.flow.audit.record(u,p,'L3',req['id'],req['title'],'collaboration_link_revoke','撤销业务链接',after={'requestId':identifier})
        return {'ok':True}
    def upload(self,u,token,key,name,mime,content):
        row=self.token_link(u,token,True,True);need(key and len(key)<=120,'附件请求编号不合法');identifier='clat'+hashlib.sha256((row['id']+':'+key).encode()).hexdigest()[:32]
        old=self.files.get_any(u,identifier)
        if old:return self.files.meta(old)
        from pathlib import PurePath
        need(PurePath(name or 'attachment').suffix.lower() in self.files.extensions,'不支持的附件类型')
        need(len(content)<=50*1024*1024,'单个附件不能超过 50MB',413);need(content,'不能上传空文件')
        need(len(self.files.list(u,'collaboration_link',row['id']))<10,'本轮最多上传 10 个附件')
        self.files.save(u,Principal(name=object_field(row['snapshot'])['recipientName']),'collaboration_link',row['id'],name,mime,content,identifier)
        return self.files.meta(self.files.get_any(u,identifier))
    def download(self,u,token,identifier):
        row=self.token_link(u,token);snapshot=object_field(row['snapshot']);allowed={x['id'] for x in snapshot.get('attachments',[])}
        for kind,owner in [('collaboration_link',row['id']),('collaboration_message',row.get('responseMessageId') or '')]:allowed.update(x['id'] for x in self.files.list(u,kind,owner))
        file=self.files.get(u,identifier);need(identifier in allowed and file,'附件不在本次链接的范围内',404);return file,self.files.download(file)
    def detail(self,u,p,rid):
        req,_=self.resource(u,p,rid);edit=self.flow.identity.can_edit(u,p,req,'requirement');sources=[]
        for row in self.demand.source_demands(u,rid):
            item={k:row.get(k) for k in ['id','title','description','evaluationReason','evaluationNotes','requesterName','status']};item['attachments']=self.files.list(u,'demand_pool',row['id'])
            item['reviews']=[{k:x.get(k) for k in ['reviewerName','decision','prioritySuggestion','comment','submittedAt']} for x in self.demand.rows(u,'demand_pool_reviews',row['id'])]
            item['pocs']=self.demand.rows(u,'demand_pool_pocs',row['id']);item['evaluations']=[{k:x.get(k) for k in ['phase','decision','reason','notes','operatorName','createdAt']} for x in self.demand.rows(u,'demand_pool_evaluations',row['id'])];sources.append(item)
        operations=[]
        for row in self.flow.postlaunch.operations(u,rid):
            item=self.operation_payload(u,row);item['issues']=self.flow.postlaunch.related(u,'postlaunch_issues',row['id']);item['knowledge']=self.flow.postlaunch.related(u,'postlaunch_knowledge',row['id']);operations.append(item)
        return {'canEdit':edit,'sources':sources,'baselines':[self.delivery.baseline_payload(x) for x in self.delivery.baselines(u,rid)],
            'links':[self.internal_payload(u,x,edit) for x in self.delivery.links(u,rid)],'operations':operations,'attachments':[self.files.meta(x) for x in self.evidence(u,rid)]}
