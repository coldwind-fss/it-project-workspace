from sqlalchemy import select, func, literal_column
from itpm.infrastructure.database import Repository


class CollaborationRepository(Repository):
    def __init__(self, db):
        super().__init__(db, ['business_intake_requests', 'business_collaboration_items',
            'business_collaboration_messages', 'shared_activities', 'shared_activity_comments'])

    def find(self, u, table, filters=None, active=False, order=None, limit=None):
        t = self.table(table)
        stmt = select(t)
        for key, value in (filters or {}).items():
            stmt = stmt.where(t.c[key.lower()] == value)
        if active and 'deletedat' in t.c:
            stmt = stmt.where(func.coalesce(t.c.deletedat, '') == '')
        for key, descending in (order or []):
            column=literal_column('ctid') if key=='rowid' else t.c[key.lower()]
            stmt = stmt.order_by(column.desc() if descending else column)
        if limit:
            stmt = stmt.limit(limit)
        return self.rows(u, stmt)
    def projection_scopes(self,u):
        t=self.table('business_collaboration_items');return self.rows(u,select(t.c.id,t.c.requirementid))
