import json,re

def redact(value):
    text=str(value or '')
    text=re.sub(r'(?i)(token|password|secret|authorization)(["\s:=]+)[^\s,"&}]+',r'\1\2[redacted]',text)
    return re.sub(r'(?i)(postgres(?:ql)?(?:\+psycopg2)?://)[^\s]+',r'\1[redacted]',text)

class Audit:
    def __init__(self,repo,clock,ids):self.repo,self.clock,self.ids=repo,clock,ids
    def purge_batch(self,u,bid):
        for row in self.repo.find(u,'operation_records',{'sourceBatchId':bid}):self.repo.remove(u,'operation_records',row['id'])

    def record(self,u,p,entity,identifier,name,action,summary,before=None,after=None,source_batch_id=''):
        self.repo.add(u,'operation_records',{'id':self.ids.new('op'),'entityType':entity,'entityId':identifier,'entityName':name,'action':action,
            'operator':p.name,'operatorRole':p.role,'summary':summary,'beforeValue':json.dumps(before or {},ensure_ascii=False),
            'afterValue':json.dumps(after or {},ensure_ascii=False),'createdAt':self.clock.now(),'sourceBatchId':source_batch_id})

    def log(self,u,data):
        identifier=self.ids.new('log')
        self.repo.add(u,'app_logs',{'id':identifier,'level':str(data.get('level') or 'error')[:32],'source':str(data.get('source') or '')[:64],
            'message':redact(data.get('message'))[:1000],'detail':redact(data.get('detail'))[:8000],'path':redact(data.get('path'))[:1000],
            'userAgent':str(data.get('userAgent') or '')[:1000],'userName':str(data.get('userName') or '')[:128],'createdAt':self.clock.now()})
        return identifier
