from fastapi import APIRouter,Request
from pydantic import BaseModel

class SessionAccess(BaseModel):
    userId:str
    name:str
    role:str
    devOwnerName:str
    isDeveloper:bool
    authenticated:bool
    permissions:list[str]
    actions:list[str]
    performanceAllowed:bool

def router(http,identity,insights):
    r=APIRouter()
    @r.get('/api/session',response_model=SessionAccess)
    def session(request:Request):return http.call(request,lambda u,p:{**identity.session_access(u,p),'performanceAllowed':insights.performance_allowed(p)},read=True)
    return r
