from fastapi import APIRouter,Request
from .schemas import (DashboardStats,CategorySummary,CategoryWork,DashboardActivityView,WorkReport,PerformanceResult,PerformanceWrite,PerformanceRecord)

def router(http,insights):
    r=APIRouter()
    @r.get('/api/dashboard/stats',response_model=DashboardStats)
    def stats(request:Request):return http.call(request,lambda u,p:insights.dashboard(u,'stats'),read=True)
    @r.get('/api/dashboard/bycategory',response_model=list[CategoryWork],response_model_exclude_unset=True)
    def category(request:Request):return http.call(request,lambda u,p:insights.dashboard(u,'bycategory'),read=True)
    @r.get('/api/dashboard/bycategory/summary',response_model=list[CategorySummary],response_model_exclude_unset=True)
    def summary(request:Request):return http.call(request,lambda u,p:insights.dashboard(u,'summary'),read=True)
    @r.get('/api/dashboard/activities',response_model=list[DashboardActivityView],response_model_exclude_unset=True)
    def activities(request:Request):return http.call(request,lambda u,p:insights.dashboard(u,'activities'),read=True)
    @r.get('/api/work-reports',response_model=WorkReport,response_model_exclude_unset=True)
    def reports(request:Request,period:str='week'):return http.call(request,lambda u,p:insights.report(u,period),read=True)
    @r.get('/api/performance/me',response_model=PerformanceResult,response_model_exclude_unset=True)
    def performance(request:Request,month:str=''):return http.call(request,lambda u,p:insights.performance(u,p,month),read=True)
    @r.put('/api/performance/me',response_model=PerformanceRecord,response_model_exclude_unset=True)
    def save(data:PerformanceWrite,request:Request):return http.call(request,lambda u,p:insights.save_performance(u,p,data.model_dump(exclude_unset=True)))
    return r
