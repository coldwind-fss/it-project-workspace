from pathlib import Path
import sys,json,uuid,unittest,os
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'scripts')]
from runtime import prepare_database
from fixtures import seed,NOW
from itpm.settings import Settings
from itpm.app import create_app
from itpm.infrastructure.database import UnitOfWork,catalog,schema_difference
from itpm.core.events import Dispatcher,Event
from itpm.core.ports import Ids
from sqlalchemy import text
from fastapi.testclient import TestClient

class FixedClock:
    def now(self):return NOW

class ProjectWorkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        password=json.loads((ROOT/'.runtime/runtime-secret.json').read_text('utf-8'))['password']
        cls.name='pm_test_rebuild_check_'+uuid.uuid4().hex[:10]
        cls.url=prepare_database(cls.name,password);seed(cls.url)
        cls.app=create_app(Settings(cls.url,profile='test',read_auth=True),clock=FixedClock());cls.client=TestClient(cls.app);cls.client.__enter__()
        cls.headers={'X-PM-Session':'fixture-stage-super'};cls.db=cls.app.state.database
        cls.coverage=[]
    @classmethod
    def tearDownClass(cls):cls.client.__exit__(None,None,None)
    def call(self,method,path,data=None,expected=200,headers=None):
        r=self.client.request(method,path,json=data,headers=self.headers if headers is None else headers)
        self.assertEqual(r.status_code,expected,f'{method} {path}: {r.text}')
        self.coverage.append({'method':method,'path':path,'status':expected})
        return r.json()
    def project(self,**extra):
        return self.call('POST','/api/projects',{'name':'阶段合成项目','department':'隔离测试部','devOwner':'隔离开发者','businessOwner':'隔离业务','targetEndDate':'2027-01-01','solutionType':'custom_application',**extra})
    def requirement(self,pid,**extra):
        return self.call('POST','/api/requirements',{'title':'阶段合成工作','projectId':pid,'department':'隔离测试部','assignee':'隔离开发者','requester':'隔离业务','expectedDeliveryTime':'2027-01-01',**extra})
    def test_01_foundation(self):
        self.call('GET','/api/health',headers={});self.call('GET','/pm/api/ready',headers={})
        with self.db.engine.connect() as c:
            self.assertEqual(schema_difference(catalog(c)),[])
            before=c.execute(text('SELECT count(*) FROM system_settings')).scalar()
        self.call('GET','/api/not-implemented',expected=404,headers={})
        with self.assertRaises(ValueError):Settings('postgresql://x@127.0.0.1:5432/live')
        self.call('GET','/api/projects',expected=401,headers={'X-PM-Role':'super_admin'})
        self.assertEqual(self.call('GET','/api/categories',expected=401,headers={})['error'],'请在钉钉内重新登录后操作')
        with self.db.engine.connect() as c:self.assertEqual(c.execute(text('SELECT count(*) FROM system_settings')).scalar(),before)
        with self.assertRaises(RuntimeError):
            with UnitOfWork(self.db,self.app.state.dispatcher) as u:
                u.connection.execute(text("INSERT INTO system_settings(key,value) VALUES('rollback-test','1')"));raise RuntimeError('inject')
        with self.db.engine.connect() as c:self.assertEqual(c.execute(text("SELECT count(*) FROM system_settings WHERE key='rollback-test'")).scalar(),0)
    def test_02_categories_and_projects(self):
        cat=self.call('POST','/api/categories',{'name':'阶段分类','owner':['隔离业务']});cid=cat['id']
        self.call('GET','/api/categories/'+cid)
        self.call('PUT','/api/categories/'+cid,{'name':'阶段分类编辑'})
        proj=self.project(categoryId=cid,createInitialL3=True);pid=proj['id'];rid=proj['initialRequirementId'];self.assertTrue(rid)
        self.assertGreater(len(self.call('GET',f'/api/requirements/{rid}/phases')),0)
        self.call('GET',f'/api/categories/{cid}/projects')
        self.call('DELETE',f'/api/categories/{cid}',expected=400)
        self.call('DELETE',f'/api/projects/{pid}',expected=400)
        self.call('PUT',f'/api/projects/{pid}',{'description':'updated'})
        self.call('PUT',f'/api/projects/{pid}',{'devOwner':'隔离项目管理员'},expected=403,headers={'X-PM-Session':'fixture-stage-editor'})
        self.call('PUT',f'/api/projects/{pid}',{'description':'no'},expected=403,headers={'X-PM-Session':'fixture-stage-other'})
        self.call('DELETE',f'/api/requirements/{rid}');self.call('DELETE',f'/api/projects/{pid}');self.call('DELETE',f'/api/categories/{cid}')
    def test_03_work_and_phases(self):
        pid=self.project()['id'];rid=self.requirement(pid,images=[{'name':'tiny','type':'image/png','data':'data:image/png;base64,YQ=='}])['id']
        row=self.call('GET',f'/api/requirements/{rid}');self.assertNotIn('data',row['images'][0])
        self.call('PUT',f'/api/requirements/{rid}',{'description':'edited','images':row['images']})
        image=self.client.get(f'/api/requirements/{rid}/attachments/0',headers=self.headers);self.assertEqual(image.content,b'a')
        self.call('POST',f'/api/requirements/{rid}/work-logs',{'content':'工作进展','visibility':'business_shared'})
        self.call('GET',f'/api/requirements/{rid}/work-logs')
        self.call('POST',f'/api/requirements/{rid}/work-logs',{'content':' '},expected=400)
        self.call('PUT',f'/api/requirements/{rid}',{'status':'进行中'},expected=400)
        self.call('PUT',f'/api/requirements/{rid}',{'status':'进行中','reason':'开始开发'})
        self.call('PUT',f'/api/requirements/{rid}',{'status':'待交付','reason':'提交'},expected=400)
        ph=self.call('POST',f'/api/requirements/{rid}/phases',{'phaseKey':'custom','phaseLabel':'自定义阶段'})
        self.call('PUT',f"/api/requirements/{rid}/phases/{ph['id']}",{'status':'in_progress'})
        self.call('GET',f'/api/requirements/{rid}/changelogs');self.call('GET','/api/changelogs')
        self.call('GET','/api/requirements/live?projectId='+pid)
        self.call('GET','/api/requirements?status=进行中')
        self.call('POST','/api/requirements/bulk-classification',{'ids':[rid],'status':'已交付','reason':'历史补录'})
        self.assertEqual(self.call('GET',f'/api/requirements/{rid}')['status'],'已交付')
        self.call('POST','/api/requirements/bulk-delete',{'ids':[rid,'missing']})
        self.call('POST','/api/projects/bulk-delete',{'ids':[pid,'missing']})
        self.requirement(self.project()['id'],flowMode='quick_iteration',expectedDeliveryTime='2027-01-01') if False else None
    def test_04_roles(self):
        cfg=self.call('GET','/api/system/personnel')
        self.call('PUT','/api/system/personnel',{'assignments':cfg['assignments'],'customRoles':[]})
        roles=[{'key':'custom_first','label':'一','pages':['requirements'],'actions':['project.create']},{'key':'custom_second','label':'二','pages':['workspace'],'actions':[]}]
        self.call('PUT','/api/system/personnel',{'assignments':cfg['assignments'],'customRoles':roles})
        self.assertEqual(len(self.call('GET','/api/system/personnel')['customRoles']),2)
        self.call('PUT','/api/system/personnel',{'assignments':[]},expected=400)
        self.call('GET','/api/system/personnel',expected=403,headers={'X-PM-Session':'fixture-stage-editor'})
        self.call('PUT','/api/system/personnel',{'assignments':cfg['assignments'],'customRoles':[]})
    def test_05_iterations_audit(self):
        pid=self.project()['id'];sp=self.call('POST','/api/sprints',{'name':'合成迭代','projectId':pid})['id']
        self.call('GET','/api/sprints');self.call('GET','/api/sprints/'+sp);self.call('PUT','/api/sprints/'+sp,{'status':'已发布'})
        self.call('GET','/api/sprints/current',expected=404);self.call('DELETE','/api/sprints/'+sp)
        rel=self.call('POST','/api/releases',{'projectId':pid,'version':'v1.0.0'})['id'];self.call('GET','/api/releases');self.call('GET','/api/releases/'+rel)
        self.call('POST','/api/app-logs',{'message':'token=secret password=hidden','source':'synthetic'},headers={})
        logs=self.call('GET','/api/app-logs?source=synthetic');self.assertNotIn('secret',logs[0]['message'])
        self.call('GET','/api/operations');self.call('GET','/api/dingtalk/options');self.call('GET','/api/dingtalk/config',headers={})
        self.call('POST','/api/dingtalk/login',{},expected=400,headers={})
        self.app.state.gateway.auth_codes['synthetic-code']={'userid':'stage-editor','name':'隔离开发者'}
        login=self.call('POST','/api/dingtalk/login',{'authCode':'synthetic-code'},headers={});self.assertTrue(login['user']['sessionToken'])
        self.call('GET','/api/todos/unread-count')

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ProjectWorkTests))
    output={'passed':result.wasSuccessful(),'tests':result.testsRun,'cases':ProjectWorkTests.coverage,'database':getattr(ProjectWorkTests,'name',''),'failures':len(result.failures),'errors':len(result.errors)}
    (ROOT/'.runtime/test-results/project-work.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    sys.exit(0 if result.wasSuccessful() else 1)
