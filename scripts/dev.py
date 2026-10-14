"""Run the two development processes; Ctrl+C stops only children started here."""
import os,shutil,subprocess,sys
from runtime import ROOT,environment
def main():
    env=environment();base=env.get('ITPM_PUBLIC_BASE','/pm/');api=int(env.get('ITPW_API_PORT','8084'));ui=int(env.get('ITPW_UI_PORT','3004'))
    env.update(VITE_PUBLIC_BASE=base,VITE_API_BASE=base+'api',VITE_API_TARGET=f'http://127.0.0.1:{api}',VITE_SESSION_KEY='itpm-demo-user',VITE_PREVIEW_ENTRY=base+'preview-login')
    npm=shutil.which('npm.cmd' if os.name=='nt' else 'npm')
    if not npm:raise SystemExit('npm missing; run dependency setup first.')
    children=[]
    try:
        children.append(subprocess.Popen([sys.executable,str(ROOT/'scripts/serve.py')],cwd=ROOT,env=env))
        children.append(subprocess.Popen([npm,'run','dev','--','--port',str(ui)],cwd=ROOT/'frontend',env=env))
        print(f'Workspace: http://127.0.0.1:{ui}{base}',flush=True)
        while all(child.poll() is None for child in children):
            import time
            time.sleep(.5)
    except KeyboardInterrupt:pass
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
                try:child.wait(timeout=8)
                except subprocess.TimeoutExpired:child.kill()
if __name__=='__main__':main()
