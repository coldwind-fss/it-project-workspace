import json,hashlib
from itpm.core.errors import require,AppError
from .rules import _work_sync_normalize_item,_work_sync_normalize_name,_work_sync_source,_work_sync_payload_hash,_work_sync_preview_item,_work_sync_result

class WorkSync:
    def __init__(self,repo,clock,ids,portfolio,work):self.repo,self.clock,self.ids,self.portfolio,self.work=repo,clock,ids,portfolio,work
    def project(self,u,data):
        identifier=str(data.get('projectId') or (data.get('project') or {}).get('id') or '').strip()
        if identifier:
            row=self.portfolio.project(u,identifier);require(row,'项目不存在或已在回收站',404,'NOT_FOUND');return row
        name=str(data.get('projectName') or (data.get('project') or {}).get('name') or '').strip();require(name,'projectId 或 projectName 必填，不能自动新建项目')
        rows=self.portfolio.projects(u);exact=[r for r in rows if _work_sync_normalize_name(r.get('name'))==_work_sync_normalize_name(name)]
        if len(exact)==1:return exact[0]
        candidates=[{k:r.get(k) or '' for k in ['id','name','department']} for r in rows if _work_sync_normalize_name(name) in _work_sync_normalize_name(r.get('name'))]
        if not exact and not candidates:raise AppError('没有找到完全匹配的目标项目',404,'NOT_FOUND',safe_details={'projectName':name})
        raise AppError('目标项目不唯一，请明确选择 projectId',409,safe_details={'projectName':name,'candidates':candidates})
    def normalize(self,p,data,project):
        mode=str(data.get('mode') or 'preview').strip().lower();require(mode in {'preview','commit'},'mode 只能是 preview 或 commit')
        records=data.get('records');require(isinstance(records,list) and records,'records 必须是非空数组');require(len(records)<=100,'单批最多同步100条工作记录')
        source=_work_sync_source(data);actor={**p.dto(),'isService':p.role=='work_sync_service'}
        mapped=[_work_sync_normalize_item(r,i,project,source,actor,generated_at=self.clock.now()) for i,r in enumerate(records)]
        key=str(data.get('idempotencyKey') or '').strip();require(mode!='commit' or key,'commit 必须提供 idempotencyKey')
        if not key:key='preview-'+hashlib.sha256(json.dumps(mapped,ensure_ascii=False,sort_keys=True,default=str).encode()).hexdigest()[:24]
        return mode,source,mapped,key
    def preview(self,u,project,items):
        rows=self.work.requirements(u,project_id=project['id'])
        return [_work_sync_preview_item(i,item,project,next((r for r in rows if _work_sync_normalize_name(r.get('title'))==_work_sync_normalize_name(item['title'])),None)) for i,item in enumerate(items)]
    def result(self,project,bid,key,source,items,status):return _work_sync_result(project,bid,key,source,items,status)
    def batch(self,u,bid,lock=False):return self.repo.get(u,'work_sync_batches',bid,lock=lock)
    def items(self,u,bid):return self.repo.find(u,'work_sync_items',{'batchId':bid},order=[('itemIndex',False)])
    def replay(self,u,p,key,data,project):
        u.lock_key('work-sync',key);rows=self.repo.find(u,'work_sync_batches',{'idempotencyKey':key},lock=True)
        if not rows:return None
        row=rows[0];require(row['payloadHash']==_work_sync_payload_hash(data,project),'idempotencyKey 已用于不同内容，必须更换幂等键',409,'CONFLICT')
        require(p.role!='work_sync_service' or row['operatorUserId']==p.userId,'工作同步服务只能读取自己创建的批次',403,'FORBIDDEN')
        return {**json.loads(row.get('result') or '{}'),'status':'idempotent_replay'}
    def begin(self,u,p,key,data,project,source):
        bid=self.ids.new('ws',12);now=self.clock.now()
        self.repo.add(u,'work_sync_batches',dict(id=bid,idempotencyKey=key,sourceType=source['type'],sourceRef=source['ref'],sourceRangeStart=source['rangeStart'],sourceRangeEnd=source['rangeEnd'],projectId=project['id'],projectName=project.get('name') or '',operatorUserId=p.userId,operatorName=p.devOwnerName or p.name,payloadHash=_work_sync_payload_hash(data,project),status='processing',result='{}',createdAt=now,completedAt='',rolledBackAt=''))
        return bid
    def add_item(self,u,bid,index,action,item,rid):
        guarded={**item,'_rollbackGuard':self.repo.evidence(u,rid,bid)} if rid else item
        self.repo.add(u,'work_sync_items',dict(id=self.ids.new('wsi'),batchId=bid,itemIndex=index,action=action,recordKind=item['kind'],requirementId=rid,title=item['title'],payload=json.dumps(guarded,ensure_ascii=False),createdAt=self.clock.now()))
    def finish(self,u,bid,result,rollback=False):self.repo.change(u,'work_sync_batches',bid,{'status':'rolled_back' if rollback else 'committed','result':json.dumps(result,ensure_ascii=False),'rolledBackAt' if rollback else 'completedAt':self.clock.now()})
    def detail(self,u,bid):
        row=self.batch(u,bid);require(row,'同步批次不存在',404,'NOT_FOUND')
        return {**json.loads(row.get('result') or '{}'),**{k:row[k] for k in ['status','createdAt','completedAt','rolledBackAt']},'batchId':bid,'items':[{k:r[k] for k in ['id','itemIndex','action','recordKind','requirementId','title','createdAt']} for r in self.items(u,bid)]}
    def manual_after(self,u,bid,rids):
        items=self.items(u,bid)
        for item in items:
            rid=item.get('requirementId')
            if not rid:continue
            baseline=json.loads(item.get('payload') or '{}').get('_rollbackGuard')
            if baseline is None:
                if self.repo.manual_after(u,bid,[rid]):return True
            elif any(set(values)-set(baseline.get(key,[])) for key,values in self.repo.evidence(u,rid,bid).items()):return True
        return False
