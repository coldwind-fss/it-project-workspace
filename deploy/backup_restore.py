"""Explicit quiesced snapshot and restore to a NEW guarded synthetic database."""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'scripts')]
from runtime import environment,admin_url,load_config,runtime_role
from sqlalchemy import create_engine,inspect,select,MetaData,Table
from sqlalchemy.engine import make_url
import psycopg2
from psycopg2 import sql
def hashes(url):
    engine=create_engine(url,hide_parameters=True);result={}
    try:
        with engine.connect() as connection:
            for name in sorted(inspect(connection).get_table_names(schema='public')):
                table=Table(name,MetaData(),schema='public',autoload_with=connection)
                rows=sorted([dict(row) for row in connection.execute(select(table)).mappings()],key=lambda row:json.dumps(row,sort_keys=True,default=str))
                result[name]={'count':len(rows),'sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,default=str).encode()).hexdigest()}
    finally:engine.dispose()
    return result
def files(folder):return {file.relative_to(folder).as_posix():hashlib.sha256(file.read_bytes()).hexdigest() for file in folder.rglob('*') if file.is_file()}
def pg_command(command,url,*arguments):
    parsed=make_url(url);env={**os.environ,'PGPASSWORD':parsed.password or ''}
    subprocess.run([command,'-h',parsed.host,'-p',str(parsed.port or 5432),'-U',parsed.username,*arguments,parsed.database],check=True,env=env)
def main():
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='action',required=True)
    backup=sub.add_parser('backup');backup.add_argument('--output',required=True,type=Path);backup.add_argument('--quiesced',action='store_true',required=True)
    restore=sub.add_parser('restore');restore.add_argument('--backup',required=True,type=Path);restore.add_argument('--database',required=True)
    args=parser.parse_args();env=environment();cfg=load_config() if (ROOT/'.runtime/config.json').exists() else {}
    url=env.get('ITPM_DATABASE_URL') or cfg.get('database_url')
    if not url:raise SystemExit('Application database URL required')
    attachments=Path(env.get('ITPM_ATTACHMENT_DIR',str(ROOT/'.runtime/attachments')))
    if args.action=='backup':
        output=args.output.resolve()
        if output.exists():raise SystemExit('Use a new, explicit backup directory')
        output.mkdir(parents=True);output.chmod(0o700)
        before=hashes(url);file_hashes=files(attachments)
        pg_command('pg_dump',url,'-Fc','--no-owner','-f',str(output/'database.dump'))
        if attachments.exists():shutil.copytree(attachments,output/'attachments')
        else:(output/'attachments').mkdir()
        if hashes(url)!=before or files(attachments)!=file_hashes:raise RuntimeError('Data changed during snapshot; do not accept this backup')
        manifest={'tables':before,'files':file_hashes,'dumpSha256':hashlib.sha256((output/'database.dump').read_bytes()).hexdigest()}
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        print(json.dumps({'backup':str(output),'tables':len(before),'attachments':len(file_hashes)}));return
    name=args.database
    if not name.startswith('pm_test_rebuild_') or not name.replace('_','').isalnum():raise SystemExit('New local synthetic database required')
    backup=args.backup.resolve();manifest=json.loads((backup/'manifest.json').read_text())
    assert hashlib.sha256((backup/'database.dump').read_bytes()).hexdigest()==manifest['dumpSha256']
    assert files(backup/'attachments')==manifest['files']
    connection=psycopg2.connect(admin_url());connection.autocommit=True
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1 FROM pg_database WHERE datname=%s',[name])
            if cursor.fetchone():raise SystemExit('Existing restore target refused')
            cursor.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
    finally:connection.close()
    # pg_restore uses explicit -d; pg_dump's positional database convention is different.
    admin=make_url(admin_url(name));restore_env={**os.environ,'PGPASSWORD':admin.password or ''}
    subprocess.run(['pg_restore','-h',admin.host,'-p',str(admin.port),'-U',admin.username,'--no-owner','--no-privileges','--exit-on-error','-d',name,str(backup/'database.dump')],check=True,env=restore_env)
    role=make_url(url).username
    with psycopg2.connect(admin_url(name)) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL('REVOKE CREATE ON SCHEMA public FROM PUBLIC,{}').format(sql.Identifier(role)))
            cursor.execute(sql.SQL('GRANT USAGE ON SCHEMA public TO {}').format(sql.Identifier(role)))
            cursor.execute(sql.SQL('GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA public TO {}').format(sql.Identifier(role)))
            cursor.execute(sql.SQL('GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO {}').format(sql.Identifier(role)))
            cursor.execute(sql.SQL('REVOKE CREATE,TEMPORARY ON DATABASE {} FROM PUBLIC,{}').format(sql.Identifier(name),sql.Identifier(role)))
    restored=make_url(url).set(database=name).render_as_string(hide_password=False)
    assert hashes(restored)==manifest['tables']
    print(json.dumps({'database':name,'tablesCompared':len(manifest['tables']),'attachmentHashes':len(manifest['files']),'passed':True}))
if __name__=='__main__':main()
