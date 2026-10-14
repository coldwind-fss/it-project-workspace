from sqlalchemy import select, func
from itpm.infrastructure.database import Repository
from itpm.core.errors import require
from itpm.core.events import AfterCommitAction

FIELDS = 'id ownerType ownerId originalName mimeType fileExtension sizeBytes sha256 createdByUserId createdByName createdAt'.split()


class Attachments:
    def __init__(self, db, clock, ids, storage, base, extensions):
        self.repo = Repository(db, ['business_attachments'])
        self.clock, self.ids, self.storage, self.base, self.extensions = clock, ids, storage, base, extensions

    def payload(self, row):
        return {**{k: row[k] for k in FIELDS}, 'isImage': row['mimeType'].startswith('image/'),
            'isVideo': row['mimeType'].startswith('video/'),
            'url': self.base.rstrip('/') + '/api/business-attachments/' + row['id'] + '/download'}

    def list(self, u, owner, identifier):
        t = self.repo.table('business_attachments')
        rows = self.repo.rows(u, select(*[t.c[k.lower()] for k in FIELDS]).where(
            t.c.ownertype == owner, t.c.ownerid == identifier, func.coalesce(t.c.deletedat, '') == '').order_by(t.c.createdat.desc()))
        return [self.payload(row) for row in rows]

    def get(self, u, identifier):
        return self.repo.get(u, 'business_attachments', identifier, True)

    def save(self, u, p, owner, identifier, name, mime, content,attachment_id=''):
        values = self.storage.put(owner, name, mime, content, self.extensions)
        u.on_rollback.append(lambda: self.storage.remove(values['storageKey']))
        row = {**values, 'id': attachment_id or self.ids.new('bat'), 'ownerType': owner, 'ownerId': identifier,
            'createdByUserId': p.userId, 'createdByName': p.name, 'createdAt': self.clock.now(), 'deletedAt': ''}
        self.repo.add(u, 'business_attachments', row)
        return self.payload(row)
    def get_any(self,u,identifier):return self.repo.get(u,'business_attachments',identifier)
    def move_owner(self,u,owner,identifier,new_owner,new_id):
        for file in self.list(u,owner,identifier):self.repo.change(u,'business_attachments',file['id'],{'ownerType':new_owner,'ownerId':new_id})
    def meta(self,row):
        return {**{k:row.get(k) for k in ['id','originalName','mimeType','sizeBytes','fileExtension','createdAt']},
            'isImage':str(row.get('mimeType') or '').startswith('image/'),'isVideo':str(row.get('mimeType') or '').startswith('video/'),
            'url':self.base.rstrip('/')+'/api/business-attachments/'+row['id']+'/download'}

    def delete(self, u, row):
        self.repo.change(u, 'business_attachments', row['id'], {'deletedAt': self.clock.now()})
        u.events.append(AfterCommitAction(lambda: self.storage.remove(row['storageKey'])))
        return {'ok': 1}

    def download(self, row):
        path = self.storage.path(row['storageKey'])
        require(path and path.is_file(), '附件文件不存在', 404, 'NOT_FOUND')
        return path
