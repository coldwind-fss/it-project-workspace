from sqlalchemy import select,func,text
from itpm.infrastructure.database import Repository

class SyncRepository(Repository):
    def __init__(self,db):super().__init__(db,['work_sync_batches','work_sync_items'])
    def manual_after(self,u,bid,rids):
        if not rids:return False
        params={'bid':bid,'rids':rids}
        checks=["SELECT count(*) FROM operation_records WHERE entityType='L3' AND entityId=ANY(:rids) AND coalesce(sourceBatchId,'')<>:bid",
            "SELECT count(*) FROM requirement_work_logs WHERE requirementId=ANY(:rids) AND coalesce(sourceBatchId,'')<>:bid",
            "SELECT count(*) FROM shared_activity_comments c JOIN shared_activities a ON a.id=c.activityId WHERE a.requirementId=ANY(:rids)",
            "SELECT count(*) FROM business_collaboration_messages m JOIN business_collaboration_items b ON b.id=m.collaborationId WHERE b.requirementId=ANY(:rids)",
            "SELECT count(*) FROM business_attachments f WHERE (f.ownerType='shared_activity' AND f.ownerId IN (SELECT id FROM shared_activities WHERE requirementId=ANY(:rids))) OR (f.ownerType='collaboration' AND f.ownerId IN (SELECT id FROM business_collaboration_items WHERE requirementId=ANY(:rids))) OR (f.ownerType='shared_activity_comment' AND f.ownerId IN (SELECT c.id FROM shared_activity_comments c JOIN shared_activities a ON a.id=c.activityId WHERE a.requirementId=ANY(:rids))) OR (f.ownerType='collaboration_message' AND f.ownerId IN (SELECT m.id FROM business_collaboration_messages m JOIN business_collaboration_items b ON b.id=m.collaborationId WHERE b.requirementId=ANY(:rids)))"]
        return any(u.connection.execute(text(sql),params).scalar() for sql in checks)
    def evidence(self,u,rid,bid):
        queries={
            'operations':"SELECT id FROM operation_records WHERE entityType='L3' AND entityId=:rid",
            'logs':'SELECT id FROM requirement_work_logs WHERE requirementId=:rid',
            'comments':'SELECT c.id FROM shared_activity_comments c JOIN shared_activities a ON a.id=c.activityId WHERE a.requirementId=:rid',
            'messages':'SELECT m.id FROM business_collaboration_messages m JOIN business_collaboration_items b ON b.id=m.collaborationId WHERE b.requirementId=:rid',
            'attachments':"SELECT f.id FROM business_attachments f WHERE (f.ownerType='shared_activity' AND f.ownerId IN (SELECT id FROM shared_activities WHERE requirementId=:rid)) OR (f.ownerType='collaboration' AND f.ownerId IN (SELECT id FROM business_collaboration_items WHERE requirementId=:rid)) OR (f.ownerType='shared_activity_comment' AND f.ownerId IN (SELECT c.id FROM shared_activity_comments c JOIN shared_activities a ON a.id=c.activityId WHERE a.requirementId=:rid)) OR (f.ownerType='collaboration_message' AND f.ownerId IN (SELECT m.id FROM business_collaboration_messages m JOIN business_collaboration_items b ON b.id=m.collaborationId WHERE b.requirementId=:rid))"}
        return {key:sorted(u.connection.execute(text(sql+(" AND coalesce(sourceBatchId,'')<>:bid" if key in {'operations','logs'} else '')),{'rid':rid,'bid':bid}).scalars().all()) for key,sql in queries.items()}
