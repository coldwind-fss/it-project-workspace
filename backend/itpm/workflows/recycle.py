from datetime import datetime,timedelta
from itpm.core.errors import require

class Recycle:
    KINDS={'category':('L1','大类','name'),'project':('L2','项目','name'),'requirement':('L3','需求','title'),'demand':('需求池','需求池','title')}
    def __init__(self,flow,demand):self.flow,self.demand=flow,demand
    def get(self,u,kind,identifier):
        require(kind in self.KINDS,'不支持的回收站类型')
        return self.flow.portfolio.recycle_get(u,kind,identifier) if kind in {'category','project'} else self.flow.work.raw_requirement(u,identifier) if kind=='requirement' else self.demand.get(u,identifier)
    def view(self,kind,row):
        try:expires=(datetime.strptime(row['deletedAt'],'%Y-%m-%d %H:%M:%S')+timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError,TypeError):expires=''
        return dict(type=kind,entityType=self.KINDS[kind][0],id=row['id'],name=row.get(self.KINDS[kind][2]) or row['id'],deletedAt=row.get('deletedAt') or '',deletedByName=row.get('deletedByName') or '',expiresAt=expires)
    def rows(self,u,p):
        self.flow.identity.action(u,p,'recycle.manage');rows=[]
        for kind in self.KINDS:
            records=self.flow.portfolio.recycle_rows(u,kind) if kind in {'category','project'} else self.flow.work.recycle_rows(u) if kind=='requirement' else self.demand.recycle_rows(u)
            rows.extend(self.view(kind,r) for r in records)
        return sorted(rows,key=lambda r:r['deletedAt'],reverse=True)
    def restore(self,u,p,kind,identifier):
        self.flow.identity.action(u,p,'recycle.manage');row=self.get(u,kind,identifier);require(row and row.get('deletedAt'),'回收站记录不存在',404,'NOT_FOUND')
        try:expired=datetime.strptime(self.flow.clock.now(),'%Y-%m-%d %H:%M:%S')>datetime.strptime(row['deletedAt'],'%Y-%m-%d %H:%M:%S')+timedelta(days=30)
        except (ValueError,TypeError):expired=False
        require(not expired,'该记录已超过 30 天恢复期限')
        parent=self.flow.portfolio.recycle_get(u,'category',row.get('categoryId') or '') if kind=='project' else self.flow.portfolio.raw_project(u,row.get('projectId') or '') if kind=='requirement' else None
        require(not parent or not parent.get('deletedAt'),'请先恢复所属上级记录')
        if kind in {'category','project'}:self.flow.portfolio.recycle_restore(u,kind,identifier)
        elif kind=='requirement':self.flow.work.recycle_restore(u,identifier)
        else:self.demand.recycle_restore(u,identifier)
        self.flow.audit.record(u,p,self.KINDS[kind][0],identifier,row.get(self.KINDS[kind][2]) or identifier,'restore','从回收站恢复',before=row);return {'ok':1}
    def purge(self,u,p,kind,identifier):
        self.flow.identity.super_admin(p);row=self.get(u,kind,identifier);require(row and row.get('deletedAt'),'回收站记录不存在',404,'NOT_FOUND')
        if kind=='category':require(not self.flow.portfolio.raw_category_children(u,identifier),'请先彻底删除大类下的项目')
        if kind=='project':require(not self.flow.work.raw_project_children(u,identifier),'请先彻底删除项目下的需求');self.flow.work.purge_project_sprints(u,identifier)
        if kind=='requirement':self.flow.work.recycle_purge(u,identifier);self.flow.inbox.purge_for_work(u,identifier)
        elif kind in {'category','project'}:self.flow.portfolio.recycle_purge(u,kind,identifier)
        else:self.demand.recycle_purge(u,identifier)
        self.flow.audit.record(u,p,self.KINDS[kind][0],identifier,row.get(self.KINDS[kind][2]) or identifier,'purge','从回收站彻底删除',before=row);return {'ok':1}
