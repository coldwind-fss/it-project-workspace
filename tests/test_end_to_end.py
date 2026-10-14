"""Whole product flow and restart compatibility on an independent synthetic PG database."""
import json,unittest,hashlib
import test_demand_delivery as fixtures
from demo_flow import run_flow
from itpm.app import create_app
from itpm.infrastructure.gateway import FakeGateway
from fastapi.testclient import TestClient
from sqlalchemy import select
ROOT=fixtures.ROOT

class EndToEndTests(unittest.TestCase):
    setUpClass=classmethod(fixtures.DemandDeliveryTests.setUpClass.__func__)
    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None,None,None)
        (ROOT/'.runtime/test-results/end-to-end.json').write_text(json.dumps({'passed':getattr(cls,'passed',False),'checks':cls.checks,'results':getattr(cls,'results',{})},ensure_ascii=False,indent=2),encoding='utf-8')
    def call(self,method,path,payload=None,role='super',headers=None):
        r=self.client.request(method,path,json=payload,headers={'X-PM-Session':'fixture-stage-'+role,**(headers or {})})
        self.assertEqual(r.status_code,200,r.text);self.checks.append({'method':method,'path':path,'status':r.status_code});return r.json()
    def snapshot(self):
        with self.db.engine.connect() as connection:
            return {table.name:hashlib.sha256(json.dumps(sorted([dict(r) for r in connection.execute(select(table)).mappings()],key=lambda r:json.dumps(r,sort_keys=True,default=str)),sort_keys=True,default=str).encode()).hexdigest() for table in self.db.metadata.sorted_tables}
    def test_product_and_restart(self):
        docs=self.client.get('/pm/api/docs');self.assertEqual(docs.status_code,200)
        self.assertIn('/pm/api/openapi.json',docs.text)
        self.assertEqual(self.client.get('/pm/api/openapi.json').status_code,200)
        result=run_flow(self.call);self.assertTrue(self.db.check())
        before=self.snapshot();old_gateway_calls=len(self.app.state.gateway.calls)
        restarted=create_app(self.db.settings,clock=self.app.state.flow.clock,gateway=FakeGateway())
        with TestClient(restarted) as client:
            self.assertEqual(client.get('/api/ready').status_code,200)
            headers={'X-PM-Session':'fixture-stage-super'}
            for rid in result['requirementIds']:
                response=client.get('/api/requirements/'+rid+'/lifecycle',headers=headers)
                self.assertEqual(response.status_code,200,response.text)
            self.assertEqual(client.get('/api/requirements').status_code,401)
            self.assertEqual(restarted.state.gateway.calls,[])
            self.assertEqual(self.snapshot(),before)
        self.assertEqual(len(self.app.state.gateway.calls),old_gateway_calls)
        type(self).passed=True;type(self).results={'fullFlow':'two parallel L3 -> verification -> explicit IT delivery -> distinct +3/+30 receipts -> metrics -> PoC/AI -> knowledge/proposal -> notification Fake -> sync',
            'schema':'matched','restart':'all 51 table row fingerprints unchanged; no seed or outbound','apiAnonymous':'401','realProvider':'not_run'}
    def test_real_provider_login_and_contacts_without_network(self):
        from dataclasses import replace
        import httpx
        from itpm.infrastructure.gateway import gateway_for
        requests=[];bound={}
        def handler(request):
            self.assertEqual(bound['app'].state.database.engine.pool.checkedout(),0,'provider IO must not hold a business connection')
            requests.append(request.url.path)
            if request.url.path=='/gettoken':data={'errcode':0,'access_token':'synthetic-provider-token','expires':7200}
            elif request.url.path.endswith('getuserinfo'):data={'errcode':0,'result':{'userid':'stage-editor'}}
            elif request.url.path.endswith('user/get'):data={'errcode':0,'result':{'name':'隔离开发者','dept_id_list':[1]}}
            elif request.url.path.endswith('user/listsimple'):data={'errcode':0,'result':{'list':[{'userid':'stage-editor','name':'隔离开发者'}],'has_more':False}}
            else:data={'errcode':0,'result':[]}
            return httpx.Response(200,json=data)
        settings=replace(self.db.settings,profile='production',integration_mode='real',dingtalk_app_key='synthetic-app',dingtalk_app_secret='synthetic-secret',dingtalk_corp_id='synthetic-corp')
        gateway=gateway_for(settings,self.app.state.flow.v,transport=httpx.MockTransport(handler))
        app=create_app(settings,clock=self.app.state.flow.clock,gateway=gateway);bound['app']=app
        with TestClient(app) as client:
            self.assertEqual(requests,[])
            config=client.get('/api/dingtalk/config');self.assertTrue(config.json()['configured']);self.assertNotIn('synthetic-secret',config.text)
            self.assertEqual(client.get('/api/dingtalk/options').status_code,401);self.assertEqual(requests,[])
            login=client.post('/api/dingtalk/login',json={'authCode':'synthetic-auth-code'});self.assertEqual(login.status_code,200,login.text)
            user=login.json()['user'];self.assertEqual(user['role'],'editor')
            options=client.get('/api/dingtalk/options',headers={'X-PM-Session':user['sessionToken']});self.assertEqual(options.status_code,200,options.text)
            self.assertTrue(any(x.get('userid')=='stage-editor' for x in options.json()['users']))
        type(self).results['realProviderProtocolApi']='MockTransport auth code -> configured role/session -> authenticated contacts; no IO while business connection held'
if __name__=='__main__':unittest.main()
