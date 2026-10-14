"""Public direct notices and rule ports; provider calls are outside transactions."""
from .service import Notifications
from .rules import (normalize_target,notification_recipient_ids,notification_record_matches,notification_schedule_due,notification_schedule_key)
class Notices:
    def __init__(self,gateway,public_url):self.gateway,self.base=gateway,public_url.rstrip('/')
    def todo(self,todo):
        if not todo.get('recipientUserId'):return False
        title=todo.get('requirementTitle') or '未命名需求'
        pending=self.base+'/#/workspace?focus=pending&todoId='+todo['id'];detail=self.base+'/#/requirements/'+todo['requirementId']
        text='\n'.join([f'## 请处理需求：{title}',f"> 来自：{todo.get('sourceName') or '系统'}",'',f'- 需求：**{title}**',
            f"- 项目：{todo.get('projectName') or '未归属项目'}",f"- 当前动作：{todo.get('message') or '请查看并处理该需求'}",'',f'[打开待办]({pending})  |  [查看需求详情]({detail})'])
        self.gateway.send_markdown_to_users([todo['recipientUserId']],f'请处理需求：{title}',text);return True
    def completion(self,notice):
        text='\n'.join(['## 需求已交付',f"- 需求：**{notice['title'] or '-'}**",f"- 项目：{notice['project'] or '-'}",f"- 完成人：{notice['actor']}",'',
            f"[查看业务页面]({notice['url']})" if notice['url'] else '如需查看交付内容，请联系 IT 发起业务链接。'])
        self.gateway.send_markdown_to_users([notice['userId']],'需求交付通知',text)
    def complete_native(self,todo):
        recipient=todo.get('dingTalkUnionId') or self.gateway.union_id(todo.get('recipientUserId') or '')
        operator=self.gateway.union_id(todo['recipientUserId']) if todo.get('recipientUserId') else recipient
        self.gateway.complete_todo(recipient,todo['dingTalkTaskId'],operator)
    def collaboration(self,todo,notice):
        action=notice['action'];title=todo.get('requirementTitle') or '未命名需求'
        text='\n'.join([f'## {action}：{title}',f"> 项目：{todo.get('projectName') or '未归属项目'}",f"> 协作主题：**{notice['topic']}**",f"> 发起人：{todo.get('sourceName') or '系统'}",'',
            notice['content'][:4000] or '请按页面提示完成本轮协作。','',
            '打开链接即可填写，浏览器无需登录。' if notice['public'] else '请打开待办继续处理。',f"[立即处理]({notice['url']})"])
        self.gateway.send_markdown_to_users([todo['recipientUserId']],f'{action}：{title}',text);return True
