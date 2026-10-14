import base64,re
from fastapi import Request
from itpm.infrastructure.router import ContractRouter
from fastapi.responses import JSONResponse,Response
from itpm.core.errors import require
from itpm.core.json_fields import list_field
from .schemas import RequirementWrite,BulkClassification,WorkLogWrite,PhaseWrite,SprintWrite,ReleaseWrite
from itpm.core.schemas import BulkIds

NO_CACHE={'Cache-Control':'no-store, no-cache, must-revalidate, max-age=0','Pragma':'no-cache','Expires':'0'}

def router(http,flow,work,inbox,v):
    r=ContractRouter()
    @r.get('/api/project-lifecycle/options')
    def lifecycle_options(request:Request):return http.call(request,lambda u,p:{'solutionTypes':v['PROJECT_SOLUTION_TYPES'],'itemKinds':v['L3_ITEM_KINDS'],'phaseStatuses':v['PHASE_STATUS_OPTIONS'],
        'templates':{x['key']:work.templates(u,x['key']) for x in v['PROJECT_SOLUTION_TYPES'] if x['key']!='unknown'}},read=True)
    @r.get('/api/requirements/live')
    @r.get('/api/requirements')
    def requirements(request:Request,type:str='',priority:str='',status:str='',projectId:str='',categoryId:str=''):
        result=http.call(request,lambda u,p:flow.list_requirements(u,{'type':type,'priority':priority,'status':status,'projectId':projectId,'categoryId':categoryId}),read=True)
        return JSONResponse(result,headers=NO_CACHE)
    @r.post('/api/requirements')
    def create_requirement(data:RequirementWrite,request:Request):return http.call(request,lambda u,p:flow.create_requirement(u,p,data.model_dump(exclude_unset=True)))
    @r.post('/api/requirements/bulk-delete')
    def bulk_delete_requirements(data:BulkIds,request:Request):return http.call(request,lambda u,p:flow.bulk_requirements(u,p,data.ids or []))
    @r.post('/api/requirements/bulk-classification')
    def bulk_classification(data:BulkClassification,request:Request):return http.call(request,lambda u,p:flow.bulk_classification(u,p,data.model_dump(exclude_unset=True)))
    @r.get('/api/requirements/{rid}/attachments/{image_index}')
    def attachment(rid:str,image_index:int,request:Request):
        def execute(u,p):
            row=work.requirement(u,rid);require(row,'需求不存在',404,'NOT_FOUND');images=list_field(row.get('images'));require(0<=image_index<len(images),'附件不存在',404,'NOT_FOUND')
            image=images[image_index];source=image.get('data','') if isinstance(image,dict) else str(image or '')
            match=re.match(r'^data:([^;,]+)?;base64,(.*)$',source,re.DOTALL);require(match,'附件格式不支持')
            try:content=base64.b64decode(match.group(2),validate=True)
            except (ValueError,TypeError):require(False,'附件内容无效')
            return Response(content,media_type=match.group(1) or (image.get('type') if isinstance(image,dict) else '') or 'application/octet-stream',headers={'Cache-Control':'no-store'})
        return http.call(request,execute,read=True)
    @r.get('/api/requirements/{rid}')
    def requirement(rid:str,request:Request):return JSONResponse(http.call(request,lambda u,p:flow.requirement(u,rid),read=True),headers=NO_CACHE)
    @r.put('/api/requirements/{rid}')
    def update_requirement(rid:str,data:RequirementWrite,request:Request):return http.call(request,lambda u,p:flow.update_requirement(u,p,rid,data.model_dump(exclude_unset=True)))
    @r.delete('/api/requirements/{rid}')
    def delete_requirement(rid:str,request:Request):return http.call(request,lambda u,p:flow.delete_requirement(u,p,rid))
    @r.get('/api/requirements/{rid}/work-logs')
    def logs(rid:str,request:Request):
        def execute(u,p):
            req=work.requirement(u,rid);require(req,'需求不存在',404,'NOT_FOUND');project=flow.portfolio.project(u,req.get('projectId') or '')
            rows=work.logs(u,rid)
            return rows if flow.identity.can_edit(u,p,req,'requirement',project) else [x for x in rows if x.get('visibility')!='it_private']
        return JSONResponse(http.call(request,execute,read=True),headers=NO_CACHE)
    @r.post('/api/requirements/{rid}/work-logs')
    def create_log(rid:str,data:WorkLogWrite,request:Request):return http.call(request,lambda u,p:flow.log(u,p,rid,data.model_dump(exclude_unset=True)))
    @r.get('/api/requirements/{rid}/phases')
    def phases(rid:str,request:Request):
        def execute(u,p):require(work.requirement(u,rid),'需求不存在',404,'NOT_FOUND');return work.phases(u,rid)
        return JSONResponse(http.call(request,execute,read=True),headers=NO_CACHE)
    @r.post('/api/requirements/{rid}/phases')
    def create_phase(rid:str,data:PhaseWrite,request:Request):return http.call(request,lambda u,p:flow.phase(u,p,rid,data.model_dump(exclude_unset=True)))
    @r.put('/api/requirements/{rid}/phases/{phase_id}')
    def update_phase(rid:str,phase_id:str,data:PhaseWrite,request:Request):return http.call(request,lambda u,p:flow.phase(u,p,rid,data.model_dump(exclude_unset=True),phase_id))
    @r.get('/api/requirements/{rid}/changelogs')
    def changelog(rid:str,request:Request):return http.call(request,lambda u,p:work.changelogs(u,rid=rid),read=True)
    @r.get('/api/changelogs')
    def changelogs(request:Request,projectId:str=''):return http.call(request,lambda u,p:work.changelogs(u,project=projectId),read=True)
    @r.get('/api/sprints')
    def sprints(request:Request):return http.call(request,lambda u,p:work.sprints(u),read=True)
    @r.get('/api/sprints/{sid}')
    def sprint(sid:str,request:Request):
        def execute(u,p):row=work.sprint(u,sid);require(row,'迭代不存在',404,'NOT_FOUND');return row
        return http.call(request,execute,read=True)
    # Order intentionally preserves V1's historical current-route shadowing.
    @r.get('/api/sprints/current')
    def current(request:Request):
        def execute(u,p):
            sp=next((x for x in work.sprints(u) if x['status']=='进行中'),None);require(sp,'无进行中迭代',404,'NOT_FOUND')
            reqs=[x for x in work.requirements(u,include_deleted=True) if x['sprintId']==sp['id']]
            return {'sprint':sp,'requirements':reqs,'bugCount':sum(x['type'] in {'问题修复','Bug修复'} for x in reqs)}
        return http.call(request,execute,read=True)
    @r.post('/api/sprints')
    def create_sprint(data:SprintWrite,request:Request):return http.call(request,lambda u,p:work.create_sprint(u,data.model_dump(exclude_unset=True)),read=True)
    @r.put('/api/sprints/{sid}')
    def update_sprint(sid:str,data:SprintWrite,request:Request):return http.call(request,lambda u,p:work.update_sprint(u,sid,data.model_dump(exclude_unset=True)),read=True)
    @r.delete('/api/sprints/{sid}')
    def delete_sprint(sid:str,request:Request):return http.call(request,lambda u,p:work.delete_sprint(u,sid),read=True)
    @r.get('/api/releases')
    def releases(request:Request,projectId:str=''):return http.call(request,lambda u,p:work.releases(u,projectId),read=True)
    @r.post('/api/releases')
    def create_release(data:ReleaseWrite,request:Request):return http.call(request,lambda u,p:work.create_release(u,data.model_dump(exclude_unset=True)),read=True)
    @r.get('/api/releases/{rid}')
    def release(rid:str,request:Request):
        def execute(u,p):row=work.release(u,rid);require(row,'发布版本不存在',404,'NOT_FOUND');return row
        return http.call(request,execute,read=True)
    return r
