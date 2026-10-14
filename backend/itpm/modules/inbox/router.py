from fastapi import APIRouter,Request
from itpm.infrastructure.router import ContractRouter
def router(http,inbox,workflow=None):
    r=ContractRouter()
    @r.get('/api/todos')
    def todos(request:Request,status:str=''):return http.call(request,lambda u,p:inbox.visible(u,p,status),read=True)
    @r.get('/api/todos/unread-count')
    def unread(request:Request):return http.call(request,lambda u,p:{'count':inbox.unread(u,p)},read=True)
    @r.put('/api/todos/{tid}/read')
    def read(tid:str,request:Request):return http.call(request,lambda u,p:workflow.personal_action(u,p,tid),read=True)
    @r.put('/api/todos/{tid}/done')
    def done(tid:str,request:Request):return http.call(request,lambda u,p:workflow.personal_action(u,p,tid,True),read=True)
    return r
