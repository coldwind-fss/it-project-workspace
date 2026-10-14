"""Early inbox capabilities needed by WP01/02. Full personal actions in WP03.
assign/close consume a shared UoW. No network while business transaction open.
"""
from itpm.infrastructure.database import Repository
from sqlalchemy import select, update, or_,case
from itpm.modules.identity.public import IdentityPort

class Inbox:
    def __init__(self,db,clock,ids,people:IdentityPort):
        self.repo=Repository(db,['todos']);self.clock,self.ids,self.people=clock,ids,people
    def assign(self,u,p,req,message,recipients,policy,kind='requirement_assigned'):
        created=[];t=self.repo.table('todos')
        for name in recipients:
            if name in {'待分配','未分配'} or not name:continue
            if policy.get('skipSelfAssignedTodo') and self.people.matches(u,p,name):continue
            s=select(t).where(t.c.requirementid==req['id'],t.c.recipientname==name,t.c.status!='done').order_by(t.c.createdat.desc())
            if kind=='shared_activity':s=s.where(t.c.type==kind)
            old=self.repo.one(u,s)
            if old:continue
            row={'id':self.ids.new('td'),'recipientUserId':self.people.person_id(u,name),'recipientName':name,'requirementId':req['id'],
                'requirementTitle':req.get('title') or '','projectId':req.get('projectId') or '','projectName':req.get('projectName') or req.get('pname') or '',
                'sourceUserId':p.userId,'sourceName':p.name,'type':kind,'status':'unread','message':message,'dingTalkSent':0,'createdAt':self.clock.now(),'readAt':'','doneAt':''}
            self.repo.add(u,'todos',row);row=self.repo.get(u,'todos',row['id']);row['dingTalkSent']=bool(row['dingTalkSent']);created.append(row)
        return created
    def close(self,u,rid):
        t=self.repo.table('todos');rows=self.repo.rows(u,select(t).where(t.c.requirementid==rid,t.c.status!='done'))
        u.connection.execute(update(t).where(t.c.requirementid==rid,t.c.status!='done').values(status='done',doneat=self.clock.now()));return rows
    def mark_sent(self,u,tid):self.repo.change(u,'todos',tid,{'dingTalkSent':1})
    def mark_error(self,u,tid,error):self.repo.change(u,'todos',tid,{'dingTalkError':error})
    def creator_hint(self,u,rid):
        t=self.repo.table('todos');return self.repo.one(u,select(t.c.sourceuserid,t.c.sourcename).where(t.c.requirementid==rid).order_by(t.c.createdat).limit(1))
    def visible(self,u,p,status=''):
        t=self.repo.table('todos');clauses=[t.c.recipientuserid==p.userId,t.c.recipientname==p.name,t.c.recipientname.like('%'+p.name+'%')]
        if p.devOwnerName and p.devOwnerName!=p.name:clauses.extend([t.c.recipientname==p.devOwnerName,t.c.recipientname.like('%'+p.devOwnerName+'%')])
        stmt=select(t).where(or_(*clauses))
        if status and status!='all':stmt=stmt.where(t.c.status==status)
        rows=self.repo.rows(u,stmt.order_by(case((t.c.status=='unread',0),(t.c.status=='read',1),else_=2),t.c.createdat.desc()))
        return [{**x,'dingTalkSent':bool(x.get('dingTalkSent'))} for x in rows]
    def unread(self,u,p):return len(self.visible(u,p,'unread'))
    def purge_for_work(self,u,rid):
        for row in self.repo.find(u,'todos',{'requirementId':rid}):self.repo.remove(u,'todos',row['id'])
    def personal_action(self,u,p,tid,done=False):
        from itpm.core.errors import require
        row=next((x for x in self.visible(u,p) if x['id']==tid),None)
        require(row,'待办不存在或无权访问',404,'NOT_FOUND');now=self.clock.now()
        if done:self.repo.change(u,'todos',tid,{'status':'done','readAt':row.get('readAt') or now,'doneAt':now})
        elif row['status']=='unread':self.repo.change(u,'todos',tid,{'status':'read','readAt':now})
        after=self.repo.get(u,'todos',tid);after['dingTalkSent']=bool(after.get('dingTalkSent'))
        return row,after
    def collaboration_todo(self,u,p,thread,req):
        name=str(thread.get('recipientName') or '').strip()
        if not name or not req:return None
        now=self.clock.now();row={'id':self.ids.new('td'),'recipientUserId':thread.get('recipientUserId') or self.people.person_id(u,name),
            'recipientName':name,'requirementId':req['id'],'businessCollaborationId':thread.get('id') or '',
            'requirementTitle':req.get('title') or '','projectId':req.get('projectId') or '',
            'projectName':req.get('pname') or req.get('projectName') or '', 'sourceUserId':p.userId,'sourceName':p.name,
            'type':'business_collaboration','status':'unread','message':thread.get('content') or thread.get('title') or '请处理业务协作事项',
            'dingTalkSent':0,'createdAt':now,'readAt':'','doneAt':''}
        self.repo.add(u,'todos',row);return self.repo.get(u,'todos',row['id'])
    def close_collaboration(self,u,identifier):
        t=self.repo.table('todos');rows=self.repo.rows(u,select(t).where(t.c.businesscollaborationid==identifier,t.c.status!='done'))
        now=self.clock.now()
        for row in rows:self.repo.change(u,'todos',row['id'],{'status':'done','readAt':row.get('readAt') or now,'doneAt':now})
        return rows
    def close_lifecycle(self,u,thread_id='',rid='',assigned_only=False):
        t=self.repo.table('todos');stmt=select(t).where(t.c.status!='done')
        if thread_id:stmt=stmt.where(t.c.businesscollaborationid==thread_id)
        if rid:stmt=stmt.where(t.c.requirementid==rid)
        if assigned_only:stmt=stmt.where(t.c.type=='requirement_assigned')
        else:stmt=stmt.where(t.c.type=='business_collaboration')
        rows=self.repo.rows(u,stmt)
        for row in rows:self.repo.change(u,'todos',row['id'],{'status':'done','doneAt':self.clock.now()})
