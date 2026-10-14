import hmac
from fastapi import APIRouter,Request
from itpm.core.ports import Principal
from itpm.core.errors import require
from itpm.infrastructure.database import UnitOfWork
from .rules import WORK_SYNC_SERVICE_HEADER,WORK_SYNC_SERVICE_TOKEN_MIN_LENGTH,WORK_SYNC_SERVICE_USER_ID,WORK_SYNC_SERVICE_NAME,WORK_SYNC_KIND_TYPE_MAP
from .schemas import SyncWrite,OwnerCorrection,SyncResult,OwnerResult,IntakeSchema

def router(http,sync,workflow,v):
    r=APIRouter()
    def call(request,operation):
        expected=http.settings.work_sync_token.strip();presented=request.headers.get(WORK_SYNC_SERVICE_HEADER,'').strip()
        if len(expected)>=WORK_SYNC_SERVICE_TOKEN_MIN_LENGTH and len(presented)>=WORK_SYNC_SERVICE_TOKEN_MIN_LENGTH and hmac.compare_digest(expected,presented):
            require(not http.db.ready_code,'隔离数据库尚未就绪',503,'DATABASE_UNAVAILABLE')
            with UnitOfWork(http.db,http.dispatcher) as u:
                u.correlation_id=getattr(request.state,'request_id','');return operation(u,Principal(userId=WORK_SYNC_SERVICE_USER_ID,name=WORK_SYNC_SERVICE_NAME,role='work_sync_service',authenticated=True))
        return http.call(request,operation,read=True)
    @r.get('/api/work-intake/schema',response_model=IntakeSchema)
    def schema():
        return dict(adapter='pm-app-l2-l3',projectEntity='L2',workEntity='L3',activityEntity='requirement_work_logs',requiredWorkFields=['title','projectId'],serviceRequiredWorkFields=['developerOwner','businessOwner'],
            fields={'type':v['REQUIREMENT_TYPE_OPTIONS'],'status':v['REQUIREMENT_STATUS_OPTIONS'],'priority':['P0','P1','P2','P3','P4'],'changeObject':v['REQUIREMENT_CHANGE_OBJECT_OPTIONS'],'impactLevel':v['REQUIREMENT_IMPACT_OPTIONS'],'workloadLevel':v['REQUIREMENT_WORKLOAD_OPTIONS'],'logType':['工作进展','遇到问题','交付说明','下一步']},
            canonicalKinds=sorted(set(WORK_SYNC_KIND_TYPE_MAP)),canonicalPhases=['planned','in_progress','delivered','closed'],
            authentication={'preview':['X-PM-Session',WORK_SYNC_SERVICE_HEADER],'commit':['X-PM-Session',WORK_SYNC_SERVICE_HEADER],'serviceScope':'work-intake only; service rollback and owner correction are limited to batches/records created by this service'})
    @r.post('/api/work-intake',response_model=SyncResult,response_model_exclude_unset=True)
    def intake(data:SyncWrite,request:Request):return call(request,lambda u,p:workflow.intake(u,p,data.model_dump(exclude_unset=True)))
    @r.post('/api/work-intake/owner-correction',response_model=OwnerResult)
    def correct(data:OwnerCorrection,request:Request):return call(request,lambda u,p:workflow.correct(u,p,data.model_dump(exclude_unset=True)))
    @r.get('/api/work-intake/{batch_id}',response_model=SyncResult,response_model_exclude_unset=True)
    def detail(batch_id:str,request:Request):
        def execute(u,p):
            if p.role=='work_sync_service':
                batch=sync.batch(u,batch_id);require(batch,'同步批次不存在',404,'NOT_FOUND');require(batch['operatorUserId']==WORK_SYNC_SERVICE_USER_ID,'工作同步服务只能读取自己创建的批次',403,'FORBIDDEN')
            return sync.detail(u,batch_id)
        return call(request,execute)
    @r.post('/api/work-intake/{batch_id}/rollback',response_model=SyncResult,response_model_exclude_unset=True)
    def rollback(batch_id:str,request:Request):return call(request,lambda u,p:workflow.rollback(u,p,batch_id))
    return r
