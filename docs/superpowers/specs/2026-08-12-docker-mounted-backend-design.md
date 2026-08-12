# Docker 挂载式后端部署设计

## 目标

将旅行推荐 FastAPI 后端部署为 Docker 容器，同时把应用代码、SQLite 数据库和生产环境变量保留在宿主机，使日常代码更新只需重启容器，无需重新构建镜像。

## 架构

- `travel-api` 镜像只包含 Python 3.12、项目依赖和启动工具；首次部署或 `backend/pyproject.toml` 变更时构建。
- `/opt/travelling/backend` 挂载到容器 `/app`，包含 `app`、迁移目录及运行时代码。
- `/opt/travelling/backend/data` 挂载为 SQLite 数据目录；其内容不进入镜像。
- `/etc/travelling/travel-api.env` 以只读 env 文件提供 API 密钥、JWT 和第三方配置；不提交 Git，也不打进镜像。
- 容器只发布 `127.0.0.1:8000`；宿主机 Caddy 将 `api.sunks.cc` 的 HTTPS 请求反向代理到此端口。

## 日常操作

- 代码更新：将新的后端包同步到 `/opt/travelling/backend`，执行 `/opt/travelling/scripts/restart-backend.sh`。
- 脚本会验证环境文件、确保数据目录存在、重启容器、执行 Alembic 迁移并请求 `/health`。
- 只有依赖变更时才执行 `/opt/travelling/scripts/build-backend-image.sh`，然后执行重启脚本。

## 安全与边界

- 不暴露 8000 端口到公网，不修改现有 SSH 规则。
- SQLite 保持单容器单 worker，避免并发写入争用。
- 环境文件由 root 管理，权限为 `600`；容器以非 root 的 `travel` 用户运行。
- 镜像构建与重启失败时脚本返回非零状态，不清除现有数据库或环境文件。

## 验收

- `docker compose config` 成功解析。
- `restart-backend.sh` 后，`http://127.0.0.1:8000/health` 返回 `{"status":"ok"}`。
- `https://api.sunks.cc/health` 在 Caddy 配置完成后返回同一结果。
