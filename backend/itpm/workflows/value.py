from itpm.core.errors import require
from itpm.core.ports import Principal
from itpm.core.events import AfterCommitAction


class ValueWorkflow:
    def __init__(self,value,flow,demand,postlaunch,gateway):
        self.value,self.flow,self.demand,self.postlaunch,self.gateway=value,flow,demand,postlaunch,gateway
    def target(self,u,row):
        if row.get('demandId'):
            demand=self.demand.get(u,row['demandId'])
            if demand:return demand
        if row.get('requirementId'):
            req=self.flow.work.requirement(u,row['requirementId']);project=self.flow.portfolio.raw_project(u,(req or {}).get('projectId') or '')
            if req:return {k:req.get(k) or '' for k in ['id','title','description','department','status','requirementId','projectId']}|{'projectName':(project or {}).get('name') or req.get('projectName') or '',
                'requesterName':req.get('requester') or '','requesterUserId':'','requirementId':req['id']}
        if row.get('projectId'):
            project=self.flow.portfolio.project(u,row['projectId'])
            if project:return {k:project.get(k) or '' for k in ['id','description','department','status']}|{'title':project.get('name') or '','projectName':project.get('name') or '',
                'requesterName':project.get('businessOwner') or '','requesterUserId':'','projectId':project['id']}
        return None
    def scope(self,row):
        key=next((k for k in ['demandId','requirementId','projectId'] if row.get(k)), 'demandId')
        return {'demandId':'DEMAND_POOL','requirementId':'L3','projectId':'L2'}[key],row.get(key) or ''
    def payload(self,row,include=True):return self.value.request_payload(row,self.flow.v,self.flow.notices.base+'/',include)
    def context(self,u,token):
        row=self.value.request(u,token=token);require(row,'成果回访链接已失效或不存在',404,'NOT_FOUND');target=self.target(u,row);require(target,'关联需求或项目不存在',404,'NOT_FOUND')
        card=self.value.card(u,row);operation=self.postlaunch.operation_for_request(u,row['id'])
        if operation:
            card=card or {'baseline':{},'expected':{},'targetMet':''}
            for stage in ['day7','day30']:
                request=self.value.request(u,operation.get(stage+'RequestId') or '');card[stage]=self.payload(request,False)['responseSnapshot'] if request else {}
        return {'request':self.payload(row,False),'demand':target,'stage':self.flow.v['DEMAND_POOL_OUTCOME_STAGES'].get(row['stage'],self.flow.v['DEMAND_POOL_OUTCOME_STAGES']['goal']),
            'valueCard':card or {'status':'draft','baseline':{},'expected':{},'day7':{},'day30':{},'targetMet':''}}
    def submit(self,u,data):
        row=self.value.request(u,token=str(data.get('token') or '').strip(),lock=True);require(row,'成果回访链接已失效或不存在',404,'NOT_FOUND');target=self.target(u,row);require(target,'关联需求或项目不存在',404,'NOT_FOUND')
        if row['status']=='submitted':return self.payload(row,False)
        status,issue,summary=self.value.submit(u,row,data,target)
        if row['stage'] in {'day7','day30'} and issue in {'有问题','严重'}:self.postlaunch.callback_issue(u,row,issue,summary)
        p=Principal(userId=str(row.get('recipientUserId') or target.get('requesterUserId') or '').strip()[:120],name=str(row.get('recipientName') or target.get('requesterName') or '').strip()[:120])
        scope,sid=self.scope(row);self.flow.audit.record(u,p,scope,sid,target.get('title') or sid,'outcome_submit','业务提交'+self.flow.v['DEMAND_POOL_OUTCOME_STAGE_LABELS'].get(row['stage'],row['stage']),
            after={'requestId':row['id'],'stage':row['stage'],'status':status})
        return {'request':self.payload(self.value.request(u,row['id']),False),'status':status,'stage':row['stage']}
    def notice(self,row,target):
        require(row.get('recipientUserId'),'成果回访对象缺少钉钉 UserId，无法发送通知')
        stage=self.flow.v['DEMAND_POOL_OUTCOME_STAGES'].get(row['stage'],self.flow.v['DEMAND_POOL_OUTCOME_STAGES']['goal'])
        link=self.flow.notices.base+'/#/entry/demand-outcome?token='+row['token']
        message='\n'.join([f"## {stage['label']}通知",f"- 需求：{target.get('title') or row.get('demandId') or '-'}",f"- 提交人：{target.get('requesterName') or '-'}",'',stage['description'],'',f"[打开{stage['label']}页面]({link})"])
        self.gateway.send_markdown_to_users([row['recipientUserId']],stage['label'],message)
    def after_send(self,u,p,row,target,result,audit=False):
        def after():
            sent=True;error=''
            try:self.notice(row,target)
            except Exception as exc:sent=False;error=str(exc)[:2000]
            with self.flow.uow_factory() as write:
                self.value.notification_result(write,row['id'],sent,error);saved=self.value.request(write,row['id'])
                if audit:
                    scope,sid=self.scope(row);self.flow.audit.record(write,p,scope,sid,target.get('title') or sid,'outcome_request_send',
                        '直接发送'+self.flow.v['DEMAND_POOL_OUTCOME_STAGE_LABELS'].get(row['stage'],'上线反馈'),
                        after={'requestId':row['id'],'notificationStatus':saved['notificationStatus'],'sentAt':saved['sentAt'],'notificationError':saved['notificationError']})
                result.clear();result.update(self.payload(saved))
        u.events.append(AfterCommitAction(after))
    def send(self,u,p,identifier):
        self.flow.identity.action(u,p,'demand_pool.manage');row=self.value.request(u,identifier);require(row,'上线反馈请求不存在',404,'NOT_FOUND')
        require(row['stage'] in {'day7','day30'},'只有 3 天回执和 30 天价值验证支持直接发送');require(row['status']!='submitted','该反馈已经提交，无需再次发送')
        target=self.target(u,row);require(target,'关联需求或项目不存在',404,'NOT_FOUND');result=self.payload(row);self.after_send(u,p,row,target,result,True);return result
    def view(self,u,p,identifier):
        self.flow.identity.action(u,p,'demand_pool.manage');row=self.value.request(u,identifier);require(row,'上线反馈请求不存在',404,'NOT_FOUND');require(row['status']=='submitted','只有已提交的业务反馈可以标记为已查看')
        if not row.get('viewedAt'):
            self.value.viewed(u,identifier);target=self.target(u,row) or {};scope,sid=self.scope(row)
            self.flow.audit.record(u,p,scope,sid,target.get('title') or sid,'outcome_viewed','查看'+self.flow.v['DEMAND_POOL_OUTCOME_STAGE_LABELS'].get(row['stage'],'上线反馈'),after={'requestId':identifier,'viewedAt':self.flow.clock.now()})
        return self.payload(self.value.request(u,identifier))
    def create(self,u,p,kind,identifier,data):
        self.flow.identity.action(u,p,'demand_pool.manage')
        if kind=='demand':target=self.demand.get(u,identifier);require(target,'需求池记录不存在',404,'NOT_FOUND');scope=('demandId',identifier)
        else:
            raw=self.flow.work.requirement(u,identifier) if kind=='requirement' else self.flow.portfolio.project(u,identifier)
            require(raw,'正式 L3 不存在或已归档' if kind=='requirement' else '正式 L2 不存在或已归档',404,'NOT_FOUND')
            target={**raw,'requesterName':raw.get('requester') if kind=='requirement' else raw.get('businessOwner') or '','requesterUserId':'','title':raw.get('title') if kind=='requirement' else raw.get('name') or ''}
            if kind=='requirement':target['projectName']=(self.flow.portfolio.project(u,raw.get('projectId')) or {}).get('name') or ''
            scope=('requirementId' if kind=='requirement' else 'projectId',identifier)
        row,new=self.value.create_request(u,p,scope,data,target,kind!='demand');result=self.payload(row)
        if new:
            label=self.flow.v['DEMAND_POOL_OUTCOME_STAGE_LABELS'][row['stage']] if kind=='demand' else {'goal':'上线前业务目标确认','day7':'3 天业务回访','day30':'30 天成果复盘'}[row['stage']]
            self.flow.audit.record(u,p,'DEMAND_POOL' if kind=='demand' else 'L3' if kind=='requirement' else 'L2',identifier,target['title'],'outcome_request','发起'+label,
                after={'requestId':row['id'],'stage':row['stage'],'recipientName':row['recipientName'],'scheduledAt':row['scheduledAt']})
            if data.get('sendNow',True) and not row.get('scheduledAt'):self.after_send(u,p,row,target,result)
        return result
    def list(self,u,p,kind,identifier):
        self.flow.identity.authenticated(p)
        if kind=='demand':
            target=self.demand.get(u,identifier);require(self.demand.visible(u,p,target),'需求池记录不存在或无权访问',404,'NOT_FOUND')
        else:
            target=self.flow.work.requirement(u,identifier) if kind=='requirement' else self.flow.portfolio.project(u,identifier)
            require(target,'正式 L3 不存在或已归档' if kind=='requirement' else '正式 L2 不存在或已归档',404,'NOT_FOUND')
        key={'demand':'demandId','requirement':'requirementId','project':'projectId'}[kind]
        return [self.payload(x,self.demand.manage(u,p)) for x in self.value.requests(u,key,identifier)]
