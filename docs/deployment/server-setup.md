# 单机部署指南（FastAPI + SQLite）

第一版不需要 Docker。建议购买一台 Linux 云服务器，用 systemd 管理 FastAPI，由 Caddy 提供 HTTPS。正式发布微信小程序前仍需一个已备案域名；没有域名时可先在开发者工具中关闭合法域名校验进行本地联调，但不能作为正式发布方案。

## 本地微信开发者工具联调

仓库根目录提供三个命令：

```sh
./scripts/start-local.sh
./scripts/status-local.sh
./scripts/stop-local.sh
```

启动脚本会检查 `backend/.env` 和虚拟环境、升级数据库、在后台运行单进程 FastAPI，并将 PID 与日志保存在忽略提交的 `.local/`。重复启动不会创建第二个进程，重复停止也不会报错。小程序本地配置固定访问 `http://127.0.0.1:8000`。

在微信开发者工具中打开“详情 → 本地设置”，勾选“不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书”。localhost HTTP 配置只用于开发者工具；真机和正式发布必须换成已配置为微信合法域名的 HTTPS 地址。

## 1. 服务器准备

1. 安装 Python 3.12、Caddy、SQLite、Git。
2. 创建系统用户 `travel`，将仓库放到 `/opt/travelling`。
3. 在 `backend` 下创建虚拟环境并安装项目：`.venv/bin/pip install -e .`。
4. 创建 `/etc/travelling/travel-api.env`，权限设置为仅服务用户和管理员可读。
5. 至少配置数据库地址、JWT 密钥、微信 AppID/AppSecret、AI Token、AI 加密主密钥和高德 Key。不要把该文件提交到 Git。
6. 执行 `.venv/bin/alembic upgrade head` 和目的地种子导入。
7. 首次启用足迹地图时，在 `backend` 目录执行以下命令缓存省市边界：

```sh
.venv/bin/python -m scripts.sync_map_regions --all-provinces
.venv/bin/python -m scripts.build_map_pack
```

该命令只使用服务器环境文件中的 `TRAVEL_AMAP_KEY`，可安全重复执行；首次会调用高德 Web 服务缓存省级和市级边界，并按已有目的地的高德行政区编码（缺失时按坐标反查）匹配市级归属。为避免限流，请让命令自行完成，不要并行执行多次。不要将实际 Key 写进命令、日志或仓库。

## 2. 启动服务

将 `deploy/travel-api.service` 安装到 `/etc/systemd/system/`，随后执行：

```sh
sudo systemctl daemon-reload
sudo systemctl enable --now travel-api
curl http://127.0.0.1:8000/health
```

保持单 worker，避免 SQLite 写入竞争。数据量或并发明显增长后再迁移 MySQL/PostgreSQL。

## 3. HTTPS 与微信配置

购买并备案域名后，将 `deploy/Caddyfile.example` 的 `api.example.com` 换为真实 API 域名。解析 A/AAAA 记录到服务器，开放 80/443 端口并重载 Caddy。确认 `https://你的域名/health` 返回 `{"status":"ok"}`。

在微信公众平台把该 HTTPS 域名加入 request 合法域名；小程序 `app.js` 的 `apiBaseUrl` 和 `project.config.json` 的 AppID 改成实际值。PackyAPI、高德和微信 AppSecret 永远只放后端环境文件。

## 4. 备份与恢复

每天通过 cron 或 systemd timer 执行 `scripts/backup-sqlite.sh`。脚本使用 SQLite 在线备份命令，完成后执行完整性检查，默认保留 14 天。

恢复前停止 API，将选定备份复制为新的数据库文件，保留原数据库副本，然后运行 `PRAGMA integrity_check`、Alembic 升级和健康检查。确认用户、目的地、到访记录及推荐会话数量后再恢复流量。

## 5. 密钥轮换

泄露的 PackyAPI Token 和曾出现在聊天中的 Token 应立即在供应商后台撤销重建。AI 加密主密钥轮换需要先解密并重新加密个人 Token；不可直接替换，否则旧密文无法读取。
