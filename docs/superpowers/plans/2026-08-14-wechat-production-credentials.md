# 微信小程序正式凭据配置实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不泄露 AppSecret 的前提下，为本地 FastAPI 和线上容器配置正式微信凭据，并验证微信登录所需的配置链路。

**Architecture:** 小程序工程仅保存公开的 AppID；FastAPI 通过 Pydantic Settings 从环境变量读取 AppID 与 AppSecret。本地使用被 Git 忽略的 `backend/.env`，线上使用权限受限的 `/etc/travelling/travel-api.env`，容器重启后读取新值。

**Tech Stack:** 微信原生小程序、Python 3.12、FastAPI、Pydantic Settings、Docker、Shell

## Global Constraints

- AppSecret 不得进入小程序前端、Git、文档、测试快照、部署脚本参数或日志。
- 任何验证输出只能显示“已配置”、值长度或脱敏摘要，不得显示完整凭据。
- 保留开发版连接本地后端、体验版和正式版连接 `https://api.sunks.cc` 的现有逻辑。
- 不覆盖工作区中与本任务无关的用户修改。

---

### Task 1: 验证公开 AppID 与配置契约

**Files:**
- Inspect: `miniprogram/project.config.json`
- Inspect: `backend/app/core/config.py`
- Test: `backend/tests/test_config.py`

**Interfaces:**
- Consumes: 微信公众平台提供的 AppID；环境变量名 `TRAVEL_WECHAT_APP_ID`、`TRAVEL_WECHAT_APP_SECRET`
- Produces: 前端 AppID 与后端 Settings 字段对应关系的验证结果

- [ ] **Step 1: 运行脱敏静态检查**

Run:

```bash
python - <<'PY'
import json
from pathlib import Path

config = json.loads(Path("miniprogram/project.config.json").read_text())
assert config["appid"].startswith("wx")
assert len(config["appid"]) == 18
print("miniprogram appid configured: yes")
PY
```

Expected: 输出 `miniprogram appid configured: yes`，不打印 AppID 原值。

- [ ] **Step 2: 运行后端配置测试**

Run:

```bash
cd backend && .venv/bin/pytest tests/test_config.py -q
```

Expected: `3 passed` 或更多，且没有凭据原值出现在输出中。

### Task 2: 写入并验证本地私密环境变量

**Files:**
- Modify, untracked/ignored: `backend/.env`
- Inspect: `.gitignore`

**Interfaces:**
- Consumes: 当前会话中用户提供的 AppID 和 AppSecret
- Produces: `Settings.wechat_app_id`、`Settings.wechat_app_secret` 非空

- [ ] **Step 1: 确认私密文件被 Git 忽略**

Run:

```bash
git check-ignore backend/.env
```

Expected: 输出 `backend/.env`。

- [ ] **Step 2: 使用补丁更新本地环境文件**

将 `backend/.env` 中的 `TRAVEL_WECHAT_APP_ID` 与 `TRAVEL_WECHAT_APP_SECRET` 更新为当前会话中用户提供的两个真实值。出于凭据安全要求，本计划不复制这两个值；补丁结果和后续输出也不得回显它们。

- [ ] **Step 3: 运行脱敏读取验证**

Run:

```bash
cd backend && .venv/bin/python - <<'PY'
from app.core.config import Settings

s = Settings()
assert s.wechat_app_id.startswith("wx") and len(s.wechat_app_id) == 18
assert len(s.wechat_app_secret) >= 32
print("wechat app id configured: yes")
print("wechat app secret configured: yes")
PY
```

Expected: 两项均为 `yes`，不打印原值。

- [ ] **Step 4: 确认没有待提交的凭据文件**

Run:

```bash
git status --short
```

Expected: 不出现 `backend/.env`。

### Task 3: 写入服务器私密环境变量并重启

**Files:**
- Modify on server: `/etc/travelling/travel-api.env`
- Execute on server: `/opt/travelling/scripts/restart-backend.sh`

**Interfaces:**
- Consumes: 当前会话中的 AppID、AppSecret；现有 SSH 权限
- Produces: Docker 容器中的 `TRAVEL_WECHAT_APP_ID`、`TRAVEL_WECHAT_APP_SECRET` 非空

- [ ] **Step 1: 连接服务器并备份环境文件**

在服务器上执行：

```bash
sudo cp /etc/travelling/travel-api.env /etc/travelling/travel-api.env.before-wechat
```

Expected: 备份文件创建成功；命令不输出文件内容。

- [ ] **Step 2: 安全更新两项环境变量**

通过仅当前 SSH 会话可见的受保护输入更新两项值。不得将 AppSecret 放入仓库脚本、Shell 历史或日志。完成后设置：

```bash
sudo chmod 600 /etc/travelling/travel-api.env
```

- [ ] **Step 3: 脱敏检查服务器配置**

在服务器上执行仅返回是否存在的检查：

```bash
sudo awk -F= '
  /^TRAVEL_WECHAT_APP_ID=/{id=length($2)>=18}
  /^TRAVEL_WECHAT_APP_SECRET=/{secret=length($2)>=32}
  END {print "wechat app id configured:", id?"yes":"no"; print "wechat app secret configured:", secret?"yes":"no"}
' /etc/travelling/travel-api.env
```

Expected: 两项均为 `yes`。

- [ ] **Step 4: 重启后端并运行健康检查**

在服务器上执行：

```bash
sudo /opt/travelling/scripts/restart-backend.sh
curl -fsS http://127.0.0.1:8000/health
```

Expected: 重启脚本成功，健康检查返回 `{"status":"ok"}`。

### Task 4: 回归与上线清单

**Files:**
- Inspect: `miniprogram/miniprogram/app.js`
- Inspect: `miniprogram/miniprogram/services/auth.js`
- Inspect: `docs/superpowers/specs/2026-08-14-wechat-production-credentials-design.md`

**Interfaces:**
- Consumes: ICP 审核状态、微信公众平台配置、线上 API 状态
- Produces: 可执行的正式发布剩余事项

- [ ] **Step 1: 运行微信认证后端测试**

Run:

```bash
cd backend && .venv/bin/pytest tests/auth/test_wechat_login.py tests/test_config.py -q
```

Expected: 全部通过，且日志不含 AppSecret。

- [ ] **Step 2: 运行小程序认证测试**

Run:

```bash
cd miniprogram && npm test -- tests/services/auth.test.js
```

Expected: 全部通过。

- [ ] **Step 3: 核对正式发布前置条件**

逐项记录状态：ICP 备案、`api.sunks.cc` HTTPS、request 合法域名、小程序备案、服务类目、隐私保护指引、位置权限用途、AI 内容标识与安全措施、体验版真机验收、微信审核、公安联网备案。

- [ ] **Step 4: 密钥轮换提醒**

首次连通验证完成后，在微信公众平台重置已通过对话传递的 AppSecret；只更新本地 `backend/.env` 与服务器 `/etc/travelling/travel-api.env`，再次执行 Task 2 Step 3 和 Task 3 Step 4。
