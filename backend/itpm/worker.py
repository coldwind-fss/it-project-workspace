"""Explicit independent scheduler; importing/API startup never starts a loop."""
import argparse,json,time
from sqlalchemy import text
from itpm.app import create_app
from itpm.settings import Settings

def run_once(app):
    db=app.state.database
    if not db.check():raise RuntimeError('worker database/schema gate failed: '+db.ready_code)
    # Session lock on an autocommit connection prevents overlapping workers;
    # it does not keep a business transaction open across provider calls.
    with db.engine.connect().execution_options(isolation_level='AUTOCOMMIT') as connection:
        locked=connection.execute(text('SELECT pg_try_advisory_lock(82473013)')).scalar()
        if not locked:return {'status':'already_running','processed':0}
        try:
            results=app.state.scheduler.tick();return {'status':'completed','processed':len(results),'results':results}
        finally:connection.execute(text('SELECT pg_advisory_unlock(82473013)'))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--once',action='store_true');args=parser.parse_args()
    settings=Settings.from_env()
    if not settings.worker_enabled:raise SystemExit('Set ITPM_WORKER_ENABLED=1 for the explicitly separate worker')
    app=create_app(settings)
    try:
        while True:
            print(json.dumps(run_once(app),ensure_ascii=False),flush=True)
            if args.once:break
            time.sleep(30)
    except KeyboardInterrupt:pass
    finally:app.state.database.close();app.state.gateway.close()

if __name__=='__main__':main()
