from collections import defaultdict,deque
from time import monotonic
from fastapi import Request
from itpm.infrastructure.router import ContractRouter
from itpm.core.errors import require
from .schemas import LogWrite

def router(http,audit):
    r=ContractRouter();rates=defaultdict(deque)
    @r.post('/api/app-logs')
    def log(data:LogWrite,request:Request):
        key=request.client.host if request.client else 'local';q=rates[key];now=monotonic()
        while q and q[0]<now-60:q.popleft()
        require(len(q)<30,'日志上报过于频繁',429,'RATE_LIMITED');q.append(now)
        def execute(u,p):
            payload={'source':'frontend','path':str(request.url),'userAgent':request.headers.get('user-agent',''),'userName':p.name,**data.model_dump(exclude_unset=True)}
            audit.log(u,payload);return {'ok':1}
        return http.call(request,execute)
    @r.get('/api/app-logs')
    def logs(request:Request,level:str='',source:str='',limit:int=100):return http.call(request,lambda u,p:audit.repo.list_logs(u,level,source,limit),read=True)
    @r.get('/api/operations')
    def operations(request:Request,entityType:str='',action:str='',keyword:str='',limit:int=100):return http.call(request,lambda u,p:audit.repo.list_operations(u,entityType,action,keyword,limit),action='operation.view')
    return r
