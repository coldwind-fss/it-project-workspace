"""Scoped collection tokens and immutable campaign/recipient snapshots."""
import json
import re
from itpm.infrastructure.database import Repository
from itpm.core.errors import require
from itpm.core.ports import Principal
from itpm.core.json_fields import list_field,object_field
from itpm.modules.identity.public import same_name


def text(d,k,default='',limit=None):
    value=str(d.get(k) or default).strip();return value[:limit] if limit else value


def classify_error(error):
    value=str(error).lower()
    for markers,code,status in [(['staffid.notexisted','staff id not exist','invalidstaffid','invalid user','人员不存在'],'invalid_recipient','invalid'),
        (['qpslimit','qps limit','too many requests','http 429','flowcontrol','限流','调用频数过高','请求总次数超过'],'rate_limited','failed'),
        (['forbidden','accessdenied','permission','权限不足','无权限'],'permission_denied','failed'),
        (['timeout','timed out','连接中断','connection reset','connection aborted','read timed out'],'unknown_result','unknown'),
        (['http 500','http 502','http 503','http 504','temporarily unavailable','temporary'],'temporary_provider','failed')]:
        if any(x in value for x in markers):return code,status
    return 'provider_error','failed'


class Collection:
    def __init__(self,db,clock,ids,identity,demand,files,audit,base):
        self.repo=Repository(db,['demand_pool_link_notifications','demand_pool_link_recipients','demand_collection_batches','demand_collection_responses'])
        self.clock,self.ids,self.identity,self.demand,self.files,self.audit,self.base=clock,ids,identity,demand,files,audit,base
    def token(self,u,token,lock=False):return self.repo.get(u,'demand_pool_link_recipients',token,lock=lock) if token else None
    def actor(self,row):return Principal(userId=row.get('recipientUserId') or '',name=row.get('recipientName') or '钉钉用户')
    def used(self,u,row,did=''):
        values={'usedAt':self.clock.now()}
        if did:values['lastDemandId']=did
        self.repo.change(u,'demand_pool_link_recipients',row['token'],values)
    def entry_link(self,token,mode='collect',did=''):
        return self.base+'#/entry/demand?recipientToken='+token+('&mode='+mode if mode!='collect' else '')+('&demandId='+did if did else '')
    def entry(self,u,token):
        require(token,'提报链接缺少身份令牌');row=self.token(u,token);require(row,'提报链接已失效或不存在',404,'NOT_FOUND')
        demand=self.demand.get(u,row.get('demandId') or '')
        return {'valid':True,'notificationId':row.get('notificationId') or '','entryMode':row.get('entryMode') or 'collect','demandId':row.get('demandId') or '',
            'recipientUserId':row.get('recipientUserId') or '','recipientName':row.get('recipientName') or '钉钉用户','department':row.get('recipientDepartment') or '',
            'usedAt':row.get('usedAt') or '','demand':{k:demand.get(k) for k in ['id','title','description','department','projectName','status']} if demand else None}
    def response(self,u,identifier):return self.repo.get(u,'demand_collection_responses',identifier)
    def response_payload(self,u,row):
        item={**row,'judgmentLabel':self.demand.v['DEMAND_COLLECTION_JUDGMENT_LABELS'].get(row.get('judgment'),row.get('judgment') or '待判断'),
            'responseData':object_field(row.get('responseData')),'attachments':self.files.list(u,'demand_collection_response',row['id'])}
        converted=self.demand.get(u,row.get('convertedDemandId') or '',active=True)
        item['convertedDemand']={k:converted[k] for k in ['id','title','status']} if converted else None
        if converted:item['convertedDemand']['statusLabel']=self.demand.v['DEMAND_POOL_STATUS_LABELS'].get(converted['status'],converted['status'] or '未设置')
        return item
    def ensure_legacy_batch(self,u,row):
        if row.get('batchId'):return row['batchId']
        notice=self.repo.get(u,'demand_pool_link_notifications',row.get('notificationId') or '')
        if not notice:return ''
        identifier='dcblegacy'+notice['id'];now=self.clock.now()
        if not self.repo.get(u,'demand_collection_batches',identifier):
            self.repo.add(u,'demand_collection_batches',{'id':identifier,'notificationId':notice['id'],
                **{k:notice.get(k) or '' for k in ['targetType','targetValue','targetLabel','message','sentByUserId','sentByName']},
                'status':'historical','recipientCount':len(list_field(notice.get('recipientUserIds'))),'successCount':notice.get('successCount') or 0,'failureCount':notice.get('failureCount') or 0,
                'responseCount':0,'pendingCount':0,'valuableCount':0,'excludedCount':0,'sentAt':notice.get('sentAt') or notice.get('createdAt') or now,'createdAt':notice.get('createdAt') or now,'updatedAt':now},conflict=['id'])
        self.repo.change(u,'demand_pool_link_recipients',row['token'],{'batchId':identifier});return identifier
    def submit_response(self,u,data):
        token=text(data,'recipientToken');require(token,'主动征集链接缺少身份令牌');row=self.token(u,token,True)
        require(row and row['entryMode']=='collect','主动征集链接已失效或不存在',404,'NOT_FOUND')
        existing=self.repo.find(u,'demand_collection_responses',{'recipientToken':token},lock=True)
        if existing:return {**self.response_payload(u,existing[0]),'isCollectionResponse':True,'responseId':existing[0]['id']}
        problem=text(data,'problem');require(problem,'请填写当前遇到的问题');require(len(problem)<=10000,'问题说明最多10000字')
        department=text(data,'department',row.get('recipientDepartment') or '');require(department,'请选择归属业务部门')
        topic=text(data,'topicLabel',limit=160);frequency=text(data,'frequency',limit=80);desired=text(data,'desired',limit=5000)
        description=text(data,'description') or '\n'.join([f"【{topic or '其他想法'}】",problem]+(['发生频率：'+frequency] if frequency else [])+(['希望变化：'+desired] if desired else []))
        bid=self.ensure_legacy_batch(u,row);require(bid,'主动征集批次不存在，请联系 IT 重新发送');now=self.clock.now()
        rd={'topicKey':text(data,'topicKey',limit=80),'topicLabel':topic,'problem':problem,'frequency':frequency,'desired':desired,'department':department,
            'expectedDeliveryTime':text(data,'expectedDeliveryTime',limit=40),'businessPriority':text(data,'businessPriority','normal',40)}
        title=next((x.strip() for x in description.splitlines() if x.strip()),'未命名业务需求');title=title[:77]+'…' if len(title)>80 else title
        record={'id':self.ids.new('dcr',12),'batchId':bid,'notificationId':row.get('notificationId') or '', 'recipientToken':token,
            'recipientUserId':row.get('recipientUserId') or '','recipientName':row.get('recipientName') or '钉钉用户','recipientDepartment':row.get('recipientDepartment') or '',
            **rd,'topicLabel':topic or '其他想法','title':title,'description':description,'intakeLevel':'L3','responseData':json.dumps(rd,ensure_ascii=False),
            'judgment':'pending','judgmentReason':'','similarDemandId':'','nextAction':'','judgedByUserId':'','judgedByName':'','judgedAt':'','convertedDemandId':'','createdAt':now,'updatedAt':now}
        self.repo.add(u,'demand_collection_responses',record);self.used(u,row)
        return {**self.response_payload(u,self.response(u,record['id'])),'isCollectionResponse':True,'responseId':record['id']}
    def judge(self,u,p,identifier,data):
        self.identity.action(u,p,'demand_pool.manage');old=self.response(u,identifier);require(old,'主动征集回执不存在',404,'NOT_FOUND')
        judgment=text(data,'judgment');require(judgment in set(self.demand.v['DEMAND_COLLECTION_JUDGMENT_LABELS'])-{'pending'},'请选择有效的 IT 判断结果')
        reason=text(data,'judgmentReason',text(data,'reason'),5000);similar=text(data,'similarDemandId')
        require(judgment=='valuable' or reason,'该判断需要填写原因');require(judgment!='duplicate' or similar,'重复需求必须选择要关联的已有需求')
        if judgment=='duplicate':require(self.demand.get(u,similar,active=True),'关联的已有需求不存在')
        converted=old.get('convertedDemandId') or ''
        if judgment=='duplicate':converted=similar
        elif judgment=='valuable' and not converted:
            row=self.demand.create_collection_demand(u,p,old);converted=row['id']
        now=self.clock.now();self.repo.change(u,'demand_collection_responses',identifier,{'judgment':judgment,'judgmentReason':reason,'similarDemandId':similar if judgment=='duplicate' else '',
            'nextAction':text(data,'nextAction',limit=200),'judgedByUserId':p.userId,'judgedByName':p.name,'judgedAt':now,'convertedDemandId':converted,'updatedAt':now})
        self.audit.record(u,p,'DEMAND_POOL',identifier,old.get('title') or identifier,'collection_judge','主动征集回执判断：'+self.demand.v['DEMAND_COLLECTION_JUDGMENT_LABELS'][judgment],
            after={'judgment':judgment,'convertedDemandId':converted,'similarDemandId':similar if judgment=='duplicate' else ''},source_batch_id=old.get('batchId') or '')
        return self.response_payload(u,self.response(u,identifier))
    def recipients(self,u,target,value,uid=''):
        if target=='person' and uid:return [{'userId':uid,'name':value or uid,'department':''}]
        options=self.identity.options(u);result=[];seen=set();dept_ids=set()
        def walk(nodes):
            for node in nodes:
                if node.get('name')==value:dept_ids.add(str(node.get('id') or node.get('deptId') or ''))
                walk(node.get('children') or [])
        walk(options.get('departmentTree') or [])
        for raw in options.get('users') or []:
            identifier=text(raw,'userid',text(raw,'userId',text(raw,'dingUserId')));name=text(raw,'name',text(raw,'nickname'))
            dept=text(raw,'department',text(raw,'departmentName'))
            match=target=='all' or target=='person' and ((uid and uid==identifier) or same_name(name,value,self.demand.v['DEVELOPERS'])) or target=='department' and (text(raw,'departmentId',text(raw,'departmentID')) in dept_ids or value and value in dept)
            if identifier and identifier not in seen and match:seen.add(identifier);result.append({'userId':identifier,'name':name or identifier,'department':value if target=='department' else dept})
        return result
    def notice_payload(self,row,weekdays=False):
        item={**row,'recipientUserIds':list_field(row.get('recipientUserIds')),'recipientNames':list_field(row.get('recipientNames'))}
        if weekdays:item['scheduleWeekdays']=sorted({int(x) for x in list_field(row.get('scheduleWeekdays')) or [1,2,3,4,5] if str(x).isdigit() and 1<=int(x)<=7})
        return item
    def prepare_notice(self,u,p,data):
        self.identity.action(u,p,'demand_pool.manage');key=text(data,'requestKey',limit=160)
        if key:u.lock_key('collection-notification',key)
        old=self.repo.find(u,'demand_pool_link_notifications',{'requestKey':key}) if key else []
        if old:
            result=self.notice_payload(old[0]);batches=self.repo.find(u,'demand_collection_batches',{'notificationId':old[0]['id']},order=[('createdAt',True)])
            if batches:result.update(batchId=batches[0]['id'],**{k:batches[0][k] for k in ['status','successCount','failureCount','acceptedCount','unknownCount']})
            result['failureDetails']=[];return result,[],False,None
        mode=text(data,'entryMode',text(data,'mode','collect'));require(mode in {'collect','idea','materials'},'不支持的需求入口类型')
        did=text(data,'demandId');demand=self.demand.get(u,did) if did else None;require(mode!='materials' or demand,'指定需求资料补充必须选择有效的需求')
        cycle=text(data,'scheduleCycle','once');require(cycle in {'once','daily','weekly','monthly','custom'},'不支持的征集频率')
        send_time=text(data,'scheduleTime',limit=5)
        try:day=int(data.get('scheduleDay') or 0)
        except (ValueError,TypeError):require(False,'征集日期格式不正确')
        weekdays=sorted({int(x) for x in data.get('scheduleWeekdays',[]) if str(x).isdigit() and 1<=int(x)<=7}) if isinstance(data.get('scheduleWeekdays',[]),list) else []
        if cycle=='daily' and not weekdays:weekdays=[1,2,3,4,5]
        require(cycle=='once' or re.fullmatch(r'\d{2}:\d{2}',send_time),'定期征集需要选择发送时间')
        if cycle=='weekly' and day not in range(1,8) or cycle=='monthly' and day not in range(1,32):day=1
        require(cycle!='custom' or weekdays,'自定义征集频率至少选择一个发送日')
        if mode!='collect':cycle,send_time,day,weekdays='once','',0,[1,2,3,4,5]
        target=text(data,'targetType','person');require(target in {'person','department','all'},'不支持的发送范围')
        value=text(data,'targetValue',text(data,'department',text(data,'recipientName')));uid=text(data,'targetUserId',text(data,'recipientUserId'))
        require(target!='person' or value or uid,'请选择接收人');require(target!='department' or value,'请选择接收部门')
        recipients=self.recipients(u,target,value,uid);require(recipients,'没有找到可发送的钉钉联系人，请刷新联系人后重试')
        link=self.base+'#/entry/demand'+('?mode=materials&demandId='+did if mode=='materials' else '?mode=idea' if mode=='idea' else '')
        intro={'materials':'资料补充','idea':'新想法提报','collect':'需求征集'}[mode]
        message=text(data,'message',{'idea':'你刚才提到有一个新想法，请打开需求提报，把想做什么、当前问题和期望结果告诉 IT。','materials':'请补充这项已沟通需求的资料，几句话或上传附件即可。','collect':'有新的业务需求或复杂问题需要收集，请填写需求提报。'}[mode])
        message+='\n'+('需求：'+(demand.get('title') or '已沟通需求')+'。' if mode=='materials' else '范围：L2 项目、L3 新功能、复杂需求重构。')+f'\n\n[打开{intro}页面]({link})'
        now=self.clock.now();row={'id':self.ids.new('dpn'),'requestKey':key,'entryMode':mode,'demandId':did,'scheduleCycle':cycle,'scheduleTime':send_time,'scheduleDay':day,
            'scheduleWeekdays':json.dumps(weekdays,ensure_ascii=False),'enabled':1,'lastSentDate':'','targetType':target,'targetValue':value,'targetLabel':'全员' if target=='all' else value,
            'recipientUserIds':json.dumps([x['userId'] for x in recipients],ensure_ascii=False),'recipientNames':json.dumps([x['name'] for x in recipients],ensure_ascii=False),
            'message':message,'link':link,'sentByUserId':p.userId,'sentByName':p.name,'status':'pending' if cycle=='once' else 'scheduled','successCount':0,'failureCount':0,'error':'','sentAt':'','createdAt':now,'updatedAt':now}
        self.repo.add(u,'demand_pool_link_notifications',row);send=bool(data.get('sendNow',cycle=='once'));batch=None
        if mode=='collect' and send:
            batch={'id':self.ids.new('dcb',12),'notificationId':row['id'],'requestKey':key,'runKey':key,
                **{k:row[k] for k in ['targetType','targetValue','targetLabel','message','sentByUserId','sentByName']},'status':'sending','recipientCount':len(recipients),
                **{k:0 for k in ['successCount','failureCount','acceptedCount','unknownCount','responseCount','pendingCount','valuableCount','excludedCount']},'sentAt':'','createdAt':now,'updatedAt':now}
            self.repo.add(u,'demand_collection_batches',batch)
        deliveries=[]
        if mode!='collect' or send:
            for person in recipients:
                token=self.ids.new('',32)+self.ids.new('',32);delivery={'token':token,'notificationId':row['id'],'batchId':batch['id'] if batch else '',
                    'entryMode':mode,'demandId':did if mode!='collect' else '','recipientUserId':person['userId'],'recipientName':person['name'],
                    'recipientDepartment':person['department'] or (value if target=='department' else ''),'createdAt':now,'usedAt':'','lastDemandId':''}
                if batch:delivery.update(sendStatus='pending',attemptCount=0,lastAttemptAt='',nextAttemptAt='',acceptedAt='',errorCode='',errorMessage='',providerRequestId='')
                self.repo.add(u,'demand_pool_link_recipients',delivery);deliveries.append(self.token(u,token))
        result=self.notice_payload(row);result.update(status='sending' if batch else row['status'],unknownCount=0,batchId=batch['id'] if batch else '',failureDetails=[])
        return result,deliveries,send,batch
    def claim(self,u,token):
        row=self.repo.get(u,'demand_pool_link_recipients',token,lock=True)
        if not row or row.get('sendStatus') not in {'pending','retry_wait','failed'}:return None
        self.repo.change(u,'demand_pool_link_recipients',token,{'sendStatus':'sending','attemptCount':(row.get('attemptCount') or 0)+1,'lastAttemptAt':self.clock.now()});return row
    def schedules(self,u):return [x for x in self.repo.find(u,'demand_pool_link_notifications',{'enabled':1}) if x.get('scheduleCycle') in {'daily','weekly','monthly','custom'} and x.get('scheduleTime')]
    def scheduled_batch(self,u,row,run_key):
        u.lock_key('collection-run',run_key)
        old=self.repo.find(u,'demand_collection_batches',{'notificationId':row['id'],'runKey':run_key})
        if old:return old[0],[],False
        users=list_field(row.get('recipientUserIds'));names=list_field(row.get('recipientNames'));require(users,'定期征集没有可用的接收人')
        now=self.clock.now();batch={'id':self.ids.new('dcb',12),'notificationId':row['id'],'requestKey':row.get('requestKey') or '', 'runKey':run_key,
            **{k:row.get(k) or '' for k in ['targetType','targetValue','targetLabel','message','sentByUserId','sentByName']},'status':'sending','recipientCount':len(users),
            **{k:0 for k in ['successCount','failureCount','acceptedCount','unknownCount','responseCount','pendingCount','valuableCount','excludedCount']},'sentAt':'','createdAt':now,'updatedAt':now}
        self.repo.add(u,'demand_collection_batches',batch);deliveries=[]
        for index,uid in enumerate(users):
            token=self.ids.new('',32)+self.ids.new('',32);delivery=dict(token=token,notificationId=row['id'],batchId=batch['id'],entryMode=row.get('entryMode') or 'collect',
                demandId=row.get('demandId') or '',recipientUserId=uid,recipientName=names[index] if index<len(names) else uid,
                recipientDepartment=row.get('targetValue') or '' if row.get('targetType')=='department' else '',createdAt=now,usedAt='',lastDemandId='',
                sendStatus='pending',attemptCount=0,lastAttemptAt='',nextAttemptAt='',acceptedAt='',errorCode='',errorMessage='',providerRequestId='')
            self.repo.add(u,'demand_pool_link_recipients',delivery);deliveries.append(delivery)
        return batch,deliveries,True
    def mark_scheduled(self,u,identifier,key,values,error=''):
        self.repo.change(u,'demand_pool_link_notifications',identifier,{**{k:values.get(k) or 0 for k in ['successCount','failureCount']},'status':values.get('status') or 'failed',
            'error':error[:8000],'lastSentDate':key,'sentAt':self.clock.now(),'updatedAt':self.clock.now()})
    def retry_wait(self,u,token,code,error):
        self.repo.change(u,'demand_pool_link_recipients',token,{'sendStatus':'retry_wait','errorCode':code,'errorMessage':error[:2000],'nextAttemptAt':self.clock.now()})
    def finish_scheduled(self,u,p,result):
        count=len(result['recipientUserIds']);self.repo.change(u,'demand_pool_link_notifications',result['id'],{'status':'scheduled','failureCount':count,'updatedAt':self.clock.now()})
        result.update(status='scheduled',failureCount=count)
        self.audit.record(u,p,'DEMAND_POOL',result['id'],'需求池提报链接','notify','向'+(result.get('targetLabel') or result['targetType'])+'发送需求提报链接',after={'targetType':result['targetType'],'targetLabel':result['targetLabel'],'successCount':0,'failureCount':count})
    def delivery_result(self,u,row,sent,code='',status='',error='',provider_id=''):
        if not row.get('batchId'):return
        self.repo.change(u,'demand_pool_link_recipients',row['token'],{'sendStatus':'accepted' if sent else status,'acceptedAt':self.clock.now() if sent else row.get('acceptedAt') or '',
            'nextAttemptAt':'','errorCode':code,'errorMessage':error[:2000],'providerRequestId':provider_id})
    def finish_batch(self,u,bid):
        rows=self.repo.find(u,'demand_pool_link_recipients',{'batchId':bid});counts={}
        for r in rows:counts[r.get('sendStatus') or 'pending']=counts.get(r.get('sendStatus') or 'pending',0)+1
        accepted=counts.get('accepted',0);failed=counts.get('failed',0)+counts.get('invalid',0);unknown=counts.get('unknown',0)
        status='sending' if any(counts.get(k) for k in ['pending','sending','retry_wait']) else 'attention_required' if unknown else 'success' if accepted and not failed else 'partial' if accepted else 'failed'
        values={'status':status,'successCount':accepted,'failureCount':failed,'acceptedCount':accepted,'unknownCount':unknown,'sentAt':self.clock.now(),'updatedAt':self.clock.now()}
        self.repo.change(u,'demand_collection_batches',bid,values);return values
    def finish_notice(self,u,p,result,successes,failures,batch=None):
        values=self.finish_batch(u,batch['id']) if batch else {'status':'success' if successes and not failures else 'partial' if successes else 'failed','successCount':len(successes),'failureCount':len(failures),'unknownCount':0}
        error='\n'.join((x.get('name') or x.get('userId') or '未知接收人')+'：'+(x.get('error') or '发送失败') for x in failures)[:8000]
        notice_values={k:values[k] for k in ['status','successCount','failureCount']};notice_values.update(error=error,sentAt=self.clock.now(),updatedAt=self.clock.now())
        self.repo.change(u,'demand_pool_link_notifications',result['id'],notice_values)
        self.audit.record(u,p,'DEMAND_POOL',result['id'],'需求池提报链接','notify','向'+(result.get('targetLabel') or result['targetType'])+'发送需求提报链接',after={'targetType':result['targetType'],'targetLabel':result['targetLabel'],'successCount':values['successCount'],'failureCount':values['failureCount']})
        result.update(**notice_values,unknownCount=values['unknownCount'],failureDetails=failures[:50]);return result
    def batch(self,u,bid):return self.repo.get(u,'demand_collection_batches',bid)
    def batch_payload(self,u,row,details=False):
        responses=self.repo.find(u,'demand_collection_responses',{'batchId':row['id']},order=[('createdAt',True)])
        deliveries=self.repo.find(u,'demand_pool_link_recipients',{'batchId':row['id']},order=[('createdAt',False)]);counts={}
        for x in deliveries:counts[x.get('sendStatus') or 'pending']=counts.get(x.get('sendStatus') or 'pending',0)+1
        keys='token recipientUserId recipientName recipientDepartment sendStatus attemptCount lastAttemptAt nextAttemptAt acceptedAt errorCode errorMessage providerRequestId'.split()
        result={**row,'responseCount':len(responses),'pendingCount':sum(x.get('judgment') in {'','pending'} for x in responses),
            'valuableCount':sum(x.get('judgment')=='valuable' for x in responses),'excludedCount':sum(x.get('judgment') in {'needs_clarification','duplicate','not_feasible','not_adopted'} for x in responses),
            'acceptedCount':counts.get('accepted',0) if deliveries else row.get('acceptedCount') or row.get('successCount') or 0,
            'unknownCount':counts.get('unknown',0) if deliveries else row.get('unknownCount') or 0,'deliveryPendingCount':sum(counts.get(k,0) for k in ['pending','sending','retry_wait']),
            'deliveryStatusCounts':counts,'deliveries':[{**{k:x.get(k) for k in keys},'token':''} for x in deliveries] if details else [],
            'responses':[self.response_payload(u,x) for x in responses] if details else []}
        if deliveries:result['failureCount']=counts.get('failed',0)+counts.get('invalid',0)
        return result
    def retry_candidates(self,u,bid):return [r for r in self.repo.find(u,'demand_pool_link_recipients',{'batchId':bid},order=[('createdAt',False)]) if r['sendStatus']=='failed' and r.get('errorCode') not in {'invalid_recipient','unknown_result'}]
    def notices(self,u):return [self.notice_payload(x,True) for x in self.repo.find(u,'demand_pool_link_notifications',order=[('createdAt',True)],limit=100)]
    def batches(self,u):return [self.batch_payload(u,x) for x in self.repo.find(u,'demand_collection_batches',order=[('createdAt',True)],limit=100)]
    def update_notice(self,u,p,identifier,data):
        self.identity.action(u,p,'demand_pool.manage');row=self.repo.get(u,'demand_pool_link_notifications',identifier);require(row,'征集计划不存在',404,'NOT_FOUND')
        enabled=bool(data.get('enabled',True));self.repo.change(u,'demand_pool_link_notifications',identifier,{'enabled':int(enabled),'status':'scheduled' if enabled else 'paused','updatedAt':self.clock.now()})
        self.audit.record(u,p,'DEMAND_POOL',identifier,'需求征集计划','schedule_update','更新需求征集计划状态',after={'enabled':enabled})
        return self.notice_payload(self.repo.get(u,'demand_pool_link_notifications',identifier))
