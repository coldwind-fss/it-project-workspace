"""Run API or independent notification worker from repository configuration."""
import argparse,json,sys,time
from pathlib import Path
from runtime import ROOT,environment,load_config
sys.path.insert(0,str(ROOT/'backend'))
from itpm.app import create_app
from itpm.settings import Settings
from itpm.infrastructure.gateway import gateway_for

def configured_app():
    env=environment();cfg=load_config() if (ROOT/'.runtime/config.json').exists() else {}
    url=env.get('ITPM_DATABASE_URL') or cfg.get('database_url')
    if not url:raise RuntimeError('Set ITPM_DATABASE_URL or explicitly prepare the synthetic database.')
    base=env.get('ITPM_PUBLIC_BASE',cfg.get('public_base','/pm/'))
    ui_port=int(env.get('ITPW_UI_PORT',cfg.get('ui_port',3004)))
    settings=Settings(url,profile=env.get('ITPM_PROFILE','preview'),public_base=base,public_url=env.get('ITPW_PUBLIC_URL') or f'http://127.0.0.1:{ui_port}'+base,
        integration_mode=env.get('ITPM_INTEGRATION_MODE','fake'),performance_user_id=env.get('ITPM_PERFORMANCE_USER_ID',cfg.get('performance_user_id','stage-editor')),
        attachment_dir=Path(env.get('ITPM_ATTACHMENT_DIR',str(ROOT/'.runtime/attachments'))),work_sync_token=env.get('ITPM_WORK_SYNC_TOKEN',''),
        dingtalk_app_key=env.get('ITPM_DINGTALK_APP_KEY',''),dingtalk_app_secret=env.get('ITPM_DINGTALK_APP_SECRET',''),dingtalk_corp_id=env.get('ITPM_DINGTALK_CORP_ID',''),
        dingtalk_agent_id=env.get('ITPM_DINGTALK_AGENT_ID',''),dingtalk_robot_code=env.get('ITPM_DINGTALK_ROBOT_CODE',''))
    vocabulary=json.loads((ROOT/'contracts/business-vocabulary.json').read_text('utf-8'))
    contacts_file=Path(env.get('ITPM_CONTACTS_FILE',str(ROOT/'.runtime/contacts.json')))
    contacts=json.loads(contacts_file.read_text('utf-8')) if contacts_file.exists() else None
    return create_app(settings,gateway=gateway_for(settings,vocabulary,contacts=contacts))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--worker',action='store_true');parser.add_argument('--once',action='store_true');args=parser.parse_args()
    app=configured_app();env=environment()
    if args.worker:
        from itpm.worker import run_once
        try:
            while True:
                result=run_once(app);print(json.dumps({'status':result['status'],'processed':result['processed']}),flush=True)
                if args.once:break
                time.sleep(30)
        finally:app.state.database.close();app.state.gateway.close()
    else:
        import uvicorn
        uvicorn.run(app,host=env.get('ITPW_BIND_HOST','127.0.0.1'),port=int(env.get('ITPW_API_PORT','8084')),access_log=False)
if __name__=='__main__':main()
