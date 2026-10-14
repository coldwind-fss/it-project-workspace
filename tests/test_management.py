"""Management synthetic HTTP/PG checks. No production database or real provider."""
import json
import unittest
import test_demand_delivery as fixtures
ROOT=fixtures.ROOT

class ManagementTests(unittest.TestCase):
    settings_overrides={'work_sync_token':'synthetic-work-sync-service-key-32-characters'}
    setUpClass=classmethod(fixtures.DemandDeliveryTests.setUpClass.__func__)
    call=fixtures.DemandDeliveryTests.call
    project_work=fixtures.DemandDeliveryTests.project_work
    formal_work=fixtures.DemandDeliveryTests.formal_work
    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None,None,None)
        (ROOT/'.runtime/test-results/management.json').write_text(json.dumps({'checks':cls.checks,'q04':getattr(cls,'q04',None)},ensure_ascii=False,indent=2),encoding='utf-8')
    def test_01_poc_workbench_and_legacy(self):
        pid,rid=self.project_work()
        opts=self.call('GET','/api/poc-workbench/options')
        self.assertEqual([x['key'] for x in opts['statuses']],['draft','planned','in_progress','completed','archived'])
        self.call('POST','/api/poc-workbench/records',{'title':'无结论完成','status':'completed'},expected=400)
        poc=self.call('POST','/api/poc-workbench/records',{'title':'独立验证','projectId':pid,'requirementId':rid,'objective':'减少手工','metrics':{'accuracy':0.9},'tags':['合成']})
        self.assertEqual(poc['requirementId'],rid);self.assertEqual(poc['status'],'draft')
        file=self.call('POST','/api/business-attachments',data={'ownerType':'poc_workbench','ownerId':poc['id']},files={'file':('poc.txt',b'synthetic conclusion','text/plain')})
        self.assertEqual(self.call('GET','/api/business-attachments/'+file['id']+'/download'),b'synthetic conclusion')
        changed=self.call('PUT','/api/poc-workbench/records/'+poc['id'],{'status':'completed','conclusion':'passed','result':'通过'})
        self.assertEqual(changed['createdAt'],poc['createdAt']);self.assertTrue(changed['completedAt'])
        derived=self.call('POST','/api/poc-workbench/records/'+poc['id']+'/derive-capability',{})
        self.assertEqual(derived['recordType'],'ai_capability');self.assertEqual(derived['derivedFromId'],poc['id']);self.assertEqual(derived['status'],'draft')
        self.call('POST','/api/poc-workbench/records/'+derived['id']+'/derive-capability',{},expected=400)
        rows=self.call('GET','/api/poc-workbench/records?projectId='+pid);self.assertEqual(len(rows),2)
        self.call('GET','/api/poc-workbench/options',role='viewer',expected=403)
        demand=self.call('POST','/api/demand-pool',{'description':'历史PoC来源','department':'隔离测试部'})
        self.call('PUT','/api/demand-pool/'+demand['id'],{'status':'evaluating','solutionType':'existing_capability'})
        legacy=self.call('POST','/api/demand-pool/'+demand['id']+'/pocs',{'summary':'原始结论'})
        legacy_id='legacy-poc-'+legacy['id'];row=self.call('GET','/api/poc-workbench/records/'+legacy_id)
        self.assertTrue(row['legacy']);self.assertTrue(row['readOnly']);self.assertEqual(row['sourceId'],legacy['id'])
        self.call('PUT','/api/poc-workbench/records/'+legacy_id,{'title':'不改旧记录'},expected=400)
        capability=self.call('POST','/api/poc-workbench/records/'+legacy_id+'/derive-capability',{})
        self.assertEqual(capability['sourceRef'],legacy_id)

    def test_02_insights_personal_evidence_and_freeze(self):
        pid,rid=self.project_work()
        for path in ['/api/dashboard/stats','/api/dashboard/bycategory','/api/dashboard/bycategory/summary','/api/dashboard/activities','/api/work-reports?period=month','/api/postlaunch/dashboard']:
            self.call('GET',path)
        self.call('GET','/api/performance/me',role='viewer',expected=403)
        self.app.state.insights.allowed_user_id='stage-editor'
        result=self.call('GET','/api/performance/me?month=2026-10',role='editor')
        self.assertEqual(len(result['draft']['rows']),7)
        # Same-month unrelated requirement is excluded by the approved V2BC02 fix.
        own_count=result['draft']['counts']['requirements']
        self.call('POST','/api/requirements',{'title':'无关同月记录','projectId':pid,'department':'隔离测试部','type':'技术建设','assignee':'隔离无关编辑','requester':'隔离业务','description':'不计入本人','expectedDeliveryTime':'2027-01-01'})
        self.assertEqual(self.call('GET','/api/performance/me?month=2026-10',role='editor')['draft']['counts']['requirements'],own_count)
        saved=self.call('PUT','/api/performance/me',{'month':'2026-10','goals':'合成目标','final':True,'draft':{'counts':{'requirements':999}}},role='editor')
        stored=json.loads(saved['draft']);self.assertEqual(stored['counts']['requirements'],own_count)
        self.call('PUT','/api/requirements/'+rid,{'title':'定稿之后修改'})
        frozen=self.call('GET','/api/performance/me?month=2026-10',role='editor')
        self.assertEqual(frozen['draft'],stored)
        self.call('PUT','/api/performance/me',{'month':'2026-10','goals':'不覆盖'},role='editor',expected=409)

    def test_03_notification_sync_privacy_and_events(self):
        from unittest.mock import patch
        body={'name':'合成个人通知','deliveryChannel':'personal','recipientUserId':'stage-viewer','targetType':'global','scope':'dashboard'}
        self.call('POST','/api/notification/targets',{'name':'缺Webhook'},expected=400)
        rule=self.call('POST','/api/notification/targets',body)
        self.assertEqual(rule['scheduleWeekdays'],[1,2,3,4,5,6,7])
        readonly=self.call('GET','/api/notification/targets',role='viewer')
        self.assertEqual(readonly[0]['recipientUserId'],'');self.assertFalse(readonly[0]['canManage'])
        preview=self.call('POST','/api/notification/preview',body);self.assertIn('实际工作进展',preview['markdown'])
        self.call('POST','/api/notification/preview',body,role='viewer',expected=403)
        before=len(self.app.state.gateway.calls)
        sent=self.call('POST','/api/notification/sync',{'targetId':rule['id']});self.assertEqual(sent['ok'],1)
        self.assertEqual(len(self.app.state.gateway.calls),before+1);self.assertEqual(sent['markdown'],preview['markdown'])
        with patch.object(self.app.state.gateway,'send_markdown_to_users',side_effect=RuntimeError('synthetic provider failure')):
            self.call('POST','/api/notification/sync',{'targetId':rule['id']},expected=400)
        self.assertTrue(any(row['status']=='failed' for row in self.call('GET','/api/notification/deliveries')))
        event=self.call('POST','/api/notification/targets',{**body,'name':'事件通知','triggerType':'event','triggerEvents':['project_created']})
        before=len(self.app.state.gateway.calls);self.project_work()
        self.assertGreater(len(self.app.state.gateway.calls),before)
        source=next(e for e in reversed(self.app.state.dispatcher.events) if e.event_type=='project_created')
        before=len(self.app.state.gateway.calls);self.app.state.dispatcher.dispatch([source]);self.assertEqual(len(self.app.state.gateway.calls),before)
        self.call('DELETE','/api/notification/targets/'+event['id'])

    def test_04_work_sync_preview_commit_replay_guard_and_rollback(self):
        self.call('GET','/api/work-intake/schema')
        pid,_=self.project_work()
        data={'projectId':pid,'mode':'preview','idempotencyKey':'k3-sync-main','records':[{'title':'合成同步工作','kind':'feature','developerOwner':'隔离开发者','businessOwner':'隔离业务','logs':[{'content':'完成同步进展'}]}]}
        before=self.call('GET','/api/requirements?projectId='+pid)
        preview=self.call('POST','/api/work-intake',data);self.assertEqual(preview['summary']['create'],1)
        self.assertEqual(before,self.call('GET','/api/requirements?projectId='+pid))
        result=self.call('POST','/api/work-intake',{**data,'mode':'commit'});rid=result['items'][0]['requirementId']
        self.assertEqual(self.call('POST','/api/work-intake',{**data,'mode':'commit'})['status'],'idempotent_replay')
        req=self.call('GET','/api/requirements/'+rid);self.assertEqual(req['flowMode'],'quick_iteration')
        changed={**data,'mode':'commit','records':[{'title':'不同内容'}]};self.call('POST','/api/work-intake',changed,expected=409)
        self.call('GET','/api/work-intake/'+result['batchId'])
        clean=self.call('POST','/api/work-intake/'+result['batchId']+'/rollback',{});self.assertEqual(clean['removedRequirements'],1)
        self.assertEqual(self.call('POST','/api/work-intake/'+result['batchId']+'/rollback',{})['removedRequirements'],0)
        protected=self.call('POST','/api/work-intake',{**data,'mode':'commit','idempotencyKey':'k3-sync-protected'})
        rid=protected['items'][0]['requirementId'];self.call('POST','/api/requirements/'+rid+'/work-logs',{'content':'批次之后的人工追加'})
        self.call('POST','/api/work-intake/'+protected['batchId']+'/rollback',{},expected=409)
        self.assertEqual(self.call('GET','/api/requirements/'+rid)['deletedAt'],'')

    def test_05_worker_persistence_due_and_workdays(self):
        from itpm.worker import run_once
        from itpm.modules.notifications.public import notification_schedule_due
        from datetime import datetime
        self.assertFalse(notification_schedule_due(datetime(2026,10,17,9),'custom',schedule_weekdays=[1,2,3,4,5]))
        self.assertTrue(notification_schedule_due(datetime(2026,10,13,9),'daily',schedule_weekdays=[1]))
        rule=self.call('POST','/api/notification/targets',{'name':'定时合成通知','deliveryChannel':'personal','recipientUserId':'stage-viewer','scheduleTime':'09:00','scheduleCycle':'daily'})
        collection=self.call('POST','/api/demand-pool/notifications',{'entryMode':'collect','targetType':'person','targetUserId':'stage-viewer','targetValue':'隔离业务','scheduleCycle':'daily','scheduleTime':'09:00','sendNow':False})
        before=len(self.app.state.gateway.calls);first=run_once(self.app);self.assertGreaterEqual(first['processed'],2)
        self.assertGreater(len(self.app.state.gateway.calls),before)
        before=len(self.app.state.gateway.calls);run_once(self.app);self.assertEqual(len(self.app.state.gateway.calls),before)
        # Reconstruct the process on the same persisted DB; no implicit seed/startup.
        from itpm.app import create_app
        from itpm.infrastructure.gateway import FakeGateway
        restarted=create_app(self.app.state.database.settings,clock=self.app.state.flow.clock,gateway=FakeGateway())
        try:run_once(restarted);self.assertEqual(restarted.state.gateway.calls,[])
        finally:restarted.state.database.close()
        self.call('DELETE','/api/notification/targets/'+rule['id'])
        self.call('PUT','/api/demand-pool/notifications/'+collection['id'],{'enabled':False})

    def test_06_service_scope_and_sync_atomicity(self):
        from unittest.mock import patch
        pid,_=self.project_work();headers={'X-PM-Work-Sync-Token':self.settings_overrides['work_sync_token']}
        data={'projectId':pid,'mode':'commit','idempotencyKey':'k3-service-own','records':[{'title':'服务自有工作','developerOwner':'隔离开发者','businessOwner':'隔离业务'}]}
        response=self.client.post('/api/work-intake',json=data,headers=headers);self.assertEqual(response.status_code,200,response.text)
        result=response.json();rid=result['items'][0]['requirementId'];creator=self.call('GET','/api/requirements/'+rid)['createdByUserId']
        corrected=self.client.post('/api/work-intake/owner-correction',headers=headers,json={'requirementIds':[rid],'developerOwner':'隔离无关编辑','businessOwner':'隔离业务'})
        self.assertEqual(corrected.status_code,200,corrected.text);self.assertTrue(corrected.json()['auditCreatorUnchanged'])
        self.checks.append({'method':'POST','path':'/api/work-intake/owner-correction','expected':200,'actual':corrected.status_code,'actor':'scoped_service'})
        self.assertEqual(self.call('GET','/api/requirements/'+rid)['createdByUserId'],creator)
        _,human=self.project_work();self.assertEqual(self.client.post('/api/work-intake/owner-correction',headers=headers,json={'requirementIds':[human],'developerOwner':'隔离开发者','businessOwner':'隔离业务'}).status_code,403)
        human_batch=self.call('POST','/api/work-intake',{**data,'idempotencyKey':'k3-human-batch','records':[{'title':'人工批次'}]})
        self.assertEqual(self.client.get('/api/work-intake/'+human_batch['batchId'],headers=headers).status_code,403)
        self.assertEqual(self.client.post('/api/work-intake/'+human_batch['batchId']+'/rollback',headers=headers,json={}).status_code,403)
        before=self.call('GET','/api/requirements?projectId='+pid);original=self.app.state.flow.work.sync_create;count=0
        def fail_second(*args,**kwargs):
            nonlocal count
            count+=1
            if count==2:raise RuntimeError('synthetic second sync failure')
            return original(*args,**kwargs)
        with patch.object(self.app.state.flow.work,'sync_create',side_effect=fail_second):
            self.call('POST','/api/work-intake',{**data,'idempotencyKey':'k3-atomic-fail','records':[{'title':'原子第一项'},{'title':'原子第二项'}]},expected=500)
        self.assertEqual(before,self.call('GET','/api/requirements?projectId='+pid))

    def test_07_recycle_session_permissions_and_parent_guards(self):
        pid,rid=self.project_work();self.call('DELETE','/api/requirements/'+rid)
        rows=self.call('GET','/api/recycle-bin');self.assertTrue(any(x['id']==rid and x['type']=='requirement' for x in rows))
        self.call('POST','/api/recycle-bin/requirement/'+rid+'/restore',{});self.assertFalse(self.call('GET','/api/requirements/'+rid)['deletedAt'])
        self.call('DELETE','/api/requirements/'+rid)
        self.call('DELETE','/api/recycle-bin/requirement/'+rid,role='admin',expected=403)
        self.call('DELETE','/api/recycle-bin/requirement/'+rid);self.call('GET','/api/requirements/'+rid,expected=404)
        viewer=self.call('GET','/api/session',role='viewer');self.assertNotIn('notification.manage',viewer['actions']);self.assertIn('requirements',viewer['permissions'])
        self.call('GET','/api/recycle-bin',role='viewer',expected=403)
        self.assertEqual(self.client.get('/api/session').status_code,401)
        category=self.call('POST','/api/categories',{'name':'K3父子恢复验收'})
        project=self.call('POST','/api/projects',{'name':'K3恢复层级项目','categoryId':category['id'],'department':'隔离测试部','devOwner':'隔离开发者','targetEndDate':'2027-01-01','solutionType':'custom_application'})
        self.call('POST','/api/requirements',{'title':'K3恢复子工作','projectId':project['id'],'type':'技术建设','department':'隔离测试部','assignee':'隔离开发者','expectedDeliveryTime':'2027-01-01'})
        children=self.call('GET','/api/requirements?projectId='+project['id'])
        for child in children:self.call('DELETE','/api/requirements/'+child['id'])
        self.call('DELETE','/api/projects/'+project['id']);self.call('DELETE','/api/categories/'+category['id'])
        self.call('POST','/api/recycle-bin/project/'+project['id']+'/restore',{},expected=400)
        self.call('POST','/api/recycle-bin/requirement/'+children[0]['id']+'/restore',{},expected=400)
        self.call('DELETE','/api/recycle-bin/project/'+project['id'],expected=400)
        self.call('POST','/api/recycle-bin/category/'+category['id']+'/restore',{})
        self.call('POST','/api/recycle-bin/project/'+project['id']+'/restore',{})
        self.call('POST','/api/recycle-bin/requirement/'+children[0]['id']+'/restore',{})
        # Date gate is tested on a synthetic row only.
        self.call('DELETE','/api/requirements/'+children[0]['id'])
        from sqlalchemy import text
        with self.db.engine.begin() as connection:connection.execute(text('UPDATE requirements SET deletedAt=:date WHERE id=:rid'),{'date':'2026-08-01 09:00:00','rid':children[0]['id']})
        self.call('POST','/api/recycle-bin/requirement/'+children[0]['id']+'/restore',{},expected=400)

    def test_08_shared_callback_facts_and_independent_rounds(self):
        from sqlalchemy import select,insert,text
        from itpm.modules.postlaunch.rules import unique_requests,pending_count
        did,rid=self.formal_work();self.call('PUT','/api/requirements/'+rid,{'title':'K3-Q04共享与独立轮次'})
        first=self.call('POST','/api/postlaunch/operations',{'requirementId':rid,'deliveryRoundId':'q04-round-one','deliveryDate':'2026-09-01','useStartDate':'2026-09-01'})
        # Reproduce a historical projection referencing exactly the same two persisted requests.
        table=self.db.table('postlaunch_operations')
        with self.db.engine.begin() as connection:
            duplicate=dict(connection.execute(select(table).where(table.c.id==first['id'])).mappings().one())
            duplicate.pop('rowid',None);duplicate['id']='synthetic-q04-shared-operation'
            duplicate['deliveryroundid']='q04-historical-projection'
            connection.execute(insert(table).values(**duplicate))
        second=self.call('POST','/api/postlaunch/operations',{'requirementId':rid,'deliveryRoundId':'q04-round-two','deliveryDate':'2026-09-02','useStartDate':'2026-09-02'})
        other_did,other_rid=self.formal_work();self.call('PUT','/api/requirements/'+other_rid,{'title':'K3-Q04独立L3'})
        third=self.call('POST','/api/postlaunch/operations',{'requirementId':other_rid,'deliveryRoundId':'q04-independent-L3','deliveryDate':'2026-09-03','useStartDate':'2026-09-03'})
        operations=[first,second,third];request_ids={r['id'] for op in operations for r in op['outcomeRequests']}
        self.assertEqual(len(request_ids),6)
        before=self.call('GET','/api/postlaunch/dashboard?keyword=K3-Q04')
        self.assertEqual(before['summary']['operations'],4)
        self.assertEqual(before['summary']['day7Pending'],3);self.assertEqual(before['summary']['day30Pending'],3)
        definitions={'metrics':[{'key':'duration','baselineValue':10,'targetValue':5,'direction':'lower'}]}
        with self.db.engine.begin() as connection:
            for source in [did,other_did]:
                connection.execute(text('UPDATE demand_pool_value_cards SET baseline=:value,expected=:value WHERE demandId=:did'),{'value':json.dumps(definitions),'did':source})
            for identifier in request_ids:
                connection.execute(text("UPDATE demand_pool_value_requests SET sentAt=:sent,notificationStatus='success' WHERE id=:id"),{'sent':'2026-09-04 09:00:00','id':identifier})
        for index,operation in enumerate(operations):
            positive=index!=1
            for request in operation['outcomeRequests']:
                payload={'token':request['link'].split('token=')[1],'summary':'Q04合成回执'}
                if request['stage']=='day7':payload.update(useStatus='已正常使用' if positive else '还未开始使用',satisfaction='满意' if positive else '需要改进',goalStatus='已解决' if positive else '暂未解决')
                else:payload.update(effectStatus='有明显改善' if positive else '暂无明显改善',metricResults=[{'key':'duration','actualValue':3 if positive else 8}])
                self.call('POST','/api/demand-pool-outcome-submit',payload)
        result=self.call('GET','/api/postlaunch/dashboard?keyword=K3-Q04');metrics={x['key']:x for x in result['metrics']}
        self.assertEqual(result['summary']['day7Pending'],0);self.assertEqual(result['summary']['day30Pending'],0)
        self.assertEqual((metrics['responseRate']['numerator'],metrics['responseRate']['denominator']),(6,6))
        for key in ['satisfactionRate','usageRate','efficiencyRate']:
            self.assertEqual((metrics[key]['numerator'],metrics[key]['denominator'],metrics[key]['value']),(2,3,66.7),key)
        # Operation/round detail remains four rows; only the repeated request fact is collapsed.
        self.assertEqual(len(result['rows']),4);self.assertEqual(sum(x['l3Count'] for x in result['l2Rows']),4)
        self.assertEqual(len({r['id'] for op in result['rows'] for r in op['outcomeRequests']}),6)
        self.assertEqual(len(unique_requests([{'id':''},{'id':''}])),2)
        self.assertEqual(pending_count([{'day7DueDate':'2026-09-01','outcomeRequests':[]}] * 2,'day7','2026-10-13'),2)
        type(self).q04={'passed':True,'scope':'real isolated PG + HTTP; one repeated pair, an independent round and an independent L3',
            'operationRows':4,'uniqueRequests':6,'pendingBefore':{'day7':3,'day30':3},
            'response':{'numerator':6,'denominator':6},'satisfactionUsageEfficiency':{'numerator':2,'denominator':3,'value':66.7},
            'unknownLegacyIdentity':'preserved separately','databaseStructure':'unchanged'}

if __name__=='__main__':unittest.main()
