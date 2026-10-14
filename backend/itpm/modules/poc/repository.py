from sqlalchemy import select
from itpm.infrastructure.database import Repository

class PocRepository(Repository):
    def __init__(self,db):super().__init__(db,['poc_workbench_records'])
    def legacy(self,u,identifier=None):
        # Explicit read-only projection of old demand PoC and its source labels.
        p=self.db.table('demand_pool_pocs');d=self.db.table('demand_pool_items')
        fields=[p,*[d.c[k.lower()].label(k) for k in ['projectId','projectName','requirementId','requirementTitle']],d.c.title.label('demandTitle')]
        stmt=select(*fields).select_from(p.outerjoin(d,p.c.demandid==d.c.id)).order_by(p.c.updatedat.desc(),p.c.createdat.desc()).limit(500)
        if identifier:stmt=stmt.where(p.c.id==identifier)
        return self.rows(u,stmt)
