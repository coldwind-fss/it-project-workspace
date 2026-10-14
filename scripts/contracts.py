"""Deterministic OpenAPI/TypeScript generation; no startup or DB calls."""
from pathlib import Path
import sys,json,argparse
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from itpm.app import create_app
from itpm.settings import Settings

def ts(schema):
    if '$ref' in schema:return 'components["schemas"]["'+schema['$ref'].split('/')[-1]+'"]'
    if 'anyOf' in schema:return ' | '.join(ts(s) for s in schema['anyOf'])
    if 'enum' in schema:return ' | '.join(json.dumps(x,ensure_ascii=False) for x in schema['enum'])
    t=schema.get('type')
    if t=='null':return 'null'
    if t=='string':return 'string'
    if t in ['integer','number']:return 'number'
    if t=='boolean':return 'boolean'
    if t=='array':return '('+ts(schema.get('items',{}))+')[]'
    if t=='object' or 'properties' in schema:
        fields=[json.dumps(k)+('' if k in schema.get('required',[]) else '?')+': '+ts(v) for k,v in schema.get('properties',{}).items()]
        extra=schema.get('additionalProperties')
        if extra:fields.append('[key: string]: '+(ts(extra) if isinstance(extra,dict) else 'unknown'))
        return '{ '+ '; '.join(fields)+' }' if fields else 'Record<string, unknown>'
    return 'unknown'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    generated={}
    app=create_app(Settings('postgresql+psycopg2://unused@127.0.0.1:55432/pm_test_rebuild_contracts'))
    document=app.openapi()
    generated[ROOT/'contracts/openapi.json']=json.dumps(document,ensure_ascii=False,indent=2)+'\n'
    preview=create_app(Settings('postgresql+psycopg2://unused@127.0.0.1:55432/pm_test_rebuild_contracts',profile='preview'))
    generated[ROOT/'contracts/preview-openapi.json']=json.dumps(preview.openapi(),ensure_ascii=False,indent=2)+'\n'
    from fastapi.routing import APIRoute
    operations=[]
    for route in preview.routes:
        if not isinstance(route,APIRoute) or not route.include_in_schema:continue
        origin=route.endpoint.__module__
        owner=origin.split('modules.',1)[-1].split('.')[0] if 'modules.' in origin else 'platform'
        for method in sorted(route.methods):
            operation=preview.openapi()['paths'].get(route.path,{}).get(method.lower())
            if operation:operations.append({'method':method,'path':route.path,'owner':owner,'operationId':operation['operationId'],'security':operation.get('security',[]),'responseModel':getattr(route.response_model,'__name__',str(route.response_model))})
    generated[ROOT/'contracts/api-catalog.json']=json.dumps({'source':'Generated from application routes and Pydantic/OpenAPI; includes the explicit preview session operation','operations':sorted(operations,key=lambda item:(item['path'],item['method']))},ensure_ascii=False,indent=2)+'\n'
    definitions=document.get('components',{}).get('schemas',{})
    output=['// Generated from backend OpenAPI; run scripts/contracts.py.','export interface components { schemas: {']
    output.extend(json.dumps(name)+': '+ts(schema) for name,schema in definitions.items());output.append('} }')
    generated[ROOT/'frontend/src/api/generated.ts']='\n'.join(output)+'\n'
    drift=[]
    for file,content in generated.items():
        if args.check:
            if not file.exists() or file.read_text('utf-8')!=content:drift.append(file.relative_to(ROOT).as_posix())
        else:file.write_text(content,encoding='utf-8')
    if drift:raise SystemExit('Generated contracts differ: '+', '.join(drift)+'. Run scripts/contracts.py and review the change.')
    print('Generated contracts match.' if args.check else 'OpenAPI and TypeScript schemas generated without startup.')

if __name__=='__main__':main()
