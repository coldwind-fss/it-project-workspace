"""Early operation facts needed by terminal historical input and state updates.
No automatic reconciliation; value requests scheduled explicitly by workflow.
"""
from datetime import datetime,timedelta
from sqlalchemy import select,func
from itpm.infrastructure.database import Repository
from .rules import date,number,entries,result_entries

def date_plus(value,days):
    try:return (datetime.strptime(value[:10],'%Y-%m-%d')+timedelta(days=days)).strftime('%Y-%m-%d')
    except ValueError:return ''

class Postlaunch:
    def __init__(self,db,clock,ids):self.repo=Repository(db,['postlaunch_operations']);self.clock,self.ids=clock,ids
    def delivered(self,u,rid):
        t=self.repo.table('postlaunch_operations');return bool(u.connection.execute(select(t.c.id).where(t.c.requirementid==rid,func.coalesce(t.c.acceptancerequestid,'')!='').limit(1)).first())
    def start(self,u,p,target,target_type,owner_uid):
        rid=target['id'] if target_type=='requirement' else '';pid=target.get('projectId','') if rid else target['id'];now=self.clock.now();date=now[:10]
        t=self.repo.table('postlaunch_operations');old=self.repo.one(u,select(t).where(t.c.requirementid==rid,t.c.projectid==pid,t.c.deliverydate==date).order_by(t.c.createdat.desc()).limit(1))
        if old:return old,False
        owner=target.get('requester','') if rid else target.get('businessOwner','')
        planned=str(target.get('expectedDeliveryTime') or target.get('targetEndDate') or '').strip()[:10]
        try:
            if planned:datetime.strptime(planned,'%Y-%m-%d')
        except ValueError:planned=''
        row={'id':self.ids.new('plo'),'requirementId':rid,'projectId':pid,'demandId':target.get('demandId') or '',
            'deliveryRoundId':'','deliveryKind':'上线' if target.get('status')=='已上线' else '已交付','deliveryDate':date,'plannedDeliveryDate':planned,'useStartDate':date,
            'businessOwnerUserId':owner_uid,'businessOwnerName':owner or '','status':'active','day7DueDate':date_plus(date,3),'day30DueDate':date_plus(date,30),
            'day7RequestId':'','day30RequestId':'','notes':'','createdByUserId':p.userId,'createdByName':p.name,'createdAt':now,'updatedAt':now}
        self.repo.add(u,'postlaunch_operations',row);return row,True
    def attach_requests(self,u,oid,ids):self.repo.change(u,'postlaunch_operations',oid,{'day7RequestId':ids.get('day7',''),'day30RequestId':ids.get('day30',''),'updatedAt':self.clock.now()})
    def operations(self,u,rid=None,pid=None):return self.repo.find(u,'postlaunch_operations',{'requirementId':rid} if rid is not None else {'projectId':pid} if pid is not None else {},order=[('rowid',True)])
    def get(self,u,identifier):return self.repo.get(u,'postlaunch_operations',identifier)
    def change(self,u,identifier,values):self.repo.change(u,'postlaunch_operations',identifier,values);return self.get(u,identifier)
    def acceptance_used(self,u,identifier):return bool(self.repo.find(u,'postlaunch_operations',{'acceptanceRequestId':identifier}))
    def create(self,u,p,target,target_type,data,owner_uid):
        from itpm.core.errors import require
        rid=target['id'] if target_type=='requirement' else '';pid=target.get('projectId','') if rid else target['id'];now=self.clock.now()
        kind=str(data.get('deliveryKind') or '上线').strip()[:40];require(kind in {'上线','已交付','试运行','其他交付'},'交付类型不合法')
        date=str(data.get('deliveryDate') or now[:10]).strip()[:10]
        try:datetime.strptime(date,'%Y-%m-%d')
        except ValueError:require(False,'交付日期格式应为 YYYY-MM-DD')
        round_id=str(data.get('deliveryRoundId') or '').strip()[:120]
        old=next((r for r in self.operations(u,rid) if r['projectId']==pid and (r['deliveryRoundId']==round_id if round_id else r['deliveryDate']==date)),None)
        if old:return old,False
        planned=str(data.get('plannedDeliveryDate') or target.get('expectedDeliveryTime') or target.get('projectTargetEndDate') or target.get('targetEndDate') or '').strip()[:10]
        try:
            if planned:datetime.strptime(planned,'%Y-%m-%d')
        except ValueError:planned=''
        use_start=str(data.get('useStartDate') or date).strip()[:10]
        row={'id':self.ids.new('plo'),'requirementId':rid,'projectId':pid,'demandId':target.get('demandId') or '',
            'deliveryRoundId':round_id,'deliveryKind':kind,'deliveryDate':date,'plannedDeliveryDate':planned,'useStartDate':use_start,
            'businessOwnerUserId':owner_uid,'businessOwnerName':str(data.get('businessOwnerName') or target.get('requester') or target.get('businessOwner') or '').strip()[:120],
            'status':'active','day7DueDate':date_plus(use_start,3),'day30DueDate':date_plus(use_start,30),'day7RequestId':'','day30RequestId':'',
            'notes':str(data.get('notes') or '').strip()[:5000],'createdByUserId':p.userId,'createdByName':p.name,'createdAt':now,'updatedAt':now}
        self.repo.add(u,'postlaunch_operations',row);return row,True
