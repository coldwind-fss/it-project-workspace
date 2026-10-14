from contextlib import asynccontextmanager
from pathlib import Path
from dataclasses import dataclass
import json,uuid
from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse,FileResponse,HTMLResponse
from itpm.settings import Settings
from itpm.core.errors import AppError
from itpm.core.ports import SystemClock,Ids,NotificationGateway
from itpm.core.events import Dispatcher
from itpm.infrastructure.database import Database,UnitOfWork
from itpm.infrastructure.http import Http
from itpm.infrastructure.gateway import gateway_for
from itpm.modules.identity.repository import IdentityRepository
from itpm.modules.identity.service import Identity
from itpm.modules.identity.router import router as identity_router
from itpm.modules.portfolio.repository import PortfolioRepository
from itpm.modules.portfolio.service import Portfolio
from itpm.modules.portfolio.router import router as portfolio_router
from itpm.modules.work.repository import WorkRepository
from itpm.modules.work.service import Work
from itpm.modules.work.router import router as work_router
from itpm.modules.audit.repository import AuditRepository
from itpm.modules.audit.service import Audit
from itpm.modules.audit.router import router as audit_router
from itpm.modules.inbox.public import Inbox
from itpm.modules.inbox.router import router as inbox_router
from itpm.modules.delivery.public import DeliveryFacts
from itpm.modules.demand.public import DemandFacts
from itpm.modules.value.public import Value
from itpm.modules.postlaunch.public import Postlaunch
from itpm.modules.collaboration.public import Collaboration
from itpm.modules.notifications.public import Notices
from itpm.workflows.project_work import ProjectWork
from itpm.modules.collaboration.repository import CollaborationRepository
from itpm.modules.collaboration.service import CollaborationService
from itpm.modules.collaboration.router import router as collaboration_router
from itpm.modules.attachments.public import Attachments
from itpm.modules.attachments.router import router as attachments_router
from itpm.infrastructure.files import FileStorage
from itpm.workflows.collaboration import CollaborationWorkflow
from itpm.workflows.attachment_access import AttachmentAccess
from itpm.modules.delivery.repository import DeliveryRepository
from itpm.modules.delivery.service import Delivery
from itpm.modules.demand.repository import DemandRepository
from itpm.modules.demand.service import Demand
from itpm.modules.demand.router import router as demand_router
from itpm.modules.collection.public import Collection
from itpm.modules.collection.router import router as collection_router
from itpm.workflows.demand import DemandWorkflow
from itpm.workflows.demand_notices import DemandNotices
from itpm.workflows.collection_send import CollectionSend
from itpm.modules.postlaunch.service import PostlaunchService
from itpm.modules.postlaunch.router import router as postlaunch_router
from itpm.modules.value.router import router as value_router
from itpm.modules.delivery.router import router as delivery_router
from itpm.workflows.value import ValueWorkflow
from itpm.workflows.delivery import DeliveryWorkflow
from itpm.modules.poc.repository import PocRepository
from itpm.modules.poc.service import Poc
from itpm.modules.poc.router import router as poc_router
from itpm.modules.insights.repository import InsightsRepository
from itpm.modules.insights.service import Insights
from itpm.modules.insights.router import router as insights_router
from itpm.modules.notifications.repository import NotificationRepository
from itpm.modules.notifications.service import Notifications
from itpm.modules.notifications.router import router as notifications_router
from itpm.workflows.notification_send import NotificationSend
from itpm.modules.work_sync.repository import SyncRepository
from itpm.modules.work_sync.service import WorkSync
from itpm.modules.work_sync.router import router as work_sync_router
from itpm.workflows.work_sync import SyncWorkflow
from itpm.workflows.scheduled_notifications import ScheduledNotifications
from itpm.workflows.recycle import Recycle
from itpm.infrastructure.recycle_router import router as recycle_router
from itpm.infrastructure.session_router import router as session_router


