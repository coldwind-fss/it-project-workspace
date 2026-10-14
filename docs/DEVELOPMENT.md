# 本地开发与接手

## 前提

Python 3.12、Node.js 22/24及npm、专用PostgreSQL 18。依赖由根目录requirements.lock.txt与frontend/package-lock.json锁定。PostgreSQL明确监听127.0.0.1:55432，初始化账号可以创建开发/测试库和角色；不要提供公司生产库的管理连接。

如果已有合适的PostgreSQL实例，直接配置，无需重新安装。空环境可以使用官方PostgreSQL安装包，或已有Docker时运行专用容器：

```sh
docker run --name itpw-postgres -e POSTGRES_PASSWORD=local-only-change-me -p 127.0.0.1:55432:5432 -d postgres:18
```

容器/PG生命周期由开发者管理，应用不会删除数据库或停止其他服务。示例密码只供新本地合成实例。

## Windows

```powershell
python scripts/setup.py
Copy-Item .env.example .env
# 将ITPW_ADMIN_DATABASE_URL改为自己的本地初始化连接。
.\.venv\Scripts\python.exe scripts/runtime.py
.\.venv\Scripts\python.exe scripts/seed_demo.py
.\scripts\dev.ps1
```

Python命令应指向3.12。setup建立本仓库.venv、安装锁定依赖并npm ci；不自动初始化数据库。默认UI3004/API8084，打开http://127.0.0.1:3004/pm/。Ctrl+C只停止此开发启动器的子进程。

## Linux/macOS

```sh
python3.12 scripts/setup.py
cp .env.example .env
# 编辑本地数据库连接。
.venv/bin/python scripts/runtime.py
.venv/bin/python scripts/seed_demo.py
.venv/bin/python scripts/dev.py
```

`.env`与`.runtime`忽略；生成运行账号口令、配置、fixture、附件和测试结果不能提交。新检出自行生成运行账号，不继承旧工作区密码。不要删除.runtime的口令后期待旧PG账号自动换密码；需要重建环境时由初始化管理员明确处理相应合成角色/库。

## 配置与命令

|入口|用途|
|---|---|
|scripts/runtime.py|受保护的显式空库准备；启动前检查目录及受限角色|
|scripts/seed_demo.py|合成身份/联系人和需求到交付、回访、PoC、通知、同步样例|
|scripts/dev.py|UI与API开发进程，前缀/端口来自配置|
|scripts/serve.py|构建后API及静态UI；默认仅绑定loopback|
|scripts/serve.py --worker --once|独立执行一次持久计划，默认Fake|
|scripts/contracts.py / --check|生成/核对OpenAPI及TypeScript DTO，import不访问数据库|
|scripts/verify.py / verify.ps1|独立类型、构建、架构、文件边界、协议及PG回归|
|scripts/verify.py --no-database|仅结构/前端/协议检查，不能冒充完整验收|
|scripts/package_release.py --base /pm/|从已提交且完成完整验证的源码创建部署包|

后端完整验证需要初始化连接，会创建独立合成测试库并保留用于排错；不会删除已有项目库。结果在`.runtime/test-results/`，上传文件在`.test-runs/`。本仓库不需要旧系统源码作oracle；已保留的具体断言覆盖事务、权限、幂等、历史动态、附件、并列L3、轮次/回访、绩效、同步与Fake外部作用。

## 常见问题

- DB连接失败：确认专用PG已启动、55432监听、初始化连接可用；不要删除PG数据目录来排错。
- UNSAFE_DATABASE_ROLE：应用不能用管理员运行，显式prepare或配置受限角色。
- SCHEMA_MISMATCH：查看目录差异，确认目标库；不自动运行SQL升级历史库。
- 端口占用：在.env修改ITPW_API_PORT/UI_PORT/PUBLIC_URL，不停止其他项目。
- 依赖或契约漂移：按锁安装；生成并review契约，不能直接手改生成类型。
- 钉钉没有消息：默认Fake不会外发，页面有说明；真实接入另见部署文档。

接手先读业务/模块/接口/事件，新增或修复流程按 [CONTRIBUTING](../CONTRIBUTING.md) 执行。
