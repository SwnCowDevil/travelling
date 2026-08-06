# Phase 4: Mini Program and Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付使用 Vant Weapp 的微信原生小程序、完整联调流程和无 Docker 强制要求的部署说明。

**Architecture:** 小程序以 service 层隔离网络与微信 API；页面只消费稳定 DTO；通用状态操作和阶段式加载为独立组件；后端由 Caddy/Nginx 反向代理并以系统服务运行。

**Tech Stack:** 微信原生小程序、Vant Weapp、miniprogram-simulate、FastAPI、SQLite、Caddy/Nginx。

## Global Constraints

- 保留现有绿色主题和三页签结构。
- 使用“核心条件 + 快捷标签 + 更多筛选”替代五列下拉。
- 所有动画支持减少动态效果并避免持续循环。
- 前端不得包含任何服务密钥。
- 未实现功能不显示待扩展菜单。

---

### Task 1: 小程序骨架、Vant 与请求层

**Files:**
- Create: `miniprogram/package.json`
- Create: `miniprogram/project.config.json`
- Create: `miniprogram/miniprogram/app.js`
- Create: `miniprogram/miniprogram/app.json`
- Create: `miniprogram/miniprogram/app.wxss`
- Create: `miniprogram/miniprogram/services/api.js`
- Create: `miniprogram/tests/services/api.test.js`

**Interfaces:**
- Produces: `request({method, path, data}) -> Promise<object>`；三页签路由。

- [ ] 写测试：自动携带 bearer token；401 时清理会话；业务错误保留 `code` 和 `traceId`。
- [ ] 运行：`cd miniprogram && npm test -- services/api.test.js`，预期 FAIL。
- [ ] 初始化原生小程序和 Vant Weapp，实现请求封装及绿色主题变量。
- [ ] 运行同一测试，预期 PASS；微信开发者工具构建无错误。
- [ ] 提交：`git add miniprogram && git commit -m "chore: bootstrap native WeChat mini program"`。

### Task 2: 登录、定位与手动出发地

**Files:**
- Create: `miniprogram/miniprogram/services/auth.js`
- Create: `miniprogram/miniprogram/services/location.js`
- Create: `miniprogram/miniprogram/components/origin-picker/*`
- Create: `miniprogram/tests/services/location.test.js`

**Interfaces:**
- Produces: `login() -> Promise<UserSession>`；`resolveOrigin() -> Promise<Origin>`。

- [ ] 写测试：定位成功返回坐标；拒绝定位返回 `manual_required`；最近手动地址可复用。
- [ ] 运行：`cd miniprogram && npm test -- services/location.test.js`，预期 FAIL。
- [ ] 实现 `wx.login`、`wx.getLocation`、`wx.chooseLocation` 封装和本地非敏感缓存。
- [ ] 运行同一测试，预期 PASS。
- [ ] 提交：`git add miniprogram && git commit -m "feat: add login and origin selection"`。

### Task 3: 推荐页与阶段式 Loading

**Files:**
- Create: `miniprogram/miniprogram/pages/recommend/*`
- Create: `miniprogram/miniprogram/components/filter-bar/*`
- Create: `miniprogram/miniprogram/components/recommend-card/*`
- Create: `miniprogram/miniprogram/components/loading-stage/*`
- Create: `miniprogram/tests/pages/recommend.test.js`

**Interfaces:**
- Consumes: `POST /recommendations`、`POST /recommendations/{id}/next`。

- [ ] 写测试：默认月份提交；筛选可全部清空；加载阶段按顺序更新；成功显示三卡；失败显示规则降级提示。
- [ ] 运行：`cd miniprogram && npm test -- pages/recommend.test.js`，预期 FAIL。
- [ ] 实现核心条件卡、快捷标签、`van-popup` 更多筛选、骨架卡和换一批。
- [ ] 运行测试并在开发者工具检查 375px 与 430px 宽度，预期无横向溢出。
- [ ] 提交：`git add miniprogram && git commit -m "feat: build recommendation experience"`。

### Task 4: 详情、天气和状态操作

**Files:**
- Create: `miniprogram/miniprogram/pages/destination-detail/*`
- Create: `miniprogram/miniprogram/components/status-actions/*`
- Create: `miniprogram/miniprogram/components/weather-panel/*`
- Create: `miniprogram/tests/pages/destination-detail.test.js`

**Interfaces:**
- Consumes: 目的地、攻略、天气和状态 API。

- [ ] 写测试：已有基础内容先显示；攻略模块独立加载；天气来源标签正确；`revisit` 无访问记录时引导补录。
- [ ] 运行测试，预期 FAIL。
- [ ] 实现折叠内容、底部状态栏、一次性动效、震动和 Toast。
- [ ] 运行测试和开发者工具交互检查，预期 PASS。
- [ ] 提交：`git add miniprogram && git commit -m "feat: build destination detail page"`。

### Task 5: 地图、到访记录与我的

**Files:**
- Create: `miniprogram/miniprogram/pages/map/*`
- Create: `miniprogram/miniprogram/pages/visit-records/*`
- Create: `miniprogram/miniprogram/pages/me/*`
- Create: `miniprogram/miniprogram/pages/ai-settings/*`
- Create: `miniprogram/tests/pages/map.test.js`
- Create: `miniprogram/tests/pages/ai-settings.test.js`

**Interfaces:**
- Consumes: 地图聚合、状态、到访、用户和 AI 配置 API。

- [ ] 写测试：地图下钻与列表降级；四类筛选；访问记录计数；Token 只显示掩码；新配置测试失败不替换旧配置。
- [ ] 运行测试，预期 FAIL。
- [ ] 实现地图底部面板、标记确认、记录 CRUD、统计卡和简单/高级 AI 设置。
- [ ] 运行测试；模拟地图加载失败，确认列表仍可操作。
- [ ] 提交：`git add miniprogram && git commit -m "feat: add map footprints and profile settings"`。

### Task 6: 联调、部署与验收

**Files:**
- Create: `docs/deployment/server-setup.md`
- Create: `deploy/travel-api.service`
- Create: `deploy/Caddyfile.example`
- Create: `scripts/backup-sqlite.sh`
- Create: `docs/testing/release-checklist.md`

**Interfaces:**
- Produces: 单机 FastAPI + SQLite + HTTPS 部署和恢复流程。

- [ ] 写部署验证清单：健康检查、HTTPS、微信合法域名、服务重启、备份、恢复、日志脱敏和 Token 轮换。
- [ ] 在临时 SQLite 副本上执行备份恢复演练，校验表数量和关键记录数量一致。
- [ ] 配置 systemd 单进程启动和 Caddy HTTPS 反向代理示例，所有值使用环境变量或示例域名。
- [ ] 运行：`cd backend && python -m pytest -v`、`cd miniprogram && npm test`、微信开发者工具真机预览；预期全部通过。
- [ ] 提交：`git add docs deploy scripts && git commit -m "docs: add deployment and release verification"`。

