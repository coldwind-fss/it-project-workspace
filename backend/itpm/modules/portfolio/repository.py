from sqlalchemy import select,func
from itpm.infrastructure.database import Repository

class PortfolioRepository(Repository):
    def __init__(self,db):super().__init__(db,['categories','projects'])

    def categories(self,u):
        t=self.table('categories');return self.rows(u,select(t).where(func.coalesce(t.c.deletedat,'')=='').order_by(t.c.sortorder,t.c.name))

    def projects(self,u,category=None,identifier=None):
        t=self.table('projects');c=self.table('categories');cols=[t,c.c.name.label('categoryName')]
        if category is None:cols.append(c.c.color.label('categoryColor'))
        s=select(*cols).select_from(t.outerjoin(c,t.c.categoryid==c.c.id)).where(func.coalesce(t.c.deletedat,'')=='')
        if category is not None:s=s.where(t.c.categoryid==category)
        if identifier is not None:s=s.where(t.c.id==identifier)
        return self.rows(u,s.order_by(t.c.createdat.desc()))

    def count_projects(self,u,cid):
        t=self.table('projects');return u.connection.execute(select(func.count()).select_from(t).where(t.c.categoryid==cid,func.coalesce(t.c.deletedat,'')=='')).scalar()
    def project_map(self,u):
        t=self.table('projects');return {x['id']:x for x in self.rows(u,select(t))}
