"""Public synthetic session renewal; no real identity provider or business data reset."""
import json,unittest
from dataclasses import replace
import test_demand_delivery as fixtures
from fastapi.testclient import TestClient
from sqlalchemy import text
from itpm.app import create_app
from itpm.infrastructure.gateway import FakeGateway
from preview_entry import render_entry
ROOT=fixtures.ROOT

class PreviewEntry(unittest.TestCase):
    setUpClass=classmethod(fixtures.DemandDeliveryTests.setUpClass.__func__)
    @classmethod
    def tearDownClass(cls):cls.client.__exit__(None,None,None)
    def test_session_renewal_and_fixed_identity(self):
        gateway=FakeGateway()
        app=create_app(replace(self.db.settings,profile='preview'),clock=self.app.state.flow.clock,gateway=gateway)
        with TestClient(app) as client:
            self.assertEqual(client.get('/api/requirements').status_code,401)
            first=client.post('/pm/api/preview/session');self.assertEqual(first.status_code,200,first.text)
            self.assertEqual(first.headers['Cache-Control'],'no-store')
            user=first.json()['user'];self.assertEqual(user['dingUserId'],'stage-super');self.assertEqual(user['role'],'super_admin')
            token=user['sessionToken']
            with self.db.engine.begin() as connection:
                connection.execute(text('UPDATE app_sessions SET expiresAt=:expired WHERE token=:token'),{'expired':'2000-01-01 00:00:00','token':token})
            self.assertEqual(client.get('/api/session',headers={'X-PM-Session':token}).status_code,401)
            second=client.post('/api/preview/session');self.assertEqual(second.status_code,200,second.text)
            next_token=second.json()['user']['sessionToken'];self.assertNotEqual(next_token,token)
            session=client.get('/api/session',headers={'X-PM-Session':next_token});self.assertEqual(session.status_code,200,session.text)
            self.assertEqual(session.json()['role'],'super_admin')
            self.assertEqual(client.get('/api/requirements',headers={'X-PM-Session':next_token}).status_code,200)
            viewer=client.post('/api/preview/session?actor=viewer').json()['user']
            headers={'X-PM-Session':viewer['sessionToken']}
            self.assertEqual(viewer['role'],'viewer');self.assertEqual(client.get('/api/system/personnel',headers=headers).status_code,403)
            self.assertEqual(client.post('/api/preview/session?actor=unknown').status_code,422)
            schema=client.get('/api/openapi.json').json()
            self.assertNotIn('security',schema['paths']['/api/preview/session']['post'])
            self.assertIn('security',schema['paths']['/api/requirements']['get'])
            self.assertEqual(gateway.calls,[])
    def test_route_absent_outside_preview_and_entry_errors_visible(self):
        self.assertIn(self.client.post('/api/preview/session').status_code,[404,405])
        self.assertNotIn('/api/preview/session',self.app.openapi()['paths'])
        app=create_app(replace(self.db.settings,profile='production',integration_mode='disabled'),gateway=FakeGateway())
        with TestClient(app) as client:
            self.assertIn(client.post('/api/preview/session').status_code,[404,405])
            self.assertNotIn('/api/preview/session',app.openapi()['paths'])
        html=render_entry()
        self.assertIn("method:'POST'",html);self.assertIn('api/preview/session',html)
        self.assertIn('api/session',html);self.assertIn('重新进入',html)
        self.assertIn('未向钉钉实际发送消息',html);self.assertNotIn('fixture-stage-',html)
        self.assertIn(r'/[\r\n#]/',html)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(PreviewEntry))
    (ROOT/'.runtime/test-results/preview-entry.json').write_text(json.dumps({'passed':result.wasSuccessful(),'tests':result.testsRun,
        'checks':['preview POST establishes configured synthetic identity','expired session -> new token -> session and ledger access',
        'viewer permission preserved','unknown identity rejected','public preview contract/internal authentication retained',
        'route absent in test and production','no provider calls','HTML failure/retry explanation, no fixed token']},ensure_ascii=False,indent=2),encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)
