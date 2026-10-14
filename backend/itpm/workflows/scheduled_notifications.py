from datetime import datetime
from itpm.core.events import AfterCommitAction
from itpm.core.ports import Principal
from itpm.modules.notifications.public import notification_schedule_due,notification_schedule_key

class ScheduledNotifications:
    def __init__(self,rules,sender,collection,collection_sender,value,value_flow,postlaunch,work,uow_factory,clock):
        self.rules,self.sender,self.collection,self.collection_sender,self.value,self.value_flow,self.postlaunch,self.work,self.uow_factory,self.clock=rules,sender,collection,collection_sender,value,value_flow,postlaunch,work,uow_factory,clock
    def tick(self):
        now=datetime.strptime(self.clock.now(),'%Y-%m-%d %H:%M:%S');results=[]
        with self.uow_factory() as u:rules=self.rules.scheduled_targets(u);collections=self.collection.schedules(u);requests=self.value.due_requests(u)
        def due(row):return row.get('scheduleTime')==now.strftime('%H:%M') and notification_schedule_due(now,row.get('scheduleCycle'),row.get('scheduleDay'),row.get('scheduleWeekdays')) and row.get('lastSentDate')!=notification_schedule_key(now,row.get('scheduleCycle'))
        for row in rules:
            if not due(row):continue
            key=notification_schedule_key(now,row.get('scheduleCycle'))
            with self.uow_factory() as u:result=self.sender.prepare(u,row,trigger='schedule',key='schedule:'+key,schedule_key=key)
            results.append({'kind':'rule','id':row['id'],'result':result})
        for row in collections:
            if not due(row):continue
            key=notification_schedule_key(now,row.get('scheduleCycle'));run_key=row['id']+':'+key
            with self.uow_factory() as u:batch,deliveries,created=self.collection.scheduled_batch(u,row,run_key)
            if created:
                success,failures=self.collection_sender.dispatch(deliveries,row)
                with self.uow_factory() as u:
                    values=self.collection.finish_batch(u,batch['id']);self.collection.mark_scheduled(u,row['id'],key,values,'; '.join(x.get('error') or '' for x in failures))
            else:
                values=batch
                with self.uow_factory() as u:self.collection.mark_scheduled(u,row['id'],key,values)
            results.append({'kind':'collection','id':row['id'],'status':values['status']})
        for row in requests:
            with self.uow_factory() as u:
                current=self.value.request(u,row['id']);target=self.value_flow.target(u,current)
                if not current or current.get('sentAt') or current['status']!='pending':continue
                operation=self.postlaunch.operation_for_request(u,row['id'])
                if operation:
                    req=self.work.raw_requirement(u,row.get('requirementId') or '');eligibility=self.value.eligibility(u,req,row.get('requirementId') or '')
                    if not eligibility['eligible']:
                        self.value.reschedule(u,row['id'],operation,row['stage'],False,eligibility['reason']);continue
                if not target:continue
                result={};self.value_flow.after_send(u,Principal(userId='scheduler',name='系统调度',authenticated=True),current,target,result)
            results.append({'kind':'value','id':row['id'],'status':result.get('notificationStatus')})
        return results
