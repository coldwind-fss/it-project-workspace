"""Install the repository's own pinned environment; PostgreSQL is configured separately."""
import argparse,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--database',action='store_true');args=parser.parse_args()
    if sys.version_info[:2]!=(3,12):raise SystemExit('Python 3.12 is required.')
    python=ROOT/('.venv/Scripts/python.exe' if os.name=='nt' else '.venv/bin/python')
    if not python.exists():subprocess.run([sys.executable,'-m','venv',str(ROOT/'.venv')],check=True)
    subprocess.run([str(python),'-m','pip','install','--disable-pip-version-check','-r',str(ROOT/'requirements.lock.txt')],check=True)
    npm=shutil.which('npm.cmd' if os.name=='nt' else 'npm')
    if not npm:raise SystemExit('Node.js 20+ and npm are required.')
    subprocess.run([npm,'ci'],cwd=ROOT/'frontend',check=True)
    if args.database:subprocess.run([str(python),str(ROOT/'scripts/runtime.py')],check=True)
    print('Dependencies ready. Configure .env, then run python scripts/runtime.py and python scripts/seed_demo.py.')
if __name__=='__main__':main()