def create_app(settings:Settings|None=None,clock=None,ids=None,gateway:NotificationGateway|None=None,dispatcher=None):
    settings=settings or Settings.from_env();clock=clock or SystemClock();ids=ids or Ids();dispatcher=dispatcher or Dispatcher()
    db=Database(settings);v=json.loads((Path(__file__).resolve().parents[2]/'contracts/business-vocabulary.json').read_text('utf-8'))
    gateway=gateway or gateway_for(settings,v)
    identity=Identity(IdentityRepository(db),clock,ids,v,gateway);portfolio=Portfolio(PortfolioRepository(db),clock,ids,v)
    work=Work(WorkRepository(db),clock,ids,v,settings.public_base);audit=Audit(AuditRepository(db),clock,ids)
    inbox=Inbox(db,clock,ids,identity);delivery=Delivery(DeliveryRepository(db),clock,ids,v);demands=DemandFacts(db)
    value=Value(db,clock,ids,demands);postlaunch=Postlaunch(db,clock,ids);collaboration=Collaboration(db,clock,ids)
    flow=ProjectWork(identity,portfolio,work,audit,inbox,delivery,postlaunch,value,collaboration,clock,ids,v,
        Notices(gateway,settings.public_url),lambda:UnitOfWork(db,dispatcher))
    http=Http(db,dispatcher,identity,settings)
    files=Attachments(db,clock,ids,FileStorage(settings.attachment_dir),settings.public_base,v['BUSINESS_ATTACHMENT_EXTENSIONS'])
    shared=CollaborationService(CollaborationRepository(db),clock,ids,v,identity,work,portfolio,files,settings.public_url.rstrip('/')+'/')
    collaboration_flow=CollaborationWorkflow(shared,flow,files)
    file_access=AttachmentAccess(identity,collaboration_flow)
    demand=Demand(DemandRepository(db),clock,ids,v,identity,work,portfolio,files,value,audit,settings.public_url.rstrip('/')+'/')
    collection=Collection(db,clock,ids,identity,demand,files,audit,settings.public_url.rstrip('/')+'/')
    demand_flow=DemandWorkflow(demand,flow,delivery,value)
    demand_notices=DemandNotices(demand,gateway,lambda:UnitOfWork(db,dispatcher),settings.public_url)
    collection_sender=CollectionSend(collection,gateway,lambda:UnitOfWork(db,dispatcher),settings.public_url)
    postlaunch=PostlaunchService(db,clock,ids,v,identity,work,portfolio,demand,value,delivery,audit,settings.public_url.rstrip('/')+'/')
    flow.postlaunch=postlaunch
    value_flow=ValueWorkflow(value,flow,demand,postlaunch,gateway)
    delivery_flow=DeliveryWorkflow(delivery,flow,shared,demand,files)
    delivery_flow.operation_payload=postlaunch.payload
    from itpm.workflows.stage2_files import configure_files
    configure_files(file_access,identity,collaboration_flow,demand,collection,value,value_flow,delivery)
    poc=Poc(PocRepository(db),clock,ids,identity,portfolio,work,demand,files,audit)
    insights=Insights(InsightsRepository(db),clock,ids,identity,postlaunch,settings.performance_user_id)
    notification_rules=Notifications(NotificationRepository(db),clock,ids,identity,portfolio,work,insights,settings.public_url)
    notification_sender=NotificationSend(notification_rules,gateway,lambda:UnitOfWork(db,dispatcher),audit)
    dispatcher.subscribers.append(notification_sender.event)
    work_sync=WorkSync(SyncRepository(db),clock,ids,portfolio,work);sync_flow=SyncWorkflow(work_sync,flow)
    scheduler=ScheduledNotifications(notification_rules,notification_sender,collection,collection_sender,value,value_flow,postlaunch,work,lambda:UnitOfWork(db,dispatcher),clock)
    recycle=Recycle(flow,demand)
    file_access.owner_policies['poc_workbench']=lambda u,p,identifier,write=False: bool(poc.get(u,identifier) and identity.has(u,p,'demand_pool.manage'))
    @asynccontextmanager
    async def lifespan(app):
        db.check()
        try:yield
        finally:db.close();gateway.close()
    app=FastAPI(title='IT Project Workspace',docs_url='/api/docs',openapi_url='/api/openapi.json',lifespan=lifespan)
    app.state.database=db;app.state.gateway=gateway;app.state.dispatcher=dispatcher;app.state.flow=flow
    app.state.collaboration=shared;app.state.collaboration_flow=collaboration_flow;app.state.files=files;app.state.file_access=file_access
    app.state.demand=demand;app.state.collection=collection;app.state.demand_flow=demand_flow;app.state.delivery=delivery
    app.state.postlaunch=postlaunch;app.state.value_flow=value_flow;app.state.delivery_flow=delivery_flow
    app.state.poc=poc
    app.state.insights=insights
    app.state.notification_rules=notification_rules;app.state.notification_sender=notification_sender
    app.state.work_sync=work_sync;app.state.sync_flow=sync_flow
    app.state.scheduler=scheduler
    app.state.recycle=recycle
    @app.middleware('http')
    async def boundary(request:Request,call_next):
        prefix=settings.public_base.rstrip('/')
        if request.scope['path']==prefix or request.scope['path'].startswith(prefix+'/'):
            mapped=request.scope['path'][len(prefix):] or '/';request.scope['path']=mapped;request.scope['raw_path']=mapped.encode()
            request.scope['root_path']=prefix
        request.state.request_id=uuid.uuid4().hex
        try:response=await call_next(request)
        except Exception:response=JSONResponse({'error':'系统处理失败，请稍后重试'},500)
        response.headers['X-Request-Id']=request.state.request_id
        return response
    @app.exception_handler(AppError)
    async def error(request,exc):return JSONResponse({exc.field:exc.message,**exc.safe_details},exc.status)
    @app.get('/api/health')
    def health():return {'status':'ok'}
    @app.get('/api/ready')
    def ready(request:Request):
        if db.check():return {'status':'ready'}
        return JSONResponse({'status':'not_ready','code':db.ready_code,'requestId':request.state.request_id},503)
    app.include_router(identity_router(http,identity,audit,v));app.include_router(portfolio_router(http,flow,portfolio))
    app.include_router(work_router(http,flow,work,inbox,v));app.include_router(audit_router(http,audit))
    app.include_router(inbox_router(http,inbox,collaboration_flow))
    app.include_router(collaboration_router(http,collaboration_flow,shared,v))
    app.include_router(attachments_router(http,files,file_access))
    app.include_router(collection_router(http,collection,collection_sender))
    app.include_router(demand_router(http,demand,demand_flow,demand_notices,collection))
    app.include_router(delivery_router(http,delivery_flow))
    app.include_router(value_router(http,value,value_flow,demand))
    app.include_router(postlaunch_router(http,postlaunch))
    app.include_router(poc_router(http,poc))
    app.include_router(insights_router(http,insights))
    app.include_router(notifications_router(http,notification_rules,notification_sender))
    app.include_router(work_sync_router(http,work_sync,sync_flow,v))
    app.include_router(recycle_router(http,recycle))
    app.include_router(session_router(http,identity,insights))
    original_openapi=app.openapi
    def contract_openapi():
        schema=original_openapi();schema.setdefault('components',{})['securitySchemes']={'Session':{'type':'apiKey','in':'header','name':'X-PM-Session'}}
        public={('GET','/api/health'),('GET','/api/ready'),('GET','/api/dingtalk/config'),('GET','/api/dingtalk/link-icon'),('POST','/api/dingtalk/login'),('POST','/api/app-logs')}
        if settings.profile=='preview':public.add(('POST','/api/preview/session'))
        for path,operations in schema['paths'].items():
            for method,op in operations.items():
                if path.startswith('/api/') and (method.upper(),path) not in public:op['security']=[{'Session':[]}]
        scoped={'type':'apiKey','in':'header','name':'X-PM-Collaboration-Token'}
        schema['components']['securitySchemes']['CollaborationToken']=scoped
        schema['components']['securitySchemes']['WorkSyncToken']={'type':'apiKey','in':'header','name':'X-PM-Work-Sync-Token'}
        public_forms={'/api/demand-pool/entry-context','/api/demand-pool-confirmations/by-token','/api/demand-pool-reviews/by-token',
            '/api/demand-collections/responses','/api/demand-pool-outcome-context','/api/demand-pool-outcome-submit','/api/business-requests/webhook'}
        for path,operations in schema['paths'].items():
            for method,op in operations.items():
                if path in public_forms:
                    op['security']=[];op['x-authorization']='Server verifies the scoped form token or signed webhook; this is not anonymous resource access.'
                if path.startswith('/api/collaboration-link/'):
                    op['security']=[{'CollaborationToken':[]}]
                if path.startswith('/api/work-intake'):
                    op['security']=[] if path.endswith('/schema') else [{'Session':[]},{'WorkSyncToken':[]}]
                if path in {'/api/demand-pool','/api/demand-pool/materials','/api/business-attachments'} and method=='post':
                    op['security']=[{'Session':[]},{}];op['x-scoped-token-field']='recipientToken' if path!='/api/business-attachments' else 'entryToken'
        return schema
    app.openapi=contract_openapi
    if settings.profile=='preview':
        from itpm.infrastructure.preview_entry import render_entry
        @app.get('/preview-login',include_in_schema=False)
        def public_entry():return HTMLResponse(render_entry(settings.public_base),headers={'Cache-Control':'no-store'})
    if settings.preview_login:
        @app.get('/preview-login',include_in_schema=False)
        def preview_login(actor:str='super'):
            fixture_path=Path(__file__).resolve().parents[2]/'.runtime/fixture.json'
            if not fixture_path.exists():return JSONResponse({'error':'请先执行显式隔离 fixture 命令'},503)
            fixture=json.loads(fixture_path.read_text('utf-8'))
            if actor!='super':
                # Only explicit synthetic fixture identities in this local-only route.
                import copy
                names={'admin':('隔离项目管理员','admin',True),'editor':('隔离开发者','editor',True),'viewer':('隔离业务','viewer',False),'other':('隔离无关编辑','editor',True)}
                if actor not in names:return JSONResponse({'error':'未知合成演示身份'},400)
                name,role,developer=names[actor];fixture=copy.deepcopy(fixture)
                fixture.update(id='u-stage-'+actor,dingUserId='stage-'+actor,name=name,role=role,isDeveloper=developer,sessionToken='fixture-stage-'+actor)
            serialized=json.dumps(json.dumps(fixture,ensure_ascii=False)).replace('<','\\u003c')
            return HTMLResponse('<script>localStorage.setItem("pm-current-user",'+serialized+');location.replace('+json.dumps(settings.public_base+'#/requirements')+');</script>')
    @app.get('/')
    @app.get('/{full_path:path}')
    def spa(full_path:str=''):
        if full_path=='api' or full_path.startswith('api/'):
            return JSONResponse({'detail':'Not Found'},404)
        root=Path(settings.static_dir).resolve();candidate=(root/full_path).resolve()
        if not candidate.is_relative_to(root):return JSONResponse({'detail':'Not Found'},404)
        if candidate.is_file():return FileResponse(candidate)
        if '.' in Path(full_path).name or full_path.startswith('assets/') or not (root/'index.html').is_file():return JSONResponse({'detail':'Not Found'},404)
        return FileResponse(root/'index.html')
    return app
