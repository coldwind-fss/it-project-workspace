import json
from itpm.core.errors import require
from .rules import values,labels,RECORD_TYPES,STATUSES,CONCLUSIONS

class Poc:
    def __init__(self,repo,clock,ids,identity,portfolio,work,demand,files,audit):
        self.repo,self.clock,self.ids,self.identity=repo,clock,ids,identity
        self.portfolio,self.work,self.demand,self.files,self.audit=portfolio,work,demand,files,audit
    def payload(self,u,row,legacy=False):
        if not row:return None
        item=labels(row);item.update(readOnly=legacy,legacy=legacy,
            attachments=self.files.list(u,'demand_pool_poc' if legacy else 'poc_workbench',row.get('sourceId') or row['id']))
        return item
    def legacy_payload(self,u,source):
        state=source.get('status') or 'running';title=source.get('demandTitle') or source.get('demandId') or ''
        row={k:'' for k in 'hypothesis method limitations nextSteps modelName modelVersion promptOrApproach reuseGuidance sourceRef derivedFromId archivedAt'.split()}
        row.update({k:source.get(k) or '' for k in 'ownerUserId ownerName projectId projectName requirementId requirementTitle demandId demandTitle scope successCriteria result createdByUserId createdByName createdAt completedAt'.split()})
        row.update(id='legacy-poc-'+source['id'],sourceId=source['id'],recordType='poc',
            title=(source.get('goal') or '').strip() or (title+' · POC 验证' if title else '需求池 POC 验证'),
            status='completed' if state=='completed' else 'archived' if state=='cancelled' else 'in_progress',
            conclusion=source.get('conclusion') or ('documented' if state=='completed' else ''),sourceType='demand_pool',sourceRef=source.get('demandId') or '',
            objective=source.get('goal') or '',sampleData=source.get('testData') or '',metrics={},tags=[],artifactType=source.get('artifactType') or 'text',
            updatedAt=source.get('updatedAt') or source.get('createdAt') or '')
        return self.payload(u,row,True)
    def get(self,u,identifier):
        if identifier.startswith('legacy-poc-'):
            rows=self.repo.legacy(u,identifier[len('legacy-poc-'):]);return self.legacy_payload(u,rows[0]) if rows else None
        return self.payload(u,self.repo.get(u,'poc_workbench_records',identifier))
    def options(self):
        return {'recordTypes':RECORD_TYPES,'statuses':STATUSES,'conclusions':CONCLUSIONS,
            'artifactTypes':[{'key':k,'label':v} for k,v in [('text','文字结论'),('flow','流程 / 步骤图'),('image','截图 / 图片'),('link','链接 / 代码'),('other','其他')]]}
    def records(self,u,filters):
        exact={k:filters[k] for k in ['recordType','status','projectId','requirementId'] if filters.get(k)}
        rows=self.repo.find(u,'poc_workbench_records',exact,order=[('updatedAt',True),('createdAt',True)],limit=500)
        keyword=filters.get('keyword') or ''
        rows=[self.payload(u,r) for r in rows if not keyword or keyword[:80] in ' '.join(str(r.get(k) or '') for k in ['title','objective','result','reuseGuidance'])]
        for raw in self.repo.legacy(u):
            row=self.legacy_payload(u,raw)
            if all(row.get(k)==v for k,v in exact.items()) and (not keyword or keyword.lower() in ' '.join(str(row.get(k) or '') for k in ['title','objective','result','demandTitle']).lower()):rows.append(row)
        return sorted(rows,key=lambda r:str(r.get('updatedAt') or r.get('createdAt') or ''),reverse=True)[:500]
    def linked(self,u,row):
        if row['projectId']:
            p=self.portfolio.project(u,row['projectId']);require(p,'关联项目不存在');row['projectName']=p.get('name') or row['projectName']
        if row['requirementId']:
            r=self.work.requirement(u,row['requirementId']);require(r,'关联需求不存在')
            row['requirementTitle']=r.get('title') or row['requirementTitle']
            for k in ['projectId','projectName','demandId']:row[k]=row[k] or r.get(k) or ''
        if row['demandId']:
            d=self.demand.get(u,row['demandId'],active=True);require(d,'关联需求池记录不存在');row['demandTitle']=d.get('title') or row['demandTitle']
            for k in ['projectId','projectName','requirementId','requirementTitle']:row[k]=row[k] or d.get(k) or ''
        return row
    def save(self,u,p,data,identifier=''):
        old=self.repo.get(u,'poc_workbench_records',identifier) if identifier else None
        if identifier and not old:
            legacy=self.get(u,identifier);require(not legacy,'历史需求池 POC 仅支持查看，请在此基础上新建独立记录')
            require(False,'POC / AI 能力记录不存在',404,'NOT_FOUND')
        row=self.linked(u,values(data,old or {},p,self.clock.now(),identifier or self.ids.new('poc',12)))
        record={**row,'metrics':json.dumps(row['metrics'],ensure_ascii=False),'tags':json.dumps(row['tags'],ensure_ascii=False)}
        if old:self.repo.change(u,'poc_workbench_records',identifier,{k:v for k,v in record.items() if k not in {'id','createdAt','createdByUserId','createdByName'}})
        else:self.repo.add(u,'poc_workbench_records',record)
        self.audit.record(u,p,'POC_WORKBENCH',row['id'],row['title'],'update' if old else 'create','更新 POC / AI 能力记录' if old else '创建'+next(x['label'] for x in RECORD_TYPES if x['key']==row['recordType']),before=old,after=record)
        return self.get(u,row['id'])
    def derive(self,u,p,identifier,data):
        source=self.get(u,identifier);require(source,'来源 POC 记录不存在',404,'NOT_FOUND');require(source['recordType']=='poc','只有 POC 验证记录可以沉淀为 AI 能力')
        row=values({**source,'recordType':'ai_capability','title':str(data.get('title') or source['title']+' · 可复用 AI 能力').strip()[:200],
            'status':'draft','conclusion':'','ownerUserId':p.userId,'ownerName':(p.devOwnerName or p.name),'sourceType':'derived_from_poc','sourceRef':identifier,'derivedFromId':identifier,
            'reuseGuidance':str(data.get('reuseGuidance') or source.get('reuseGuidance') or '请补充适用场景、使用边界和复用注意事项').strip()[:10000]}, {},p,self.clock.now(),self.ids.new('aic',11))
        row=self.linked(u,row);record={**row,'metrics':json.dumps(row['metrics'],ensure_ascii=False),'tags':json.dumps(row['tags'],ensure_ascii=False)}
        self.repo.add(u,'poc_workbench_records',record)
        self.audit.record(u,p,'POC_WORKBENCH',row['id'],row['title'],'derive_capability','从 POC 沉淀 AI 能力',after={'sourceId':identifier,'recordId':row['id']})
        return self.get(u,row['id'])
