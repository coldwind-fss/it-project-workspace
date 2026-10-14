from fastapi import Request
from itpm.infrastructure.router import ContractRouter
from .schemas import CategoryWrite,ProjectWrite,BulkIds

def router(http,flow,portfolio):
    r=ContractRouter()
    @r.get('/api/categories')
    def categories(request:Request):return http.call(request,lambda u,p:portfolio.categories(u),read=True)
    @r.get('/api/categories/{cid}')
    def category(cid:str,request:Request):return http.call(request,lambda u,p:flow.category(u,cid),read=True)
    @r.get('/api/categories/{cid}/projects')
    def category_projects(cid:str,request:Request):return http.call(request,lambda u,p:flow.list_projects(u,category=cid),read=True)
    @r.post('/api/categories')
    def create_category(data:CategoryWrite,request:Request):return http.call(request,lambda u,p:flow.create_category(u,p,data.model_dump(exclude_unset=True)))
    @r.put('/api/categories/{cid}')
    def update_category(cid:str,data:CategoryWrite,request:Request):return http.call(request,lambda u,p:flow.update_category(u,p,cid,data.model_dump(exclude_unset=True)))
    @r.delete('/api/categories/{cid}')
    def delete_category(cid:str,request:Request):return http.call(request,lambda u,p:flow.delete_category(u,p,cid))
    @r.get('/api/projects')
    def projects(request:Request):return http.call(request,lambda u,p:flow.list_projects(u),read=True)
    @r.post('/api/projects')
    def create_project(data:ProjectWrite,request:Request):return http.call(request,lambda u,p:flow.create_project(u,p,data.model_dump(exclude_unset=True)))
    @r.post('/api/projects/bulk-delete')
    def bulk_delete_projects(data:BulkIds,request:Request):return http.call(request,lambda u,p:flow.bulk_projects(u,p,data.ids or []))
    @r.get('/api/projects/{pid}')
    def project(pid:str,request:Request):return http.call(request,lambda u,p:flow.list_projects(u,identifier=pid),read=True)
    @r.put('/api/projects/{pid}')
    def update_project(pid:str,data:ProjectWrite,request:Request):return http.call(request,lambda u,p:flow.update_project(u,p,pid,data.model_dump(exclude_unset=True)))
    @r.delete('/api/projects/{pid}')
    def delete_project(pid:str,request:Request):return http.call(request,lambda u,p:flow.delete_project(u,p,pid))
    return r
