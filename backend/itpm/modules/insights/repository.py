from sqlalchemy import text
from itpm.infrastructure.database import Repository

class InsightsRepository(Repository):
    """Read-only projections of declared source fields; only monthly records writable."""
    def __init__(self,db):super().__init__(db,['performance_months'])
    def query(self,u,sql,params=None):return self.rows(u,text(sql),) if params is None else [self.db.row(x) for x in u.connection.execute(text(sql),params).mappings()]
    def dashboard(self,u,kind):
        if kind=='bycategory':return self.query(u,'SELECT r.*,p.name AS pname,p.categoryId,c.name AS cname FROM requirements r LEFT JOIN projects p ON r.projectId=p.id LEFT JOIN categories c ON p.categoryId=c.id ORDER BY r.createdAt DESC LIMIT 50')
        if kind=='activities':return self.query(u,'SELECT cl.*,r.type,r.status,r.priority,r.assignee,r.requester,r.department AS "reqDepartment",p.name AS "projectName",p.id AS "projectId",p.department AS "projectDepartment",p.status AS "projectStatus",c.name AS cname,c.id AS "categoryId" FROM changelogs cl LEFT JOIN requirements r ON r.id=cl.requirementId LEFT JOIN projects p ON p.id=r.projectId LEFT JOIN categories c ON c.id=p.categoryId ORDER BY cl.createdAt DESC LIMIT 80')
        if kind=='summary':return self.query(u,"SELECT c.id,c.name,c.color,c.owner,COUNT(r.id) AS \"reqCount\",SUM(CASE WHEN r.status IN ('已交付','已上线','已关闭','已归档') THEN 1 ELSE 0 END) AS \"doneCount\",COUNT(DISTINCT p.id) AS \"projectCount\" FROM categories c LEFT JOIN projects p ON p.categoryId=c.id AND p.status NOT IN ('已归档','已关闭','archived') LEFT JOIN requirements r ON r.projectId=p.id GROUP BY c.id ORDER BY c.sortOrder ASC")
    def stats(self,u,month):
        values={}
        queries={'activeProjects':"SELECT count(*) AS c FROM projects WHERE status NOT IN ('已归档','已关闭','archived')",
            'pendingBugs':"SELECT count(*) AS c FROM requirements WHERE type IN ('问题修复','Bug修复') AND status NOT IN ('已交付','已上线','已关闭','已归档')",
            'monthlyReleases':'SELECT count(*) AS c FROM releases','monthlyNewRequirements':'SELECT count(*) AS c FROM requirements WHERE createdAt LIKE :month'}
        for key,sql in queries.items():values[key]=self.query(u,sql,{'month':month+'%'})[0]['c']
        return values
    def report_sources(self,u,start,end,developer=''):
        params={'start':start,'end':end,'developer':'%'+developer+'%','short':'%'+(developer.split('-',1)[1] if '-' in developer else developer)+'%'}
        scope=" AND (r.assignee LIKE :developer OR r.assignee LIKE :short OR p.devOwner LIKE :developer OR p.devOwner LIKE :short)" if developer else ''
        project_scope=" AND (p.devOwner LIKE :developer OR p.devOwner LIKE :short)" if developer else ''
        projects=self.query(u,'SELECT p.*,c.name AS "categoryName" FROM projects p LEFT JOIN categories c ON c.id=p.categoryId WHERE p.createdAt>=:start AND p.createdAt<:end'+project_scope+' ORDER BY p.createdAt ASC LIMIT 100',params)
        reqs=self.query(u,"SELECT r.*,p.name AS \"projectName\",p.id AS \"projectId\",c.name AS \"categoryName\" FROM requirements r LEFT JOIN projects p ON p.id=r.projectId LEFT JOIN categories c ON c.id=p.categoryId WHERE r.createdAt>=:start AND r.createdAt<:end AND coalesce(r.deletedAt,'')='' AND coalesce(r.reportingEligible,0)=1"+scope+' ORDER BY p.name,r.createdAt ASC LIMIT 300',params)
        changes=self.query(u,"SELECT cl.*,r.title,r.createdAt AS \"requirementCreatedAt\",r.assignee,r.type,r.changeObject,r.impactLevel,r.workloadLevel,p.name AS \"projectName\",p.id AS \"projectId\",c.name AS \"categoryName\" FROM changelogs cl LEFT JOIN requirements r ON r.id=cl.requirementId LEFT JOIN projects p ON p.id=r.projectId LEFT JOIN categories c ON c.id=p.categoryId WHERE cl.createdAt>=:start AND cl.createdAt<:end AND cl.fieldName='status' AND coalesce(r.deletedAt,'')='' AND coalesce(r.reportingEligible,0)=1"+scope+' ORDER BY cl.createdAt DESC LIMIT 500',params)
        project_changes=self.query(u,"SELECT entityId,entityName,beforeValue,afterValue,createdAt FROM operation_records WHERE entityType='L2' AND action='update' AND createdAt>=:start AND createdAt<:end ORDER BY createdAt DESC LIMIT 200",params)
        return projects,reqs,changes,project_changes
    def performance_sources(self,u,p,month,end_month):
        params={'uid':p.userId,'name':p.devOwnerName or p.name,'month':month,'end_month':end_month}
        ops=self.query(u,"SELECT o.*,r.title,r.assignee,r.createdByUserId AS \"requirementCreatedByUserId\",r.createdByName AS \"requirementCreatedByName\",r.expectedDeliveryTime AS \"requirementExpectedDeliveryTime\",p.name AS \"projectName\",p.devOwner,p.solutionType AS \"projectSolutionType\" FROM postlaunch_operations o LEFT JOIN requirements r ON r.id=o.requirementId LEFT JOIN projects p ON p.id=o.projectId WHERE (o.createdByUserId=:uid OR o.createdByName=:name OR r.assignee=:name OR p.devOwner=:name) AND substr(coalesce(o.deliveryDate,o.createdAt),1,7)>=:month AND substr(coalesce(o.deliveryDate,o.createdAt),1,7)<:end_month ORDER BY o.createdAt DESC",params)
        reqs=self.query(u,"SELECT * FROM requirements WHERE coalesce(deletedAt,'')='' AND (createdByUserId=:uid OR createdByName=:name OR assignee=:name) AND substr(coalesce(updatedAt,createdAt),1,7)>=:month AND substr(coalesce(updatedAt,createdAt),1,7)<:end_month ORDER BY updatedAt DESC,createdAt DESC",params)
        result={'ops':ops,'requirements':reqs}
        for key,table in [('issues','postlaunch_issues'),('proposals','improvement_proposals'),('knowledge','postlaunch_knowledge')]:
            result[key]=self.query(u,'SELECT * FROM '+table+' WHERE (createdByUserId=:uid OR ownerUserId=:uid OR createdByName=:name OR ownerName=:name) AND substr(createdAt,1,7)>=:month AND substr(createdAt,1,7)<:end_month ORDER BY createdAt DESC',params)
        result['pocs']=self.query(u,'SELECT p.*,d.title FROM demand_pool_pocs p LEFT JOIN demand_pool_items d ON d.id=p.demandId WHERE (p.createdByUserId=:uid OR p.ownerUserId=:uid OR p.createdByName=:name OR p.ownerName=:name) AND substr(p.createdAt,1,7)>=:month AND substr(p.createdAt,1,7)<:end_month ORDER BY p.createdAt DESC',params)
        result['work_logs']=self.query(u,'SELECT l.*,r.title FROM requirement_work_logs l LEFT JOIN requirements r ON r.id=l.requirementId WHERE (l.operatorUserId=:uid OR l.operatorName=:name) AND substr(coalesce(l.occurredAt,l.createdAt),1,7)>=:month AND substr(coalesce(l.occurredAt,l.createdAt),1,7)<:end_month ORDER BY l.createdAt DESC LIMIT 200',params)
        return result
