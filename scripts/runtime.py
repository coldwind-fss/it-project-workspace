"""Explicit local database preparation. No parent workspace or automatic startup DDL."""
from pathlib import Path
import hashlib,json,os,secrets,sys
import psycopg2
from psycopg2 import sql
from sqlalchemy.engine import make_url
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))

def environment():
    values={}
    file=ROOT/'.env'
    if file.exists():
        for line in file.read_text('utf-8-sig').splitlines():
            line=line.strip()
            if not line or line.startswith('#'):continue
            key,separator,value=line.partition('=')
            if not separator:raise ValueError('Invalid .env assignment')
            values[key.strip()]=value.strip().strip('"').strip("'")
    values.update(os.environ)
    return values

def admin_url(database='postgres'):
    value=environment().get('ITPW_ADMIN_DATABASE_URL','')
    if not value:raise RuntimeError('Set ITPW_ADMIN_DATABASE_URL in .env or the environment; see docs/DEVELOPMENT.md')
    url=make_url(value)
    if url.get_backend_name()!='postgresql' or url.host!='127.0.0.1' or url.port!=55432:
        raise RuntimeError('Database initializer must target dedicated local PostgreSQL at 127.0.0.1:55432')
    if database!='postgres' and not database.startswith('pm_test_rebuild_'):raise ValueError('Synthetic database name required')
    return url.set(database=database,drivername='postgresql').render_as_string(hide_password=False)

def runtime_role():return 'itpw_runtime_'+hashlib.sha256(str(ROOT).encode()).hexdigest()[:8]

def prepare_database(name,password):
    if not name.startswith('pm_test_rebuild_') or not name.replace('_','').isalnum():raise ValueError('Synthetic database name required')
    role=runtime_role()
    with psycopg2.connect(admin_url()) as check:
        with check.cursor() as cur:
            cur.execute('SELECT 1 FROM pg_roles WHERE rolname=%s',[role]);role_exists=bool(cur.fetchone())
    connection=psycopg2.connect(admin_url());connection.autocommit=True
    try:
        with connection.cursor() as cur:
            if not role_exists:cur.execute(sql.SQL('CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD {}').format(sql.Identifier(role),sql.Literal(password)))
            cur.execute('SELECT 1 FROM pg_database WHERE datname=%s',[name])
            if not cur.fetchone():cur.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
    finally:connection.close()
    with psycopg2.connect(admin_url(name)) as connection:
        with connection.cursor() as cur:
            cur.execute("SELECT count(*) FROM pg_tables WHERE schemaname='public'")
            if cur.fetchone()[0]==0:cur.execute((ROOT/'contracts/schema.sql').read_text('utf-8'))
            cur.execute(sql.SQL('REVOKE CREATE ON SCHEMA public FROM PUBLIC,{}').format(sql.Identifier(role)))
            cur.execute(sql.SQL('GRANT USAGE ON SCHEMA public TO {}').format(sql.Identifier(role)))
            cur.execute(sql.SQL('GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA public TO {}').format(sql.Identifier(role)))
            cur.execute(sql.SQL('GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO {}').format(sql.Identifier(role)))
            cur.execute(sql.SQL('GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO {}').format(sql.Identifier(role)))
            cur.execute(sql.SQL('REVOKE CREATE,TEMPORARY ON DATABASE {} FROM PUBLIC,{}').format(sql.Identifier(name),sql.Identifier(role)))
    return make_url(admin_url(name)).set(username=role,password=password,drivername='postgresql+psycopg2').render_as_string(hide_password=False)

def load_config():return json.loads((ROOT/'.runtime/config.json').read_text('utf-8'))

def prepare():
    folder=ROOT/'.runtime';folder.mkdir(exist_ok=True);(folder/'test-results').mkdir(exist_ok=True)
    secret=folder/'runtime-secret.json'
    if secret.exists():password=json.loads(secret.read_text('utf-8'))['password']
    else:
        password=environment().get('ITPW_RUNTIME_PASSWORD') or secrets.token_urlsafe(32)
        secret.write_text(json.dumps({'password':password}),encoding='utf-8');secret.chmod(0o600)
    suffix=hashlib.sha256(str(ROOT).encode()).hexdigest()[:8]
    url=prepare_database('pm_test_rebuild_workspace_'+suffix,password)
    env=environment()
    cfg={'database_url':url,'backend_port':int(env.get('ITPW_API_PORT','8084')),'ui_port':int(env.get('ITPW_UI_PORT','3004')),'public_base':env.get('ITPM_PUBLIC_BASE','/pm/'),'integration_mode':'fake','performance_user_id':'stage-editor'}
    config=folder/'config.json';config.write_text(json.dumps(cfg,indent=2),encoding='utf-8');config.chmod(0o600)
    from itpm.settings import Settings
    from itpm.infrastructure.database import Database
    db=Database(Settings(url))
    try:
        if not db.check():
            (folder/'schema-differences.json').write_text(json.dumps(db.differences,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps({'readiness':db.ready_code,'differences':db.differences},ensure_ascii=False))
            raise RuntimeError('Database readiness failed: '+db.ready_code)
    finally:db.close()
    print('Dedicated synthetic database prepared; application role restricted; no credentials printed.')

if __name__=='__main__':prepare()
