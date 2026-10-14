# 事件契约

信封由 `backend/itpm/core/events.py` 定义：event_type/schema_version、稳定event_id/source_ref、occurred_at、可信actor、correlation/causation、aggregate身份、当时payload快照及dedupe_key。追踪ID不冒充幂等键；不通过事后最新记录重建旧快照。

|事件|生产事实归属|消费与用途|
|---|---|---|
|project_created / project_updated|portfolio及项目工作workflow|配置匹配的提交后通知|
|requirement_created / requirement_updated|work及各合法创建/更新workflow|工作事件通知；具体入口保留次数与条件|
|requirement_assigned|work及负责人调整|分派相关通知|
|requirement_delivered|原已登记的工作状态动作|交付事件通知；不额外把所有delivery登记都冒充此事件|
|todo_created|inbox及业务workflow|个人待办通知|
|shared_activity_created|collaboration及已登记阶段动作|共享活动通知，IT私有范围守卫|
|shared_activity_comment_created|collaboration评论workflow|评论通知与接收范围守卫|

事件目录有九类名称；新用例必须明确实际触发点，不假定每次业务操作都产生全部事件。历史GET投影不重发通知，账户会话创建不产生这些业务事件。

## 事务与失败

事务内收集，rollback丢弃；commit完成后dispatcher调用消费者。必需业务事实、待办、审计和交付/运营/价值关联由workflow在一个UoW完成，不依赖异步订阅拼业务闭环。

notifications只消费提交后事实，接收对象与报表数据对象分开。原同步发送/重发在HTTP返回前取得结果；worker只处理原持久计划，API不启动调度线程。发送记录在独立短事务更新。

Fake用于检验触发、内容、链接、接收人、次数和成功/失败处理，不表示真实到达。Disabled明确拒绝外发，Real由单独gateway实现。

delivery_logs不是完整outbox；普通事件没有通用可靠重放或严格一次保证。已持久的计划请求与成功记录支持已验证的重启/去重；模糊发送结果不能盲目自动重发。

## 新增/修改事件

登记名称/版本、生产者/消费者、payload、触发条件、事务与发送时点、失败/重试/恢复/去重，以及现有消费者兼容。验收至少覆盖事务失败、重复、停用规则、接收范围、超时/拒绝和重启适用范围。不要直接用改事件载荷的方式绕过模块数据归属。
