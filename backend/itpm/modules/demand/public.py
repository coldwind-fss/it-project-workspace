"""Read eligibility facts for imported/full-demand records, no demand writes."""
from sqlalchemy import select,func
from .rules import text
from .rules import branches as normalized_branches
class DemandFacts:
    def __init__(self,db):self.db=db
    def confirmed_conversion(self,u,demandid):
        d=self.db.table('demand_pool_items');c=self.db.table('demand_pool_confirmations')
        demand=u.connection.execute(select(d.c.id).where(d.c.id==demandid,d.c.status=='converted',func.coalesce(d.c.deletedat,'')=='')).first()
        confirmation=u.connection.execute(select(c.c.id).where(c.c.demandid==demandid,c.c.status=='confirmed').limit(1)).first() if demand else None
        return bool(confirmation)
    def conversion_facts(self,u,demandid):
        d=self.db.table('demand_pool_items');c=self.db.table('demand_pool_confirmations')
        row=u.connection.execute(select(d.c.id,d.c.status).where(d.c.id==demandid,func.coalesce(d.c.deletedat,'')=='')).mappings().first()
        confirmation=u.connection.execute(select(c.c.id).where(c.c.demandid==demandid,c.c.status=='confirmed').order_by(c.c.createdat.desc()).limit(1)).scalar()
        return dict(row) if row else None,confirmation
