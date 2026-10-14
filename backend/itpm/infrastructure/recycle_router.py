from fastapi import APIRouter,Request
from pydantic import BaseModel
from itpm.core.responses import Ok

class RecycleRow(BaseModel):
    type:str
    entityType:str
    id:str
    name:str
    deletedAt:str
    deletedByName:str
    expiresAt:str

def router(http,recycle):
    r=APIRouter()
    @r.get('/api/recycle-bin',response_model=list[RecycleRow])
    def rows(request:Request):return http.call(request,lambda u,p:recycle.rows(u,p))
    @r.post('/api/recycle-bin/{item_type}/{entity_id}/restore',response_model=Ok)
    def restore(item_type:str,entity_id:str,request:Request):return http.call(request,lambda u,p:recycle.restore(u,p,item_type,entity_id))
    @r.delete('/api/recycle-bin/{item_type}/{entity_id}',response_model=Ok)
    def purge(item_type:str,entity_id:str,request:Request):return http.call(request,lambda u,p:recycle.purge(u,p,item_type,entity_id))
    return r
