from itpm.core.events import AfterCommitAction
from itpm.core.errors import require
from itpm.modules.notifications.public import normalize_target,notification_recipient_ids,notification_record_matches

class NotificationSend:
    def __init__(self,notifications,gateway,uow_factory,audit):self.notifications,self.gateway,self.uow_factory,self.audit=notifications,gateway,uow_factory,audit
    def prepare(self,u,target,event_type='',record=None,trigger='manual',key='',schedule_key=''):
        n=self.notifications;target=normalize_target(target);markdown=n.markdown(u,target,event_type,record)
        identifier=n.reserve(u,target,trigger,event_type,key);result={}
        if not identifier:return {'ok':1,'skipped':True}
        def after():
            sent=True;error='';response={};title=(target.get('developer') or '开发者')+'工作同步' if target.get('scope')=='developer' else '项目产品变化同步'
            try:
                if target['deliveryChannel']=='personal':
                    recipients=notification_recipient_ids(target);require(recipients,'当前个人通知规则未配置接收人 UserId')
                    response=self.gateway.send_markdown_to_users(recipients,title,markdown)
                else:
                    require(target.get('webhook'),'当前通知规则未配置群机器人 Webhook')
                    response=self.gateway.send_group_markdown(target['webhook'],target.get('secret') or '',title,markdown)
            except Exception as exc:sent=False;error=str(exc)
            with self.uow_factory() as write:error=n.finish(write,target,identifier,sent,error,schedule_key)
            result.update({'ok':1,'result':response,'markdown':markdown} if sent else {'error':error[:4000]})
        u.events.append(AfterCommitAction(after));return result
    def manual(self,u,p,data):
        n=self.notifications
        if data.get('targetId'):
            target=n.get(u,data['targetId']);require(target,'通知目标不存在',404,'NOT_FOUND');return self.prepare(u,target)
        targets=n.select_targets(u,data.get('scope') or 'dashboard')
        if data.get('developer'):targets=[r for r in targets if not r.get('developer') or r['developer']==data['developer']]
        if data.get('developerUserId'):targets=[r for r in targets if not r.get('developerUserId') or r['developerUserId']==data['developerUserId']]
        results=[self.prepare(u,r) for r in targets];result={}
        def combine():
            failed=next((r for r in results if r.get('error')),None);result.update(failed or {'ok':1,'sent':len(results)})
        u.events.append(AfterCommitAction(combine));return result
    def event(self,event):
        n=self.notifications
        with self.uow_factory() as u:
            for target in n.event_targets(u):
                if event.event_type not in target['triggerEvents'] or not notification_record_matches(target,event.payload):continue
                self.prepare(u,target,event.event_type,event.payload,'event',event.dedupe_key)
