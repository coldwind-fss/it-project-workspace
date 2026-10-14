from datetime import datetime,timedelta
import json
from itpm.core.errors import require
from itpm.core.json_fields import object_field,list_field
from itpm.modules.identity.public import same_name
from .performance_rules import score_evidence,PERFORMANCE_ALLOWED_NAMES
from .report_rules import work_report,project_changes

class Insights:
    def __init__(self,repo,clock,ids,identity,postlaunch,allowed_user_id=''):
        self.repo,self.clock,self.ids,self.identity,self.postlaunch,self.allowed_user_id=repo,clock,ids,identity,postlaunch,allowed_user_id
    def dashboard(self,u,kind):
        if kind=='stats':return self.repo.stats(u,self.clock.now()[:7])
        rows=self.repo.dashboard(u,kind)
        if kind=='summary':
            for row in rows:row['owner']=list_field(row.get('owner'))
        return rows
    def report(self,u,period='week',developer=''):
        period='month' if period=='month' else 'week';now=datetime.strptime(self.clock.now(),'%Y-%m-%d %H:%M:%S');today=now.replace(hour=0,minute=0,second=0,microsecond=0)
        start=today.replace(day=1) if period=='month' else today-timedelta(days=today.weekday())
        facts=self.repo.report_sources(u,start.strftime('%Y-%m-%d %H:%M:%S'),(today+timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),developer)
        return work_report(period,self.clock.now(),*facts[:3],project_changes(facts[3]))
    def notification_sources(self,u,start,end,developer=''):
        projects,requirements,changes,_=self.repo.report_sources(u,start,end,developer)
        return projects,requirements,changes
    def performance_identity(self,p):
        self.identity.authenticated(p);require(p.userId,'请在钉钉内重新登录后操作',401,'AUTH_REQUIRED')
        require(self.performance_allowed(p),'个人绩效工作台仅对十叶开放',403,'FORBIDDEN')
    def performance_allowed(self,p):return bool(p.authenticated and (self.allowed_user_id and p.userId==self.allowed_user_id or any(same_name(p.devOwnerName or p.name,name) for name in PERFORMANCE_ALLOWED_NAMES)))
    def month(self,month):
        value=str(month or self.clock.now()[:7]).strip()[:7]
        try:start=datetime.strptime(value+'-01','%Y-%m-%d')
        except ValueError:value=self.clock.now()[:7];start=datetime.strptime(value+'-01','%Y-%m-%d')
        return value,(start+timedelta(days=32)).replace(day=1).strftime('%Y-%m')
    def draft(self,u,p,month):
        month,end=self.month(month);sources=self.repo.performance_sources(u,p,month,end)
        operations=[self.postlaunch.payload(u,row) for row in sources.pop('ops')]
        return score_evidence(operations,month=month,user_name=p.devOwnerName or p.name,generated_at=self.clock.now(),**sources)
    def performance(self,u,p,month):
        self.performance_identity(p);month,_=self.month(month);draft=self.draft(u,p,month)
        rows=self.repo.find(u,'performance_months',{'userId':p.userId,'month':month})
        row=rows[0] if rows else None
        if row:
            row['draft']=object_field(row.get('draft'))
            if row['status']=='final' and row['draft'].get('rows'):draft=row['draft']
        return {'record':row,'draft':draft}
    def save_performance(self,u,p,data):
        self.performance_identity(p);month,_=self.month(data.get('month'));u.lock_key('performance',p.userId+':'+month)
        rows=self.repo.find(u,'performance_months',{'userId':p.userId,'month':month},lock=True);old=rows[0] if rows else None
        require(not old or old['status']!='final','本月绩效已定稿，如需修改请由管理员重新开启',409,'FINALIZED')
        now=self.clock.now();status='final' if bool(data.get('final')) else 'draft'
        row={k:str(data.get(k) or '').strip()[:30000 if k=='finalText' else 10000] for k in ['goals','plan','nextPlan','finalText']}
        row.update(draft=json.dumps(self.draft(u,p,month),ensure_ascii=False),status=status,updatedAt=now,finalizedAt=now if status=='final' else (old or {}).get('finalizedAt') or '')
        identifier=old['id'] if old else self.ids.new('pm')
        if old:self.repo.change(u,'performance_months',identifier,row)
        else:self.repo.add(u,'performance_months',{**row,'id':identifier,'userId':p.userId,'month':month,'createdAt':now})
        return self.repo.get(u,'performance_months',identifier)
