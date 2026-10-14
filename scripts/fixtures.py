"""Explicit synthetic data only, no automatic app startup seed."""
from pathlib import Path
import json
from datetime import datetime,timedelta
import psycopg2
from sqlalchemy.engine import make_url

ROOT=Path(__file__).resolve().parents[1]
ACTORS=[('stage-super','隔离管理员','super_admin',True),('stage-admin','隔离项目管理员','admin',True),('stage-editor','隔离开发者','editor',True),('stage-viewer','隔离业务','viewer',False),('stage-other','隔离无关编辑','editor',True)]
NOW='2026-10-13 09:00:00'

def seed(url,now=NOW):
    parsed=make_url(url)
    if parsed.host!='127.0.0.1' or parsed.port!=55432 or not parsed.database.startswith('pm_test_rebuild_'):
        raise RuntimeError('fixture target refused')
    url=parsed.set(drivername='postgresql').render_as_string(hide_password=False)
    templates=json.loads((ROOT/'contracts/phase-template-seed.json').read_text('utf-8'))
    with psycopg2.connect(url) as c:
        with c.cursor() as cur:
            for uid,name,role,developer in ACTORS:
                cur.execute('INSERT INTO app_users(id,dingUserId,name,role,department,devOwnerName,lastLoginAt) VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(dingUserId) DO NOTHING',
                    ['u-'+uid,uid,name,role,'隔离测试部',name if developer else '',now])
                cur.execute('INSERT INTO app_sessions(token,userId,expiresAt,createdAt) VALUES(%s,%s,%s,%s) ON CONFLICT(token) DO UPDATE SET expiresAt=excluded.expiresAt',
                    ['fixture-'+uid,uid,(datetime.strptime(now,'%Y-%m-%d %H:%M:%S')+timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S'),now])
            cfg={'users':[{'name':name,'userId':uid,'accessRole':role,'isDeveloper':dev,'enabled':True} for uid,name,role,dev in ACTORS],'customRoles':[]}
            cur.execute('INSERT INTO system_settings(key,value,updatedAt) VALUES(%s,%s,%s) ON CONFLICT(key) DO NOTHING',['access_control',json.dumps(cfg,ensure_ascii=False),now])
            personnel={'developers':[{'name':name,'shortName':name,'nick':name,'userId':uid,'role':'developer','permissions':['requirements','kanban','knowledge','changelog','sprints','workspace','intake','demandPool','notifications']} for uid,name,role,dev in ACTORS if dev],
                'admins':[{'name':name,'userId':uid,'role':'admin','permissions':['requirements','kanban','knowledge','changelog','sprints','workspace','intake','demandPool','notifications','operations','system']} for uid,name,role,dev in ACTORS if role in ['super_admin','admin']]}
            cur.execute('INSERT INTO system_settings(key,value,updatedAt) VALUES(%s,%s,%s) ON CONFLICT(key) DO NOTHING',['personnel',json.dumps(personnel,ensure_ascii=False),now])
            for st,phases in templates.items():
                for i,(key,label,description,required) in enumerate(phases):
                    cur.execute('INSERT INTO requirement_phase_templates(id,solutionType,phaseKey,phaseLabel,description,required,sortOrder,enabled,createdAt,updatedAt) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(solutionType,phaseKey) DO NOTHING',
                        ['rpt-'+st+'-'+key,st,key,label,description,required,i+1,1,now,now])
    uid,name,role,_=ACTORS[0]
    return {'id':'u-'+uid,'dingUserId':uid,'name':name,'role':role,'sessionToken':'fixture-'+uid,'isDeveloper':True,'permissions':['requirements','system'],'profile':'rebuild'}

if __name__=='__main__':
    cfg=json.loads((ROOT/'.runtime/config.json').read_text('utf-8'))
    fixture=seed(cfg['database_url'])
    (ROOT/'.runtime/fixture.json').write_text(json.dumps(fixture,ensure_ascii=False),encoding='utf-8')
    contacts={'source':'dingtalk','integrationMode':'fake','users':[{'userId':uid,'name':name,'department':'隔离测试部'} for uid,name,role,dev in ACTORS],
        'developers':[{'userId':uid,'name':name,'shortName':name,'nick':name} for uid,name,role,dev in ACTORS if dev],
        'businessOwners':['隔离业务'],'departments':['隔离测试部'],'departmentTree':[{'id':'stage-dept','name':'隔离测试部','children':[]}]}
    (ROOT/'.runtime/contacts.json').write_text(json.dumps(contacts,ensure_ascii=False),encoding='utf-8')
    print('Synthetic local actors/templates ready; credentials not printed')
