# 构建、部署与恢复

当前在线演示仍是已发布的独立应用：http://114.55.146.5/pm-v2/preview-login。公开仓库整理不自动切换现有服务器、数据库或服务。本仓库提供新的独立发布工具；由运营者配置目标路径、账号和端口。

## 发布包

在本仓库依赖与专用PG就绪后运行完整验证、提交源码，再打包：

```sh
python scripts/verify.py
git add .
git commit -m "Describe the reviewed change"
python scripts/package_release.py --base /pm/
```

包在忽略的.runtime，manifest包含源码提交、全部成员SHA256与publicBase。包含后端、前端dist、锁、必要契约/脚本与部署样例；不包含.env、venv、node_modules、PG数据、附件、测试token或日志。包校验不能代替对变更后代码的实际验证。

服务器需要Python3.12、PG18、Nginx和已有应用运行账号。配置外置，例如 `/etc/it-project-workspace/workspace.env`，权限root:应用组640；基于 [workspace.env.example](../deploy/workspace.env.example) 填写受限DSN及真实路径。演示profile为preview+fake，生产真实钉钉为production+real；公开演示入口在production不注册。

初始数据库只能由管理员显式创建空合成库/角色并加载schema，再运行合成seed；运行服务不会代劳。迁移已有业务库要先目录采用与备份，不能重新加载schema.sql。

## Nginx与systemd

样例 [nginx.conf.example](../deploy/nginx.conf.example) / [api.service.example](../deploy/api.service.example) / [worker.service.example](../deploy/worker.service.example)。将示例路径、用户、端口、前缀替换为目标配置；Nginx先`nginx -t`再reload。新服务使用独立名称，不覆盖其他项目服务。

`deploy/install_release.py`校验ZIP与成员、在新release暂存并探测ready/静态资产/匿名权限后切换当前指针；失败恢复原指针。只启动指定的新服务，数据库/上传目录外置。worker是独立进程，不由API启动。

```sh
python deploy/install_release.py --archive /tmp/workspace.zip --sha256 <package-sha256> \
  --root /opt/it-project-workspace --config /etc/it-project-workspace/workspace.env \
  --user itpw --service it-project-workspace --port 18090 --stage-port 18091
```

只在已准备好配置/账号/库的目标主机执行，示例端口应确认未被其他服务占用。SSH密钥与远程连接方法由运营者管理，不写入代码。

## 健康、备份与恢复

`/api/health`是存活；`/api/ready`检查目录和受限角色。HTTP、页面、数据库和外部集成结果分别核验，不把health200当完整业务通过。

备份前停止写入该库/附件的API与worker。使用 [backup_restore.py](../deploy/backup_restore.py)，它不会自动停止其他服务：

```sh
python deploy/backup_restore.py backup --output /var/lib/it-project-workspace/backups/unique-name --quiesced
python deploy/backup_restore.py restore --backup /var/lib/it-project-workspace/backups/unique-name \
  --database pm_test_rebuild_restore_example
```

提供当前应用DSN/附件路径及初始化连接；pg_dump/pg_restore应可用。恢复只创建新的本地合成库，不覆盖当前库；逐表行指纹及附件哈希验证后才接受。备份包含私有会话/业务资料，外置保存，禁止推送GitHub。

代码回滚：选择已校验的历史release，替换current指针并重启这两个新服务，核对ready、资产和关键记录。只有schema兼容时才允许这样回滚；破坏性迁移需要数据恢复方案，不能仅换代码。

## 可选真实钉钉

`ITPM_PROFILE=production`、`ITPM_INTEGRATION_MODE=real`及明确APP_KEY/APP_SECRET，必要corpId/agentId/robotCode配置。供应方支持授权码/通讯录缓存、个人Markdown/群签名与已有原生待办完成；外部HTTP不持有业务连接。当前只有MockTransport协议/API证据，实际权限、接收人和抵达未联调。不要对原公司默认联系人试发。
