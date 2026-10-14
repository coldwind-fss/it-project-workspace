"""Create a current, verified source/UI release; runtime configuration stays external."""
import argparse,hashlib,json,os,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--base',default='/pm/');parser.add_argument('--allow-uncommitted',action='store_true');args=parser.parse_args()
    if not args.base.startswith('/') or not args.base.endswith('/') or '..' in args.base:raise SystemExit('Invalid public base')
    checks=json.loads((ROOT/'.runtime/test-results/verification.json').read_text('utf-8'))
    if not checks.get('passed') or not checks.get('database'):raise SystemExit('Run the independent full verification before packaging.')
    subprocess.run([str(ROOT/('.venv/Scripts/python.exe' if os.name=='nt' else '.venv/bin/python')),str(ROOT/'scripts/repository_check.py')],check=True,cwd=ROOT)
    git_env={**os.environ,'GIT_CONFIG_GLOBAL':os.devnull}
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,env=git_env,text=True).strip()
    dirty=bool(subprocess.check_output(['git','status','--porcelain','--untracked-files=normal'],cwd=ROOT,env=git_env,text=True).strip())
    if dirty and not args.allow_uncommitted:raise SystemExit('Commit current sources before release packaging.')
    build=ROOT/'.runtime/release-build';build.mkdir(parents=True,exist_ok=True)
    env={**os.environ,'VITE_PUBLIC_BASE':args.base,'VITE_API_BASE':args.base+'api','VITE_SESSION_KEY':'itpm-demo-user','VITE_PREVIEW_ENTRY':args.base+'preview-login'}
    subprocess.run(['npm.cmd' if os.name=='nt' else 'npm','run','build','--','--outDir',str(build)],cwd=ROOT/'frontend',env=env,check=True)
    files={}
    for folder in ['backend','frontend/src','frontend/configs','scripts','contracts','deploy']:
        for file in (ROOT/folder).rglob('*'):
            if file.is_file() and '__pycache__' not in file.parts:files[file.relative_to(ROOT).as_posix()]=file
    for name in ['package.json','package-lock.json','index.html']:files['frontend/'+name]=ROOT/'frontend'/name
    for file in build.rglob('*'):
        if file.is_file():files['frontend/dist/'+file.relative_to(build).as_posix()]=file
    files['requirements.lock.txt']=ROOT/'requirements.lock.txt'
    manifest={'product':'IT Project Workspace','sourceCommit':commit,'uncommitted':dirty,'publicBase':args.base,'files':{name:hashlib.sha256(file.read_bytes()).hexdigest() for name,file in sorted(files.items())}}
    encoded=json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2).encode();identifier=hashlib.sha256(encoded).hexdigest()[:12]
    archive=ROOT/'.runtime'/('it-project-workspace-'+identifier+'.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as package:
        for name,file in files.items():package.write(file,name)
        package.writestr('release-manifest.json',encoded)
    print(json.dumps({'archive':str(archive),'sourceCommit':commit,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':len(files)}))
if __name__=='__main__':main()
