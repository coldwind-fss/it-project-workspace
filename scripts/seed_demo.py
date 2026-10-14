"""Explicit synthetic actors and one existing product-flow example; never runs on startup."""
import json,sys
from runtime import ROOT,load_config
from fixtures import seed
from demo_flow import run_flow
sys.path.insert(0,str(ROOT/'backend'))
from itpm.core.ports import SystemClock
from fastapi.testclient import TestClient
from serve import configured_app
def main():
    cfg=load_config();fixture=seed(cfg['database_url'],now=SystemClock().now())
    (ROOT/'.runtime/fixture.json').write_text(json.dumps(fixture,ensure_ascii=False),encoding='utf-8')
    from fixtures import ACTORS
    contacts={'source':'synthetic','users':[{'userId':uid,'name':name,'department':'隔离测试部'} for uid,name,role,dev in ACTORS],
        'developers':[{'userId':uid,'name':name,'shortName':name,'nick':name} for uid,name,role,dev in ACTORS if dev],
        'businessOwners':['隔离业务'],'departments':['隔离测试部'],'departmentTree':[{'id':'demo-dept','name':'隔离测试部','children':[]}]}
    (ROOT/'.runtime/contacts.json').write_text(json.dumps(contacts,ensure_ascii=False),encoding='utf-8')
    app=configured_app()
    if app.state.database.settings.integration_mode!='fake':raise SystemExit('Demo seed requires Fake integration.')
    with TestClient(app) as client:
        def call(method,path,payload=None,role='super',headers=None):
            response=client.request(method,path,json=payload,headers={'X-PM-Session':'fixture-stage-'+role,**(headers or {})})
            response.raise_for_status();return response.json()
        if any(row['name']=='演示协作产品' for row in call('GET','/api/projects')):
            print('Synthetic actors ready; existing demo project preserved.');return
        result=run_flow(call)
    (ROOT/'.runtime/demo-flow.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Synthetic flow prepared; no real messages sent; private link tokens remain ignored.')
if __name__=='__main__':main()
