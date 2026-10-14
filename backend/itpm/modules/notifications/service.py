from datetime import datetime
import json
from itpm.core.errors import require
from .rules import (normalize_target,parse_list_field,notification_weekday_values,notification_record_matches,
    NOTIFICATION_EVENT_OPTIONS,NOTIFICATION_REPORT_SCENES,REPORTING_ACTIVE_STATUSES,LEGACY_STATUS_MAP,
    target_range,target_range_label,_notification_status_phrase,render_report,notification_event_detail)

class Notifications:
    def __init__(self,repo,clock,ids,identity,portfolio,work,insights,base):
        self.repo,self.clock,self.ids,self.identity,self.portfolio,self.work,self.insights,self.base=repo,clock,ids,identity,portfolio,work,insights,base.rstrip('/')
    def get(self,u,identifier):return self.repo.get(u,'notification_targets',identifier)
    def select_targets(self,u,scope):return self.repo.find(u,'notification_targets',{'enabled':1,'scope':scope})
    def event_targets(self,u):return [normalize_target(x) for x in self.repo.find(u,'notification_targets',{'enabled':1,'triggerType':'event'})]
    def scheduled_targets(self,u):return [normalize_target(x) for x in self.repo.find(u,'notification_targets',{'enabled':1}) if (x.get('triggerType') or 'schedule')=='schedule' and x.get('scheduleTime')]
    def targets(self,u,p):
        manage=self.identity.has(u,p,'notification.manage');rows=[]
        for raw in self.repo.find(u,'notification_targets',order=[('createdAt',True)]):
            row=normalize_target(raw);row['canManage']=manage
            if not manage:
                for key in ['webhook','secret','recipientUserId','developerUserId','ownerUserId']:row[key]=''
            rows.append(row)
        return rows
    def values(self,u,p,data,old=None):
        old=old or {};merged={**old,**data};channel=merged.get('deliveryChannel') or 'group';kind=merged.get('targetType') or 'global';trigger=merged.get('triggerType') or 'schedule'
        require(merged.get('name'),'name required');require(channel in {'group','personal'},'不支持的通知渠道')
        require(channel!='group' or merged.get('webhook'),'群机器人通知必须填写 Webhook');require(channel!='personal' or str(merged.get('recipientUserId') or '').strip(),'个人通知必须选择至少一名接收人')
        require(kind in {'global','developer','project','requirement'},'不支持的数据对象范围')
        if kind=='project':require(merged.get('projectId'),'单独项目通知必须选择项目');require(self.portfolio.project(u,merged['projectId']),'指定项目不存在或已在回收站')
        if kind=='requirement':require(merged.get('requirementId'),'单独需求通知必须选择需求');require(self.work.requirement(u,merged['requirementId']),'指定需求不存在或已在回收站')
        require(trigger in {'schedule','event'},'不支持的触发方式');events=parse_list_field(merged.get('triggerEvents'),[])
        require(trigger!='event' or events,'事件触发规则至少选择一个事件');require(all(x in NOTIFICATION_EVENT_OPTIONS for x in events),'包含不支持的事件类型')
        scene=str(merged.get('reportScene') or ('milestone' if trigger=='event' else 'daily')).strip();require(scene in NOTIFICATION_REPORT_SCENES,'不支持的通知场景')
        cycle=merged.get('scheduleCycle') or 'daily';require(cycle in {'daily','weekly','monthly','custom'},'不支持的同步频率')
        days=notification_weekday_values(cycle,merged.get('scheduleWeekdays'),fallback=[]);require(cycle!='custom' or days,'自定义频率至少选择一个发送日')
        time_range=merged.get('contentRange') or 'today';require(time_range in {'today','last7days','thisMonth','lastMonth','custom'},'不支持的数据时间范围')
        require(time_range!='custom' or merged.get('customRangeStart') and merged.get('customRangeEnd'),'自定义范围必须填写开始和结束日期')
        fields='name webhook secret cardConversationId cardTemplateId cardRobotCode recipientName recipientUserId projectId requirementId developer developerUserId customContent scheduleTime customRangeStart customRangeEnd'.split()
        row={k:merged.get(k) or '' for k in fields}
        row.update(deliveryChannel=channel,cardTargetType=merged.get('cardTargetType') or 'personal',scope='developer' if kind=='developer' else merged.get('scope') or 'dashboard',
            targetType=kind,ownerUserId=merged.get('ownerUserId') or p.userId,ownerName=merged.get('ownerName') or p.name,
            contentTypes=json.dumps(data.get('contentTypes',parse_list_field(old.get('contentTypes'),['dashboard','todayActivities'])),ensure_ascii=False),
            enabled=int(bool(merged.get('enabled',True))),scheduleCycle=cycle,scheduleDay=int(merged.get('scheduleDay') or 0),scheduleWeekdays=json.dumps(days,ensure_ascii=False),
            triggerType=trigger,triggerEvents=json.dumps(events,ensure_ascii=False),reportScene=scene,contentRange=time_range,updatedAt=self.clock.now())
        return row
    def save(self,u,p,data,identifier=''):
        old=self.get(u,identifier) if identifier else None
        require(not identifier or old,'通知目标不存在',404,'NOT_FOUND');row=self.values(u,p,data,old)
        if old:self.repo.change(u,'notification_targets',identifier,row)
        else:
            identifier=self.ids.new('nt',8);self.repo.add(u,'notification_targets',{**row,'id':identifier,'lastSentDate':'','lastSentAt':'','lastSendStatus':'','lastSendError':'','createdAt':self.clock.now()})
        return normalize_target(self.get(u,identifier))
    def delete(self,u,identifier):self.repo.remove(u,'notification_targets',identifier);return {'ok':1}
    def deliveries(self,u,limit):return self.repo.find(u,'notification_delivery_logs',order=[('createdAt',True)],limit=min(max(int(limit or 50),1),200))
    def report_data(self,u,target):
        developer=target.get('developer') or '' if target.get('scope')=='developer' else '';start,end=target_range(target,self.clock.now())
        projects,reqs,changes=self.insights.notification_sources(u,start,end,developer)
        logs=[r for r in self.repo.progress(u,start,end,developer) if notification_record_matches(target,r)]
        link=lambda rid:self.base+'/#/requirements/'+str(rid)
        milestones=[{'at':r.get('createdAt') or '','title':r.get('title') or '未命名 L3','projectName':r.get('projectName') or r.get('pname') or '未关联 L2','text':'正式登记并进入开发流程','link':link(r['id'])} for r in reqs]
        milestones.extend({'at':r.get('createdAt') or '','title':r.get('title') or '未命名 L3','projectName':r.get('projectName') or r.get('pname') or '未关联 L2','text':_notification_status_phrase('',r.get('oldValue'),r.get('newValue')),'link':link(r['requirementId'])} for r in changes if r.get('requirementId'))
        unique=[];seen=set()
        for row in sorted(milestones,key=lambda r:r['at']):
            key=(row['title'],row['text'],row['at'])
            if key not in seen:seen.add(key);unique.append(row)
        actual=[];seen=set()
        for row in logs:
            key=row.get('workLogId') or row.get('sourceRef') or (row.get('requirementId'),row.get('content'),row.get('workDate'))
            if key in seen:continue
            seen.add(key);actual.append({'at':row.get('workDate') or row.get('occurredAt') or row.get('createdAt') or '',
                'title':row.get('linkedRequirementTitle') or '未命名 L3','projectName':row.get('projectName') or '未关联 L2','content':row.get('content') or '',
                'logType':row.get('logType') or '工作进展','link':link(row.get('requirementId') or '')})
        active=[];today=datetime.strptime(self.clock.now()[:10],'%Y-%m-%d').date()
        for row in self.repo.active(u,developer):
            status=LEGACY_STATUS_MAP.get(row.get('status') or '',row.get('status') or '')
            if status not in REPORTING_ACTIVE_STATUSES or not notification_record_matches(target,row):continue
            anchor=(self.repo.first_started(u,row['id']) or row.get('createdAt') or '')[:10]
            try:days=max((today-datetime.strptime(anchor,'%Y-%m-%d').date()).days+1,1)
            except ValueError:days=1
            active.append({'id':row['id'],'title':row.get('title') or '未命名 L3','projectId':row.get('projectId') or '',
                'projectName':row.get('projectName') or row.get('pname') or '未关联 L2','status':status or '进行中','daysInProgress':days,'latestProgress':self.repo.latest(u,row['id']),'link':link(row['id'])})
        return {'actualProgress':sorted(actual,key=lambda r:r['at']),'milestones':unique,'activeProducts':sorted(active,key=lambda r:(r['projectName'],r['title'])),'rangeLabel':target_range_label(target),'start':start,'end':end,'newProjects':projects}
    def markdown(self,u,target,event_type='',record=None):
        target=normalize_target(target);developer=target.get('developer') or '' if target.get('scope')=='developer' else ''
        markdown=render_report(self.report_data(u,target),target,developer,self.clock.now())
        return markdown.rstrip()+'\n\n'+notification_event_detail(event_type,record) if event_type else markdown
    def preview(self,u,data):
        target=normalize_target(data or {});title=(target.get('developer') or '全部开发者')+'需求进度预览' if target.get('scope')=='developer' else '项目大盘进度预览'
        return {'ok':1,'title':title,'markdown':self.markdown(u,target)}
    def reserve(self,u,target,trigger,event_type,key):
        if key:
            u.lock_key('notification-send',target['id']+':'+key)
            prior=self.repo.find(u,'notification_delivery_logs',{'targetId':target['id'],'dedupeKey':key})
            if any(x['status'] in {'success','sending'} for x in prior):return None
        identifier=self.ids.new('ndl',18);now=self.clock.now()
        self.repo.add(u,'notification_delivery_logs',dict(id=identifier,targetId=target.get('id') or '',targetName=target.get('name') or '',triggerType=trigger,eventType=event_type,dedupeKey=key,status='sending',error='',sentAt='',createdAt=now,updatedAt=now))
        return identifier
    def finish(self,u,target,identifier,sent,error='',schedule_key=''):
        now=self.clock.now();status='success' if sent else 'failed'
        for value in [target.get('secret'),target.get('webhook')]:
            if value:error=error.replace(value,'[redacted]')
        self.repo.change(u,'notification_delivery_logs',identifier,{'status':status,'error':error[:4000],'sentAt':now if sent else '','updatedAt':now})
        if target.get('id'):
            values={'lastSentAt':now,'lastSendStatus':status,'lastSendError':error[:4000],'updatedAt':now}
            if sent and schedule_key:values['lastSentDate']=schedule_key
            self.repo.change(u,'notification_targets',target['id'],values)
        return error[:4000]
