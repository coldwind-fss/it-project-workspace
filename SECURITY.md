# 安全边界与已知依赖告警

演示身份只能用于合成数据环境。production配置不会注册公开演示登录；真实部署必须提供受限数据库账号、可信外部配置与明确授权。不要把公开演示入口接到公司真实业务库。

凭据、会话token、数据库dump、附件与日志存放在忽略/外置目录，不提交GitHub。处理安全问题时先联系维护者，不在公开issue中贴凭据或真实业务记录。

## 2026-10-14依赖检查

本次实际运行npm audit，原锁报告17个受影响依赖包节点（13 high、4 moderate）；执行现有semver范围内的兼容修复后，剩余9个节点（6 high、3 moderate、0 critical）。这些是依赖图节点计数，不是9个独立攻击场景。兼容修复已写入锁，类型/构建/业务回归须重新通过。

剩余节点为Vite/Tailwind构建和开发工具链及其传递依赖（braces、chokidar、fast-glob、micromatch、esbuild、postcss-nested、postcss-selector-parser等）。npm推荐的完全修复涉及Vite/Tailwind主版本迁移，本次不强制升级并改变既有构建/样式体系。依赖审计尚未全绿，CI当前验证功能/契约/架构，不冒充安全认证。

本项目发布的是静态前端与FastAPI服务，不在公开生产端口运行Vite开发服务或Vue SSR；开发服务绑定loopback。这是运行边界说明，不表示告警已修复。Vite相关风险见[维护者审阅的路径遍历公告](https://github.com/advisories/GHSA-4w7w-66w2-5vf9)，braces见[官方审阅公告](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm)。已修复的Vue SSR传递依赖公告见[GHSA-g2v6-rqmx-r4w6](https://github.com/advisories/GHSA-g2v6-rqmx-r4w6)。

后续升级作为独立技术变更：核对兼容/样式、更新锁，重新跑类型/构建/关键页面与业务关卡，再发布。当前Python依赖仍沿用既有锁，本次不声称完成其全部安全审计。
