import time
from itpm.core.events import AfterCommitAction
from itpm.core.errors import require
from itpm.modules.collection.public import classify_error


class CollectionSend:
    def __init__(self,collection,gateway,uow_factory,public_url):
        self.collection,self.gateway,self.uow_factory,self.base=collection,gateway,uow_factory,public_url.rstrip('/')
    def dispatch(self,deliveries,notice):
        successes,failures=[],[];c=self.collection
        for delivery in deliveries:
            success=False;error='';code='';status='';provider_id=''
            for attempt in range(1,4):
                if delivery.get('batchId'):
                    with self.uow_factory() as u:
                        if not c.claim(u,delivery['token']):break
                link=c.entry_link(delivery['token'],delivery['entryMode'],delivery.get('demandId') or '')
                public=self.base+'/#'+link.split('#',1)[1]
                message=notice['message'].replace(']('+notice['link']+')',']('+public+')')
                title={'materials':'需求资料补充通知','idea':'新想法提报通知','collect':'需求征集通知'}[delivery['entryMode']]
                try:
                    response=self.gateway.send_markdown_to_users([delivery['recipientUserId']],title,message)
                    provider_id=str((response or {}).get('requestId') or (response or {}).get('request_id') or (response or {}).get('messageId') or '')
                    success=True;code='';status='accepted';error=''
                except Exception as exc:
                    error=str(exc)[:2000];code,status=classify_error(error)
                with self.uow_factory() as u:c.delivery_result(u,delivery,success,code,status,error,provider_id)
                if success or code not in {'rate_limited','temporary_provider'} or attempt==3:break
                if delivery.get('batchId'):
                    with self.uow_factory() as u:c.retry_wait(u,delivery['token'],code,error)
                time.sleep(min(5,2**(attempt-1)))
            result={'userId':delivery['recipientUserId'],'name':delivery['recipientName'],'success':success,'status':status,'attempts':attempt}
            if success:result['providerRequestId']=provider_id;successes.append(result)
            else:result.update(errorCode=code,error=error);failures.append(result)
        return successes,failures
    def send(self,u,p,data):
        c=self.collection;result,deliveries,send,batch=c.prepare_notice(u,p,data)
        if not send:
            if deliveries or result.get('status') in {'pending','scheduled'}:c.finish_scheduled(u,p,result)
            return result
        def after():
            successes,failures=self.dispatch(deliveries,result)
            with self.uow_factory() as write:c.finish_notice(write,p,result,successes,failures,batch)
        u.events.append(AfterCommitAction(after));return result
    def retry(self,u,p,bid):
        c=self.collection;c.identity.action(u,p,'demand_pool.manage');batch=c.batch(u,bid);require(batch,'主动征集批次不存在',404,'NOT_FOUND')
        deliveries=c.retry_candidates(u,bid);require(deliveries,'本批次没有可安全补发的明确失败人员');result={}
        def after():
            successes,failures=self.dispatch(deliveries,{**batch,'link':c.base+'#/entry/demand'})
            with self.uow_factory() as write:
                values=c.finish_batch(write,bid);c.audit.record(write,p,'DEMAND_POOL',bid,'主动征集批次','retry_failures',f'补发主动征集失败人员：{len(successes)} 人已受理',
                    after={'status':values['status'],'successCount':len(successes),'failureCount':len(failures)})
                result.update(status=values['status'],successCount=len(successes),failureCount=len(failures),failureDetails=failures,batch=c.batch_payload(write,c.batch(write,bid),True))
        u.events.append(AfterCommitAction(after));return result
