import json
from datetime import datetime,timedelta
from itpm.core.ports import Principal
from itpm.core.errors import require, AppError
from .rules import BASE_ROLES, PAGE_KEYS, same_name, split_people, clean_access,normalize_person


class Identity:
    def __init__(self, repository, clock, ids, vocabulary, gateway):
        self.repo,self.clock,self.ids,self.v,self.gateway=repository,clock,ids,vocabulary,gateway

    def access(self,u):
        value=self.repo.setting(u,'access_control',None)
        if isinstance(value,dict):
            return {'users':value.get('users',[]),'customRoles':value.get('customRoles',[])}
        personnel=self.repo.setting(u,'personnel',{}) or {}
        devs=personnel.get('developers',self.v['DEVELOPERS']);admins=personnel.get('admins',[{'name':x} for x in ['路得','桑葚','薏米','Ben','十叶-冯硕硕','星河-李子文','惜君-吴旭骏']])
        people=[]
        for d in [*admins,*devs]:
            name=d.get('name','')
            if not name or any(x['name']==name for x in people):continue
            developer=any(same_name(name,x.get('name'),self.v['DEVELOPERS']) for x in devs)
            super_admin=any(same_name(name,x,self.v['DEVELOPERS']) for x in self.v['SUPER_ADMIN_NAMES'])
            people.append({'name':name,'userId':'','accessRole':'super_admin' if super_admin else 'editor','isDeveloper':developer,'enabled':True})
        for name in self.v['SUPER_ADMIN_NAMES']:
            if not any(same_name(name,x['name'],self.v['DEVELOPERS']) for x in people):
                people.append({'name':name,'userId':'','accessRole':'super_admin','isDeveloper':False,'enabled':True})
        return {'users':people,'customRoles':[]}

    def roles(self,u):
        roles={k:{'key':k,**v,'builtIn':True} for k,v in BASE_ROLES.items()}
        for r in self.access(u)['customRoles']:
            key=str(r.get('key') or '').strip()
            if key and key not in roles:roles[key]={'key':key,'label':r.get('label') or key,'description':r.get('description') or '自定义角色','pages':[p for p in r.get('pages',[]) if p in PAGE_KEYS],'actions':r.get('actions',[]),'builtIn':False}
        return roles

    def access_user(self,u,uid,name):
        users=[x for x in self.access(u)['users'] if x.get('enabled',True)]
        return next((x for x in users if uid and x.get('userId')==uid),None) or next((x for x in users if same_name(name,x.get('name'),self.v['DEVELOPERS'])),{})

    def resolve(self,u,token):
        row=self.repo.user_for_session(u,token,self.clock.now()) if token else None
        if not row:return Principal()
        cfg=self.access_user(u,row['dingUserId'],row['name']);role=cfg.get('accessRole','viewer')
        if role not in self.roles(u):role='viewer'
        return Principal(row['dingUserId'],row['name'],role,row.get('devOwnerName','') if cfg.get('isDeveloper') else '',bool(cfg.get('isDeveloper')),True)
    def session_access(self,u,p):
        self.authenticated(p);role=self.roles(u).get(p.role,{})
        return {**p.dto(),'permissions':role.get('pages',[]),'actions':role.get('actions',[])}

    def authenticated(self,p):require(p.authenticated,'请在钉钉内重新登录后操作',401,'AUTH_REQUIRED')

    def has(self,u,p,action):
        actions=self.roles(u).get(p.role,{}).get('actions',[])
        return '*' in actions or action in actions

    def action(self,u,p,action):
        self.authenticated(p);require(self.has(u,p,action),'当前角色没有此操作权限',403,'FORBIDDEN')

    def super_admin(self,p):require(p.authenticated and p.role=='super_admin','只有超级管理员可以管理人员和权限',403,'FORBIDDEN')

    def person_id(self,u,name):
        cfg=self.repo.setting(u,'personnel',{}) or {}
        for x in cfg.get('developers',self.v['DEVELOPERS']):
            if same_name(name,x.get('name'),self.v['DEVELOPERS']):return x.get('userId') or x.get('userid') or x.get('dingUserId') or ''
        contacts=self.gateway.contacts()
        for x in [*contacts.get('users',[]),*contacts.get('developers',[])]:
            if same_name(name,x.get('name'),self.v['DEVELOPERS']):return x.get('userId') or x.get('userid') or x.get('dingUserId') or ''
        return ''

    def matches(self,u,p,people):
        return any((p.userId and self.person_id(u,n)==p.userId) or same_name(p.name,n,self.v['DEVELOPERS']) for n in split_people(people))

    def created_by(self,p,row):
        return bool((p.userId and row.get('createdByUserId')==p.userId) or same_name(p.name,row.get('createdByName'),self.v['DEVELOPERS']))

    def can_edit(self,u,p,row,entity,project=None):
        if p.role in {'admin','super_admin'}:return True
        if not self.has(u,p,entity+'.update.own'):return False
        if self.created_by(p,row):return True
        fields=['businessOwner','devOwner'] if entity=='project' else ['assignee','requester']
        if any(self.matches(u,p,row.get(x)) for x in fields):return True
        return bool(project and any(self.matches(u,p,project.get(x)) for x in ['businessOwner','devOwner']))

    def delete_permission(self,u,p,row,entity):
        self.authenticated(p)
        if p.role in {'admin','super_admin'}:return
        require(self.has(u,p,entity+'.delete.own'),'当前角色没有删除权限',403,'FORBIDDEN')
        require(self.created_by(p,row),'只能删除自己创建的记录',403,'FORBIDDEN')

    def policy(self,u):
        cfg=self.repo.setting(u,'todo_policy',{}) or {}
        return {'skipSelfAssignedTodo':bool(cfg.get('skipSelfAssignedTodo',False)),'notifyRequesterOnOnline':bool(cfg.get('notifyRequesterOnOnline',True))}

    def options(self,u):
        opts=self.gateway.contacts(); personnel=self.repo.setting(u,'personnel',{}) or {}
        devs=personnel.get('developers',[{'name':x['name'],'shortName':x.get('shortName',''),'nick':x.get('nick',''),'userId':x.get('userId',''),'role':'developer','permissions':self.v['DEFAULT_DEVELOPER_PERMISSIONS']} for x in self.v['DEVELOPERS']])
        users={x['name']:x for x in opts.get('users',[]) if x.get('name')}
        for x in self.repo.users(u):users.setdefault(x['name'],x)
        default_admins=[{'name':name,'userId':'','role':'admin','permissions':PAGE_KEYS} for name in ['路得','桑葚','薏米','Ben','十叶-冯硕硕','星河-李子文','惜君-吴旭骏']]
        devs=[normalize_person(d,opts.get('developers',[]),self.v['DEVELOPERS'],'developer') for d in devs]
        devs=[{'name':d['name'],'shortName':d.get('shortName') or d['name'].split('-',1)[-1],'nick':d.get('nick') or d['name'].split('-',1)[0],
            'role':'developer','userId':d.get('userId') or d.get('userid') or d.get('dingUserId') or '','permissions':d.get('permissions') or self.v['DEFAULT_DEVELOPER_PERMISSIONS']} for d in devs if d.get('name')]
        admins=[normalize_person(a,[*users.values(),*opts.get('developers',[])],self.v['DEVELOPERS'],'admin') for a in personnel.get('admins',default_admins)]
        opts.update(users=list(users.values()),businessOwners=sorted(set(opts.get('businessOwners',[]))|set(users)),developers=devs,admins=admins)
        return opts

    def personnel(self,u,p):
        self.super_admin(p);cfg=self.access(u)
        contacts=self.gateway.contacts();pool=[*contacts.get('users',[]),*contacts.get('developers',[])]
        assignments=[]
        for item in cfg['users']:
            person=normalize_person(item,pool,self.v['DEVELOPERS']);person.update(accessRole=item.get('accessRole') if item.get('accessRole') in self.roles(u) else 'viewer',
                isDeveloper=bool(item.get('isDeveloper')),enabled=bool(item.get('enabled',True)));assignments.append(person)
        users={x['name']:x for x in self.gateway.contacts().get('users',[]) if x.get('name')}
        for x in self.repo.users(u):
            if x.get('name'):users[x['name']]={'userId':x.get('dingUserId'),'name':x.get('name'),'role':x.get('role'),'devOwnerName':x.get('devOwnerName'),'lastLoginAt':x.get('lastLoginAt')}
        return {'accessRoles':[{'key':k,'label':r.get('label',k),'description':r.get('description',''),'pages':r['pages'],'actions':r['actions'],'builtIn':r['builtIn']} for k,r in self.roles(u).items()],
            'assignments':assignments,'customRoles':cfg['customRoles'],'permissionGroups':self.v['PERMISSION_GROUPS'],'todoSettings':self.policy(u),'users':list(users.values()),'operator':p.dto()}

    def save_personnel(self,u,p,data):
        self.super_admin(p);old=self.access(u)
        data={'assignments':old['users'],'customRoles':old['customRoles'],**data}
        if not isinstance(data.get('assignments'),list):data['assignments']=old['users']
        if not isinstance(data.get('customRoles'),list):data['customRoles']=old['customRoles']
        clean=clean_access(data,self.options(u)['users'],self.v['DEVELOPERS']);now=self.clock.now()
        self.repo.set_setting(u,'access_control',clean,now)
        self.repo.set_setting(u,'personnel',{'developers':[{'name':x['name'],'userId':x['userId'],'role':'developer','permissions':self.v['DEFAULT_DEVELOPER_PERMISSIONS']} for x in clean['users'] if x['isDeveloper']],
            'admins':[{'name':x['name'],'userId':x['userId'],'role':'admin','permissions':PAGE_KEYS} for x in clean['users'] if x['accessRole'] in {'admin','super_admin'}]},now)
        if isinstance(data.get('todoSettings'),dict):
            self.repo.set_setting(u,'todo_policy',{'skipSelfAssignedTodo':bool(data['todoSettings'].get('skipSelfAssignedTodo',False)),'notifyRequesterOnOnline':bool(data['todoSettings'].get('notifyRequesterOnOnline',True))},now)
        return clean

    def exchange(self,code):
        require(code,'authCode required')
        try:return self.gateway.exchange(code)
        except ValueError as e:raise AppError(str(e))
    def preview_login(self,u,actor):
        # Only explicit synthetic identities; permissions still come from stored configuration.
        require(actor in {'super','admin','editor','viewer','other'},'无效的演示身份',422,'VALIDATION_ERROR')
        uid='stage-'+actor
        row=next((x for x in self.repo.users(u) if x['dingUserId']==uid),None)
        require(row is not None,'演示身份尚未配置，请稍后重试',503,'INTEGRATION_UNAVAILABLE')
        require(bool(self.access_user(u,uid,row['name'])),'演示身份未启用，请稍后重试',503,'INTEGRATION_UNAVAILABLE')
        return self.login(u,{'userid':uid,'name':row['name'],'dept_id_list':[row.get('department') or '隔离测试部']})
    def login(self,u,user):
        uid=user.get('userid') or user.get('unionid') or '';require(uid,'未识别到钉钉用户')
        name=user.get('name') or user.get('nickname') or uid;cfg=self.access_user(u,uid,name);role=cfg.get('accessRole','viewer')
        user.update(role=role,devOwnerName=name if cfg.get('isDeveloper') else '')
        row=self.repo.save_user(u,{'id':self.ids.new('u',8),'dingUserId':uid,'name':name,'mobile':user.get('mobile',''),'avatar':user.get('avatar',''),'title':user.get('title',''),'department':','.join(map(str,user.get('dept_id_list',[]))),'role':role,'devOwnerName':user['devOwnerName'],'raw':json.dumps(user,ensure_ascii=False),'lastLoginAt':self.clock.now()})
        row.update(role=role,isDeveloper=bool(cfg.get('isDeveloper')),permissions=self.roles(u).get(role,BASE_ROLES['viewer'])['pages'])
        token=self.ids.new('',32)+self.ids.new('',32);now=self.clock.now()
        self.repo.session(u,uid,token,now,(datetime.strptime(now,'%Y-%m-%d %H:%M:%S')+timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S'))
        row['sessionToken']=token
        return {'user':row,'developers':self.v['DEVELOPERS']}
