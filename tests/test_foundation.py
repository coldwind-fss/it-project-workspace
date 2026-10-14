"""Infrastructure gates + real transaction failure risks, no shared DB changes."""
from pathlib import Path
import unittest,json,sys,uuid,subprocess,os
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'scripts')]
from runtime import prepare_database,admin_url
from fixtures import seed,NOW
from itpm.app import create_app
from itpm.settings import Settings
from itpm.core.events import Dispatcher,Event
from itpm.infrastructure.database import Database,UnitOfWork,catalog
from itpm.modules.identity.repository import IdentityRepository
from itpm.modules.portfolio.repository import PortfolioRepository
from fastapi.testclient import TestClient
from sqlalchemy import text
import psycopg2

class Clock:
    def now(self):return NOW

class Foundation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pwd=json.loads((ROOT/'.runtime/runtime-secret.json').read_text('utf-8'))['password'];cls.pwd=pwd
        cls.name='pm_test_rebuild_gate_'+uuid.uuid4().hex[:10];cls.url=prepare_database(cls.name,pwd);seed(cls.url)
        cls.app=create_app(Settings(cls.url,profile='test',read_auth=True),clock=Clock());cls.client=TestClient(cls.app);cls.client.__enter__();cls.db=cls.app.state.database
    @classmethod
    def tearDownClass(cls):cls.client.__exit__(None,None,None)
    def counts(self):
        with self.db.engine.connect() as c:
            return {name:c.execute(text('SELECT count(*) FROM public.'+name)).scalar() for name in [x['name'] for x in catalog(c)['tables']]}
    def test_import_pure(self):
        # Audit hooks enforce no filesystem writes or socket connections on imports.
        code="""import sys,pathlib
sys.path.insert(0,sys.argv[1]);sys.dont_write_bytecode=True
def audit(event,args):
 if event=='socket.connect':raise RuntimeError('import opened a connection')
 if event=='open' and isinstance(args[1],str) and any(x in args[1] for x in 'wax+'):raise RuntimeError('import wrote a file')
sys.addaudithook(audit)
import itpm.app,itpm.workflows.project_work
assert not any(x=='server' or x.startswith('server.') for x in sys.modules)
print('import pure')
"""
        r=subprocess.run([sys.executable,'-B','-c',code,str(ROOT/'backend')],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
    def test_get_startup_readonly(self):
        before=self.counts()
        for _ in range(2):
            with TestClient(create_app(Settings(self.url,profile='test',read_auth=True))) as c:
                for path in ['/api/health','/api/ready','/api/projects','/api/categories','/api/requirements']:
                    self.assertEqual(c.get(path,headers={'X-PM-Session':'fixture-stage-super'}).status_code,200)
        self.assertEqual(self.counts(),before);self.assertEqual(self.app.state.gateway.calls,[])
    def test_commit_rollback_dispatch(self):
        dispatcher=Dispatcher();observed=[]
        def consumer(event):
            with self.db.engine.connect() as c:observed.append(c.execute(text("SELECT value FROM system_settings WHERE key='event-commit-test'")).scalar())
        dispatcher.subscribers=[consumer]
        event=Event('project_created','evt-test','project:p','2026-10-13',{},'project','p',{'id':'p'})
        with UnitOfWork(self.db,dispatcher) as u:
            repo=IdentityRepository(self.db);repo.set_setting(u,'event-commit-test',{'ok':1},NOW);u.events.append(event)
            self.assertEqual(observed,[])
        self.assertEqual(observed,['{"ok": 1}'])
        with self.assertRaises(RuntimeError):
            with UnitOfWork(self.db,dispatcher) as u:
                repo.set_setting(u,'event-commit-test',{'ok':2},NOW);u.events.append(event);raise RuntimeError('inject')
        self.assertEqual(len(observed),1)
        dispatcher.subscribers=[lambda e:(_ for _ in ()).throw(RuntimeError('fake delivery failure'))]
        with UnitOfWork(self.db,dispatcher) as u:repo.set_setting(u,'event-commit-test',{'ok':3},NOW);u.events.append(event)
        self.assertEqual(len(dispatcher.failures),1)
        with self.db.engine.connect() as c:self.assertEqual(c.execute(text("SELECT value FROM system_settings WHERE key='event-commit-test'")).scalar(),'{"ok": 3}')
    def test_multi_repository_atomic(self):
        before=self.counts()
        with self.assertRaises(RuntimeError):
            with UnitOfWork(self.db,self.app.state.dispatcher) as u:
                PortfolioRepository(self.db).add(u,'projects',{'id':'atomic-risk-project','name':'fault fixture'})
                IdentityRepository(self.db).set_setting(u,'atomic-risk-setting',{'ok':1},NOW)
                raise RuntimeError('fail after two repositories')
        self.assertEqual(self.counts(),before)
    def test_runtime_role_rejects_ddl(self):
        with self.assertRaises(Exception):
            with self.db.engine.begin() as c:c.execute(text('CREATE TABLE public.runtime_ddl_forbidden(id text)'))
        with self.db.engine.connect() as c:self.assertIsNone(c.execute(text("SELECT to_regclass('public.runtime_ddl_forbidden')")).scalar())
    def test_unavailable_and_mismatch(self):
        app=create_app(Settings('postgresql+psycopg2://unknown@127.0.0.1:55432/pm_test_rebuild_absent',profile='test'))
        with TestClient(app) as c:
            self.assertEqual(c.get('/api/health').status_code,200);r=c.get('/api/ready');self.assertEqual(r.status_code,503);self.assertEqual(r.json()['code'],'DATABASE_UNAVAILABLE');self.assertNotIn('postgres',r.text)
        name='pm_test_rebuild_mismatch_'+uuid.uuid4().hex[:10];url=prepare_database(name,self.pwd)
        with psycopg2.connect(admin_url(name)) as c:
            with c.cursor() as cur:cur.execute('ALTER TABLE public.system_settings ADD COLUMN isolated_mismatch_marker text')
        with TestClient(create_app(Settings(url,profile='test'))) as c:
            self.assertEqual(c.get('/api/ready').json()['code'],'SCHEMA_MISMATCH');self.assertEqual(c.post('/api/projects',json={'name':'blocked'}).status_code,503)
    def test_settings_and_static(self):
        os.environ['PM_DATABASE_URL']='postgresql://not-a-target/live'
        with unittest.mock.patch.dict(os.environ,{'ITPM_DATABASE_URL':self.url}):self.assertEqual(Settings.from_env().database_url,self.url)
        for path in ['/api/missing','/pm/api/missing','/assets/missing.js']:
            r=self.client.get(path);self.assertEqual(r.status_code,404);self.assertIn('json',r.headers['content-type'])
        r=self.client.get('/');self.assertEqual(r.status_code,200);self.assertIn('text/html',r.headers['content-type'])
        asset=next((ROOT/'frontend/dist/assets').glob('*.js'));r=self.client.get('/pm/assets/'+asset.name);self.assertEqual(r.status_code,200);self.assertIn('javascript',r.headers['content-type'])
        schema=self.app.openapi();ids=[op['operationId'] for path in schema['paths'].values() for op in path.values() if isinstance(op,dict) and 'operationId' in op];self.assertEqual(len(ids),len(set(ids)))

if __name__=='__main__':
    import unittest.mock
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Foundation))
    (ROOT/'.runtime/test-results/foundation.json').write_text(json.dumps({'passed':result.wasSuccessful(),'tests':result.testsRun,'errors':len(result.errors),'failures':len(result.failures),'database':Foundation.name},indent=2),encoding='utf-8')
    sys.exit(0 if result.wasSuccessful() else 1)
