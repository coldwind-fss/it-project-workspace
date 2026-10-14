from fastapi import Request
from itpm.infrastructure.router import ContractRouter
from fastapi.responses import Response
from .schemas import LoginWrite,PersonnelWrite
from typing import Literal
from itpm.core.responses import LoginResult

def router(http,identity,audit,v):
    r=ContractRouter()
    if http.settings.profile=='preview':
        @r.post('/api/preview/session',response_model=LoginResult,response_model_exclude_unset=True)
        def preview_session(request:Request,actor:Literal['super','admin','editor','viewer','other']='super'):
            result=http.call(request,lambda u,p:identity.preview_login(u,actor))
            return Response(LoginResult.model_validate(result).model_dump_json(exclude_unset=True),media_type='application/json',headers={'Cache-Control':'no-store'})
    @r.get('/api/dingtalk/config')
    def config():return identity.gateway.config()
    @r.get('/api/dingtalk/link-icon')
    def icon():
        from pathlib import Path
        svg=(Path(__file__).resolve().parents[4]/'contracts/link-icon.svg').read_text('utf-8')
        return Response(svg,media_type='image/svg+xml',headers={'Cache-Control':'public, max-age=86400'})
    @r.post('/api/dingtalk/login')
    def login(data:LoginWrite,request:Request):
        user=identity.exchange(data.authCode or data.code)
        return http.call(request,lambda u,p:identity.login(u,user))
    @r.get('/api/dingtalk/options')
    def options(request:Request):
        http.call(request,lambda u,p:None,read=True)
        identity.gateway.refresh_contacts()  # Authenticated; no business UoW held across HTTP.
        return http.call(request,lambda u,p:identity.options(u),read=True)
    @r.get('/api/system/personnel')
    def personnel(request:Request):
        http.call(request,lambda u,p:identity.super_admin(p))
        identity.gateway.refresh_contacts()
        return http.call(request,lambda u,p:identity.personnel(u,p))
    @r.put('/api/system/personnel')
    def save_personnel(data:PersonnelWrite,request:Request):
        def execute(u,p):
            result=identity.save_personnel(u,p,data.model_dump(exclude_unset=True));audit.record(u,p,'SYSTEM','access_control','人员与权限','update','更新人员角色与权限',after=result);return {'ok':1}
        return http.call(request,execute)
    return r
