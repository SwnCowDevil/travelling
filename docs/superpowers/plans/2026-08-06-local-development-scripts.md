# Local Development Scripts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 提供安全、幂等的一键启动、停止和检查本地 FastAPI 服务脚本，并让微信开发者工具固定访问 localhost。

**Architecture:** 公共 Shell 库统一解析仓库路径、PID、日志和进程身份，三个命令脚本只编排各自流程。小程序从无敏感信息的本地配置模块读取 API 地址。

**Tech Stack:** POSIX shell、Uvicorn、Alembic、curl、微信原生小程序 CommonJS、Node test runner。

## Global Constraints

- API 地址固定为 `http://127.0.0.1:8000`，仅用于微信开发者工具。
- PID 与日志位于忽略提交的 `.local/`。
- 停止操作必须验证进程身份，不使用 `pkill` 或模糊匹配杀进程。
- 脚本不得读取、打印或复制 `.env` 内容。
- 重复启动与重复停止必须幂等。

---

### Task 1: 小程序本地 API 配置

**Files:**
- Create: `miniprogram/miniprogram/config/local.js`
- Modify: `miniprogram/miniprogram/app.js`
- Create: `miniprogram/tests/config/local.test.js`

**Interfaces:**
- Produces: `apiBaseUrl: string`，供 `createApiClient(wx, apiBaseUrl)` 使用。

- [ ] 写失败测试，导入 `config/local` 并断言值严格等于 `http://127.0.0.1:8000`，且对象不包含 token、secret、key 字段。
- [ ] 运行 `cd miniprogram && npm test -- tests/config/local.test.js`，预期因模块不存在而失败。
- [ ] 创建配置模块并修改 `app.js` 使用 `localConfig.apiBaseUrl`。
- [ ] 重新运行测试，预期通过。

### Task 2: 安全启停与状态脚本

**Files:**
- Create: `scripts/local-service-lib.sh`
- Create: `scripts/start-local.sh`
- Create: `scripts/stop-local.sh`
- Create: `scripts/status-local.sh`
- Create: `scripts/tests/local-service-scripts.sh`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `start-local.sh`、`stop-local.sh`、`status-local.sh` 三个用户命令。
- Runtime: `.local/backend.pid`、`.local/backend.log`。

- [ ] 写 Shell 集成测试，使用临时目录和伪 Uvicorn 进程验证 PID 身份校验、失效 PID 清理、重复停止和运行状态。
- [ ] 运行 `sh scripts/tests/local-service-scripts.sh`，预期因脚本不存在而失败。
- [ ] 实现公共路径、`is_backend_running`、`remove_stale_pid` 与日志尾部函数。
- [ ] 实现启动脚本：检查 `.venv`/`.env`，Alembic 升级，后台启动，最多等待 15 秒健康检查，失败时清理 PID。
- [ ] 实现停止脚本：发送 TERM，最多等待 10 秒，幂等清理；实现状态脚本显示地址和日志。
- [ ] 为三个入口和测试脚本增加可执行权限，将 `.local/` 加入 `.gitignore`。
- [ ] 运行 Shell 集成测试与 `sh -n scripts/*.sh`，预期通过。

### Task 3: 真实启动停止与回归验证

**Files:**
- Modify: `docs/deployment/server-setup.md`

**Interfaces:**
- Consumes: Task 1 和 Task 2 的配置及脚本。

- [ ] 在部署文档增加微信开发者工具“不校验合法域名”设置和三个本地命令的使用说明。
- [ ] 运行 `scripts/start-local.sh`，预期 `/health` 返回 `{"status":"ok"}`。
- [ ] 再次运行启动脚本，确认 PID 不变。
- [ ] 运行 `scripts/status-local.sh`，预期显示运行中、localhost 地址与日志路径。
- [ ] 运行 `scripts/stop-local.sh` 两次，预期两次均正常结束且端口不再监听。
- [ ] 运行 `cd backend && .venv/bin/python -m pytest -q`、`cd miniprogram && npm test`、`git diff --check`。
- [ ] 提交：`git add .gitignore scripts miniprogram docs/deployment docs/superpowers/plans && git commit -m "feat: add local development service controls"`。
