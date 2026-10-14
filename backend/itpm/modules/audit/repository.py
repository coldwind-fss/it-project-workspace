from sqlalchemy import select, or_
from itpm.infrastructure.database import Repository

class AuditRepository(Repository):
    def __init__(self,db):super().__init__(db,['operation_records','app_logs'])

    def list_operations(self,u,entityType='',action='',keyword='',limit=100):
        t=self.table('operation_records');s=select(t)
        if entityType and entityType!='全部':s=s.where(t.c.entitytype==entityType)
        if action and action!='全部':s=s.where(t.c.action==action)
        if keyword:s=s.where(or_(t.c.entityname.like('%'+keyword+'%'),t.c.operator.like('%'+keyword+'%'),t.c.summary.like('%'+keyword+'%')))
        return self.rows(u,s.order_by(t.c.createdat.desc()).limit(min(max(limit,1),300)))

    def list_logs(self,u,level='',source='',limit=100):
        t=self.table('app_logs');s=select(t)
        if level:s=s.where(t.c.level==level)
        if source:s=s.where(t.c.source==source)
        return self.rows(u,s.order_by(t.c.createdat.desc()).limit(min(max(limit,1),500)))
