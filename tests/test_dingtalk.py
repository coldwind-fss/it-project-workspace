"""Actual provider protocol checks through MockTransport; zero real external requests."""
import base64,hashlib,hmac,json,sys,unittest
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from itpm.settings import Settings
from itpm.infrastructure.gateway import gateway_for,DisabledGateway
class DingTalkProtocol(unittest.TestCase):
    def setUp(self):
        self.requests=[];self.failure=None
        self.settings=Settings('postgresql+psycopg2://unused@127.0.0.1:55432/pm_test_rebuild_mock',profile='production',integration_mode='real',
            dingtalk_app_key='synthetic-app',dingtalk_app_secret='synthetic-secret',dingtalk_corp_id='synthetic-corp',dingtalk_agent_id='synthetic-agent')
        self.v=json.loads((ROOT/'contracts/business-vocabulary.json').read_text('utf-8'))
        def handler(request):
            self.requests.append(request);path=request.url.path
            if self.failure=='http' and 'batchSend' in path:return httpx.Response(500,json={'message':'synthetic-secret access_token=sensitive-upstream-data'})
            if path=='/gettoken':return httpx.Response(200,json={'errcode':0,'access_token':'synthetic-access-token','expires':7200})
            if path.endswith('getuserinfo'):return httpx.Response(200,json={'errcode':0,'result':{'userid':'synthetic-user'}})
            if path.endswith('user/get'):return httpx.Response(200,json={'errcode':0,'result':{'name':'十叶-冯硕硕','unionid':'union/one','dept_id_list':[2]}})
            if path.endswith('department/listsub'):
                body=json.loads(request.content);return httpx.Response(200,json={'errcode':0,'result':[{'dept_id':2,'name':'开发部'}] if body['dept_id']==1 else []})
            if path.endswith('user/listsimple'):return httpx.Response(200,json={'errcode':0,'result':{'list':[{'userid':'synthetic-user','name':'十叶-冯硕硕'}],'has_more':False}})
            if 'batchSend' in path:return httpx.Response(200,json={'processQueryKey':'synthetic-ack','invalidStaffIdList':['synthetic-bad-user'] if self.failure=='invalid' else []})
            return httpx.Response(200,json={'errcode':0})
        self.gateway=gateway_for(self.settings,self.v,transport=httpx.MockTransport(handler));self.assertEqual(self.requests,[])
    def tearDown(self):self.gateway.close()
    def test_auth_contacts_and_cache(self):
        self.assertTrue(self.gateway.config()['configured']);self.assertEqual(self.requests,[])
        user=self.gateway.exchange('synthetic-code');self.assertEqual(user['userid'],'synthetic-user')
        self.assertEqual(self.gateway.union_id('synthetic-user'),'union/one');self.gateway.refresh_contacts()
        contacts=self.gateway.contacts();self.assertEqual(contacts['departments'],['开发部']);self.assertEqual(len(contacts['users']),1)
        self.assertEqual(contacts['users'][0]['userid'],'synthetic-user')
        before=len(self.requests);self.gateway.refresh_contacts();self.gateway.union_id('synthetic-user');self.gateway.contacts();self.assertEqual(len(self.requests),before)
        self.assertEqual(sum(r.url.path=='/gettoken' for r in self.requests),1)
    def test_personal_group_and_native_completion(self):
        sent=self.gateway.send_markdown_to_users(['u'+str(x) for x in range(21)]+['u0'],'题目','**合成**')
        self.assertEqual(sent['sentCount'],21)
        batches=[json.loads(r.content) for r in self.requests if 'batchSend' in r.url.path]
        self.assertEqual([len(x['userIds']) for x in batches],[20,1]);self.assertEqual(batches[0]['robotCode'],'synthetic-app')
        self.assertEqual(batches[0]['msgKey'],'sampleMarkdown');self.assertEqual(json.loads(batches[0]['msgParam']),{'title':'题目','text':'**合成**'})
        self.gateway.now=lambda:1234
        self.gateway.send_group_markdown('https://oapi.dingtalk.com/robot/send?access_token=synthetic-hook','synthetic-signing-secret','标题','内容')
        request=self.requests[-1];expected=base64.b64encode(hmac.new(b'synthetic-signing-secret',b'1234000\nsynthetic-signing-secret',hashlib.sha256).digest()).decode()
        self.assertEqual(request.url.params['access_token'],'synthetic-hook');self.assertEqual(request.url.params['sign'],expected)
        self.gateway.complete_todo('union/one','task/two','union/actor');request=self.requests[-1]
        self.assertEqual(request.method,'PUT');self.assertEqual(request.url.params['operatorId'],'union/actor')
        self.assertIn('union%2Fone',request.url.raw_path.decode());self.assertEqual(json.loads(request.content),{})
    def test_failures_are_safe_and_real_is_explicit(self):
        self.failure='http'
        with self.assertRaises(RuntimeError) as error:self.gateway.send_markdown_to_users(['u1'],'title','text')
        self.assertNotIn('synthetic-secret',str(error.exception));self.assertNotIn('access_token',str(error.exception))
        self.failure='invalid'
        with self.assertRaises(RuntimeError):self.gateway.send_markdown_to_users(['u1'],'title','text')
        with self.assertRaises(ValueError):Settings(self.settings.database_url,profile='preview',integration_mode='real',dingtalk_app_key='x',dingtalk_app_secret='y')
        self.assertNotIn('synthetic-secret',repr(self.settings))
        with self.assertRaises(RuntimeError):DisabledGateway().send_group_markdown('unused','','','')
if __name__=='__main__':
    result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(DingTalkProtocol))
    (ROOT/'.runtime/test-results/dingtalk.json').write_text(json.dumps({'passed':result.wasSuccessful(),'tests':result.testsRun,'provider':'real adapter with MockTransport; no real network',
        'scope':['auth code + user detail','token/union/contact caching','department traversal/user deduplication','20-person Markdown batches','signed webhook','native todo completion','safe failure and explicit activation']},ensure_ascii=False,indent=2),encoding='utf-8')
    sys.exit(0 if result.wasSuccessful() else 1)
