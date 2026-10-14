from fastapi import APIRouter,Request
from itpm.core.errors import require
from .schemas import PocWrite,PocView,DeriveWrite,PocOptions

def router(http,poc):
    r=APIRouter()
    def call(request,operation):return http.call(request,operation,action='demand_pool.manage')
    @r.get('/api/poc-workbench/options',response_model=PocOptions)
    def options(request:Request):return call(request,lambda u,p:poc.options())
    @r.get('/api/poc-workbench/records',response_model=list[PocView],response_model_exclude_unset=True)
    def records(request:Request,recordType:str='',status:str='',keyword:str='',projectId:str='',requirementId:str=''):
        return call(request,lambda u,p:poc.records(u,dict(recordType=recordType,status=status,keyword=keyword,projectId=projectId,requirementId=requirementId)))
    @r.get('/api/poc-workbench/records/{record_id}',response_model=PocView,response_model_exclude_unset=True)
    def detail(record_id:str,request:Request):
        def execute(u,p):
            item=poc.get(u,record_id);require(item,'POC / AI 能力记录不存在',404,'NOT_FOUND');return item
        return call(request,execute)
    @r.post('/api/poc-workbench/records',response_model=PocView,response_model_exclude_unset=True)
    def create(data:PocWrite,request:Request):return call(request,lambda u,p:poc.save(u,p,data.model_dump(exclude_unset=True)))
    @r.put('/api/poc-workbench/records/{record_id}',response_model=PocView,response_model_exclude_unset=True)
    def update(record_id:str,data:PocWrite,request:Request):return call(request,lambda u,p:poc.save(u,p,data.model_dump(exclude_unset=True),record_id))
    @r.post('/api/poc-workbench/records/{record_id}/derive-capability',response_model=PocView,response_model_exclude_unset=True)
    def derive(record_id:str,data:DeriveWrite,request:Request):return call(request,lambda u,p:poc.derive(u,p,record_id,data.model_dump(exclude_unset=True)))
    return r
