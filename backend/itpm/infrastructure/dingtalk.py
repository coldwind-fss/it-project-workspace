"""Independent HTTP provider. Construction, config and cached contacts perform no network IO."""
import base64,copy,hashlib,hmac,json,threading,time
from urllib.parse import quote,urlsplit
import httpx

class DingTalkGateway:
    def __init__(self,settings,vocabulary,transport=None,now=time.time):
        if not settings.dingtalk_app_key or not settings.dingtalk_app_secret:raise ValueError('钉钉应用凭证未配置')
        self.settings,self.v,self.now=settings,vocabulary,now
        self.client=httpx.Client(timeout=httpx.Timeout(15,connect=5),transport=transport,follow_redirects=False)
        self.lock=threading.RLock();self.token='';self.token_expires=0;self.contacts_expires=0;self.unions={}
        self.cached_contacts=self.fallback()
    def close(self):self.client.close()
    def config(self):return {'configured':True,'corpId':self.settings.dingtalk_corp_id,'agentId':self.settings.dingtalk_agent_id}
    def request(self,method,url,body=None,params=None,headers=None):
        try:r=self.client.request(method,url,json=body,params=params,headers=headers)
        except httpx.HTTPError:raise RuntimeError('钉钉接口连接失败或超时') from None
        if not 200<=r.status_code<300:raise RuntimeError('钉钉接口失败（HTTP '+str(r.status_code)+'）')
        try:data=r.json()
        except ValueError:raise RuntimeError('钉钉接口返回格式错误') from None
        if not isinstance(data,dict):raise RuntimeError('钉钉接口返回格式错误')
        if data.get('errcode') not in (0,None) or data.get('code') and str(data['code']).lower() not in {'ok','0','success'}:
            raise RuntimeError('钉钉接口拒绝请求，请检查应用权限及配置')
        return data
    def access_token(self):
        with self.lock:
            if self.token and self.token_expires>self.now()+60:return self.token
            data=self.request('GET','https://oapi.dingtalk.com/gettoken',params={'appkey':self.settings.dingtalk_app_key,'appsecret':self.settings.dingtalk_app_secret})
            if not data.get('access_token'):raise RuntimeError('钉钉未返回访问令牌')
            self.token=data['access_token'];self.token_expires=self.now()+int(data.get('expires') or 7200);return self.token
    def old_api(self,path,body):return self.request('POST','https://oapi.dingtalk.com/'+path,body,params={'access_token':self.access_token()})
    def dev_name(self,user):
        text=' '.join(str(user.get(k,'')) for k in ['name','nickname','title','job_number'])
        for dev in self.v['DEVELOPERS']:
            if any(alias and alias in text for alias in [dev['name'],dev.get('shortName'),dev.get('nick'),*dev.get('aliases',[])]):return user.get('name') or user.get('nickname') or dev['name']
        return ''
    def exchange(self,code):
        try:
            uid=(self.old_api('topapi/v2/user/getuserinfo',{'code':code}).get('result') or {}).get('userid')
            if not uid:raise RuntimeError('钉钉未返回用户身份')
            user=self.old_api('topapi/v2/user/get',{'userid':uid,'language':'zh_CN'}).get('result') or {}
            return {**user,'userid':uid,'devOwnerName':self.dev_name(user)}
        except RuntimeError as e:raise ValueError(str(e)) from None
    def union_id(self,userid):
        if not userid:return ''
        if userid not in self.unions:
            user=self.old_api('topapi/v2/user/get',{'userid':userid,'language':'zh_CN'}).get('result') or {}
            if not user.get('unionid'):raise RuntimeError('钉钉未返回用户 unionId')
            self.unions[userid]=user['unionid']
        return self.unions[userid]
    def fallback(self):
        departments=['人事行政部','财务部','电商部','法务部','产品部','客服部','供应链中心','营销中心','集团人才法','集团中台']
        owners=['桑葚-於思旭','玖杉-周荣','安妮-宗艳琪']
        return {'configured':True,'source':'fallback','departments':departments,'departmentTree':[{'id':'fallback-'+str(i),'name':n,'children':[]} for i,n in enumerate(departments)],
            'developers':copy.deepcopy(self.v['DEVELOPERS']),'businessOwners':owners,'users':[{'name':d['name'],'role':d.get('role','developer'),'devOwnerName':d['name'],'source':'fallback'} for d in self.v['DEVELOPERS']]+[{'name':n,'role':'business','devOwnerName':'','source':'fallback'} for n in owners]}
    def contacts(self):return copy.deepcopy(self.cached_contacts)
    def role_hint(self,user):
        text=' '.join(str(user.get(k,'')) for k in ['name','nickname','title','job_number'])
        return 'admin' if any(name and name in text for name in self.v['ADMINS']) else 'developer' if self.dev_name(user) else 'viewer'
    def refresh_contacts(self):
        with self.lock:
            if self.contacts_expires>self.now():return
            users=[];visited=set()
            def read_department(identifier):
                if identifier in visited or len(visited)>=200 or len(users)>=500:return []
                visited.add(identifier);cursor=0;seen_cursors=set()
                while len(users)<500:
                    result=self.old_api('topapi/user/listsimple',{'dept_id':identifier,'cursor':cursor,'size':min(100,500-len(users)),'language':'zh_CN'}).get('result') or {}
                    for user in result.get('list',[]):
                        name=user.get('name') or user.get('nickname')
                        if name:users.append({'userid':user.get('userid',''),'name':name,'devOwnerName':self.dev_name(user),'departmentId':str(identifier),'source':'dingtalk','role':self.role_hint(user)})
                    if not result.get('has_more'):break
                    next_cursor=result.get('next_cursor') or 0
                    if next_cursor==cursor or next_cursor in seen_cursors:raise RuntimeError('钉钉通讯录分页无法推进')
                    seen_cursors.add(cursor);cursor=next_cursor
                nodes=[]
                for department in self.old_api('topapi/v2/department/listsub',{'dept_id':identifier,'language':'zh_CN'}).get('result') or []:
                    name=department.get('name') or department.get('dept_name') or '';child=department.get('dept_id') or department.get('id')
                    if not child:continue
                    children=read_department(child)
                    if '有限公司' in name or name.endswith('公司'):nodes.extend(children)
                    elif name:nodes.append({'id':str(child),'name':name,'children':children})
                return nodes
            try:
                tree=read_department(1);dedup={}
                for user in users:dedup.setdefault(user.get('userid') or user['name'],user)
                users=list(dedup.values());fallback=self.fallback()
                def flatten(nodes):return [name for n in nodes for name in [n['name'],*flatten(n['children'])]]
                devs=[{'name':u['devOwnerName'],'shortName':u['name'],'nick':u['name'],'role':'developer','userId':u['userid']} for u in users if u['devOwnerName']]
                self.cached_contacts={**fallback,'source':'dingtalk','users':users or fallback['users'],'developers':devs or fallback['developers'],
                    'businessOwners':list(dict.fromkeys(u['name'] for u in users)) or fallback['businessOwners'],'departmentTree':tree or fallback['departmentTree'],'departments':list(dict.fromkeys(flatten(tree))) or fallback['departments']}
                self.contacts_expires=self.now()+600
            except RuntimeError:
                self.cached_contacts={**self.fallback(),'error':'通讯录暂不可用，请检查钉钉应用权限或网络'}
                self.contacts_expires=self.now()+30
    def send_markdown_to_users(self,recipients,title,markdown):
        ids=list(dict.fromkeys(str(x).strip() for x in recipients if str(x).strip()))
        if not ids:raise RuntimeError('没有可用的钉钉 UserId')
        results=[]
        for start in range(0,len(ids),20):
            data=self.request('POST','https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend',{'robotCode':self.settings.dingtalk_robot_code or self.settings.dingtalk_app_key,'userIds':ids[start:start+20],'msgKey':'sampleMarkdown','msgParam':json.dumps({'title':title,'text':markdown},ensure_ascii=False,separators=(',',':'))},headers={'x-acs-dingtalk-access-token':self.access_token()})
            if any(data.get(k) for k in ['invalidStaffIdList','invalidUserIds','flowControlledStaffIdList','flowControlledUserIds']):raise RuntimeError('钉钉接收人无效或触发流控')
            results.append(data)
        return {'sentCount':len(ids),'batches':results}
    def send_group_markdown(self,webhook,secret,title,markdown):
        parsed=urlsplit(webhook)
        if parsed.scheme!='https' or parsed.hostname!='oapi.dingtalk.com' or parsed.path!='/robot/send':raise RuntimeError('未配置有效的钉钉机器人 webhook')
        params=None
        if secret:
            timestamp=str(round(self.now()*1000));signature=base64.b64encode(hmac.new(secret.encode(),(timestamp+'\n'+secret).encode(),hashlib.sha256).digest()).decode()
            # Keep the webhook token/query intact; httpx encodes the signature once.
            from urllib.parse import parse_qsl
            params=[*parse_qsl(parsed.query,keep_blank_values=True),('timestamp',timestamp),('sign',signature)]
        return self.request('POST',webhook,{'msgtype':'markdown','markdown':{'title':title,'text':markdown}},params=params)
    def complete_todo(self,recipient_union,task_id,operator_union):
        if not recipient_union or not task_id:return {}
        path='https://api.dingtalk.com/v1.0/todo/users/'+quote(recipient_union,safe='')+'/tasks/'+quote(task_id,safe='')+'/executorStatus'
        return self.request('PUT',path,{},params={'operatorId':operator_union or recipient_union},headers={'x-acs-dingtalk-access-token':self.access_token()})
