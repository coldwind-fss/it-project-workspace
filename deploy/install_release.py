"""Explicit Linux release installation; no database initialization or seed."""
import argparse,hashlib,json,os,pwd,re,subprocess,sys,time,urllib.request,zipfile,socket,signal
from pathlib import Path
def run(*args,**kwargs):subprocess.run([str(x) for x in args],check=True,**kwargs)
def parse_env(file):
    values={}
    for line in file.read_text('utf-8').splitlines():
        line=line.strip()
        if line and not line.startswith('#'):
            key,separator,value=line.partition('=')
            if not separator:raise ValueError('Invalid environment file')
            values[key.strip()]=value.strip().strip('"').strip("'")
    return values
def ready(port,base):
    for _ in range(40):
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}'+base+'api/ready',timeout=2) as response:
                if response.status==200:return
        except Exception:pass
        time.sleep(.25)
    raise RuntimeError('Candidate readiness failed')
def probe(port,base):
    origin=f'http://127.0.0.1:{port}'
    with urllib.request.urlopen(origin+base) as response:html=response.read().decode();assert response.status==200
    for asset in re.findall(r'(?:src|href)="('+re.escape(base)+r'assets/[^\"]+)"',html):
        with urllib.request.urlopen(origin+asset) as response:assert response.status==200
    try:urllib.request.urlopen(origin+base+'api/requirements')
    except urllib.error.HTTPError as error:assert error.code==401
    else:raise RuntimeError('Anonymous internal ledger unexpectedly accepted')
def switch(root,release):
    temporary=root/'current-next';temporary.unlink(missing_ok=True);temporary.symlink_to(release);os.replace(temporary,root/'current')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--archive',required=True,type=Path);parser.add_argument('--sha256',required=True)
    parser.add_argument('--root',required=True,type=Path);parser.add_argument('--config',required=True,type=Path);parser.add_argument('--user',required=True)
    parser.add_argument('--service',default='it-project-workspace');parser.add_argument('--port',type=int,default=18090);parser.add_argument('--stage-port',type=int,default=18091);args=parser.parse_args()
    if sys.platform!='linux' or os.geteuid()!=0:raise SystemExit('Run explicitly as administrator on the intended Linux host.')
    if not re.fullmatch('[a-z_][a-z0-9_-]*',args.user) or not re.fullmatch('[a-z0-9-]+',args.service):raise SystemExit('Invalid service/user')
    pwd.getpwnam(args.user)
    root=args.root.resolve();config=args.config.resolve()
    if root==Path('/') or any(x in str(root)+str(config) for x in ['\n','\r',' ']):raise SystemExit('Explicit safe installation/config paths required')
    assert hashlib.sha256(args.archive.read_bytes()).hexdigest()==args.sha256
    env={**os.environ,**parse_env(config)}
    if int(env.get('ITPW_API_PORT','8084'))!=args.port:raise SystemExit('Configured API port differs from --port')
    for port in [args.stage_port]+([] if (root/'current').is_symlink() else [args.port]):
        with socket.socket() as check:check.bind(('127.0.0.1',port))
    for service in [args.service,args.service+'-worker']:
        unit=Path('/etc/systemd/system',service+'.service')
        if unit.exists() and str(root) not in unit.read_text():raise SystemExit('Existing unrelated service refused')
    with zipfile.ZipFile(args.archive) as package:
        manifest=json.loads(package.read('release-manifest.json'));base=manifest['publicBase']
        release=root/'releases'/hashlib.sha256(package.read('release-manifest.json')).hexdigest()[:12]
        release.mkdir(parents=True,exist_ok=True)
        for member in package.infolist():
            if not (release/member.filename).resolve().is_relative_to(release) or member.filename.startswith('/') or (member.external_attr>>16)&0o170000==0o120000:raise RuntimeError('Unsafe archive member')
        package.extractall(release)
    for name,digest in manifest['files'].items():assert hashlib.sha256((release/name).read_bytes()).hexdigest()==digest
    if env.get('ITPM_PUBLIC_BASE','/pm/')!=base:raise RuntimeError('Package and server public prefixes differ')
    python=root/'venv/bin/python'
    if not python.exists():run(sys.executable,'-m','venv',root/'venv')
    run(python,'-m','pip','install','--disable-pip-version-check','-r',release/'requirements.lock.txt');run(python,'-m','pip','check')
    # Existing account and external paths are owned/configured by the operator.
    run('chown','-R',args.user+':'+pwd.getpwnam(args.user).pw_name,release,root/'venv')
    staged_env={**env,'ITPW_API_PORT':str(args.stage_port),'ITPW_BIND_HOST':'127.0.0.1'}
    candidate=subprocess.Popen(['runuser','-u',args.user,'--',str(python),str(release/'scripts/serve.py')],cwd=release,env=staged_env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
    try:ready(args.stage_port,base);probe(args.stage_port,base)
    finally:
        if candidate.poll() is None:os.killpg(candidate.pid,signal.SIGTERM)
        candidate.wait(timeout=10)
    previous=(root/'current').resolve() if (root/'current').is_symlink() else None
    switch(root,release)
    try:
        for kind in ['api','worker']:
            template=(release/'deploy'/f'{kind}.service.example').read_text()
            template=template.replace('/opt/it-project-workspace',str(root)).replace('/etc/it-project-workspace/workspace.env',str(config)).replace('User=itpw','User='+args.user)
            filename=args.service+('-worker' if kind=='worker' else '')+'.service'
            Path('/etc/systemd/system',filename).write_text(template)
        run('systemctl','daemon-reload')
        run('systemctl','enable',args.service,args.service+'-worker')
        run('systemctl','restart',args.service,args.service+'-worker')
        ready(args.port,base);probe(args.port,base)
    except Exception:
        if previous:switch(root,previous);run('systemctl','restart',args.service,args.service+'-worker')
        else:run('systemctl','stop',args.service,args.service+'-worker')
        raise
    print(json.dumps({'release':str(release),'sourceCommit':manifest['sourceCommit'],'previous':str(previous) if previous else None,'ready':True,'databaseChanged':False}))
if __name__=='__main__':main()
