# 接口契约与维护规则

Pydantic请求模型与响应模型是字段结构的权威；`contracts/openapi.json`为常规接口，`preview-openapi.json`包含公开演示会话。语义在本文及业务/模块说明中记录，不再手工复制整套字段类型。

## 每个动作必须明确

method/path/operationId、所属模块/用例、调用身份/资源范围、输入必填/缺省/null/空串、成功/错误响应、过滤/排序、事务写入、外部作用、幂等/并发和验证场景。新增接口先定契约，再实现。前端从生成DTO取类型，执行 `python scripts/contracts.py` 更新，`--check`只检查不重写。

## 既有协议

公开前缀由配置决定，内部为 `/api`；既有路径、大小写字段、合法别名和数组/对象/文件响应保留。不能为“统一”给全部接口套新envelope或强制分页。PATCH式更新只使用显式提交字段，历史额外字段按具体模型约定处理。

AppError集中错误分类及安全信息；HTTP边界保持具体接口的error/detail和状态。400/401/403/404/409/410/422/503按用途映射，不暴露堆栈、DSN、token或上游原始响应。requestId用于追踪，不充当幂等键。前端ApiError区分失败与空结果。

内部默认有效会话，具体动作/资源继续核验。另有定向表单token、协作链接token、签名webhook、受限同步服务及公共健康/配置。公开表单不是匿名访问内部台账。请求中的姓名、role或“可交付”布尔值不能授予权限或改变权威规则。

已有clientKey/idempotencyKey及token保持作用域；同键同内容返回原结果，冲突按具体契约处理，PG锁保护检查+写入。GET没有业务写入、历史批量回填或通知作用。

## 浏览器演示入口

`POST /api/preview/session`仅preview配置存在。actor白名单super/admin/editor/viewer/other，默认super；未知422。成功LoginResult包含服务器创建的7天sessionToken，Cache-Control:no-store；身份未准备/未启用或数据库未就绪503。没有任意userId/角色参数，不调用钉钉，不产生业务通知事件。

`GET /preview-login`只返回入口HTML；脚本POST建立会话、GET `/api/session`核验后缓存，再返回本站hash目标。内部直达/401恢复有限重试；建立最多12秒、查询最多8秒。加载/失败有提示，外部定向表单保留自己的身份/token规则。它不是面向真实人员的账号密码登录系统。

当前公开仓库将入口HTML放在应用内，便于独立运行；原线上地址和协议仍可使用。响应模型、OpenAPI及浏览器入口测试共同约束该能力。

## 示例变更流程

给运营增加一个业务动作时：先明确operationId/权限/状态、请求与结果、哪些表由postlaunch写入、是否需要跨域workflow、是否有新的提交后通知；然后补Pydantic模型与测试、更新生成契约和事件目录。不能在页面直接拼SQL或调用外部SDK，也不能用新的字段隐式覆盖旧回执快照。
