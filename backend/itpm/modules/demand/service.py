"""Demand gate: local state, evidence and scoped review/confirmation records."""
import json
from datetime import datetime
from itpm.core.errors import require
from itpm.core.json_fields import object_field,list_field
from itpm.core.ports import Principal
from itpm.modules.identity.public import same_name
from .rules import text,answers,TRANSITIONS,branches,confirmation_content,validate_confirmation


class Demand:
    def __init__(self,repo,clock,ids,v,identity,work,portfolio,files,value,audit,base):
        self.repo,self.clock,self.ids,self.v=repo,clock,ids,v
        self.identity,self.work,self.portfolio,self.files,self.value,self.audit,self.base=identity,work,portfolio,files,value,audit,base
    def manage(self,u,p):
        return p.authenticated and (p.role in {'admin','super_admin','editor'} or self.identity.has(u,p,'demand_pool.manage'))
    def get(self,u,did,lock=False,active=False):return self.repo.get(u,'demand_pool_items',did,active,lock)
    def source(self,u,table,identifier):return self.repo.get(u,table,identifier)
    def recycle_rows(self,u):return [x for x in self.repo.find(u,'demand_pool_items') if x.get('deletedAt')]
    def recycle_restore(self,u,identifier):self.repo.change(u,'demand_pool_items',identifier,dict(deletedAt='',deletedByUserId='',deletedByName=''))
    def recycle_purge(self,u,identifier):self.repo.remove(u,'demand_pool_items',identifier)
    def rows(self,u,table,did):return self.repo.find(u,table,{'demandId':did},order=[('createdAt',False)])
    def visible(self,u,p,row):
        if not row or not p.authenticated or row.get('deletedAt'):return False
        if self.manage(u,p):return True
        if p.userId and p.userId==row.get('requesterUserId') or same_name(p.name,row.get('requesterName'),self.v['DEVELOPERS']):return True
        return any(r['status']!='cancelled' and (p.userId and p.userId==r.get('reviewerUserId') or r.get('reviewerName')==p.name)
            for r in self.rows(u,'demand_pool_reviews',row['id']))
    def reviewer_visible(self,u,p,row):
        return p.authenticated and (self.manage(u,p) or p.userId and p.userId==row.get('reviewerUserId') or same_name(p.name,row.get('reviewerName'),self.v['DEVELOPERS']))
    def confirmation_visible(self,u,p,row,demand):
        return p.authenticated and (self.manage(u,p) or any(p.userId and p.userId==r.get(k) or same_name(p.name,r.get(n),self.v['DEVELOPERS'])
            for r,k,n in [(row,'recipientUserId','recipientName'),(demand,'requesterUserId','requesterName')]))
    def branch_rows(self,u,did,removed=False):
        rows=self.repo.find(u,'demand_pool_l3_branches',{'demandId':did},order=[('sortOrder',False),('createdAt',False),('id',False)])
        return rows if removed else [r for r in rows if r['status']!='removed']
    def branch_payload(self,row):
        result=dict(row)
        for field,key,default in [('relationToValue','DEMAND_POOL_L3_BRANCH_RELATIONS','共用主线价值口径'),
            ('businessDecision','DEMAND_POOL_REVIEW_DECISION_LABELS',''),('itDecision','DEMAND_POOL_DECISION_LABELS',''),
            ('status','DEMAND_POOL_L3_BRANCH_STATUS_LABELS','待分流'),('proposedPriority','DEMAND_POOL_PRIORITY_LABELS','')]:
            result[field+'Label']=self.v[key].get(row.get(field),row.get(field) or default)
        result['itemKindLabel']=next((x['label'] for x in self.v['L3_ITEM_KINDS'] if x['key']==row.get('itemKind')),row.get('itemKind') or '新功能 / 模块')
        return result
    def review_payload(self,u,p,row,token=False):
        item=dict(row);item['reviewerRoleLabel']=item.get('reviewerRoleLabel') or self.v['DEMAND_POOL_REVIEW_ROLE_LABELS'].get(item.get('reviewerRole'),item.get('reviewerRole') or '业务评估')
        item['statusLabel']=self.v['DEMAND_POOL_REVIEW_STATUS_LABELS'].get(row['status'],row['status'] or '未设置')
        item['decisionLabel']=self.v['DEMAND_POOL_REVIEW_DECISION_LABELS'].get(row.get('decision'),row.get('decision') or '')
        item['branchDecisions']=list_field(row.get('branchDecisions')) if not isinstance(object_field(row.get('branchDecisions')),dict) or not object_field(row.get('branchDecisions')) else object_field(row.get('branchDecisions'))
        item['link']='' if row['reviewerRole']=='existing_communication' else self.base+'#/entry/demand-review?'+('token='+row['token'] if row.get('token') else 'reviewId='+row['id'])
        item['canSubmit']=row['status']=='pending' and (token or self.reviewer_visible(u,p,row));item['canManage']=self.manage(u,p)
        if not self.manage(u,p):item.pop('token',None)
        return item
    def normalize_template(self,value):return self.v['DELIVERY_STANDARD_TEMPLATE_ALIASES'].get(value,value or 'custom')
    def confirmation_payload(self,u,p,row,public=False):
        item=dict(row);content=object_field(row.get('content'))
        for key,column in [('scope','usageScope'),('scenarios','businessProcess'),('expected','acceptanceCriteria')]:content[key]=content.get(key) or row.get(column) or ''
        content.setdefault('evidence','');content.setdefault('exclusions','');item['content']=content
        item['templateType']=self.normalize_template(row.get('templateType') or row.get('demandSolutionType') or 'custom')
        item['templateLabel']=self.v['DELIVERY_STANDARD_TEMPLATE_LABELS'].get(item['templateType'],'通用交付标准')
        item['statusLabel']=self.v['DEMAND_CONFIRMATION_STATUS_LABELS'].get(row['status'],row['status'] or '未设置')
        item['link']=self.base+'#/entry/demand-confirm?'+('token='+row['token'] if row.get('token') else 'confirmationId='+row['id'])
        item['canConfirm']=row['status']=='pending' and (public or not self.manage(u,p))
        if not public:item['canManage']=self.manage(u,p)
        return item
    def supplement_payload(self,u,row,link=True,attachments=True):
        item={**row,'questions':list_field(row.get('questions')),'answers':object_field(row.get('answers'))}
        if link:item['link']=self.base+'#/entry/demand-supplement?supplementId='+row['id']
        if attachments:item['attachments']=self.files.list(u,'demand_pool_supplement',row['id'])
        return item
    def payload(self,u,p,row):
        item=dict(row);item['intakeLevel']=str(row.get('intakeLevel') or 'L3').upper()
        for field,key,default in [('intakeLevel','INTAKE_LEVEL','L3'),('status','STATUS','未设置'),('evaluationDecision','DECISION',''),
            ('businessPriority','PRIORITY','暂无明确时间'),('solutionType','SOLUTION_TYPE','待判断'),('aiMode','AI','不涉及 AI'),('pocRequirement','POC','不需要 PoC')]:
            item[field+'Label']=self.v['DEMAND_POOL_'+key+'_LABELS'].get(item.get(field),item.get(field) or default)
        for field,key,default in [('impactScope','IMPACT_SCOPE','单部门'),('complexityLevel','COMPLEXITY','中')]:
            item[field+'Label']=next((x['label'] for x in self.v['DEMAND_POOL_'+key+'_OPTIONS'] if x['key']==item.get(field)),item.get(field) or default)
        item['attachments']=self.files.list(u,'demand_pool',row['id']);item['requirementLink']=self.base+'#/requirements/'+row['requirementId'] if row.get('requirementId') else ''
        reqs=[x for x in self.work.requirements(u) if x.get('demandId')==row['id']]
        reqs.sort(key=lambda x:x['createdAt'])
        if not reqs and row.get('requirementId'):
            req=self.work.requirement(u,row['requirementId']);reqs=[req] if req else []
        item['requirements']=[{**r,'pname':(self.portfolio.project(u,r.get('projectId')) or {}).get('name'),'images':list_field(r.get('images'))} for r in reqs]
        item['requirementIds']=[x['id'] for x in reqs];item['l3Branches']=[self.branch_payload(b) for b in self.branch_rows(u,row['id'])];item['hasL3Decomposition']=bool(item['l3Branches'])
        confirmations=self.rows(u,'demand_pool_confirmations',row['id']);confirmations.sort(key=lambda x:(-{'pending':0,'confirmed':1,'changes_requested':2}.get(x['status'],3),x['updatedAt'],x['createdAt']),reverse=True)
        confirmation=confirmations[0] if confirmations else None
        item['confirmation']=self.confirmation_payload(u,p,confirmation) if confirmation and self.confirmation_visible(u,p,confirmation,row) else None
        reviews=self.rows(u,'demand_pool_reviews',row['id']);item['reviews']=[self.review_payload(u,p,x) for x in reviews if self.reviewer_visible(u,p,x)]
        item['reviewSummary']={'total':sum(x['status']!='cancelled' for x in reviews),'submitted':sum(x['status']=='submitted' for x in reviews),'pending':sum(x['status']=='pending' for x in reviews)}
        item['evaluations']=[{**x,'answers':list_field(x['answers'])} for x in self.rows(u,'demand_pool_evaluations',row['id'])]
        item['supplements']=[self.supplement_payload(u,x) for x in reversed(self.rows(u,'demand_pool_supplements',row['id']))]
        item['pocs']=[{**x,'attachments':self.files.list(u,'demand_pool_poc',x['id'])} for x in reversed(self.rows(u,'demand_pool_pocs',row['id']))]
        card,requests=self.value.demand_facts(u,row['id']);item['valueCard']=card
        item['outcomeRequests']=[]
        for x in requests:
            x={**x,'stageLabel':self.v['DEMAND_POOL_OUTCOME_STAGE_LABELS'].get(x['stage'],x['stage'] or ''),'statusLabel':{'pending':'待填写','submitted':'已提交','cancelled':'已取消'}.get(x['status'],x['status'] or ''),
                'link':self.base+'#/entry/demand-outcome?token='+x['token']}
            if not self.manage(u,p):x.pop('token',None)
            item['outcomeRequests'].append(x)
        item['valuePolicy']=self.value.policy(item);item['canEvaluate']=self.manage(u,p);item['canEdit']=self.visible(u,p,item)
        item['canDelete']=p.role in {'admin','super_admin'} or self.identity.has(u,p,'demand.delete.own') and self.identity.created_by(p,{'createdByUserId':row.get('requesterUserId'),'createdByName':row.get('requesterName')})
        return item
    def list(self,u,p,status='',department=''):
        rows=self.repo.find(u,'demand_pool_items',active=True,order=[('createdAt',True)],limit=500)
        return [self.payload(u,p,row) for row in rows if self.visible(u,p,row) and (not status or status=='all' or row['status']==status) and (not department or department=='all' or row.get('department')==department)]
    def create(self,u,p,data,token_row=None,record_audit=True):
        description=text(data,'description',text(data,'problemAndOutcome',text(data,'originalFeedback',text(data,'content'))))
        require(description,'请填写当前问题和期望结果');require(len(description)<=10000,'需求说明最多10000字')
        name=(token_row or {}).get('recipientName') or text(data,'requesterName',p.name);require(name,'提出人不能为空')
        pid=text(data,'projectId');project=self.portfolio.project(u,pid) if pid else None
        require(not pid or project,'所属项目不存在或已在回收站')
        department=text(data,'department',(project or {}).get('department') or (token_row or {}).get('recipientDepartment') or '')
        require(department,'请选择归属业务部门')
        level=text(data,'intakeLevel','L3').upper();priority=text(data,'businessPriority',text(data,'businessUrgency','normal'))
        title=text(data,'title',next((x.strip() for x in description.splitlines() if x.strip()),'未命名业务需求'))
        if not text(data,'title') and len(title)>80:title=title[:77]+'…'
        now=self.clock.now();row={'id':self.ids.new('dpi'),'title':title[:300],'intakeLevel':level if level in self.v['DEMAND_POOL_INTAKE_LEVEL_LABELS'] else 'L3','description':description,
            'solutionType':'','intakePath':'','aiMode':'none','aiScenario':'','pocRequirement':'none','impactScope':'single_department','complexityLevel':'medium','completeness':'complete','similarDemandId':'','nextAction':'final_review',
            'requesterUserId':(token_row or {}).get('recipientUserId') or text(data,'requesterUserId',p.userId),'requesterName':name,'department':department,
            'projectId':pid,'projectName':(project or {}).get('name') or '','expectedDeliveryTime':text(data,'expectedDeliveryTime',limit=40),
            'businessPriority':priority if priority in self.v['DEMAND_POOL_PRIORITY_LABELS'] else 'normal','sourceType':text(data,'sourceType','in_app',80),'sourceRef':text(data,'sourceRef',limit=300),
            'status':'pending_evaluation','requestType':'','evaluationDecision':'','evaluationReason':'','evaluationNotes':'','evaluationOwnerUserId':'','evaluationOwnerName':'','evaluatedAt':'','confirmedAt':'','requirementId':'','requirementTitle':'',
            'createdAt':now,'updatedAt':now,'closedAt':''}
        if token_row:row['sourceRef']=f"notification:{token_row.get('notificationId') or ''};token:{token_row['token']}"[:300]
        self.repo.add(u,'demand_pool_items',row)
        if record_audit:self.audit.record(u,p,'DEMAND_POOL',row['id'],row['title'],'create','提交需求池提报',after=row)
        return self.get(u,row['id'])
    def create_collection_demand(self,u,p,response):
        return self.create(u,p,{'title':response['title'],'description':response['description'],'intakeLevel':response.get('intakeLevel') or 'L3',
            'requesterUserId':response.get('recipientUserId') or '','requesterName':response.get('recipientName') or '',
            'department':response.get('department') or response.get('recipientDepartment') or '',
            'expectedDeliveryTime':response.get('expectedDeliveryTime') or '','businessPriority':response.get('businessPriority') or 'normal',
            'sourceType':'active_collection','sourceRef':f"collection:{response.get('batchId') or ''};response:{response['id']};notification:{response.get('notificationId') or ''}"[:300]},record_audit=False)
    def update(self,u,p,did,data):
        self.identity.action(u,p,'demand_pool.manage');old=self.get(u,did,True);require(old,'需求池记录不存在',404,'NOT_FOUND')
        status=text(data,'status',old['status'] or 'pending_evaluation');require(status in self.v['DEMAND_POOL_STATUS_LABELS'],'不支持的需求池状态')
        require(status==old['status'] or status in TRANSITIONS.get(old['status'],set()),f"不能从“{self.v['DEMAND_POOL_STATUS_LABELS'].get(old['status'],old['status'])}”直接变更为“{self.v['DEMAND_POOL_STATUS_LABELS'].get(status,status)}”")
        decision=text(data,'evaluationDecision',old.get('evaluationDecision') or '')
        if decision:
            option=next((x for x in self.v['DEMAND_POOL_DECISION_OPTIONS'] if x['key']==decision),None);require(option,'不支持的评估结论')
            if decision=='implement':
                reviews=[x for x in self.rows(u,'demand_pool_reviews',did) if x['status']!='cancelled'];require(reviews,'请先发起直属领导或部门负责人评估，再形成综合结论')
                require(all(x['status']=='submitted' for x in reviews),'业务评估尚未全部完成，暂不能形成综合结论')
                if text(data,'pocRequirement',old.get('pocRequirement') or 'none')=='required':
                    require(any(x['status']=='completed' and x['conclusion'] in {'passed','partial','continue','documented'} for x in self.rows(u,'demand_pool_pocs',did)),'当前需求必须先完成 PoC 验证，再形成实施结论')
            if decision=='poc':require(text(data,'pocRequirement',old.get('pocRequirement') or 'none')!='none','请先将 PoC 策略设置为“建议”或“必须”，再登记 PoC')
            require(option['status']==old['status'] or option['status'] in TRANSITIONS.get(old['status'],set()),f"当前阶段不能形成“{option['label']}”结论")
            status=option['status']
        fields='requestType solutionType intakePath aiMode aiScenario pocRequirement impactScope complexityLevel completeness similarDemandId nextAction evaluationReason evaluationNotes'.split()
        values={k:str(data.get(k,old.get(k) or '') or '').strip() for k in fields};values.update(status=status,evaluationDecision=decision);values['requestType']=values['requestType'][:80]
        for key,vkey,error in [('solutionType','SOLUTION_TYPE','请选择有效的需求类型'),('aiMode','AI','请选择有效的 AI 能力判断'),('pocRequirement','POC','请选择有效的 PoC 判断')]:
            require(key=='solutionType' and not values[key] or values[key] in self.v['DEMAND_POOL_'+vkey+'_LABELS'],error)
        require(values['impactScope'] in {x['key'] for x in self.v['DEMAND_POOL_IMPACT_SCOPE_OPTIONS']} and values['complexityLevel'] in {x['key'] for x in self.v['DEMAND_POOL_COMPLEXITY_OPTIONS']},'影响范围或复杂度不合法')
        require(status=='pending_evaluation' or values['solutionType'],'进入评估流程前请先选择需求类型')
        require(values['nextAction']!='supplement' or values['solutionType'],'请先选择需求类型，再发起业务补充')
        require(decision not in {'defer','reject'} or values['evaluationReason'],'暂缓或不实施时请填写原因')
        if any(values[k]!=(old.get(k) or '') for k in values):
            now=self.clock.now();self.repo.change(u,'demand_pool_items',did,{**values,'evaluationOwnerUserId':p.userId,'evaluationOwnerName':p.name,'evaluatedAt':now,'updatedAt':now})
            defaults={'aiMode':'none','pocRequirement':'none','impactScope':'single_department','complexityLevel':'medium','completeness':'complete'}
            evaluation={k:text(data,k,defaults.get(k,''),5000 if k=='aiScenario' else None) for k in fields if k not in {'requestType','evaluationReason','evaluationNotes'}}
            evaluation.update(id=self.ids.new('dpe'),demandId=did,phase='final' if decision else 'triage',decision=decision,reason=values['evaluationReason'][:5000],notes=values['evaluationNotes'][:5000],answers=json.dumps(answers(data),ensure_ascii=False),operatorUserId=p.userId,operatorName=p.name,createdAt=now,updatedAt=now)
            self.repo.add(u,'demand_pool_evaluations',evaluation)
            audit_after={k:values[k] for k in ['status','requestType','solutionType','intakePath','aiMode','pocRequirement','evaluationDecision','evaluationReason','evaluationNotes']}
            self.audit.record(u,p,'DEMAND_POOL',did,old['title'],'evaluate','更新需求池评估结论',old,audit_after)
        return self.get(u,did)
    def delete(self,u,p,did):
        old=self.get(u,did,True,True);require(old,'需求池记录不存在',404,'NOT_FOUND')
        self.identity.delete_permission(u,p,{'createdByUserId':old.get('requesterUserId'),'createdByName':old.get('requesterName')},'demand')
        self.repo.change(u,'demand_pool_items',did,{'deletedAt':self.clock.now(),'deletedByUserId':p.userId,'deletedByName':p.name,'updatedAt':self.clock.now()})
        self.audit.record(u,p,'DEMAND_POOL',did,old['title'],'delete','移入回收站',before=old);return {'ok':1}
    def save_branches(self,u,p,did,data):
        self.identity.action(u,p,'demand_pool.manage');demand=self.get(u,did,True,True);require(demand,'需求池记录不存在',404,'NOT_FOUND')
        normalized=branches(data.get('branches'),self.v,bool(data.get('requireMultiple')));old=self.branch_rows(u,did,True);bykey={x['branchKey']:x for x in old};keys={x['branchKey'] for x in normalized};now=self.clock.now();mode=text(data,'mode','triage')
        for row in old:
            if row['branchKey'] not in keys and not row.get('formalRequirementId'):self.repo.change(u,'demand_pool_l3_branches',row['id'],{'status':'removed','updatedAt':now})
        for row in normalized:
            existing=bykey.get(row['branchKey']);values={k:v for k,v in row.items() if k not in {'id','branchKey'}}
            if existing:
                values['formalRequirementId']=row['formalRequirementId'] or existing.get('formalRequirementId') or '';values.update(status='draft' if mode=='triage' else existing['status'] or 'draft',updatedAt=now)
                self.repo.change(u,'demand_pool_l3_branches',existing['id'],values)
            else:self.repo.add(u,'demand_pool_l3_branches',{**values,'id':self.ids.new('dpb',12),'demandId':did,'branchKey':row['branchKey'],'status':'draft','createdByUserId':p.userId,'createdByName':p.name,'createdAt':now,'updatedAt':now})
        self.audit.record(u,p,'DEMAND_POOL',did,demand['title'],'decompose_l3','历史记录补充独立 L3 工作项' if mode=='historical_backfill' else '保存独立 L3 工作项',after={'mode':mode,'branches':normalized})
        return [self.branch_payload(x) for x in self.branch_rows(u,did)]
    def branch_decisions(self,u,p,did,data):
        self.identity.action(u,p,'demand_pool.manage');demand=self.get(u,did,True,True);require(demand,'需求池记录不存在',404,'NOT_FOUND');rows=self.branch_rows(u,did)
        require(rows,'当前需求还没有可决策的独立 L3 工作项');require(isinstance(data.get('decisions'),list),'独立 L3 决策格式不正确')
        bykey={text(x,'branchId',text(x,'branchKey')):x for x in data['decisions'] if isinstance(x,dict)};clean=[]
        for row in rows:
            answer=bykey.get(row['id']) or bykey.get(row['branchKey']) or {};decision=text(answer,'decision');reason=text(answer,'reason',limit=5000);notes=text(answer,'notes',limit=5000)
            require(decision in self.v['DEMAND_POOL_DECISION_LABELS'],f"请为“{row['title'] or '独立 L3 工作项'}”选择 IT 结论")
            require(decision not in {'defer','reject'} or reason,f"“{row['title'] or '独立 L3 工作项'}”暂缓或不承接时请填写原因")
            clean.append({'branchId':row['id'],'branchKey':row['branchKey'],'decision':decision,'reason':reason,'notes':notes})
        for answer in clean:self.repo.change(u,'demand_pool_l3_branches',answer['branchId'],{'itDecision':answer['decision'],'itReason':answer['reason'],'itNotes':answer['notes'],'status':'approved' if answer['decision'] in {'implement','poc'} else 'it_review','updatedAt':self.clock.now()})
        self.audit.record(u,p,'DEMAND_POOL',did,demand['title'],'branch_decision','保存独立 L3 的 IT 决策',after={'decisions':clean})
    def review_gate(self,demand,reuse=False):
        require(demand,'需求池记录不存在',404,'NOT_FOUND')
        require(demand.get('solutionType'),'请先完成 IT 初筛并选择需求类型')
        require(demand['status']!='pending_evaluation','请先保存 IT 初评，再复用已有业务沟通' if reuse else '请先保存 IT 初评，再发起直属领导或部门负责人评估')
        require(demand['status'] not in {'converted','business_confirmed','awaiting_confirmation','not_implemented','deferred'},'当前阶段不能重新完成业务评估' if reuse else '当前阶段不能重新发起业务评估')
    def assign_reviews(self,u,p,did,data):
        self.identity.action(u,p,'demand_pool.manage');demand=self.get(u,did,True);self.review_gate(demand)
        reviewers=[];seen=set()
        for raw in data.get('reviewers',[]) if isinstance(data.get('reviewers'),list) else []:
            if not isinstance(raw,dict):continue
            role=text(raw,'role',text(raw,'reviewerRole'));name=text(raw,'name',text(raw,'reviewerName'))
            uid=text(raw,'userId',text(raw,'reviewerUserId',self.identity.person_id(u,name)))
            if role not in self.v['DEMAND_POOL_REVIEW_ROLE_LABELS'] or not (uid or name) or (uid or name) in seen:continue
            seen.add(uid or name);reviewers.append({'role':role,'roleLabel':self.v['DEMAND_POOL_REVIEW_ROLE_LABELS'][role],
                'userId':uid,'name':name or uid,'department':text(raw,'department',text(raw,'reviewerDepartment'),120)})
        require(reviewers,'请至少选择一位直属领导或部门负责人进行评估');require(all(r['userId'] for r in reviewers),'评估人缺少钉钉 UserId，请从联系人列表中选择')
        old=[r for r in self.rows(u,'demand_pool_reviews',did) if r['status'] in {'pending','submitted'}];created=[];resend=[];now=self.clock.now()
        keys={(r['reviewerRole'],r.get('reviewerUserId') or r.get('reviewerName')) for r in old};selected={(r['role'],r['userId'] or r['name']) for r in reviewers}
        for row in old:
            key=(row['reviewerRole'],row.get('reviewerUserId') or row.get('reviewerName'))
            if not row.get('token'):
                row['token']=self.ids.new('',32)+self.ids.new('',32);self.repo.change(u,'demand_pool_reviews',row['id'],{'token':row['token'],'updatedAt':now})
            if row['status']=='pending' and key in selected and row.get('reviewerUserId') and 'token=' not in row.get('link',''):
                row['link']=self.base+'#/entry/demand-review?token='+row['token'];self.repo.change(u,'demand_pool_reviews',row['id'],{'link':row['link'],'updatedAt':now});resend.append(row)
            if row['status']=='pending' and key not in selected:self.repo.change(u,'demand_pool_reviews',row['id'],{'status':'cancelled','updatedAt':now})
        for reviewer in reviewers:
            if (reviewer['role'],reviewer['userId'] or reviewer['name']) in keys:continue
            token=self.ids.new('',32)+self.ids.new('',32)
            row={'id':self.ids.new('dpr'),'demandId':did,'token':token,'reviewerRole':reviewer['role'],'reviewerRoleLabel':reviewer['roleLabel'],
                'reviewerUserId':reviewer['userId'],'reviewerName':reviewer['name'],'reviewerDepartment':reviewer['department'],
                'status':'pending','decision':'','valueAssessment':'','prioritySuggestion':'','expectedOutcome':'','riskNotes':'','comment':'',
                'link':self.base+'#/entry/demand-review?token='+token,'notificationStatus':'pending','notificationError':'','sentAt':'','submittedAt':'','createdAt':now,'updatedAt':now}
            self.repo.add(u,'demand_pool_reviews',row);created.append(row)
        self.repo.change(u,'demand_pool_items',did,{'status':'business_review','updatedAt':now})
        self.audit.record(u,p,'DEMAND_POOL',did,demand['title'],'assign_reviewers','发起直属领导/部门负责人评估',after={'reviewers':reviewers,'createdCount':len(created)})
        return created,resend,demand
    def reuse_review(self,u,p,did,data):
        self.identity.action(u,p,'demand_pool.manage');demand=self.get(u,did,True);self.review_gate(demand,True)
        name=text(data,'contactName',demand.get('requesterName') or '',120);uid=text(data,'contactUserId',limit=120);date=text(data,'communicationDate',limit=10)
        require(name,'请填写已有沟通的业务确认人')
        try:datetime.strptime(date,'%Y-%m-%d');valid=len(date)==10
        except ValueError:valid=False
        require(valid,'请填写有效的沟通日期');decision=text(data,'decision');priority=text(data,'prioritySuggestion');summary=text(data,'summary',limit=5000)
        require(decision in self.v['DEMAND_POOL_REVIEW_DECISION_LABELS'],'请选择已有沟通形成的业务判断');require(priority in {'P0','P1','P2','P3'},'请选择优先级建议');require(summary,'请记录已有业务沟通的结论摘要')
        old=[r for r in self.rows(u,'demand_pool_reviews',did) if r['status'] in {'pending','submitted'}]
        require(not any(r['status']=='submitted' for r in old),'该需求已经有已提交的业务评估，无需重复复用')
        require(not any(r['status']=='pending' and r.get('sentAt') for r in old),'已有业务评估通知已经发送，请先处理现有评估，不能直接改为复用记录')
        evidence={'mode':'existing_communication','communicationDate':date,'source':text(data,'source','既有业务沟通',80),'contactName':name,'contactUserId':uid,'summary':summary};now=self.clock.now();rid=self.ids.new('dpr')
        row={'id':rid,'demandId':did,'token':'','reviewerRole':'existing_communication','reviewerRoleLabel':'复用已有业务沟通','reviewerUserId':uid,'reviewerName':name,'reviewerDepartment':'',
            'status':'submitted','decision':decision,'valueAssessment':'','prioritySuggestion':priority,'expectedOutcome':'','riskNotes':'','comment':summary,'branchDecisions':json.dumps(evidence,ensure_ascii=False),'link':'',
            'notificationStatus':'skipped','notificationError':'已复用既有业务沟通，未发送新的评估通知','sentAt':'','submittedAt':now,'createdAt':now,'updatedAt':now}
        for r in old:self.repo.change(u,'demand_pool_reviews',r['id'],{'status':'cancelled','notificationStatus':'cancelled','notificationError':'改为复用已有业务沟通记录','updatedAt':now})
        self.repo.add(u,'demand_pool_reviews',row);self.repo.change(u,'demand_pool_items',did,{'status':'review_complete','updatedAt':now})
        self.audit.record(u,p,'DEMAND_POOL',did,demand['title'],'review_reuse','复用已有业务沟通完成业务评估',after={**evidence,'decision':decision,'prioritySuggestion':priority,'reviewId':rid})
    def joined_form(self,u,table,identifier='',token=''):
        rows=self.repo.find(u,table,{'token':token}) if token else []
        row=rows[0] if rows else self.repo.get(u,table,identifier) if not token else None
        demand=self.get(u,(row or {}).get('demandId') or '')
        if not row or not demand:return None,None
        keys='title description department requesterUserId requesterName status projectName solutionType'.split()
        if table=='demand_pool_reviews':keys+='intakeLevel intakePath aiMode pocRequirement impactScope complexityLevel expectedDeliveryTime businessPriority evaluationDecision nextAction evaluationReason evaluationNotes sourceType sourceRef createdAt'.split()
        return {**row,**{'demand'+k[0].upper()+k[1:]:demand.get(k) for k in keys}},demand
    def review_demand(self,u,demand,token=''):
        fields='id title description department requesterName requesterUserId status projectName intakeLevel sourceType sourceRef createdAt solutionType intakePath aiMode pocRequirement impactScope complexityLevel expectedDeliveryTime businessPriority evaluationDecision nextAction evaluationReason evaluationNotes'.split()
        result={k:demand.get(k) for k in fields};result['intakeLevel']=result.get('intakeLevel') or 'L3'
        result['attachments']=self.files.list(u,'demand_pool',demand['id'])
        if token:
            for attachment in result['attachments']:attachment['url']+='?reviewToken='+token
        for field,vkey,default in [('intakeLevel','INTAKE_LEVEL','L3'),('solutionType','SOLUTION_TYPE','待判断'),('aiMode','AI','不涉及 AI'),('pocRequirement','POC','不需要 PoC'),('businessPriority','PRIORITY','暂无明确时间'),('evaluationDecision','DECISION','尚未形成 IT 结论')]:
            result[field+'Label']=self.v['DEMAND_POOL_'+vkey+'_LABELS'].get(result.get(field),result.get(field) or default)
        for field,vkey,default in [('impactScope','IMPACT_SCOPE','单部门'),('complexityLevel','COMPLEXITY','中'),('nextAction','NEXT_ACTION','待确定')]:result[field+'Label']=next((x['label'] for x in self.v['DEMAND_POOL_'+vkey+'_OPTIONS'] if x['key']==result.get(field)),result.get(field) or default)
        result['intakePathLabel']={'new_l2':'新建 L2 项目','new_l3':'已有项目下新建 L3','link_l3':'关联已有 L3','merge':'合并已有需求','ordinary':'转普通事项'}.get(result.get('intakePath'),result.get('intakePath') or '待判断')
        result['l3Branches']=[self.branch_payload(x) for x in self.branch_rows(u,demand['id'])];return result
    def review_form(self,u,p,identifier='',token=''):
        if not token:self.identity.authenticated(p)
        row,demand=self.joined_form(u,'demand_pool_reviews',identifier,token)
        require(row,'评估链接已失效或不存在' if token else '评估单不存在',404,'NOT_FOUND')
        if token:p=Principal(userId=row.get('reviewerUserId') or '',name=row.get('reviewerName') or '业务评估人')
        require(token or self.reviewer_visible(u,p,row),'当前身份不是该评估单的接收人',403,'FORBIDDEN')
        return row,demand,p
    def submit_review(self,u,p,row,demand,data):
        if row['status']=='submitted':return
        decision=text(data,'decision');require(decision in self.v['DEMAND_POOL_REVIEW_DECISION_LABELS'],'请选择评估意见')
        fields={k:text(data,k) for k in ['decision','valueAssessment','prioritySuggestion','expectedOutcome','riskNotes','comment']}
        require(fields['prioritySuggestion'] in {'P0','P1','P2','P3'},'请选择优先级建议');require(all(len(x)<=5000 for x in fields.values()),'评估内容过长，请精简后提交')
        branch_rows=self.branch_rows(u,demand['id']);decisions=data.get('branchDecisions');clean=[]
        if branch_rows:
            require(isinstance(decisions,list),'请逐项填写每个独立 L3 工作项的业务判断');byid={text(x,'branchId',text(x,'id')):x for x in decisions if isinstance(x,dict)}
            for branch in branch_rows:
                a=byid.get(branch['id']) or byid.get(branch['branchKey']) or {}
                require(text(a,'decision') in self.v['DEMAND_POOL_REVIEW_DECISION_LABELS'],f"请补充“{branch['title'] or '独立 L3 工作项'}”的业务判断")
                require(text(a,'prioritySuggestion') in {'P0','P1','P2','P3'},f"请补充“{branch['title'] or '独立 L3 工作项'}”的优先级建议")
                require(len(text(a,'comment'))<=5000,'独立 L3 工作项评审意见过长，请精简后提交')
                clean.append({'branchId':branch['id'],'branchKey':branch['branchKey'],'decision':a['decision'],'prioritySuggestion':a['prioritySuggestion'],'comment':text(a,'comment')})
        else:clean=decisions if isinstance(decisions,(list,dict)) else []
        now=self.clock.now();self.repo.change(u,'demand_pool_reviews',row['id'],{**fields,'status':'submitted','branchDecisions':json.dumps(clean,ensure_ascii=False),'submittedAt':now,'updatedAt':now})
        self.audit.record(u,p,'DEMAND_POOL',demand['id'],demand['title'],'review','提交'+(row.get('reviewerRoleLabel') or '业务评估'),after={**fields,'branchDecisions':clean,'reviewId':row['id']})
        if not any(r['status']=='pending' for r in self.rows(u,'demand_pool_reviews',demand['id'])) and demand['status']=='business_review':self.repo.change(u,'demand_pool_items',demand['id'],{'status':'review_complete','updatedAt':now})
    def create_confirmation(self,u,p,did,data):
        self.identity.action(u,p,'demand_pool.manage');demand=self.get(u,did,True);require(demand,'需求池记录不存在',404,'NOT_FOUND')
        require(demand['status'] in {'awaiting_confirmation','business_confirmed'},'只有评估为实施的提报可以发起交付与价值确认')
        pending=[r for r in self.rows(u,'demand_pool_confirmations',did) if r['status']=='pending'];pending.sort(key=lambda r:(r['updatedAt'],r['createdAt']),reverse=True)
        if pending:return pending[0],demand
        name=text(data,'recipientName',demand.get('requesterName') or '');require(name,'交付与价值确认需要指定业务确认人')
        content=confirmation_content(data.get('content'),data);validate_confirmation(content,True);now=self.clock.now()
        row={'id':self.ids.new('dpc'),'demandId':did,'token':self.ids.new('',32)+self.ids.new('',32),
            'recipientUserId':text(data,'recipientUserId',demand.get('requesterUserId') or ''),'recipientName':name,'status':'pending',
            'templateType':self.normalize_template(text(data,'templateType',demand.get('solutionType') or 'custom')),
            'content':json.dumps(content,ensure_ascii=False),'businessProcess':content.get('scenarios') or '','usageScope':content.get('scope') or '',
            'usageFrequency':'','acceptanceCriteria':content.get('expected') or '', 'successMetric':'、'.join(x.get('label') or '' for x in content.get('valueDefinition',{}).get('metrics',[]))[:10000],
            'confirmationComment':'','notificationStatus':'not_sent','notificationError':'','sentAt':'','confirmedByUserId':'','confirmedByName':'','confirmedAt':'','createdAt':now,'updatedAt':now}
        self.repo.add(u,'demand_pool_confirmations',row)
        self.audit.record(u,p,'DEMAND_POOL',did,demand['title'],'request_confirmation','保存上线前交付与价值确认单',after={'confirmationId':row['id'],'recipientName':name,'recipientUserId':row['recipientUserId'],'verificationMode':content['valueDefinition'].get('verificationMode')})
        return self.repo.get(u,'demand_pool_confirmations',row['id']),demand
    def confirmation_form(self,u,p,identifier='',token=''):
        if not token:self.identity.authenticated(p)
        row,demand=self.joined_form(u,'demand_pool_confirmations',identifier,token)
        require(row,'确认链接已失效或不存在' if token else '二次确认单不存在',404,'NOT_FOUND')
        if token:p=Principal(userId=row.get('recipientUserId') or '',name=row.get('recipientName') or '业务确认人')
        require(token or self.confirmation_visible(u,p,row,demand),'当前身份不是该二次确认单的接收人',403,'FORBIDDEN')
        return row,demand,p
    def submit_confirmation(self,u,p,row,demand,data):
        if row['status']!='pending':return
        content=confirmation_content(object_field(row.get('content')),legacy=row);validate_confirmation(content,False)
        decision=text(data,'decision','confirmed');require(decision in {'confirmed','changes_requested'},'请选择确认通过或退回修改')
        comment=text(data,'confirmationComment',limit=3000);require(decision!='changes_requested' or comment,'退回修改时请说明需要调整的内容')
        now=self.clock.now();fields={'businessProcess':content['scenarios'],'usageScope':content['scope'],'usageFrequency':'','acceptanceCriteria':content['expected'],
            'successMetric':'、'.join(x.get('label') or '' for x in content.get('valueDefinition',{}).get('metrics',[]))[:10000],'confirmationComment':comment}
        self.repo.change(u,'demand_pool_confirmations',row['id'],{**fields,'status':decision,'content':json.dumps(content,ensure_ascii=False),'confirmedByUserId':p.userId,'confirmedByName':p.name,'confirmedAt':now,'updatedAt':now})
        status='business_confirmed' if decision=='confirmed' else 'awaiting_confirmation'
        self.repo.change(u,'demand_pool_items',demand['id'],{'status':status,'confirmedAt':now if decision=='confirmed' else '','updatedAt':now})
        if decision=='confirmed':
            card=self.value.sync_confirmation(u,p,row,demand,content)
            self.audit.record(u,p,'DEMAND_POOL',demand['id'],demand['title'],'confirm','业务确认上线前交付与价值口径',after={**fields,'confirmationId':row['id'],'valueCardId':card or '','status':status})
        else:self.audit.record(u,p,'DEMAND_POOL',demand['id'],demand['title'],'request_changes','业务退回上线前交付与价值确认单',after={'confirmationId':row['id'],'confirmationComment':comment,'status':status})
    def create_supplement(self,u,p,did,data):
        self.identity.action(u,p,'demand_pool.manage');demand=self.get(u,did);require(demand,'需求池记录不存在',404,'NOT_FOUND')
        solution=text(data,'solutionType',demand.get('solutionType') or '');require(solution in self.v['DEMAND_POOL_SOLUTION_TYPE_LABELS'],'请先选择有效的需求类型')
        questions=data.get('questions') if isinstance(data.get('questions'),list) else self.v['DEMAND_POOL_TEMPLATE_QUESTIONS'].get(solution,[])
        questions=[q for q in questions if isinstance(q,dict) and q.get('key') and q.get('label')][:12]
        name=text(data,'recipientName',demand.get('requesterName') or '');require(name,'请指定业务补充人');now=self.clock.now()
        row={'id':self.ids.new('dps'),'demandId':did,'solutionType':solution,'status':'pending','questions':json.dumps(questions,ensure_ascii=False),'answers':'{}',
            'recipientUserId':text(data,'recipientUserId',demand.get('requesterUserId') or ''),'recipientName':name,'submittedAt':'','createdByUserId':p.userId,'createdByName':p.name,'createdAt':now,'updatedAt':now}
        self.repo.add(u,'demand_pool_supplements',row);self.repo.change(u,'demand_pool_items',did,{'solutionType':solution,'status':'awaiting_supplement','nextAction':'supplement','updatedAt':now})
        self.audit.record(u,p,'DEMAND_POOL',did,demand['title'],'request_supplement','发起业务补充信息',after={'supplementId':row['id'],'solutionType':solution,'questionCount':len(questions)})
        return self.supplement_payload(u,row,True,False)
    def supplement(self,u,p,identifier,data=None):
        self.identity.authenticated(p);row=self.repo.get(u,'demand_pool_supplements',identifier);require(row,'补充单不存在',404,'NOT_FOUND');demand=self.get(u,row['demandId'])
        require(self.visible(u,p,demand),'当前身份不是该补充单接收人',403,'FORBIDDEN')
        if data is None:
            item=self.supplement_payload(u,row,True,False);item['demand']={k:demand.get(k) for k in ['id','title','description','department','requesterName']};return item
        clean=answers(data);questions=list_field(row.get('questions'));require(all(clean.get(q.get('key')) for q in questions if isinstance(q,dict) and q.get('required')),'请补充所有必填信息')
        now=self.clock.now();self.repo.change(u,'demand_pool_supplements',identifier,{'status':'submitted','answers':json.dumps(clean,ensure_ascii=False),'submittedAt':now,'updatedAt':now})
        self.finish_supplement(u,demand)
        self.audit.record(u,p,'DEMAND_POOL',demand['id'],demand['title'],'submit_supplement','业务补充信息已提交',after={'supplementId':identifier,'answers':clean})
        return self.supplement_payload(u,self.repo.get(u,'demand_pool_supplements',identifier),False,False)
    def finish_supplement(self,u,demand):
        if demand['status']=='awaiting_supplement':self.repo.change(u,'demand_pool_items',demand['id'],{'status':'review_complete','completeness':'complete','nextAction':'final_review','updatedAt':self.clock.now()})
    def materials(self,u,p,did,data):
        demand=self.get(u,did);require(demand,'指定需求不存在',404,'NOT_FOUND');additional=text(data,'additionalInfo',text(data,'description'))
        require(additional or data.get('hasAttachments'),'请填写需要补充的内容，或上传至少一个附件');require(len(additional)<=10000,'补充内容最多10000字')
        old=[r for r in self.rows(u,'demand_pool_supplements',did) if r['solutionType']=='materials'];now=self.clock.now();clean={'additionalInfo':additional}
        if old:
            row=old[-1];self.repo.change(u,'demand_pool_supplements',row['id'],{'status':'submitted','answers':json.dumps(clean,ensure_ascii=False),'submittedAt':now,'updatedAt':now})
        else:
            row={'id':self.ids.new('dps'),'demandId':did,'solutionType':'materials','status':'submitted','questions':json.dumps([{'key':'additionalInfo','label':'补充内容','type':'textarea','required':False}],ensure_ascii=False),
                'answers':json.dumps(clean,ensure_ascii=False),'recipientUserId':p.userId,'recipientName':p.name,'submittedAt':now,'createdByUserId':p.userId,'createdByName':p.name,'createdAt':now,'updatedAt':now}
            self.repo.add(u,'demand_pool_supplements',row)
        self.finish_supplement(u,demand);self.audit.record(u,p,'DEMAND_POOL',did,demand['title'],'submit_materials','业务提交需求补充资料',after={'supplementId':row['id'],'hasText':bool(additional)})
        return self.supplement_payload(u,self.repo.get(u,'demand_pool_supplements',row['id']),False,True)
    def create_poc(self,u,p,did,data):
        self.identity.action(u,p,'demand_pool.manage');demand=self.get(u,did);require(demand,'需求池记录不存在',404,'NOT_FOUND');require(demand['status'] in {'evaluating','poc','review_complete'},'当前阶段不能创建 PoC')
        summary=text(data,'summary',text(data,'result',text(data,'artifactText')));light=bool(summary);now=self.clock.now()
        values={k:text(data,k,limit=5000) for k in ['goal','successCriteria','ownerName','dueDate']}
        if light:
            for k,v in {'goal':'PoC 过程记录','successCriteria':'已形成可复用的验证结论','ownerName':p.name,'dueDate':now[:10]}.items():values[k]=values[k] or v
        require(all(values.values()),'PoC 请填写验证目标、通过标准、负责人和计划完成时间；也可以直接填写一段 PoC 结论')
        row={**values,'id':self.ids.new('dpc'),'demandId':did,'status':'completed' if light else 'running',**{k:text(data,k,limit=5000) for k in ['baseline','scope','testData','aiNotes']},
            'ownerUserId':text(data,'ownerUserId'),'result':summary[:10000],'conclusion':'documented' if light else '',
            'artifactType':text(data,'artifactType','text',40),'aiUsed':text(data,'aiUsed','none',40),'createdByUserId':p.userId,'createdByName':p.name,'createdAt':now,'updatedAt':now,'completedAt':now if light else ''}
        self.repo.add(u,'demand_pool_pocs',row)
        if light and demand['status'] in {'poc','evaluating'}:self.repo.change(u,'demand_pool_items',did,{'status':'review_complete','nextAction':'final_review','updatedAt':now})
        self.audit.record(u,p,'DEMAND_POOL',did,demand['title'],'poc_create','创建 PoC 验证记录',after=row);return row
    def update_poc(self,u,p,identifier,data):
        self.identity.action(u,p,'demand_pool.manage');old=self.repo.get(u,'demand_pool_pocs',identifier);require(old,'PoC 记录不存在',404,'NOT_FOUND')
        status=text(data,'status',old['status'] or 'running');conclusion=text(data,'conclusion',old.get('conclusion') or '')
        require(status in {'running','completed','cancelled'},'PoC 状态不合法');require(status!='completed' or conclusion in {'passed','partial','failed','continue'},'完成 PoC 时请选择验证结论');now=self.clock.now()
        self.repo.change(u,'demand_pool_pocs',identifier,{'status':status,'result':text(data,'result',old.get('result') or '',5000),'conclusion':conclusion,'updatedAt':now,'completedAt':now if status in {'completed','cancelled'} else ''})
        demand=self.get(u,old['demandId'])
        if status=='completed' and conclusion in {'passed','partial','documented'} and demand['status'] in {'poc','evaluating'}:self.repo.change(u,'demand_pool_items',demand['id'],{'status':'review_complete','nextAction':'final_review','updatedAt':now})
        elif status in {'completed','cancelled'} and conclusion=='failed' and demand['status']=='poc':self.repo.change(u,'demand_pool_items',demand['id'],{'status':'deferred','evaluationReason':'PoC 验证未通过','nextAction':'','updatedAt':now})
        self.audit.record(u,p,'DEMAND_POOL',old['demandId'],old['demandId'],'poc_update','更新 PoC 验证记录',old,{'status':status,'conclusion':conclusion});return self.repo.get(u,'demand_pool_pocs',identifier)
    def notification_result(self,u,table,identifier,sent,error=''):
        values={'notificationStatus':'success' if sent else 'failed','notificationError':error[:2000],'updatedAt':self.clock.now()}
        if sent:values['sentAt']=self.clock.now()
        self.repo.change(u,table,identifier,values)
    def latest_confirmation(self,u,did,status='confirmed'):
        rows=[r for r in self.rows(u,'demand_pool_confirmations',did) if r['status']==status];rows.sort(key=lambda r:(r['updatedAt'],r['createdAt']),reverse=True);return rows[0] if rows else None
    def formalize(self,u,did,reqs):
        req=reqs[0];self.repo.change(u,'demand_pool_items',did,{'status':'converted','projectId':req.get('projectId') or '',
            'projectName':req.get('projectName') or req.get('pname') or '','requirementId':req['id'],'requirementTitle':req['title'],'updatedAt':self.clock.now()})
    def formalize_branch(self,u,did,bid,rid):
        row=self.repo.get(u,'demand_pool_l3_branches',bid)
        if row and row['demandId']==did:self.repo.change(u,'demand_pool_l3_branches',bid,{'formalRequirementId':rid,'status':'formalized','updatedAt':self.clock.now()})
    def backfill_branch(self,u,bid,rid):self.repo.change(u,'demand_pool_l3_branches',bid,{'formalRequirementId':rid,'status':'backfilled','updatedAt':self.clock.now()})
    def source_demands(self,u,rid):return self.repo.find(u,'demand_pool_items',{'requirementId':rid},order=[('createdAt',False)])
    def project_demands(self,u,pid):return self.repo.find(u,'demand_pool_items',{'projectId':pid})
    def evidence_owners(self,u,rid):
        owners=[]
        for demand in self.source_demands(u,rid):
            owners.append(('demand_pool',demand['id']))
            for table,kind in [('demand_pool_supplements','demand_pool_supplement'),('demand_pool_pocs','demand_pool_poc')]:
                owners.extend((kind,x['id']) for x in self.rows(u,table,demand['id']))
        return owners
