"""Real isolated PG HTTP checks for demand delivery; no production database or provider."""
from pathlib import Path
import hashlib
import hmac
import json
import sys
import time
import unittest
import uuid
from sqlalchemy import text
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'scripts')]
from runtime import prepare_database
from fixtures import seed, NOW
from itpm.app import create_app
from itpm.settings import Settings
from itpm.infrastructure.gateway import FakeGateway


class Clock:
    def now(self):
        return NOW


class DemandDeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        password = json.loads((ROOT / '.runtime/runtime-secret.json').read_text('utf-8'))['password']
        url = prepare_database('pm_test_rebuild_k2_' + uuid.uuid4().hex[:10], password)
        seed(url)
        cls.attachments = ROOT / '.test-runs' / ('k2-' + uuid.uuid4().hex[:10])
        cls.app = create_app(Settings(url, profile='test', attachment_dir=cls.attachments,
            intake_webhook_secret='synthetic-test-secret',**getattr(cls,'settings_overrides',{})), clock=Clock(),
            gateway=FakeGateway(json.loads((ROOT / '.runtime/contacts.json').read_text('utf-8'))))
        cls.client = TestClient(cls.app)
        cls.client.__enter__()
        cls.db = cls.app.state.database
        cls.checks = []

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        (ROOT / '.runtime/test-results/demand-delivery.json').write_text(json.dumps({
            'scope': 'WP03–WP06 incremental HTTP scenarios', 'checks': cls.checks}, ensure_ascii=False, indent=2), encoding='utf-8')

    def call(self, method, path, payload=None, role='super', expected=200, **kwargs):
        response = self.client.request(method, path, json=payload, headers={'X-PM-Session': 'fixture-stage-' + role}, **kwargs)
        self.assertEqual(response.status_code, expected, f'{method} {path}: {response.text}')
        self.checks.append({'method': method, 'path': path, 'expected': expected, 'actual': response.status_code})
        return response.json() if 'json' in response.headers.get('content-type', '') else response.content

    def project_work(self):
        project = self.call('POST', '/api/projects', {'name': '合成产品', 'department': '隔离测试部',
            'devOwner': '隔离开发者', 'businessOwner': '隔离业务', 'solutionType': 'custom_application', 'targetEndDate':'2027-01-01'})
        req = self.call('POST', '/api/requirements', {'title': '合成工作', 'type': '技术建设',
            'projectId': project['id'], 'department': '隔离测试部', 'assignee': '隔离开发者',
            'requester': '隔离业务', 'expectedDeliveryTime': '2027-01-01', 'status': '待处理'})
        return project['id'], req['id']

    def test_01_history_private_materialization_and_files(self):
        pid, rid = self.project_work()
        public = self.call('POST', f'/api/requirements/{rid}/work-logs', {'content': '业务可见历史进度', 'visibility': 'business_shared'}, role='editor')
        private = self.call('POST', f'/api/requirements/{rid}/work-logs', {'content': '内部排查细节', 'visibility': 'it_private'}, role='editor')
        def count():
            with self.db.engine.connect() as c:
                return c.execute(text('SELECT count(*) FROM shared_activities')).scalar()
        before = count()
        rows = self.call('GET', f'/api/requirements/{rid}/shared-activities', role='viewer')
        self.assertEqual(before, count())
        self.assertTrue(any(r['sourceId'] == public['id'] for r in rows))
        self.assertFalse(any(r['sourceId'] == private['id'] for r in rows))
        aid = next(r['id'] for r in rows if r['sourceId'] == public['id'])
        private_aid = next(r['id'] for r in self.call('GET', f'/api/requirements/{rid}/shared-activities', role='editor') if r['sourceId'] == private['id'])
        self.call('POST', f'/api/shared-activities/{private_aid}/comments', {'content': '禁止私有评论'}, role='viewer', expected=403)
        comment = self.call('POST', f'/api/shared-activities/{aid}/comments', {'content': '历史进度回复'}, role='viewer')
        self.assertEqual(before + 1, count())
        file = self.call('POST', '/api/business-attachments', role='viewer',
            files={'file': ('proof.txt', b'preserved history proof', 'text/plain')},
            data={'ownerType': 'shared_activity_comment', 'ownerId': comment['id']})
        self.assertEqual(self.call('GET', '/api/business-attachments/' + file['id'] + '/download', role='viewer'), b'preserved history proof')
        reread = self.call('GET', f'/api/requirements/{rid}/shared-activities', role='viewer')
        activity = next(r for r in reread if r['id'] == aid)
        self.assertEqual(activity['comments'][0]['attachments'][0]['id'], file['id'])
        self.call('DELETE', '/api/business-attachments/' + file['id'], role='viewer')
        self.call('GET', '/api/business-attachments/' + file['id'] + '/download', role='viewer', expected=404)
        self.call('GET', f'/api/requirements/{rid}/shared-activities', role='other', expected=403)
        self.call('POST', f'/api/requirements/{rid}/shared-activities', {'content': '正式共享动态', 'activityType': 'issue'}, role='editor')
        todos = self.call('GET', '/api/todos', role='viewer')
        todo = next(t for t in todos if t['requirementId'] == rid)
        self.call('PUT', '/api/todos/' + todo['id'] + '/read', role='viewer')
        self.call('PUT', '/api/todos/' + todo['id'] + '/done', role='viewer')
        self.call('PUT', '/api/todos/' + todo['id'] + '/done', role='other', expected=404)

    def test_03_demand_parallel_confirmation(self):
        pid,_=self.project_work()
        row=self.call('POST','/api/demand-pool',{'title':'正式主线','description':'减少人工反复录入','department':'隔离测试部','requesterName':'隔离业务','requesterUserId':'stage-viewer','projectId':pid,'expectedDeliveryTime':'2027-01-01'},role='viewer')
        did=row['id'];self.assertFalse(row['requirementIds'])
        self.call('PUT',f'/api/demand-pool/{did}',{'status':'evaluating','solutionType':'existing_capability'})
        result=self.call('PUT',f'/api/demand-pool/{did}/decomposition',{'branches':[{'title':'录入模块','branchKey':'entry'},{'title':'查询模块','branchKey':'query'}],'requireMultiple':True})
        self.call('POST',f'/api/demand-pool/{did}/reviews/reuse',{'contactName':'隔离业务','contactUserId':'stage-viewer','communicationDate':'2026-10-13','decision':'support','prioritySuggestion':'P2','summary':'业务已确认有实施必要'})
        self.call('PUT',f'/api/demand-pool/{did}',{'evaluationDecision':'implement','solutionType':'existing_capability'})
        self.call('PUT',f'/api/demand-pool/{did}/branch-decisions',{'decisions':[{'branchKey':'entry','decision':'implement'},{'branchKey':'query','decision':'implement'}]})
        self.call('POST',f'/api/demand-pool/{did}/convert',{'projectId':pid,'assignee':'隔离开发者','expectedDeliveryTime':'2027-01-01'},expected=400)
        confirmation=self.call('POST',f'/api/demand-pool/{did}/confirmations',{'content':{'scope':'录入和查询','scenarios':'业务日常使用','expected':'录入可查','valueDefinition':{'verificationMode':'outcome','expectedSummary':'减少重复劳动'}}})
        self.call('POST','/api/demand-pool-confirmations/by-token',{'token':confirmation['token'],'decision':'confirmed'},role='viewer')
        self.call('GET',f'/api/demand-pool/{did}',role='viewer')
        result=self.call('POST',f'/api/demand-pool/{did}/convert',{'projectId':pid,'assignee':'隔离开发者','expectedDeliveryTime':'2027-01-01'})
        self.assertEqual(len(result['requirementIds']),2)
        repeated=self.call('POST',f'/api/demand-pool/{did}/convert',{'projectId':pid,'assignee':'隔离开发者','expectedDeliveryTime':'2027-01-01'})
        self.assertEqual(repeated['requirementIds'],result['requirementIds'])
        for rid in result['requirementIds']:
            req=self.call('GET',f'/api/requirements/{rid}');self.assertEqual(req['parentRequirementId'],'');self.assertEqual(req['demandId'],did)
        self.assertTrue(result['demand']['valueCard'])

    def test_04_collection_is_not_formal_demand(self):
        sent=self.call('POST','/api/demand-pool/notifications',{'entryMode':'collect','targetType':'person','targetUserId':'stage-viewer','targetValue':'隔离业务','requestKey':str(uuid.uuid4())})
        with self.subTest('approved_collection_sender_fix_V2BC11'):
            self.assertEqual(sent['successCount'],1,str(sent));self.assertEqual(sent['status'],'success')
        with self.db.engine.connect() as c:token=c.execute(text('SELECT token FROM demand_pool_link_recipients WHERE notificationId=:id'),{'id':sent['id']}).scalar()
        self.call('GET','/api/demand-pool/entry-context?token='+token,role='viewer')
        response=self.call('POST','/api/demand-collections/responses',{'recipientToken':token,'problem':'人工统计耗时','department':'隔离测试部'})
        self.assertFalse(response['convertedDemandId'])
        repeated=self.call('POST','/api/demand-collections/responses',{'recipientToken':token,'problem':'不覆盖原文','department':'隔离测试部'})
        self.assertEqual(response['id'],repeated['id'])
        judged=self.call('PUT','/api/demand-collections/responses/'+response['id'],{'judgment':'valuable'})
        self.assertTrue(judged['convertedDemandId'])
        self.call('GET','/api/demand-collections/batches/'+sent['batchId'])

    def test_02_threads_intake_and_signed_bridge(self):
        pid, rid = self.project_work()
        thread = self.call('POST', f'/api/requirements/{rid}/business-collaborations', {
            'kind': 'clarification', 'title': '请确认字段', 'content': '字段是否正确'}, role='editor')
        self.assertEqual(thread['direction'], 'it_to_business')
        reply = self.call('POST', '/api/business-collaborations/' + thread['id'] + '/messages', {'content': '字段正确'}, role='viewer')
        self.assertEqual(reply['status'], 'waiting_it')
        self.call('PUT', '/api/business-collaborations/' + thread['id'], {'status': 'resolved', 'response': '确认完成'}, role='editor')
        self.call('GET', '/api/business-collaborations/' + thread['id'] + '/messages', role='other', expected=403)
        intake = self.call('POST', '/api/business-requests', {'kind': 'new_requirement', 'title': '旧入口兼容',
            'originalFeedback': '旧入口仍直接登记工作', 'projectId': pid}, role='viewer')
        self.assertTrue(intake['requirementId'])
        feedback = self.call('POST', '/api/business-requests', {'kind': 'feedback', 'title': '旧反馈',
            'originalFeedback': '提供业务反馈', 'requirementId': rid}, role='viewer')
        self.assertEqual(feedback['requirementId'], rid)
        self.call('PUT', '/api/business-requests/' + feedback['id'], {'status': 'resolved', 'handlerNote': '已处理'}, role='editor')
        raw = json.dumps({'kind': 'new_requirement', 'title': '签名入口', 'originalFeedback': '合成 webhook',
            'requesterUserId': 'stage-viewer', 'requesterName': '隔离业务'}).encode()
        timestamp = str(int(time.time()))
        signature = hmac.new(b'synthetic-test-secret', (timestamp + '.').encode() + raw, hashlib.sha256).hexdigest()
        response = self.client.post('/api/business-requests/webhook', content=raw, headers={
            'X-PM-Intake-Timestamp': timestamp, 'X-PM-Intake-Signature': 'sha256=' + signature})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.client.post('/api/business-requests/webhook', content=raw,
            headers={'X-PM-Intake-Timestamp': timestamp, 'X-PM-Intake-Signature': 'invalid'}).status_code, 401)
    def formal_work(self,convert=True):
        pid,_=self.project_work()
        demand=self.call('POST','/api/demand-pool',{'title':'验收运营闭环','description':'减少反复录入','department':'隔离测试部','requesterName':'隔离业务','requesterUserId':'stage-viewer','projectId':pid,'expectedDeliveryTime':'2027-01-01'},role='viewer')
        did=demand['id'];self.call('PUT',f'/api/demand-pool/{did}',{'status':'evaluating','solutionType':'existing_capability'})
        self.call('POST',f'/api/demand-pool/{did}/reviews/reuse',{'contactName':'隔离业务','communicationDate':'2026-10-13','decision':'support','prioritySuggestion':'P2','summary':'既有业务评估通过'})
        self.call('PUT',f'/api/demand-pool/{did}',{'evaluationDecision':'implement','solutionType':'existing_capability'})
        confirmation=self.call('POST',f'/api/demand-pool/{did}/confirmations',{'content':{'scope':'录入','scenarios':'日常录入','expected':'录入可查','valueDefinition':{'verificationMode':'outcome','expectedSummary':'减少重复劳动'}}})
        self.call('POST','/api/demand-pool-confirmations/by-token',{'token':confirmation['token'],'decision':'confirmed'})
        if not convert:return did,pid
        result=self.call('POST',f'/api/demand-pool/{did}/convert',{'projectId':pid,'assignee':'隔离开发者','expectedDeliveryTime':'2027-01-01'})
        return did,result['requirementId']
    def test_05_verification_delivery_callbacks_and_operation(self):
        did,rid=self.formal_work();baseline=self.call('GET',f'/api/requirements/{rid}/delivery-baselines')['items'][0]
        link=self.call('POST',f'/api/requirements/{rid}/collaboration-links',{'clientKey':'verify-round-1','kind':'verification','title':'请验证交付','content':'请核验录入查询','recipientName':'隔离业务','baselineId':baseline['id']})
        token=link['link'].split('token=')[1];headers={'X-PM-Collaboration-Token':token}
        public=self.client.get('/api/collaboration-link/context',headers=headers);self.assertEqual(public.status_code,200,public.text)
        self.assertNotIn('token',public.json());self.assertNotIn('history',public.json()['snapshot'])
        uploaded=self.client.post('/api/collaboration-link/attachments',headers=headers,data={'uploadKey':'proof-one'},files={'file':('proof.txt',b'round evidence','text/plain')})
        self.assertEqual(uploaded.status_code,200,uploaded.text);file=uploaded.json()
        repeated=self.client.post('/api/collaboration-link/attachments',headers=headers,data={'uploadKey':'proof-one'},files={'file':('proof.txt',b'ignored duplicate','text/plain')})
        self.assertEqual(repeated.json()['id'],file['id'])
        self.assertEqual(self.client.get('/api/collaboration-link/attachments/'+file['id'],headers=headers).content,b'round evidence')
        passed=self.client.post('/api/collaboration-link/submit',headers=headers,json={'outcome':'passed','content':'录入查询正常'})
        self.assertEqual(passed.status_code,200,passed.text);self.assertEqual(self.call('GET',f'/api/requirements/{rid}')['status'],'待交付')
        operation=self.call('POST',f'/api/requirements/{rid}/deliveries',{'clientKey':'delivery-one','acceptanceRequestId':link['id'],'deliveryDate':'2026-10-13','useStartDate':'2026-10-13'})
        self.assertEqual(self.call('GET',f'/api/requirements/{rid}')['status'],'已交付');self.assertEqual(operation['day7DueDate'],'2026-10-16');self.assertEqual(operation['day30DueDate'],'2026-11-12')
        self.assertEqual(len(operation['outcomeRequests']),2);same=self.call('POST',f'/api/requirements/{rid}/deliveries',{'clientKey':'delivery-one','acceptanceRequestId':link['id']});self.assertEqual(same['id'],operation['id'])
        self.call('POST',f'/api/requirements/{rid}/deliveries',{'clientKey':'delivery-two','acceptanceRequestId':link['id']},expected=409)
        self.call('DELETE','/api/business-attachments/'+file['id'],expected=409)
        day7=operation['day7Request'];day30=operation['day30Request']
        sent=self.call('POST','/api/demand-pool-value-requests/'+day7['id']+'/send');self.assertEqual(sent['notificationStatus'],'success')
        token7=sent['token'];receipt=self.call('POST','/api/demand-pool-outcome-submit',{'token':token7,'useStatus':'已开始使用但有问题','goalStatus':'部分解决','satisfaction':'需要改进','summary':'偶尔无法查询'})
        self.assertEqual(receipt['status'],'day7_review');self.call('POST','/api/demand-pool-outcome-submit',{'token':token7,'summary':'不能覆盖第一次回执'})
        self.call('POST','/api/demand-pool-value-requests/'+day7['id']+'/view')
        updated=self.call('PUT','/api/postlaunch/operations/'+operation['id'],{'useStartDate':'2026-10-15'})
        self.assertEqual(updated['day7Request']['scheduledAt'],'2026-10-16 09:00:00');self.assertEqual(updated['day30Request']['scheduledAt'],'2026-11-14 09:00:00')
        detail=self.call('GET','/api/postlaunch/operations/'+operation['id']);self.assertEqual(len(detail['issues']),1)
        issue=detail['issues'][0];self.call('PUT','/api/postlaunch/issues/'+issue['id'],{'status':'处理中','resolution':'核实查询条件'});self.call('PUT','/api/postlaunch/issues/'+issue['id'],{'status':'已关闭','resolution':'已修复'})
        self.call('POST','/api/postlaunch/proposals',{'operationId':operation['id'],'title':'优化查询','suggestion':'增加提示'})
        self.call('POST','/api/postlaunch/knowledge',{'operationId':operation['id'],'title':'查询处理方法','content':'检查查询范围','status':'published'})
        token30=updated['day30Request']['link'].split('token=')[1]
        self.call('POST','/api/demand-pool-outcome-submit',{'token':token30,'effectStatus':'有明显改善','summary':'已减少重复劳动','metricResults':[{'key':'duration','actualValue':3}]})
        self.call('GET','/api/demand-pool-outcome-context?token='+token30)
        self.call('GET','/api/postlaunch/dashboard');self.call('GET',f'/api/requirements/{rid}/lifecycle')
        _,quick=self.project_work();quick_operation=self.call('POST',f'/api/requirements/{quick}/deliveries',{'clientKey':'quick-one','verificationExemption':'内部工具无需业务验证'})
        self.assertFalse(quick_operation['valueVerificationEligible']);self.assertEqual(quick_operation['outcomeRequests'],[])
    def test_06_atomic_conversion_and_attachment_rollback(self):
        from unittest.mock import patch
        did,pid=self.formal_work(False)
        tables=['requirements','requirement_phases','requirement_work_logs','requirement_delivery_baselines','operation_records','todos']
        def counts():
            with self.db.engine.connect() as c:return {t:c.execute(text('SELECT count(*) FROM '+t)).scalar() for t in tables}
        before=counts();events=len(self.app.state.dispatcher.events);original=self.app.state.delivery.materialize_confirmation;calls=[]
        def fail_second(*args,**kwargs):
            calls.append(1)
            if len(calls)==2:raise RuntimeError('synthetic second baseline failure')
            return original(*args,**kwargs)
        body={'projectId':pid,'assignee':'隔离开发者','expectedDeliveryTime':'2027-01-01','parallelL3s':[{'title':'原子分支一'},{'title':'原子分支二'}]}
        with patch.object(self.app.state.delivery,'materialize_confirmation',side_effect=fail_second):self.call('POST',f'/api/demand-pool/{did}/convert',body,expected=500)
        self.assertEqual(counts(),before);self.assertEqual(len(self.app.state.dispatcher.events),events)
        self.assertEqual(self.call('GET',f'/api/demand-pool/{did}')['status'],'business_confirmed')
        result=self.call('POST',f'/api/demand-pool/{did}/convert',body);self.assertEqual(len(result['requirementIds']),2)
        rid=result['requirementIds'][0];activity=self.call('POST',f'/api/requirements/{rid}/shared-activities',{'content':'附件事务检查'})
        old_files={str(x) for x in self.attachments.rglob('*') if x.is_file()};save=self.app.state.files.save
        def fail_save(*args,**kwargs):save(*args,**kwargs);raise RuntimeError('synthetic metadata failure')
        with patch.object(self.app.state.files,'save',side_effect=fail_save):
            self.call('POST','/api/business-attachments',data={'ownerType':'shared_activity','ownerId':activity['id']},files={'file':('rollback.txt',b'rollback proof','text/plain')},expected=500)
        self.assertEqual(old_files,{str(x) for x in self.attachments.rglob('*') if x.is_file()})
        self.assertEqual(self.call('GET',f'/api/shared-activities/{activity["id"]}/comments'),[])
    def test_07_same_key_concurrency_stale_round_and_scope(self):
        from concurrent.futures import ThreadPoolExecutor
        did,rid=self.formal_work();baseline=self.call('GET',f'/api/requirements/{rid}/delivery-baselines')['items'][0]
        data={'clientKey':'same-key-concurrent','kind':'verification','title':'并发验证','content':'同一轮验证','recipientName':'隔离业务','baselineId':baseline['id']}
        def create():return self.client.post(f'/api/requirements/{rid}/collaboration-links',json=data,headers={'X-PM-Session':'fixture-stage-super'})
        before=len(self.app.state.gateway.calls)
        with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(lambda _:create(),range(2)))
        self.assertTrue(all(x.status_code==200 for x in responses),str([x.text for x in responses]));first=responses[0].json();self.assertEqual(first['id'],responses[1].json()['id'])
        self.assertEqual(len(self.app.state.gateway.calls)-before,1)
        token=first['link'].split('token=')[1];headers={'X-PM-Collaboration-Token':token}
        second=self.call('POST',f'/api/requirements/{rid}/collaboration-links',{**data,'clientKey':'same-second-next'})
        self.assertEqual(self.client.get('/api/collaboration-link/context',headers=headers).status_code,410)
        self.assertEqual(self.client.post('/api/collaboration-link/submit',headers=headers,json={'outcome':'passed'}).status_code,410)
        header2={'X-PM-Collaboration-Token':second['link'].split('token=')[1]}
        self.assertEqual(self.client.post('/api/collaboration-link/submit',headers=header2,json={'outcome':'passed'}).status_code,200)
        self.call('PUT',f'/api/requirements/{rid}',{'description':'范围已经调整'})
        self.call('POST',f'/api/requirements/{rid}/deliveries',{'clientKey':'outdated-delivery','acceptanceRequestId':second['id']},expected=409)
        _,other=self.project_work();activity=self.call('POST',f'/api/requirements/{other}/shared-activities',{'content':'其他工作材料'})
        file=self.call('POST','/api/business-attachments',data={'ownerType':'shared_activity','ownerId':activity['id']},files={'file':('foreign.txt',b'foreign proof','text/plain')})
        self.assertEqual(self.client.get('/api/collaboration-link/attachments/'+file['id'],headers=header2).status_code,404)
        self.call('POST',f'/api/requirements/{rid}/collaboration-links',{**data,'clientKey':'foreign-file-round','attachmentIds':[file['id']]},expected=403)
    def test_08_supplement_review_token_poc_and_history(self):
        pid,_=self.project_work();row=self.call('POST','/api/demand-pool',{'description':'补充与评审门禁','department':'隔离测试部','projectId':pid,'requesterName':'隔离业务','requesterUserId':'stage-viewer'})
        did=row['id'];self.call('PUT',f'/api/demand-pool/{did}',{'status':'evaluating','solutionType':'existing_capability','pocRequirement':'required'})
        supplement=self.call('POST',f'/api/demand-pool/{did}/supplements',{'questions':[{'key':'scope','label':'范围','required':True}]})
        self.call('PUT','/api/demand-pool-supplements/'+supplement['id'],{'answers':{}},role='viewer',expected=400)
        self.call('PUT','/api/demand-pool-supplements/'+supplement['id'],{'answers':{'scope':'录入与查询'}},role='viewer')
        reviewed=self.call('POST',f'/api/demand-pool/{did}/reviews',{'reviewers':[{'role':'leader','userId':'stage-viewer','name':'隔离业务'}]})
        review=reviewed['reviews'][0];self.assertEqual(review['notificationStatus'],'success')
        self.call('POST','/api/demand-pool-reviews/by-token',{'token':review['token'],'decision':'support','prioritySuggestion':'P2','comment':'支持实施'})
        self.call('PUT',f'/api/demand-pool/{did}',{'evaluationDecision':'implement'},expected=400)
        poc=self.call('POST',f'/api/demand-pool/{did}/pocs',{'summary':'合成验证通过'})
        self.assertEqual(poc['conclusion'],'documented');self.call('PUT',f'/api/demand-pool/{did}',{'evaluationDecision':'implement'})
        self.call('GET',f'/api/demand-pool/{did}/supplements');self.call('GET',f'/api/demand-pool/{did}/pocs')
    def test_09_historical_orphan_and_archived_metadata(self):
        pid,rid=self.project_work();log=self.call('POST',f'/api/requirements/{rid}/work-logs',{'content':'历史共享工作日志','visibility':'business_shared'})
        thread=self.call('POST',f'/api/requirements/{rid}/business-collaborations',{'title':'保留历史主题','content':'保留原始内容','kind':'clarification'})
        with self.db.engine.begin() as c:
            c.execute(text('UPDATE requirement_work_logs SET updatedAt=:at WHERE id=:id'),{'at':'2030-01-01 09:00:00','id':log['id']})
            c.execute(text('UPDATE requirements SET projectId=:project WHERE id=:id'),{'project':'synthetic-missing-parent','id':rid})
        activities=self.call('GET',f'/api/requirements/{rid}/shared-activities',role='viewer')
        projected=next(x for x in activities if x['sourceId']==log['id']);self.assertEqual(projected['updatedAt'],log['createdAt'])
        self.call('POST','/api/shared-activities/'+projected['id']+'/comments',{'content':'孤立历史仍可回复'},role='viewer')
        with self.db.engine.begin() as c:c.execute(text('UPDATE requirements SET projectId=:project,deletedAt=:at WHERE id=:id'),{'project':pid,'at':NOW,'id':rid})
        rows=self.call('GET','/api/business-collaborations');archived=next(x for x in rows if x['id']==thread['id'])
        self.assertEqual(archived['requirementTitle'],'合成工作');self.assertEqual(archived['projectName'],'合成产品')
    def test_10_historical_decomposition_preserves_state(self):
        did,rid=self.formal_work();self.call('POST','/api/requirements/bulk-classification',{'ids':[rid],'status':'已交付','reason':'合成历史补录'})
        before=len(self.app.state.gateway.calls)
        body={'branches':[{'branchKey':'original','title':'历史独立工作一','formalRequirementId':rid},{'branchKey':'added','title':'历史独立工作二'}]}
        result=self.call('POST',f'/api/demand-pool/{did}/historical-decomposition',body)
        self.assertEqual(len(result['requirementIds']),2);self.assertEqual(self.call('GET',f'/api/requirements/{rid}')['status'],'已交付')
        self.assertEqual(len(self.app.state.gateway.calls),before)
        repeated=self.call('POST',f'/api/demand-pool/{did}/historical-decomposition',body)
        self.assertEqual(repeated['requirementIds'],result['requirementIds'])
    def test_11_create_l2_from_confirmed_demand(self):
        row=self.call('POST','/api/demand-pool',{'title':'新 L2 正式立项','intakeLevel':'L2','description':'创建独立业务应用','department':'隔离测试部',
            'requesterName':'隔离业务','requesterUserId':'stage-viewer','expectedDeliveryTime':'2027-01-01'})
        did=row['id'];self.call('PUT',f'/api/demand-pool/{did}',{'status':'evaluating','solutionType':'new_app_platform','intakePath':'new_l2'})
        self.call('POST',f'/api/demand-pool/{did}/reviews/reuse',{'contactName':'隔离业务','communicationDate':'2026-10-13','decision':'support','prioritySuggestion':'P2','summary':'新系统值得实施'})
        self.call('PUT',f'/api/demand-pool/{did}',{'evaluationDecision':'implement'})
        confirmation=self.call('POST',f'/api/demand-pool/{did}/confirmations',{'content':{'expected':'首版可用','valueDefinition':{'verificationMode':'outcome','expectedSummary':'减少手工处理'}}})
        self.call('POST','/api/demand-pool-confirmations/by-token',{'token':confirmation['token'],'decision':'confirmed'})
        created=self.call('POST',f'/api/demand-pool/{did}/convert',{'mode':'create_l2','department':'隔离测试部','devOwner':'隔离开发者','projectEndDate':'2027-01-01'})
        work=self.call('GET','/api/requirements/'+created['requirementId']);self.assertEqual(work['itemKind'],'initial_build');self.assertEqual(work['flowMode'],'full_demand')
        self.assertEqual(len(self.call('GET','/api/requirements/'+work['id']+'/phases')),8)
    def test_12_standard_confirmation_and_feedback_route(self):
        _,rid=self.project_work();baseline=self.call('POST',f'/api/requirements/{rid}/delivery-baselines',{'content':{'scope':'查询范围','scenarios':'查询场景','expected':'可准确查询'},'recipientName':'隔离业务','send':True})
        header={'X-PM-Collaboration-Token':baseline['link'].split('token=')[1]}
        self.assertEqual(self.client.post('/api/collaboration-link/submit',headers=header,json={'outcome':'confirmed'}).status_code,200)
        link=self.call('POST',f'/api/requirements/{rid}/collaboration-links',{'clientKey':'feedback-round','kind':'verification','title':'请验证查询','content':'核验查询范围','baselineId':baseline['id']})
        header={'X-PM-Collaboration-Token':link['link'].split('token=')[1]}
        response=self.client.post('/api/collaboration-link/submit',headers=header,json={'outcome':'changes','feedbackType':'other','content':'需要增加导出，请 IT 判断'})
        self.assertEqual(response.status_code,200,response.text)
        lifecycle=self.call('GET',f'/api/requirements/{rid}/lifecycle');feedback=next(x['feedback'] for x in lifecycle['links'] if x['id']==link['id'])
        routed=self.call('POST','/api/delivery-feedback/'+feedback['id']+'/route',{'routeType':'new_l3_feature'})
        self.assertEqual(routed['status'],'created');self.assertNotEqual(routed['routedRequirementId'],rid)
        followup=self.call('GET','/api/requirements/'+routed['routedRequirementId']);self.assertEqual(followup['parentRequirementId'],rid)
        self.assertEqual(self.call('POST','/api/delivery-feedback/'+feedback['id']+'/route',{'routeType':'new_l3_feature'})['routedRequirementId'],followup['id'])


    def test_13_collection_delivery_results_and_safe_retry(self):
        from unittest.mock import patch
        def send(error=None):
            body={'entryMode':'collect','targetType':'person','targetUserId':'stage-viewer',
                'targetValue':'隔离业务','requestKey':str(uuid.uuid4())}
            if error:
                with patch.object(self.app.state.gateway,'send_markdown_to_users',side_effect=RuntimeError(error)) as gateway:
                    result=self.call('POST','/api/demand-pool/notifications',body)
                    self.assertEqual(gateway.call_count,1)
            else:result=self.call('POST','/api/demand-pool/notifications',body)
            return body,result
        def recipient(notice):
            with self.db.engine.connect() as c:
                return dict(c.execute(text('SELECT * FROM demand_pool_link_recipients WHERE notificationId=:id'),{'id':notice['id']}).mappings().one())
        body,success=send();self.assertEqual(success['status'],'success')
        row=recipient(success);self.assertEqual(row['sendstatus'],'accepted');self.assertEqual(row['attemptcount'],1)
        before=len(self.app.state.gateway.calls)
        duplicate=self.call('POST','/api/demand-pool/notifications',body)
        self.assertEqual(duplicate['id'],success['id']);self.assertEqual(len(self.app.state.gateway.calls),before)
        self.assertEqual(recipient(success)['token'],row['token'])
        _,failed=send('permission denied');self.assertEqual(failed['status'],'failed');self.assertEqual(failed['failureCount'],1)
        row=recipient(failed);self.assertEqual(row['errorcode'],'permission_denied')
        retried=self.call('POST','/api/demand-collections/batches/'+failed['batchId']+'/retry-failures',{})
        self.assertEqual(retried['status'],'success');self.assertEqual(retried['successCount'],1)
        after=recipient(failed);self.assertEqual(after['token'],row['token']);self.assertEqual(after['attemptcount'],2)
        self.assertEqual(after['sendstatus'],'accepted');self.assertTrue(after['lastattemptat']);self.assertTrue(after['acceptedat'])
        for error,status,code in [('invalid user','failed','invalid_recipient'),('read timed out','attention_required','unknown_result')]:
            with self.subTest(error=error):
                _,result=send(error);self.assertEqual(result['status'],status)
                row=recipient(result);self.assertEqual(row['errorcode'],code);self.assertEqual(row['attemptcount'],1)
                self.assertEqual(result['unknownCount'],int(code=='unknown_result'))
                self.call('POST','/api/demand-collections/batches/'+result['batchId']+'/retry-failures',{},expected=400)
                self.assertEqual(recipient(result)['attemptcount'],1)
        original=self.app.state.gateway.send_markdown_to_users
        attempts=[]
        def transient(*args,**kwargs):
            attempts.append(1)
            if len(attempts)==1:raise RuntimeError('http 503 temporarily unavailable')
            return original(*args,**kwargs)
        with patch.object(self.app.state.gateway,'send_markdown_to_users',side_effect=transient):
            _,recovered=send()
        self.assertEqual(recovered['status'],'success');self.assertEqual(len(attempts),2)
        self.assertEqual(recipient(recovered)['attemptcount'],2)


if __name__ == '__main__':
    unittest.main()
