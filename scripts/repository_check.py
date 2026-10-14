"""Validate documented paths and public-file boundaries without reading runtime secrets."""
import ast,json,re,sys,subprocess,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
issues=[]
names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT,env={**os.environ,'GIT_CONFIG_GLOBAL':os.devnull}).decode('utf-8').split('\0')
files=[ROOT/name for name in set(names) if name and (ROOT/name).is_file()]
for file in files:
    relative=file.relative_to(ROOT).as_posix()
    if file.suffix in {'.pem','.key','.db','.sqlite','.p12'} or file.name=='.env':issues.append(relative+': private runtime file')
    if file.suffix not in {'.py','.ts','.vue','.mjs','.md','.json','.yml','.yaml','.ps1','.html','.txt'}:continue
    text=file.read_text('utf-8-sig')
    if re.search(r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',text):issues.append(relative+': private key')
    if re.search(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b',text):issues.append(relative+': credential-shaped value')
    if re.search(r'D:[\\/](?:Dev|Middleware)|\.tmp-' r'environment|coldwind-fss/[12](?:\.git|[\s/])',text):issues.append(relative+': old machine/workspace dependency')
    if file.suffix=='.md':
        for target in re.findall(r'\]\(([^)]+)\)',text):
            target=target.split('#',1)[0]
            if not target or re.match(r'[a-z]+://|mailto:',target):continue
            if not (file.parent/target).exists():issues.append(relative+': missing document link '+target)
print(json.dumps({'passed':not issues,'publicFilesChecked':len(files),'issues':issues},ensure_ascii=False))
raise SystemExit(1 if issues else 0)
