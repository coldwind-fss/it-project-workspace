"""Read policy port for existing delivery facts. Writer implemented in WP05."""
from sqlalchemy import select,literal_column
from itpm.modules.identity.public import same_name
from .rules import KINDS,OUTCOMES,FEEDBACK_TYPES,FEEDBACK_ROUTES,DEFAULT_ROUTES

class DeliveryFacts:
    def __init__(self,db):self.db=db
    def pending_verification(self,u,rid):
        t=self.db.table('collaboration_link_requests')
        return bool(u.connection.execute(select(t.c.id).where(t.c.requirementid==rid,t.c.kind=='verification',t.c.status=='pending').limit(1)).first())
    def public_link(self,u,rid,uid,name,now,base,vocabulary):
        l=self.db.table('collaboration_link_requests').alias('l');c=self.db.table('business_collaboration_items').alias('c')
        rows=u.connection.execute(select(l,c.c.recipientname.label('thread_name'),c.c.recipientuserid.label('thread_uid')).select_from(l.join(c,c.c.id==l.c.collaborationid))
            .where(l.c.requirementid==rid,c.c.direction=='it_to_business',l.c.status!='revoked').order_by(literal_column('l.ctid').desc()).limit(20)).mappings()
        for row in rows:
            if row['expiresat'] and row['expiresat']<=now:continue
            if (uid and uid==row['thread_uid']) or same_name(name,row['thread_name'],vocabulary['DEVELOPERS']):return base.rstrip('/')+'/#/entry/collaboration?token='+row['token']
        return None
