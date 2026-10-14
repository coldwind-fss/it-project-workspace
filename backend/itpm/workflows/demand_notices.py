from itpm.core.events import AfterCommitAction
from itpm.core.errors import require


class DemandNotices:
    def __init__(self,demand,gateway,uow_factory,public_url):
        self.demand,self.gateway,self.uow_factory,self.base=demand,gateway,uow_factory,public_url.rstrip('/')
    def link(self,path):return self.base+'/#'+path
    def review(self,row,demand):
        require(row.get('reviewerUserId'),'评估人缺少钉钉 UserId，无法发送通知')
        body='\n'.join(['## 需求池评估通知',f"- 评估角色：{row.get('reviewerRoleLabel') or '业务评估'}",f"- 评估人：{row.get('reviewerName') or row.get('reviewerUserId') or '-'}",
            f"- 需求：{demand.get('title') or row.get('demandId') or ''}",f"- 提出部门：{demand.get('department') or '-'}",'',
            f"[打开评估链接]({self.link('/entry/demand-review?token='+row['token'])})"])
        return self.gateway.send_markdown_to_users([row['reviewerUserId']],'需求池业务评估通知',body)
    def confirmation(self,row,demand):
        require(row.get('recipientUserId'),'业务确认人缺少钉钉 UserId，无法发送确认链接')
        content=row['content'];definition=content.get('valueDefinition') or {}
        body='\n'.join(['## 上线前交付与价值确认',f"- 需求：{demand.get('title') or row.get('demandId') or ''}",f"- 项目类型：{row.get('templateLabel') or '通用交付标准'}",
            f"- 交付范围：{content.get('scope') or row.get('usageScope') or '-'}",f"- 验证场景：{content.get('scenarios') or row.get('businessProcess') or '-'}",
            f"- 预期结果 / 通过条件：{content.get('expected') or row.get('acceptanceCriteria') or '-'}",f"- 上线前业务基线：{definition.get('baselineSummary') or '-'}",
            f"- 上线后期望变化：{definition.get('expectedSummary') or '-'}",'',
            '内容已由 IT 填写，请打开链接核对后选择“确认通过”或“退回修改”；无需登录系统，也无需重新填表。',
            f"[打开确认页面]({self.link('/entry/demand-confirm?token='+row['token'])})"])
        return self.gateway.send_markdown_to_users([row['recipientUserId']],'上线前交付与价值确认',body)
    def send_after_commit(self,u,p,table,rows,demand,result,refresh):
        def dispatch():
            for row in rows:
                sent=True;error=''
                try:
                    if table=='demand_pool_reviews':self.review(row,demand)
                    else:
                        with self.uow_factory() as read:payload=self.demand.confirmation_payload(read,p,row)
                        self.confirmation(payload,demand)
                except Exception as exc:sent=False;error=str(exc)[:2000]
                with self.uow_factory() as write:self.demand.notification_result(write,table,row['id'],sent,error)
            with self.uow_factory() as read:
                result.clear();result.update(refresh(read))
        u.events.append(AfterCommitAction(dispatch))
