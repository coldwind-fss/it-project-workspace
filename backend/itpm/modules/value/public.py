"""Early ValueEligibilityPolicy + scheduled requests; no external delivery."""
from datetime import datetime,timedelta
from itpm.infrastructure.database import Repository
from itpm.core.json_fields import object_field
from .rules import policy
from .rules import card_metric,receipt
import json

class Value:
    def __init__(self,db,clock,ids,demands):self.repo=Repository(db,['demand_pool_value_requests','demand_pool_value_cards']);self.clock,self.ids,self.demands=clock,ids,demands
    def demand_facts(self,u,did):
        cards=self.repo.find(u,'demand_pool_value_cards',{'demandId':did},order=[('createdAt',True)])
        card=cards[0] if cards else None
        if card:card={**card,**{k:object_field(card.get(k)) for k in ['baseline','expected','day7','day30']}}
        return card,self.repo.find(u,'demand_pool_value_requests',{'demandId':did},order=[('createdAt',True)])
    def policy(self,demand):return policy(demand)
    def sync_confirmation(self,u,p,confirmation,demand,content):
        definition=content.get('valueDefinition')
        if not isinstance(definition,dict):return None
        old,_=self.demand_facts(u,demand['id']);baseline={'summary':definition.get('baselineSummary') or ''};expected={'summary':definition.get('expectedSummary') or ''}
        metrics=definition.get('metrics') if definition.get('verificationMode')=='quantitative' else []
        if metrics:baseline['metrics']=metrics;expected['metrics']=metrics
        now=self.clock.now();values={'status':old['status'] if old and old['status'] in {'day7_review','completed'} else 'baseline_ready',
            'baseline':json.dumps(baseline,ensure_ascii=False),'expected':json.dumps(expected,ensure_ascii=False),
            'ownerName':str(definition.get('metricOwnerName') or p.name or '').strip()[:120],
            'ownerUserId':str(definition.get('metricOwnerUserId') or (old or {}).get('ownerUserId') or '').strip()[:120],'updatedAt':now}
        if old:self.repo.change(u,'demand_pool_value_cards',old['id'],values);return old['id']
        identifier=self.ids.new('dpv');self.repo.add(u,'demand_pool_value_cards',{'id':identifier,'demandId':demand['id'],
            'requirementId':demand.get('requirementId') or '','projectId':demand.get('projectId') or '',**values,'day7':'{}','day30':'{}',
            'targetMet':'','createdByUserId':p.userId,'createdByName':p.name,'createdAt':now});return identifier
    def attach_conversion(self,u,did,rids,pid):
        for table in ['demand_pool_value_requests','demand_pool_value_cards']:
            for row in self.repo.find(u,table,{'demandId':did}):
                if not row.get('requirementId'):
                    values={'projectId':pid}
                    if len(rids)==1:values['requirementId']=rids[0]
                    elif table=='demand_pool_value_cards':values['requirementId']=''
                    self.repo.change(u,table,row['id'],values)
    def historical_conversion(self,u,did,rids,pid):
        if len(rids)<=1:return self.attach_conversion(u,did,rids,pid)
        for table in ['demand_pool_value_requests','demand_pool_value_cards']:
            for row in self.repo.find(u,table,{'demandId':did}):self.repo.change(u,table,row['id'],{'requirementId':'','projectId':pid})
    def request(self,u,identifier='',token='',lock=False):
        rows=self.repo.find(u,'demand_pool_value_requests',{'token':token},lock=lock) if token else []
        return rows[0] if rows else self.repo.get(u,'demand_pool_value_requests',identifier,lock=lock) if not token else None
    def requests(self,u,scope,identifier):return self.repo.find(u,'demand_pool_value_requests',{scope:identifier},order=[('createdAt',True)])
    def request_payload(self,row,v,base,include_token=False):
        result={**row,'stageLabel':v['DEMAND_POOL_OUTCOME_STAGE_LABELS'].get(row['stage'],row['stage'] or ''),
            'statusLabel':{'pending':'待填写','submitted':'已提交','cancelled':'已取消'}.get(row['status'],row['status'] or ''),
            'responseSnapshot':object_field(row.get('responseSnapshot')),'link':base+'#/entry/demand-outcome?token='+row['token']}
        if not include_token:result.pop('token',None)
        return result
    def card(self,u,row):
        key=next((k for k in ['demandId','requirementId','projectId'] if row.get(k)),None)
        rows=self.repo.find(u,'demand_pool_value_cards',{key:row[key]},order=[('createdAt',True)]) if key else []
        return self.card_payload(rows[0]) if rows else None
    def card_payload(self,row):return {**row,**{k:object_field(row.get(k)) for k in ['baseline','expected','day7','day30']}} if row else None
    def save_card(self,u,p,demand,data):
        from itpm.core.errors import require
        old=self.card(u,{'demandId':demand['id']});values={k:card_metric(data.get(k) if k in data else data.get(k+'Summary')) for k in ['baseline','expected','day7','day30']}
        status=str(data.get('status') or ('completed' if values['day30'] else 'day7_review' if values['day7'] else 'baseline_ready' if values['baseline'] or values['expected'] else 'draft')).strip()
        pol=policy(demand);require(not pol['requiresExpectation'] or status=='draft' or values['expected'],f"{pol['label']}需要至少填写“{pol['expectationLabel']}”；暂时无法确定时可填写“暂无法量化 + 原因”")
        require(status in {'draft','baseline_ready','day7_review','completed'},'成果验证记录状态不合法');now=self.clock.now()
        changes={k:json.dumps(v,ensure_ascii=False) for k,v in values.items()};changes.update(status=status,
            targetMet=str(data.get('targetMet') or (old or {}).get('targetMet') or '').strip()[:80],
            ownerName=str(data.get('ownerName') or (old or {}).get('ownerName') or demand.get('requesterName') or p.name or '').strip()[:120],
            ownerUserId=str(data.get('ownerUserId') or (old or {}).get('ownerUserId') or demand.get('requesterUserId') or '').strip()[:120],updatedAt=now)
        if old:self.repo.change(u,'demand_pool_value_cards',old['id'],changes);identifier=old['id']
        else:
            identifier=self.ids.new('dpv');self.repo.add(u,'demand_pool_value_cards',{'id':identifier,'demandId':demand['id'],**changes,'createdByUserId':p.userId,'createdByName':p.name,'createdAt':now})
        return self.card_payload(self.repo.get(u,'demand_pool_value_cards',identifier))
    def create_request(self,u,p,scope,data,target,formal=False):
        from itpm.core.errors import require
        stage=str(data.get('stage') or 'goal').strip();require(stage in {'goal','day7','day30'},'正式项目阶段不合法' if formal else '成果回访阶段不合法')
        if formal:
            status=target.get('status') or ''
            require(stage!='goal' or status not in {'已上线','已关闭','已归档'},'项目已经上线或关闭，不能再发起上线前目标确认')
            require(stage=='goal' or status in {'已交付','已上线','维护中','已关闭','已归档','active'},'请先将项目标记为已交付或已上线，再发起交付后回访')
        name=str(data.get('recipientName') or target.get('requesterName') or '').strip()[:120 if formal else 10000]
        require(name,'请指定业务目标确认人' if formal else '请指定业务成果确认人')
        key,identifier=scope;u.lock_key('outcome-request',key+':'+identifier+':'+stage)
        pending=next((r for r in self.requests(u,key,identifier) if r['stage']==stage and r['status']=='pending'),None)
        if pending:return pending,False
        now=self.clock.now();row={'id':self.ids.new('dvr'),'demandId':target.get('demandId') or (identifier if key=='demandId' else ''),
            'requirementId':identifier if key=='requirementId' else '', 'projectId':identifier if key=='projectId' else target.get('projectId') or '' if formal else '',
            'stage':stage,'token':self.ids.new('',32)+self.ids.new('',32),'recipientUserId':str(data.get('recipientUserId') or (target.get('requesterUserId') or '' if not formal else '')).strip(),
            'recipientName':name,'status':'pending','scheduledAt':str(data.get('scheduledAt') or '').strip()[:40],'notificationStatus':'pending','notificationError':'','sentAt':'','submittedAt':'',
            'createdByUserId':p.userId,'createdByName':p.name,'createdAt':now,'updatedAt':now}
        if not formal:row.pop('requirementId');row.pop('projectId')
        self.repo.add(u,'demand_pool_value_requests',row);return self.request(u,row['id']),True
    def notification_result(self,u,identifier,sent,error=''):
        self.repo.change(u,'demand_pool_value_requests',identifier,{'notificationStatus':'success' if sent else 'failed',
            'notificationError':error[:2000],'sentAt':self.clock.now() if sent else '','updatedAt':self.clock.now()})
    def submit(self,u,row,data,target):
        values,status,target_met,snapshot,issue,summary=receipt(row.get('stage') or 'goal',data,self.card(u,row) or {})
        old=self.card(u,row);now=self.clock.now();uid=str(row.get('recipientUserId') or target.get('requesterUserId') or '').strip()[:120];name=str(row.get('recipientName') or target.get('requesterName') or '').strip()[:120]
        card_values={k:json.dumps(v,ensure_ascii=False) for k,v in values.items()};card_values.update(status=status,targetMet=target_met,ownerUserId=uid,ownerName=name,updatedAt=now)
        if old:self.repo.change(u,'demand_pool_value_cards',old['id'],card_values)
        else:self.repo.add(u,'demand_pool_value_cards',{'id':self.ids.new('dpv'),'demandId':row.get('demandId') or '','requirementId':row.get('requirementId') or '',
            'projectId':row.get('projectId') or '',**card_values,'createdByUserId':uid,'createdByName':name,'createdAt':now})
        self.repo.change(u,'demand_pool_value_requests',row['id'],{'status':'submitted','submittedAt':now,'updatedAt':now,'responseSnapshot':json.dumps(snapshot,ensure_ascii=False)})
        return status,issue,summary
    def viewed(self,u,identifier):self.repo.change(u,'demand_pool_value_requests',identifier,{'viewedAt':self.clock.now(),'updatedAt':self.clock.now()})
    def due_requests(self,u):
        from sqlalchemy import select,func
        table=self.repo.table('demand_pool_value_requests')
        return self.repo.rows(u,select(table).where(table.c.status=='pending',func.coalesce(table.c.scheduledat,'')!='',func.coalesce(table.c.sentat,'')=='',table.c.scheduledat<=self.clock.now()).limit(100))
    def reschedule(self,u,identifier,operation,stage,eligible,reason=''):
        row=self.request(u,identifier)
        if not row or row['status']!='pending' or row.get('sentAt'):return
        if not eligible:self.repo.change(u,'demand_pool_value_requests',identifier,{'status':'cancelled','notificationStatus':'cancelled','notificationError':reason,'updatedAt':self.clock.now()})
        elif operation.get('businessOwnerName') and operation.get(stage+'DueDate'):
            self.repo.change(u,'demand_pool_value_requests',identifier,{'recipientUserId':operation['businessOwnerUserId'],'recipientName':operation['businessOwnerName'],
                'scheduledAt':operation[stage+'DueDate']+' 09:00:00','updatedAt':self.clock.now()})
    def eligible(self,u,req):
        return bool(req and not req.get('deletedAt') and req.get('demandId') and self.demands.confirmed_conversion(u,req['demandId']))
    def eligibility(self,u,req,identifier):
        errors={'no_formal_requirement':'未关联正式需求，只记录交付，不触发价值验证','requirement_not_found':'正式需求不存在或已归档，不触发价值验证',
            'no_demand_pool_link':'正式需求未关联需求池记录，不触发价值验证','demand_not_converted':'需求池记录尚未完成正式转换，不触发价值验证',
            'business_not_confirmed':'需求池尚未完成业务确认，不触发价值验证'}
        code='no_formal_requirement' if not identifier else 'requirement_not_found' if not req or req.get('deletedAt') else 'no_demand_pool_link' if not req.get('demandId') else ''
        if not code:
            demand,confirmation=self.demands.conversion_facts(u,req['demandId'])
            code='demand_not_converted' if not demand or demand['status']!='converted' else 'business_not_confirmed' if not confirmation else ''
        if code:return {'eligible':False,'code':code,'reason':errors[code]}
        return {'eligible':True,'code':'full_demand_lifecycle','reason':'已完成需求池评估、业务确认和正式需求转换，可触发价值验证',
            'requirementId':identifier,'demandId':req['demandId'],'confirmationId':confirmation}
    def schedule(self,u,p,operation,eligible):
        ids={}
        for stage,key in [('day7','day7DueDate'),('day30','day30DueDate')]:
            due=operation[key]
            if not eligible or not operation['businessOwnerName'] or not due:continue
            rid=self.ids.new('dvr');ids[stage]=rid;now=self.clock.now()
            self.repo.add(u,'demand_pool_value_requests',{'id':rid,'demandId':'','requirementId':operation['requirementId'],'projectId':operation['projectId'],
                'stage':stage,'token':self.ids.new('',32)+self.ids.new('',32),'recipientUserId':operation['businessOwnerUserId'],'recipientName':operation['businessOwnerName'],
                'status':'pending','scheduledAt':due+' 09:00:00','notificationStatus':'pending','notificationError':'','sentAt':'','submittedAt':'',
                'createdByUserId':p.userId,'createdByName':p.name,'createdAt':now,'updatedAt':now})
        return ids
    def schedule_one(self,u,p,operation,stage):
        only=dict(operation);other='day30DueDate' if stage=='day7' else 'day7DueDate';only[other]=''
        return self.schedule(u,p,only,True)[stage]
