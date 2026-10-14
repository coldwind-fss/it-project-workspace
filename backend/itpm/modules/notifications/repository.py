from sqlalchemy import text
from itpm.infrastructure.database import Repository

class NotificationRepository(Repository):
    def __init__(self,db):super().__init__(db,['notification_targets','notification_delivery_logs','dingtalk_card_deliveries','dingtalk_card_interactions'])
    def read(self,u,sql,params=None):return [self.db.row(x) for x in u.connection.execute(text(sql),params or {}).mappings()]
    def progress(self,u,start,end,developer=''):
        scope=" AND (l.operatorName LIKE :dev OR r.assignee LIKE :dev OR r.assignee LIKE :short OR p.devOwner LIKE :dev OR p.devOwner LIKE :short)" if developer else ''
        params={'start':start[:10],'end':end[:10],'dev':'%'+developer+'%','short':'%'+(developer.split('-',1)[1] if '-' in developer else developer)+'%'}
        sql="SELECT l.id AS \"workLogId\",l.requirementId,l.logType,l.content,l.operatorUserId,l.operatorName,l.createdAt,l.occurredAt,l.workDate,l.visibility,l.sourceType,l.sourceRef,r.title AS \"linkedRequirementTitle\",r.type,r.status AS \"currentStatus\",r.priority,r.assignee,r.requester,r.changeObject,r.impactLevel,r.workloadLevel,p.name AS \"projectName\",p.id AS \"projectId\",p.devOwner,c.name AS cname,l.operatorName AS operator,l.createdAt AS \"activityCreatedAt\" FROM requirement_work_logs l LEFT JOIN requirements r ON r.id=l.requirementId LEFT JOIN projects p ON p.id=r.projectId LEFT JOIN categories c ON c.id=p.categoryId WHERE coalesce(nullif(l.workDate,''),substr(coalesce(nullif(l.occurredAt,''),l.createdAt),1,10))>=:start AND coalesce(nullif(l.workDate,''),substr(coalesce(nullif(l.occurredAt,''),l.createdAt),1,10))<:end AND coalesce(r.deletedAt,'')='' AND coalesce(r.reportingEligible,0)=1 AND coalesce(l.reportingEligible,0)=1 AND coalesce(l.sourceType,'') NOT IN ('system_event','status_change')"
        return self.read(u,sql+scope+' ORDER BY l.createdAt ASC LIMIT 2000',params)
    def active(self,u,developer=''):
        scope=' AND (r.assignee LIKE :dev OR r.assignee LIKE :short OR p.devOwner LIKE :dev OR p.devOwner LIKE :short)' if developer else ''
        return self.read(u,"SELECT r.*,p.name AS \"projectName\",p.name AS pname,p.devOwner,p.department AS \"projectDepartment\" FROM requirements r LEFT JOIN projects p ON r.projectId=p.id WHERE coalesce(r.deletedAt,'')='' AND coalesce(r.reportingEligible,0)=1"+scope+' ORDER BY r.updatedAt DESC,r.createdAt DESC LIMIT 1000',{'dev':'%'+developer+'%','short':'%'+(developer.split('-',1)[1] if '-' in developer else developer)+'%'})
    def first_started(self,u,rid):
        rows=self.read(u,"SELECT createdAt FROM changelogs WHERE requirementId=:rid AND fieldName='status' AND newValue IN ('进行中','开发中','联调中','测试中','待交付') ORDER BY createdAt ASC LIMIT 1",{'rid':rid})
        return rows[0].get('createdAt') if rows else ''
    def latest(self,u,rid):
        rows=self.read(u,"SELECT * FROM requirement_work_logs WHERE requirementId=:rid AND coalesce(reportingEligible,0)=1 AND coalesce(sourceType,'') NOT IN ('system_event','status_change') ORDER BY coalesce(nullif(workDate,''),nullif(occurredAt,''),createdAt) DESC,createdAt DESC LIMIT 1",{'rid':rid})
        return {k:rows[0].get(k) or '' for k in ['content','operatorName']}|{'workDate':str(rows[0].get('workDate') or rows[0].get('occurredAt') or rows[0].get('createdAt') or '')} if rows else None
