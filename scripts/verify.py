"""One independent verification entry point used locally and by CI."""
import argparse,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(*command,cwd=ROOT,env=None):subprocess.run([str(x) for x in command],cwd=cwd,env=env,check=True)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--no-database',action='store_true');args=parser.parse_args()
    npm=shutil.which('npm.cmd' if os.name=='nt' else 'npm')
    if not npm:raise SystemExit('npm missing; run scripts/setup.py first.')
    folder=ROOT/'.runtime/test-results';folder.mkdir(parents=True,exist_ok=True)
    run(sys.executable,ROOT/'scripts/contracts.py','--check')
    run(npm,'run','typecheck',cwd=ROOT/'frontend')
    build_env={**os.environ,'VITE_PUBLIC_BASE':'/pm/','VITE_API_BASE':'/pm/api','VITE_SESSION_KEY':'itpm-demo-user','VITE_PREVIEW_ENTRY':'/pm/preview-login'}
    run(npm,'run','build',cwd=ROOT/'frontend',env=build_env)
    run(sys.executable,ROOT/'scripts/architecture.py')
    run(sys.executable,ROOT/'scripts/repository_check.py')
    if not args.no_database:
        run(sys.executable,ROOT/'scripts/runtime.py')
        # Fixtures are explicitly prepared for the standalone suite's contact projections.
        run(sys.executable,ROOT/'scripts/fixtures.py')
    run(sys.executable,ROOT/'tests/test_dingtalk.py')
    run(shutil.which('node'),'tests/test_preview_entry.mjs',env={**os.environ,'PYTHON':sys.executable})
    suites=['test_foundation.py','test_project_work.py','test_demand_delivery.py','test_management.py','test_end_to_end.py','test_preview_entry.py']
    if not args.no_database:
        for suite in suites:run(sys.executable,ROOT/'tests'/suite)
    (folder/'verification.json').write_text(json.dumps({'passed':True,'database':not args.no_database,'suites':suites if not args.no_database else [],'kind':'independent repository checks'},indent=2)+'\n',encoding='utf-8')
    print('Independent workspace verification passed; live integration is not claimed.')
if __name__=='__main__':main()
