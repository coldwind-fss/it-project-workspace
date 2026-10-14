class FakeGateway:
    """Only registered synthetic auth codes are recognised; no arbitrary impersonation."""
    def __init__(self,contacts=None):
        self.auth_codes = {}
        self.calls = []
        self.contact_fixture = contacts

    def exchange(self, code):
        if code not in self.auth_codes:
            raise ValueError('隔离环境不接受真实钉钉授权码')
        return dict(self.auth_codes[code])

    def config(self):return {'configured':False,'corpId':'','agentId':''}
    def refresh_contacts(self):pass
    def close(self):pass

    def contacts(self):
        return dict(self.contact_fixture) if self.contact_fixture else {'users': [], 'developers': [], 'businessOwners': [], 'departments': []}
    def send_markdown_to_users(self,recipients,title,markdown):
        self.calls.append({'name':'send_robot_markdown_to_users','args':[recipients,title,markdown],'kwargs':{}})
        return {'ok':True,'fake':True}
    def send_group_markdown(self,webhook,secret,title,markdown):
        self.calls.append({'name':'send_robot_markdown','args':[webhook,secret,title,markdown],'kwargs':{}})
        return {'ok':True,'fake':True}
    def complete_todo(self,recipient_union,task_id,operator_union):
        self.calls.append({'name':'complete_dingtalk_todo','args':[recipient_union,task_id,operator_union],'kwargs':{}})
        return {'ok':True,'fake':True}
    def union_id(self,userid):return 'fake-'+str(userid)

class DisabledGateway(FakeGateway):
    def send_markdown_to_users(self,*args,**kwargs):raise RuntimeError('integration disabled')
    def complete_todo(self,*args,**kwargs):raise RuntimeError('integration disabled')
    def send_group_markdown(self,*args,**kwargs):raise RuntimeError('integration disabled')

def gateway_for(settings,vocabulary,contacts=None,transport=None):
    if settings.integration_mode=='real':
        from .dingtalk import DingTalkGateway
        return DingTalkGateway(settings,vocabulary,transport=transport)
    return (FakeGateway if settings.integration_mode=='fake' else DisabledGateway)(contacts)
