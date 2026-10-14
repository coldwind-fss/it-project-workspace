import json
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert
from itpm.infrastructure.database import Repository


class IdentityRepository(Repository):
    def __init__(self, db):
        super().__init__(db, ['app_users','app_sessions','system_settings'])

    def setting(self, uow, key, fallback=None):
        row = self.get(uow,'system_settings',key)
        try: return json.loads(row['value']) if row else fallback
        except (ValueError,TypeError): return fallback

    def set_setting(self,uow,key,value,now):
        t=self.table('system_settings')
        values={'key':key,'value':json.dumps(value,ensure_ascii=False),'updatedat':now}
        uow.connection.execute(insert(t).values(**values).on_conflict_do_update(index_elements=['key'],set_=values))

    def user_for_session(self,uow,token,now):
        s=self.table('app_sessions');u=self.table('app_users')
        return self.one(uow,select(u).select_from(s.join(u,u.c.dinguserid==s.c.userid)).where(s.c.token==token,s.c.expiresat>now))

    def users(self,uow):
        t=self.table('app_users');return self.rows(uow,select(t).order_by(t.c.lastloginat.desc()))

    def save_user(self,uow,values):
        t=self.table('app_users');values=self.values('app_users',values)
        uow.connection.execute(insert(t).values(**values).on_conflict_do_update(index_elements=['dinguserid'],set_={k:v for k,v in values.items() if k!='id'}))
        return self.one(uow,select(t).where(t.c.dinguserid==values['dinguserid']))

    def session(self,uow,uid,token,now,expires):
        t=self.table('app_sessions')
        uow.connection.execute(delete(t).where(t.c.expiresat<=now))
        self.add(uow,'app_sessions',{'token':token,'userId':uid,'expiresAt':expires,'createdAt':now})
