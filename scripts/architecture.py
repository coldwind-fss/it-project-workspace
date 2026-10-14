from pathlib import Path
import ast,json,re,sys
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'backend';issues=[];graph={}
for file in (SOURCE/'itpm').rglob('*.py'):
    module='.'.join(file.relative_to(SOURCE).with_suffix('').parts)
    if module.endswith('.__init__'):module=module[:-9]
    graph.setdefault(module,set());tree=ast.parse(file.read_text('utf-8'));domain=file.parent.name if 'modules' in file.parts else None
    for node in ast.walk(tree):
        imports=[]
        if isinstance(node,ast.Import):imports=[x.name for x in node.names]
        if isinstance(node,ast.ImportFrom):
            base=module.split('.')[:-node.level] if node.level else []
            imports=['.'.join([*base,node.module or '']).rstrip('.')]
        for target in imports:
            graph[module].add(target)
            if target=='server' or target.startswith('server.'):issues.append([str(file),node.lineno,'legacy import'])
            if domain and target.startswith('itpm.workflows'):issues.append([str(file),node.lineno,'module imports workflow'])
            if domain and target.startswith('itpm.modules.'):
                parts=target.split('.')
                if len(parts)>3 and parts[2]!=domain and parts[3]!='public':issues.append([str(file),node.lineno,'cross-domain private import'])
            if file.name=='rules.py' and target.split('.')[0] in {'os','socket','sqlalchemy','fastapi','httpx','requests'}:issues.append([str(file),node.lineno,'impure rules'])
            if file.name=='service.py' and target.startswith(('fastapi','httpx','requests')):issues.append([str(file),node.lineno,'HTTP in service'])
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
            if file.name=='repository.py' and node.func.attr in {'commit','rollback'}:issues.append([str(file),node.lineno,'repository owns transaction'])
        if file.name=='router.py' and isinstance(node,ast.Constant) and isinstance(node.value,str) and re.match(r'^\s*(SELECT|INSERT INTO|UPDATE \w+ SET|DELETE FROM)\b',node.value,re.I):issues.append([str(file),node.lineno,'SQL in router'])
visiting=set();visited=set()
def visit(module):
    if module in visiting:issues.append([module,0,'dependency cycle']);return
    if module in visited:return
    visiting.add(module)
    for target in graph.get(module,[]):
        if target in graph:visit(target)
    visiting.remove(module);visited.add(module)
for module in graph:visit(module)
for file in (ROOT/'frontend/src/features').rglob('*.ts'):
    s=file.read_text('utf-8')
    if re.search(r'\bfetch\s*\(',s):issues.append([str(file),0,'feature bypasses transport'])
baseline=json.loads((ROOT/'contracts/ui-baseline.json').read_text('utf-8'))
import hashlib
for name,expected in baseline['files'].items():
    file=ROOT/name
    if not file.exists():issues.append([name,0,'accepted UI file missing']);continue
    blocks=re.findall(r'<(?:template|style)\b[^>]*>[\s\S]*?</(?:template|style)>',file.read_text('utf-8'))
    actual=hashlib.sha256(json.dumps(blocks,ensure_ascii=False).encode()).hexdigest()
    if actual!=expected:issues.append([name,0,'accepted UI changed; update scope and baseline explicitly'])
result={'passed':not issues,'pythonModules':len(graph),'issues':issues,'uiBaselineFiles':len(baseline['files'])}
(ROOT/'.runtime/test-results/architecture.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False));sys.exit(1 if issues else 0)
