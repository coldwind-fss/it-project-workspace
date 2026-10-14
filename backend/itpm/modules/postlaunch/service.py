import json
from itpm.core.errors import require
from itpm.core.json_fields import object_field
from itpm.infrastructure.database import Repository
from .public import Postlaunch,date_plus
from .rules import lifecycle,metric_status,efficiency,in_period,date,metric,unique_requests,pending_count


class PostlaunchService(Postlaunch):
    def __init__(self,db,clock,ids,v,identity,work,portfolio,demand,value,delivery,audit,base):
        super().__init__(db,clock,ids)
        self.repo=Repository(db,['postlaunch_operations','postlaunch_issues','improvement_proposals','postlaunch_knowledge'])
        self.v,self.identity,self.work,self.portfolio,self.demand,self.value,self.delivery,self.audit,self.base=v,identity,work,portfolio,demand,value,delivery,audit,base
    def related(self,u,table,identifier):return self.repo.find(u,table,{'operationId':identifier},order=[('createdAt',True)])
    def operation_for_request(self,u,identifier):return next((x for x in self.operations(u) if identifier in {x.get('day7RequestId'),x.get('day30RequestId')}),None)
    def raw_target(self,u,kind,identifier):
        row=self.work.requirement(u,identifier) if kind=='requirement' else self.portfolio.project(u,identifier) if kind=='project' else None
        if row and kind=='requirement':
            project=self.portfolio.raw_project(u,row.get('projectId') or '');row={**row,'projectTargetEndDate':(project or {}).get('targetEndDate') or '',
                'projectName':(project or {}).get('name') or '','requester':row.get('requester') or (project or {}).get('businessOwner') or ''}
        return row
    def payload(self,u,row,joined=False):
        item=dict(row);req=self.work.requirement(u,row.get('requirementId') or '');project=self.portfolio.raw_project(u,row.get('projectId') or '')
        if joined:
            item.update(title=(req or {}).get('title'),requirementDepartment=(req or {}).get('department'),requirementExpectedDeliveryTime=(req or {}).get('expectedDeliveryTime'),
                projectName=(project or {}).get('name'),projectDepartment=(project or {}).get('department'),projectTargetEndDate=(project or {}).get('targetEndDate'),projectSolutionType=(project or {}).get('solutionType'))
            issues=self.related(u,'postlaunch_issues',row['id']);item.update(issueCount=len(issues),openIssueCount=sum(x['status']!='已关闭' for x in issues),
                proposalCount=len(self.related(u,'improvement_proposals',row['id'])),knowledgeCount=len(self.related(u,'postlaunch_knowledge',row['id'])))
        item['title']=item.get('title') or item.get('projectName') or item.get('requirementId') or item.get('projectId') or item['id']
        for key in ['issueCount','openIssueCount','proposalCount','knowledgeCount']:item[key]=int(item.get(key) or 0)
        item['projectType']=item.get('projectSolutionType') or item.get('solutionType') or '';item['actualDeliveryDate']=item.get('deliveryDate') or ''
        item['valueVerificationEligibility']=self.value.eligibility(u,req,row.get('requirementId') or '');item['valueVerificationEligible']=item['valueVerificationEligibility']['eligible']
        item['plannedDeliveryDate']=item.get('plannedDeliveryDate') or item.get('requirementExpectedDeliveryTime') or item.get('projectTargetEndDate') or ''
        accepted=self.delivery.link(u,row.get('acceptanceRequestId') or '');item['acceptanceOutcome']=(accepted or {}).get('outcome') or ''
        requests=[];keys='id stage status scheduledAt notificationStatus sentAt submittedAt viewedAt recipientUserId recipientName token responseSnapshot'.split()
        for key in ['day7RequestId','day30RequestId']:
            request=self.value.request(u,row.get(key) or '')
            if request:requests.append(self.value.request_payload({k:request.get(k) for k in keys},self.v,self.base))
        item['outcomeRequests']=sorted(requests,key=lambda x:x['stage']);item['day7Request']=next((x for x in requests if x['stage']=='day7'),None);item['day30Request']=next((x for x in requests if x['stage']=='day30'),None)
        card=self.value.card(u,row)
        if card:item['valueCard']={k:card.get(k) or ({} if k in {'baseline','expected','day7','day30'} else '') for k in ['id','status','baseline','expected','day7','day30','targetMet','ownerName']}
        item.update(lifecycle(item,self.clock.now()[:10]));item['metricDataStatus']=metric_status(card or {},item['day7Request'] or {},item['day30Request'] or {},self.clock.now()[:10])
        demand=self.demand.get(u,row.get('demandId') or '')
        if not demand:
            candidates=self.demand.source_demands(u,row.get('requirementId') or '') if row.get('requirementId') else self.demand.project_demands(u,row.get('projectId') or '')
            candidates.sort(key=lambda x:x['updatedAt'],reverse=True);demand=candidates[0] if candidates else None
        item['businessPriority']=(demand or {}).get('businessPriority') or '';item['businessPriorityLabel']={'urgent':'尽快处理','planned':'计划内处理','normal':'一般事项'}.get(item['businessPriority'],'暂无明确时间')
        return item
    def list(self,u,p,status='',department='',keyword=''):
        self.identity.authenticated(p);rows=sorted(self.operations(u),key=lambda x:(x['deliveryDate'],x['createdAt']),reverse=True);result=[]
        for row in rows:
            if row['status']=='cancelled' or status and row['status']!=status:continue
            item=self.payload(u,row,True)
            if department and (item['requirementDepartment'] if item['requirementDepartment'] is not None else item['projectDepartment'])!=department:continue
            if keyword and keyword not in (item.get('title') or '') and keyword not in (item.get('projectName') or ''):continue
            result.append(item)
            if len(result)>=500:break
        return result
    def detail(self,u,p,identifier):
        self.identity.authenticated(p);row=self.get(u,identifier);require(row,'运营记录不存在',404,'NOT_FOUND');result=self.payload(u,row,True)
        result.update(issues=self.related(u,'postlaunch_issues',identifier),proposals=self.related(u,'improvement_proposals',identifier),knowledge=self.related(u,'postlaunch_knowledge',identifier));return result
    def register(self,u,p,data):
        self.identity.action(u,p,'demand_pool.manage');kind=str(data.get('targetType') or ('requirement' if data.get('requirementId') else 'project')).strip();identifier=str(data.get('targetId') or data.get('requirementId') or data.get('projectId') or '').strip()
        target=self.raw_target(u,kind,identifier);require(target,'关联的 L2/L3 不存在或已归档',404,'NOT_FOUND');owner=str(data.get('businessOwnerName') or target.get('requester') or target.get('businessOwner') or '').strip()[:120]
        row,new=self.create(u,p,target,kind,{**data,'businessOwnerName':owner},str(data.get('businessOwnerUserId') or '').strip()[:120] or self.identity.person_id(u,owner))
        if new:
            self.attach_requests(u,row['id'],self.value.schedule(u,p,row,self.value.eligible(u,target if kind=='requirement' else None)))
            row=self.get(u,row['id']);self.audit.record(u,p,'L3' if kind=='requirement' else 'L2',identifier,target.get('title') or target.get('name') or '','postlaunch_start','建立交付后运营记录',after=row)
        return self.payload(u,row)
    def update_operation(self,u,p,identifier,data):
        self.identity.action(u,p,'demand_pool.manage');old=self.get(u,identifier);require(old,'运营记录不存在',404,'NOT_FOUND')
        def value(key,limit):return str(data.get(key,old.get(key) or '') or '').strip()[:limit]
        use=value('useStartDate',10) or old.get('deliveryDate') or '';require(not use or date_plus(use,3),'使用开始日期格式应为 YYYY-MM-DD');planned=value('plannedDeliveryDate',10);require(not planned or date(planned),'计划交付日期格式应为 YYYY-MM-DD')
        owner=value('businessOwnerName',120);row=self.change(u,identifier,{'plannedDeliveryDate':planned,'useStartDate':use,'businessOwnerUserId':value('businessOwnerUserId',120) or self.identity.person_id(u,owner),
            'businessOwnerName':owner,'day7DueDate':date_plus(use,3),'day30DueDate':date_plus(use,30),'status':str(data.get('status',old.get('status') or 'active'))[:30],'notes':value('notes',5000),'updatedAt':self.clock.now()})
        req=self.work.requirement(u,row.get('requirementId') or '');eligibility=self.value.eligibility(u,req,row.get('requirementId') or '')
        for stage in ['day7','day30']:
            rid=old.get(stage+'RequestId') or ''
            if rid:self.value.reschedule(u,rid,row,stage,eligibility['eligible'],eligibility['reason'])
            elif eligibility['eligible'] and owner and row.get(stage+'DueDate'):
                scheduled=self.value.schedule_one(u,p,row,stage);self.change(u,identifier,{stage+'RequestId':scheduled,'updatedAt':self.clock.now()})
        return self.payload(u,self.get(u,identifier))
    def callback_issue(self,u,request,level,summary):
        operation=self.operation_for_request(u,request['id'])
        if not operation or self.repo.find(u,'postlaunch_issues',{'sourceType':'outcome','sourceId':request['id']}):return
        now=self.clock.now();self.repo.add(u,'postlaunch_issues',{'id':self.ids.new('pli'),'operationId':operation['id'],'requirementId':operation.get('requirementId') or '',
            'projectId':operation.get('projectId') or '','sourceType':'outcome','sourceId':request['id'],'title':self.v['DEMAND_POOL_OUTCOME_STAGE_LABELS'].get(request['stage'],request['stage'])+'反馈待核实',
            'description':summary,'severity':'重大' if level=='严重' else '重要','status':'待核实','ownerUserId':'','ownerName':'','discoveredAt':now,
            'createdByUserId':request.get('recipientUserId') or '','createdByName':request.get('recipientName') or '','createdAt':now,'updatedAt':now})
    def create_issue(self,u,p,data):
        self.identity.action(u,p,'demand_pool.manage');op=self.get(u,str(data.get('operationId') or '').strip());require(op,'运营记录不存在',404,'NOT_FOUND')
        title=str(data.get('title') or '').strip()[:300];require(title,'请填写问题标题');severity=str(data.get('severity') or '一般').strip();require(severity in self.v['POSTLAUNCH_SEVERITIES'],'问题等级不合法')
        now=self.clock.now();owner=str(data.get('ownerName') or '').strip()[:120]
        row={'id':self.ids.new('pli'),'operationId':op['id'],'requirementId':op.get('requirementId') or '','projectId':op.get('projectId') or '',
            'sourceType':str(data.get('sourceType') or 'manual')[:40],'sourceId':str(data.get('sourceId') or '')[:120],
            'title':title,'description':str(data.get('description') or '').strip()[:10000],'severity':severity,'status':'待核实',
            'ownerUserId':str(data.get('ownerUserId') or '').strip()[:120] or self.identity.person_id(u,owner),'ownerName':owner,
            'dueDate':str(data.get('dueDate') or '')[:10],'resolution':'','rootCause':'','prevention':'','discoveredAt':str(data.get('discoveredAt') or now)[:40],
            'firstResponseAt':'','resolvedAt':'','reopenedCount':0,'createdByUserId':p.userId,'createdByName':p.name,'createdAt':now,'updatedAt':now,'closedAt':''}
        self.repo.add(u,'postlaunch_issues',row);self.audit.record(u,p,'L3' if row['requirementId'] else 'L2',row['requirementId'] or row['projectId'],title,'postlaunch_issue','登记交付后问题',after=row);return row
    def update_issue(self,u,p,identifier,data):
        self.identity.action(u,p,'demand_pool.manage');old=self.repo.get(u,'postlaunch_issues',identifier);require(old,'问题记录不存在',404,'NOT_FOUND');status=str(data.get('status') or old['status'] or '待核实').strip()
        require(status in self.v['POSTLAUNCH_ISSUE_STATUSES'],'问题状态不合法');now=self.clock.now()
        fields={k:str(data.get(k,old.get(k) or '') or '').strip()[:limit] for k,limit in [('ownerName',120),('ownerUserId',120),('resolution',10000),('rootCause',5000),('prevention',5000)]}
        fields.update(status=status,firstResponseAt=old.get('firstResponseAt') or (now if status in {'处理中','待验证','已关闭'} else ''),
            resolvedAt=(old.get('resolvedAt') or now) if status=='已关闭' else '',closedAt=(old.get('closedAt') or now) if status=='已关闭' else '',updatedAt=now)
        self.repo.change(u,'postlaunch_issues',identifier,fields);self.audit.record(u,p,'L3' if old.get('requirementId') else 'L2',old.get('requirementId') or old['projectId'],old.get('title') or identifier,'postlaunch_issue_update','问题更新为'+status,old,fields)
        return self.repo.get(u,'postlaunch_issues',identifier)
    def create_artifact(self,u,p,data,knowledge=False):
        self.identity.action(u,p,'demand_pool.manage');op=self.get(u,str(data.get('operationId') or '').strip());require(op,'运营记录不存在',404,'NOT_FOUND')
        title=str(data.get('title') or '').strip()[:300];content=str(data.get('content') or '').strip()[:30000]
        require(title and content if knowledge else title,'请填写知识标题和内容' if knowledge else '请填写改善提案标题');now=self.clock.now()
        row={'id':self.ids.new('plk' if knowledge else 'ipp'),'operationId':op['id'],'requirementId':op.get('requirementId') or '',
            'projectId':op.get('projectId') or '','title':title,'sourceType':str(data.get('sourceType') or ('postlaunch' if knowledge else 'manual'))[:40],
            'sourceId':str(data.get('sourceId') or '')[:120],'createdByUserId':p.userId,'createdByName':p.name,'createdAt':now,'updatedAt':now}
        if knowledge:row.update(content=content,artifactType=str(data.get('artifactType') or 'text')[:40],status=str(data.get('status') or 'draft')[:20],
            ownerUserId=p.userId,ownerName=p.name,publishedAt=now if data.get('status')=='published' else '')
        else:row.update(**{k:str(data.get(k) or '').strip()[:limit] for k,limit in [('problem',10000),('suggestion',10000),('expectedChange',5000)]},
            status=str(data.get('status') or '待评估')[:40],linkedRequirementId=str(data.get('linkedRequirementId') or '')[:80],
            ownerUserId=str(data.get('ownerUserId') or p.userId)[:120],ownerName=str(data.get('ownerName') or p.name)[:120],adoptedAt='')
        self.repo.add(u,'postlaunch_knowledge' if knowledge else 'improvement_proposals',row);return row
    def metrics(self,u,rows,period):
        ids=[x['id'] for x in rows if x.get('id')];today=self.clock.now()[:10];requests=unique_requests(x for r in rows for x in r['outcomeRequests'])
        due=[x for x in requests if x['status']!='cancelled' and x.get('scheduledAt') and x['scheduledAt'][:10]<=today and (x.get('sentAt') or x['notificationStatus'] in {'success','sent'})]
        planned=[x for x in rows if date(x.get('plannedDeliveryDate')) and x.get('useStartDate')];ontime=[x for x in planned if date(x['deliveryDate']) and date(x['deliveryDate'])<=date(x['plannedDeliveryDate'])]
        rids=list(dict.fromkeys(x['requirementId'] for x in rows if x.get('requirementId')))
        accepted=[x for rid in rids for x in self.delivery.links(u,rid) if x['kind']=='verification' and x['status']=='submitted']
        day7=[x for x in requests if x['stage']=='day7' and x['status']=='submitted' and x['responseSnapshot'].get('useStatus') and x['responseSnapshot'].get('satisfaction')]
        a=total=0;effids=[];seen_day30=set()
        for row in rows:
            identifier=(row.get('day30Request') or {}).get('id')
            if identifier and identifier in seen_day30:continue
            if identifier:seen_day30.add(identifier)
            achieved,count=efficiency(self.value.card(u,row),(row.get('day30Request') or {}).get('responseSnapshot') or {});a+=achieved;total+=count
            if count:effids.append(row['id'])
        specs=[('responseRate','回访响应率',sum(x['status']=='submitted' for x in due),len(due),len(requests),ids,'已提交回执 ÷ 已发送且到期的回执'),
            ('onTimeDeliveryRate','按期交付率',len(ontime),len(planned),len(rows),[x['id'] for x in planned],'实际交付日期 ≤ 计划交付日期'),
            ('acceptancePassRate','验收通过率',sum(x['outcome']=='passed' for x in accepted),len(accepted),len(accepted),ids,'通过的交付验收轮次 ÷ 已提交验收轮次'),
            ('satisfactionRate','满意率',sum(x['responseSnapshot']['satisfaction'] in {'满意','基本满意'} for x in day7),len(day7),len(day7),ids,'满意 + 基本满意 ÷ 有效 3 天回执'),
            ('usageRate','使用率',sum(x['responseSnapshot']['useStatus'] in {'已正常使用','正常使用','已开始使用但有问题'} for x in day7),len(day7),len(day7),ids,'已正常使用 + 已开始使用但有问题 ÷ 有效 3 天回执'),
            ('efficiencyRate','提效比例',a,total,total,effids,'有目标值且有实际值的结构化指标中达到目标的比例')]
        return [metric(key,label,n,d,period,c,i,note) for key,label,n,d,c,i,note in specs]
    def l2_rows(self,rows):
        groups={}
        for row in rows:
            key=row.get('projectId') or 'unassigned:'+row['id']
            if key not in groups:groups[key]={'key':key,'projectId':row.get('projectId') or '', 'name':row.get('projectName') or '未归属项目',
                'projectType':row.get('projectType') or '','department':row.get('projectDepartment') or row.get('requirementDepartment') or '',
                'businessPriority':row.get('businessPriority') or '','businessPriorityLabel':row.get('businessPriorityLabel') or '暂无明确时间',
                'operations':0,'l3Rows':[],'latestAt':row.get('updatedAt') or row.get('deliveryDate') or ''}
            group=groups[key];group['operations']+=1
            if not group['businessPriority'] and row.get('businessPriority'):group.update(businessPriority=row['businessPriority'],businessPriorityLabel=row['businessPriorityLabel'])
            item={'id':row.get('requirementId') or row['id'],'operationId':row['id'],'title':row.get('title') or '未命名事项'}
            for k in ['deliveryDate','plannedDeliveryDate','lifecycleStage','acceptanceOutcome','valueVerificationStatus','dataStatus']:item[k]=row.get(k) or ''
            for k in ['lifecycleProgress','openIssueCount']:item[k]=row.get(k) or 0
            for stage in ['day7','day30']:
                request=row.get(stage+'Request') or {};item[stage+'Status']=request.get('status') or '';item[stage+'SubmittedAt']=request.get('submittedAt') or ''
            group['l3Rows'].append(item)
            if str(row.get('updatedAt') or '')>str(group['latestAt']):group['latestAt']=row['updatedAt']
        for group in groups.values():
            statuses=[x['valueVerificationStatus'] for x in group['l3Rows']];group['l3Count']=len(statuses)
            group['valueVerificationStatus']='待整改' if '待整改' in statuses else '已完成' if statuses and all(x=='已完成' for x in statuses) else next((x for x in statuses if x and x!='未开始'),'未开始')
            group['lifecycleStage']=group['l3Rows'][0]['lifecycleStage'] if len(statuses)==1 else '多阶段'
        return sorted(groups.values(),key=lambda x:str(x['latestAt']),reverse=True)
    def dashboard(self,u,p,filters):
        rows=self.list(u,p,department=filters.get('department',''),keyword=filters.get('keyword',''));period=str(filters.get('period') or 'all').strip().lower()
        if period not in {'all','day','week','month','quarter','year'}:period='all'
        month=str(filters.get('deliveryMonth') or '').strip()[:7];rows=[x for x in rows if in_period(x['deliveryDate'],period,self.clock.now())]
        if month and len(month)==7:rows=[x for x in rows if x['deliveryDate'][:7]==month]
        for parameter,key in [('solutionType','projectType'),('lifecycleStage','lifecycleStage'),('valueStatus','valueVerificationStatus'),('businessPriority','businessPriority')]:
            if filters.get(parameter):rows=[x for x in rows if x.get(key)==filters[parameter]]
        excluded=sum(not x['valueVerificationEligible'] for x in rows);rows=[x for x in rows if x['valueVerificationEligible']];today=self.clock.now()[:10]
        summary={'operations':len(rows),'trial':sum(x['deliveryKind']=='试运行' for x in rows),'live':sum(x['deliveryKind'] in {'上线','已交付'} for x in rows),
            'openIssues':sum(x['openIssueCount'] for x in rows),'proposals':sum(x['proposalCount'] for x in rows),'knowledge':sum(x['knowledgeCount'] for x in rows)}
        for stage in ['day7','day30']:summary[stage+'Pending']=pending_count(rows,stage,today)
        return {'summary':summary,'metrics':self.metrics(u,rows,period),'l2Rows':self.l2_rows(rows),'rows':rows,'generatedAt':self.clock.now(),'excludedOperations':excluded,
            'filters':{'period':period,'deliveryMonth':month,**{k:filters.get(k,'') for k in ['department','solutionType','lifecycleStage','valueStatus','businessPriority']}}}
