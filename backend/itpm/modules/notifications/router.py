from fastapi import APIRouter,Request
from fastapi.responses import JSONResponse
from itpm.core.responses import Ok
from .schemas import NotificationWrite,NotificationView,DeliveryLog,NotificationSync,NotificationResult

def router(http,notifications,sender):
    r=APIRouter()
    @r.get('/api/notification/targets',response_model=list[NotificationView],response_model_exclude_unset=True)
    def targets(request:Request):return http.call(request,lambda u,p:notifications.targets(u,p),read=True)
    @r.get('/api/notification/deliveries',response_model=list[DeliveryLog])
    def deliveries(request:Request,limit:int=50):return http.call(request,lambda u,p:notifications.deliveries(u,limit),action='notification.manage')
    @r.post('/api/notification/targets',response_model=NotificationView,response_model_exclude_unset=True)
    def create(data:NotificationWrite,request:Request):return http.call(request,lambda u,p:notifications.save(u,p,data.model_dump(exclude_unset=True)),action='notification.manage')
    @r.put('/api/notification/targets/{tid}',response_model=NotificationView,response_model_exclude_unset=True)
    def update(tid:str,data:NotificationWrite,request:Request):return http.call(request,lambda u,p:notifications.save(u,p,data.model_dump(exclude_unset=True),tid),action='notification.manage')
    @r.delete('/api/notification/targets/{tid}',response_model=Ok)
    def delete(tid:str,request:Request):return http.call(request,lambda u,p:notifications.delete(u,tid),action='notification.manage')
    @r.post('/api/notification/preview',response_model=NotificationResult,response_model_exclude_unset=True)
    def preview(data:NotificationWrite,request:Request):return http.call(request,lambda u,p:notifications.preview(u,data.model_dump(exclude_unset=True)),action='notification.manage')
    @r.post('/api/notification/sync',response_model=NotificationResult,response_model_exclude_unset=True)
    def sync(data:NotificationSync,request:Request):
        result=http.call(request,lambda u,p:sender.manual(u,p,data.model_dump(exclude_unset=True)),action='notification.manage')
        return JSONResponse(result,400) if 'error' in result else result
    return r
