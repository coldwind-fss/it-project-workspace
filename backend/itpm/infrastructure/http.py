from itpm.core.errors import AppError
from itpm.infrastructure.database import UnitOfWork

class Http:
    def __init__(self,db,dispatcher,identity,settings):self.db,self.dispatcher,self.identity,self.settings=db,dispatcher,identity,settings
    def call(self,request,operation,read=False,action=None):
        if self.db.ready_code:
            raise AppError('隔离数据库尚未就绪',503,self.db.ready_code)
        with UnitOfWork(self.db,self.dispatcher) as u:
            u.correlation_id=getattr(request.state,'request_id','')
            p=self.identity.resolve(u,request.headers.get('X-PM-Session',''))
            if read and self.settings.read_auth:self.identity.authenticated(p)
            if action:self.identity.action(u,p,action)
            return operation(u,p)
