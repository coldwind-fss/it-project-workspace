# 模块职责与公开能力

HTTP入口在各域router，字段在schemas/core响应模型；跨域能力在public或注入的声明接口，实际写入通过同一个UoW。`contracts/api-catalog.json`列出运行中的method/path/owner与响应模型，OpenAPI补全部字段。

|模块|职责与数据归属|调用边界|
|---|---|---|
|identity|用户、会话、人员/角色配置|解析Principal、检查动作/资源；会话/人员写入本域，通讯录刷新在业务事务外|
|portfolio|L1分类、L2项目|workflow组织初始L3及层级删除/恢复，不直接写work仓储|
|work|L3、阶段、日志、变更、迭代/发布|权威工作状态与进度；交付资格经公开查询，规则不由页面决定|
|demand|需求池、评审、补充、分支、确认和历史来源|正式转换由workflow调用work/delivery/value，全部分支在同一事务|
|collection|定向提报、征集批次/接收人/回执|prepare/claim/result等公开动作，投递在事务外，判断后才转需求|
|collaboration|共享动态/评论及旧协作记录|私有范围守卫、稳定历史投影、首次写入物化；附件经拥有者策略|
|delivery|交付标准、链接、轮次、反馈|验证通过与IT交付分离；跨域交付由workflow编排|
|value|价值卡、回访请求、资格与回执|唯一ValueEligibilityPolicy；3/30天计划、不可覆盖的回执快照|
|postlaunch|运营轮次、问题、提案、知识|事实归属operationId，回访问题按requestId单次创建|
|attachments|附件元数据、拥有者策略、文件存储|写入/下载先验证拥有者范围；不允许跨L3串文件|
|poc|PoC记录及AI能力派生|本域持久化；历史需求PoC仅兼容只读投影|
|insights|成果/工作/运营报表、个人绩效和定稿|跨表read model明确只读，只有performance_months由本域写入|
|notifications|通知目标/规则、投递日志|消费提交后来源，接收人/数据对象分开，gateway可替换|
|inbox|个人待办及状态动作|个人资源范围、创建/关闭、投递标记；不凭任意请求姓名获取他人待办|
|audit|业务操作记录及技术日志|业务审计同事务，技术日志脱敏/限长|
|work_sync|同步批次/映射/幂等|自有批次权限，workflow调用work/协作；人工后续操作阻止撤回|

## 典型跨域用例

- ProjectWork：项目与初始工作、阶段进展、分派待办、审计和原通知条件。
- DemandWorkflow：多分支转换、工作创建、标准与价值来源关联。
- DeliveryWorkflow：明确交付动作与运营/价值事实、标准快照、轮次一致性。
- ValueWorkflow：回执写入、查看与问题/运营分流。
- AttachmentAccess：声明附件拥有者访问策略，校验实际业务资源。
- Recycle / SyncWorkflow：层级恢复/清理和同步撤回守卫。
- DemandNotices / CollectionSend / NotificationSend / ScheduledNotifications：准备事实、提交后外发、结果记录；不把这些消费者用来补必需业务事实。

模块没有权限自行提交数据库事务；workflow不能复制各域权威规则成为另一个巨型服务。新增模块需登记提供者、消费者、command/query、DTO/错误、数据写入与事件，不以创建一个public.py文件代替边界设计。
