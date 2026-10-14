import json
from itpm.core.errors import require
from itpm.core.json_fields import object_field,list_field
from itpm.modules.demand.public import text
from itpm.modules.portfolio.public import solution_type


class DemandWorkflow:
    def __init__(self,demand,flow,delivery,value):
        self.demand,self.flow,self.delivery,self.value=demand,flow,delivery,value
    def specs(self,data,demand,stored):
        raw=data.get('parallelL3s',data.get('units'))
        if text(data,'mode','create_l2' if demand.get('intakeLevel')=='L2' else 'create')=='create' and (raw is None or raw==[]):
            explicit=any(x.get('itDecision') for x in stored);selected=[x for x in stored if not explicit or x.get('itDecision') in {'implement','poc'}]
            if selected:raw=[{**x,'branchId':x['id']} for x in selected]
        if raw is None:return []
        require(isinstance(raw,list),'独立 L3 工作项清单格式不正确');result=[]
        for i,item in enumerate(raw,1):
            require(isinstance(item,dict),f'独立 L3 工作项清单第 {i} 项格式不正确');title=text(item,'title',limit=300);require(title,f'请补充第 {i} 个独立 L3 工作项标题')
            result.append({'branchId':text(item,'branchId',text(item,'id')),'title':title,'scope':text(item,'scope',limit=5000),
                'acceptanceDelta':text(item,'acceptanceDelta',limit=5000),'itemKind':text(item,'itemKind',text(data,'itemKind','feature')),
                'valueMetricKeys':[str(x or '').strip()[:160] for x in item.get('valueMetricKeys',[]) if str(x or '').strip()][:30] if isinstance(item.get('valueMetricKeys'),list) else []})
        return result
    def convert(self,u,p,did,data):
        d,f=self.demand,self.flow;f.identity.action(u,p,'demand_pool.manage');demand=d.get(u,did,True);require(demand,'需求池记录不存在',404,'NOT_FOUND')
        if demand['status']=='converted' and demand.get('requirementId'):
            payload=d.payload(u,p,demand);return {'demand':payload,'requirementId':demand['requirementId'],'requirementIds':payload['requirementIds'] or [demand['requirementId']],'requirementTitle':demand.get('requirementTitle') or ''}
        require(demand['status'] in {'awaiting_confirmation','business_confirmed','ready_for_l3'},'只有 IT 综合决策为“实施”的提报可以正式创建或关联 L2/L3')
        confirmation=d.latest_confirmation(u,did);require(confirmation,'正式立项前必须先完成上线前交付与价值确认，请发起确认链接并等待业务提交')
        mode=text(data,'mode','create_l2' if demand.get('intakeLevel')=='L2' else 'create');require(mode in {'create','create_l2','link'},'不支持的正式关联方式')
        specs=self.specs(data,demand,d.branch_rows(u,did));require(mode!='create_l2' or len(specs)<=1,'新建 L2 模式先生成一个初始建设 L3；如同一提报要拆成多个 L3，请先选择已有 L2')
        content=object_field(confirmation.get('content'));acceptance=content.get('expected') or confirmation.get('acceptanceCriteria') or data.get('acceptanceCriteria') or '';now=f.clock.now();reqs=[]
        if mode=='link':
            req=f.work.requirement(u,text(data,'requirementId'),True);project=f.portfolio.project(u,(req or {}).get('projectId') or '')
            require(req and project,'请选择有效的已有 L3 需求');require(text(data,'projectId') and req.get('projectId')==text(data,'projectId'),'请选择该 L2 下的已有 L3 需求')
            req=f.work.internal_change(u,req['id'],{'demandId':did,'flowMode':'full_demand','lifecycleVersion':2,'reportingEligible':1,'registeredAt':req.get('registeredAt') or now,'updatedAt':now})
            f.work.log(u,p,req,{'content':'需求池综合决策完成，已关联已有 L3。验收标准：'+(acceptance or '后续在 L3 方案与测试阶段确认'),'sourceType':'system_event','sourceRef':'demand-pool:'+did})
            f.audit.record(u,p,'L3',req['id'],req['title'],'demand_pool_link','需求池综合决策后关联已有 L3',after={'demandPoolId':did,'confirmationId':confirmation['id'],'acceptanceCriteria':acceptance});reqs=[req]
        elif mode=='create_l2':
            department=text(data,'department',demand.get('department') or '');owner=text(data,'devOwner',text(data,'projectOwner'));end=text(data,'projectEndDate',demand.get('expectedDeliveryTime') or '')
            require(department and owner and end,'正式创建 L2 需要填写业务部门、项目负责人和目标结束时间')
            solution=solution_type(text(data,'solutionType',demand.get('solutionType') or ''),f.v);require(solution!='unknown','新建 L2 前必须先确定项目类型')
            project=f.portfolio.create_project(u,p,{'name':text(data,'projectName',demand['title']),'description':demand['description'],'status':'已立项','solutionType':solution,
                'lifecycleTemplate':solution,'complexityLevel':demand.get('complexityLevel') or 'medium','priority':data.get('priority') or 'P2','department':department,
                'businessOwner':demand.get('requesterName') or '','devOwner':owner,'currentVersion':'v1.0.0','startDate':now[:10],'targetEndDate':end,'categoryId':text(data,'categoryId'),'images':[]})
            f.audit.record(u,p,'L2',project['id'],project['name'],'create','需求池确认后正式创建 L2 项目',after={'id':project['id'],'name':project['name'],'sourceDemandId':did,'solutionType':solution})
            req=f.work.initial(u,p,project,data.get('phaseTemplateKeys'));req=f.work.internal_change(u,req['id'],{'demandId':did,'flowMode':'full_demand','lifecycleVersion':2,'reportingEligible':1,'acceptanceCriteria':acceptance})
            f.work.mark_initial_reporting(u,req['id']);f.audit.record(u,p,'L3',req['id'],'初始建设','create','创建 L2 时生成初始建设 L3',after={'projectId':project['id'],'itemKind':'initial_build'})
            reqs=[req];specs=specs or [{'title':'初始建设','scope':'','acceptanceDelta':'','itemKind':'initial_build','valueMetricKeys':[]}]
        else:
            project=f.portfolio.project(u,text(data,'projectId',demand.get('projectId') or ''));require(project,'正式创建 L3 前必须选择有效项目')
            department=text(data,'department',demand.get('department') or project.get('department') or '');assignee=text(data,'assignee');expected=text(data,'expectedDeliveryTime',demand.get('expectedDeliveryTime') or '')
            require(department and assignee and expected,'正式创建 L3 需要填写归属部门、开发负责人和预计交付时间');priority=text(data,'priority','P2');priority=priority if priority in {'P0','P1','P2','P3','P4'} else 'P2'
            specs=specs or [{'title':text(data,'title',demand['title']),'scope':'','acceptanceDelta':'','itemKind':text(data,'itemKind','feature'),'valueMetricKeys':[]}]
            for spec in specs:
                kind=spec['itemKind'] if spec['itemKind'] in {x['key'] for x in f.v['L3_ITEM_KINDS']} else 'feature';unit_acceptance=acceptance
                if spec.get('scope'):unit_acceptance+='\n本独立 L3 工作项独有交付范围：'+spec['scope']
                if spec.get('acceptanceDelta'):unit_acceptance+='\n本独立 L3 工作项验收补充：'+spec['acceptanceDelta']
                req=f.work.formal(u,p,{**data,'title':spec['title'],'type':data.get('type') or ('技术建设' if kind=='initial_build' else '新增功能'),
                    'itemKind':kind,'status':'待处理','changeObject':data.get('changeObject') or '功能','impactLevel':data.get('impactLevel') or '重要','workloadLevel':data.get('workloadLevel') or '中',
                    'demandId':did,'department':department,'assignee':assignee,'expectedDeliveryTime':expected,'priority':priority,'requester':demand.get('requesterName') or '',
                    'description':demand['description'],'acceptanceCriteria':unit_acceptance,'demandTitle':demand['title']},project)
                f.audit.record(u,p,'L3',req['id'],req['title'],'create','需求池业务确认后正式创建 L3',after={k:v for k,v in req.items() if k not in {'deliveredAt','deliveryRegisteredAt','deletedAt','deletedByUserId','deletedByName'}});reqs.append(req)
        for i,req in enumerate(reqs):
            spec=specs[i] if mode!='link' and i<len(specs) else None;baseline,summary=self.delivery.materialize_confirmation(u,p,req['id'],confirmation,spec)
            if summary:req=f.work.internal_change(u,req['id'],{'acceptanceCriteria':summary,'updatedAt':now});reqs[i]=req
            if spec and spec.get('branchId'):d.formalize_branch(u,did,spec['branchId'],req['id'])
        d.formalize(u,did,reqs);rids=[r['id'] for r in reqs];self.value.attach_conversion(u,did,rids,reqs[0]['projectId'])
        if mode!='link':
            for req in reqs:
                result={**req,'pname':(f.portfolio.project(u,req['projectId']) or {}).get('name'),'images':list_field(req.get('images'))}
                f.assign_todos(u,p,result,'需求池已确认，正式 L3 已创建，请确认处理');f.emit(u,p,'requirement_created',result,'requirement')
                if req.get('assignee') and req['assignee']!='待分配':f.emit(u,p,'requirement_assigned',result,'requirement')
        first=reqs[0];f.audit.record(u,p,'DEMAND_POOL',did,demand['title'],'convert','需求池综合决策后进入正式 L2/L3',demand,{'status':'converted','requirementId':first['id'],'requirementIds':rids,'requirementTitle':first['title'],'mode':mode,'confirmationId':confirmation['id']})
        return {'demand':d.payload(u,p,d.get(u,did)),'requirementId':first['id'],'requirementIds':rids,'requirementTitle':first['title']}
    def historical(self,u,p,did,data):
        d,f=self.demand,self.flow;f.identity.action(u,p,'demand_pool.manage');demand=d.get(u,did,True,True);require(demand,'需求池记录不存在',404,'NOT_FOUND')
        require(demand['status']=='converted','历史补充分解只适用于已完成正式立项的需求')
        old=[x for x in f.work.requirements(u) if x.get('demandId')==did or x['id']==demand.get('requirementId')];old.sort(key=lambda x:x['createdAt'])
        pid=demand.get('projectId') or (old[0].get('projectId') if old else '') or '';project=f.portfolio.project(u,pid)
        require(project,'历史补录前无法确定原 L2 项目，请先为原需求关联有效项目')
        from itpm.modules.demand.public import normalized_branches
        normalized=normalized_branches(data.get('branches'),f.v,True)
        for branch in normalized:
            if branch.get('formalRequirementId'):
                req=f.work.requirement(u,branch['formalRequirementId']);require(req and req.get('projectId')==pid,f"分支“{branch['title']}”对应的已有 L3 不属于当前 L2")
        d.save_branches(u,p,did,{'branches':normalized,'mode':'historical_backfill','requireMultiple':True})
        stored={x['branchKey']:x for x in d.branch_rows(u,did)};confirmation=d.latest_confirmation(u,did) or {};content=object_field(confirmation.get('content'));base=content.get('expected') or confirmation.get('acceptanceCriteria') or ''
        department=demand.get('department') or project.get('department') or '';assignee=(old[0].get('assignee') if old else '') or '待分配';expected=demand.get('expectedDeliveryTime') or (old[0].get('expectedDeliveryTime') if old else '') or '';reqs=[]
        for branch in normalized:
            mapped=branch.get('formalRequirementId') or stored[branch['branchKey']].get('formalRequirementId') or '';acceptance=base or (old[0].get('acceptanceCriteria') if old else '') or ''
            if branch.get('scope'):acceptance+='\n本独立 L3 工作项独有交付范围：'+branch['scope']
            if branch.get('difference'):acceptance+='\n本独立 L3 工作项验收补充：'+branch['difference']
            if mapped:
                before=f.work.requirement(u,mapped,True);require(before,f"分支“{branch['title']}”关联的 L3 不存在")
                req=f.work.internal_change(u,mapped,{'title':branch['title'],'itemKind':branch['itemKind'],'parentRequirementId':'','demandId':did,
                    'projectName':project['name'],'department':department,'acceptanceCriteria':acceptance[:10000],'updatedAt':f.clock.now()})
                f.audit.record(u,p,'L3',mapped,branch['title'],'historical_backfill_split','已完成需求不重跑流程，保留原 L3 并补充工作项归属',before,{'title':branch['title'],'demandId':did,'branchKey':branch['branchKey']})
            else:
                req=f.work.formal(u,p,{'title':branch['title'],'type':'技术建设' if branch['itemKind']=='initial_build' else '新增功能','itemKind':branch['itemKind'],
                    'status':'待处理','changeObject':'功能','impactLevel':'重要','workloadLevel':'中','demandId':did,'assignee':assignee,'department':department,
                    'expectedDeliveryTime':expected,'requester':demand.get('requesterName') or '','description':demand.get('description') or '','acceptanceCriteria':acceptance[:10000]},project,True)
                f.audit.record(u,p,'L3',req['id'],branch['title'],'historical_backfill_split','已完成需求不重跑流程，新增独立 L3 工作项',after={'demandId':did,'branchKey':branch['branchKey']})
            _,summary=self.delivery.materialize_confirmation(u,p,req['id'],confirmation,branch)
            if summary:req=f.work.internal_change(u,req['id'],{'acceptanceCriteria':summary,'updatedAt':f.clock.now()})
            d.backfill_branch(u,stored[branch['branchKey']]['id'],req['id']);reqs.append(req)
        rids=[x['id'] for x in reqs];self.value.historical_conversion(u,did,rids,pid);d.formalize(u,did,reqs)
        f.audit.record(u,p,'DEMAND_POOL',did,demand['title'],'historical_backfill_split','已完成需求历史补充独立 L3 工作项，不重新发送业务确认',demand,{'requirementIds':rids,'branchCount':len(normalized),'status':'converted'})
        return {'demand':d.payload(u,p,d.get(u,did)),'requirementIds':rids,'requirementId':rids[0]}
