from sqlalchemy import select,func,case
from itpm.infrastructure.database import Repository
from .rules import LIST_FIELDS

class WorkRepository(Repository):
    def __init__(self,db):super().__init__(db,['requirements','requirement_work_logs','requirement_phase_templates','requirement_phases','changelogs','sprints','releases'])
    def requirements(self,u,filters=None,project_id=None,include_deleted=False):
        t=self.table('requirements');s=select(t)
        if not include_deleted:s=s.where(func.coalesce(t.c.deletedat,'')=='')
        if project_id is not None:s=s.where(t.c.projectid==project_id)
        for k,v in (filters or {}).items():
            if k in ['type','priority','status','projectId'] and v and v!='全部':s=s.where(t.c[k.lower()]==v)
        return self.rows(u,s.order_by(t.c.createdat.desc()))
    def list_requirements(self,u,filters):
        t=self.table('requirements');count=case((func.json_valid(func.coalesce(t.c.images,'[]')),func.json_array_length(t.c.images)),else_=0)
        s=select(*[t.c[k.lower()] for k in LIST_FIELDS],count.label('imageCount')).where(func.coalesce(t.c.deletedat,'')=='')
        for k,v in filters.items():
            if k in ['type','priority','status','projectId'] and v and v!='全部':s=s.where(t.c[k.lower()]==v)
        return self.rows(u,s.order_by(t.c.createdat.desc()))
    def progress_rows(self,u,ids):
        t=self.table('requirements');return self.rows(u,select(t.c.projectid,t.c.status).where(t.c.projectid.in_(ids),func.coalesce(t.c.deletedat,'')==''))
    def linked(self,u,table,key,value,order='createdat'):
        t=self.table(table);s=select(t).where(t.c[key.lower()]==value)
        if order:s=s.order_by(t.c[order].desc())
        return self.rows(u,s)
    def templates(self,u,st):
        t=self.table('requirement_phase_templates');return self.rows(u,select(t.c.id,t.c.solutiontype,t.c.phasekey,t.c.phaselabel,t.c.description,t.c.required,t.c.sortorder,t.c.enabled).where(t.c.solutiontype==st,t.c.enabled==1).order_by(t.c.sortorder))
    def phases(self,u,rid):
        t=self.table('requirement_phases');return self.rows(u,select(t).where(t.c.requirementid==rid).order_by(t.c.sortorder,t.c.createdat))
    def phase(self,u,rid,key):
        t=self.table('requirement_phases');return self.one(u,select(t).where(t.c.requirementid==rid,t.c.phasekey==key))
    def list_table(self,u,table,order):
        t=self.table(table);return self.rows(u,select(t).order_by(t.c[order].desc()))
    def projection_scopes(self,u):
        result=[]
        for table,source in [('requirement_work_logs','work_log'),('changelogs','changelog')]:
            t=self.table(table)
            result.extend((source,row['id'],row['requirementId']) for row in self.rows(u,select(t.c.id,t.c.requirementid)))
        return result
    def changelogs(self,u,project=None,rid=None):
        t=self.table('changelogs');s=select(t)
        if rid:s=s.where(t.c.requirementid==rid)
        if project:
            r=self.table('requirements');s=s.where(t.c.requirementid.in_(select(r.c.id).where(r.c.projectid==project)))
        s=s.order_by(t.c.createdat.desc())
        if not rid:s=s.limit(50)
        return self.rows(u,s)
