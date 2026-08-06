# Phase 3: Footprints and Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付目的地与行政区状态、到访次数及地图聚合 API。

**Architecture:** 目的地状态、行政区直接状态和到访记录分表保存；领域服务集中维护状态约束；地图查询按当前层级和分类聚合，不把聚合结果反写为用户直接状态。

**Tech Stack:** FastAPI、SQLAlchemy 2、Pydantic 2、pytest、SQLite。

## Global Constraints

- 状态枚举固定为 `want`、`visited`、`revisit`、`avoid`。
- `revisit` 必须至少有一条到访记录。
- 去过次数只能从有效到访记录统计。
- 行政区直接状态与目的地聚合状态不得混写。

---

### Task 1: 状态模型与领域规则

**Files:**
- Create: `backend/app/footprints/models.py`
- Create: `backend/app/footprints/schemas.py`
- Create: `backend/app/footprints/service.py`
- Create: `backend/tests/footprints/test_status_rules.py`

**Interfaces:**
- Produces: `set_destination_status`、`set_region_status`、`clear_status`。

- [ ] 写测试：状态互斥；无到访记录不能设 `revisit`；设置 `avoid` 时保留历史记录并返回冲突警告。
- [ ] 运行：`cd backend && python -m pytest tests/footprints/test_status_rules.py -v`，预期 FAIL。
- [ ] 实现枚举、唯一约束、事务和领域异常。
- [ ] 运行同一测试，预期 PASS。
- [ ] 提交：`git add backend/app/footprints backend/tests/footprints backend/alembic && git commit -m "feat: add footprint status rules"`。

### Task 2: 到访记录与次数统计

**Files:**
- Create: `backend/app/visits/models.py`
- Create: `backend/app/visits/schemas.py`
- Create: `backend/app/visits/service.py`
- Create: `backend/app/visits/router.py`
- Create: `backend/tests/visits/test_records.py`

**Interfaces:**
- Produces: `GET/POST/PATCH/DELETE /visit-records`；`count_visits(user_id, destination_id) -> int`。

- [ ] 写测试：首条记录自动设为 `visited`；第二条将次数变为 2；同日重复返回确认冲突；删除最后记录时 `revisit` 必须同时转换。
- [ ] 运行：`cd backend && python -m pytest tests/visits -v`，预期 FAIL。
- [ ] 实现记录 CRUD、幂等键、重复确认参数和原子状态转换。
- [ ] 运行同一测试，预期 PASS。
- [ ] 提交：`git add backend/app/visits backend/tests/visits backend/alembic && git commit -m "feat: track dated destination visits"`。

### Task 3: 状态 API

**Files:**
- Create: `backend/app/footprints/router.py`
- Create: `backend/tests/footprints/test_api.py`

**Interfaces:**
- Produces: `PUT/DELETE /destination-statuses/{destination_id}`；`PUT/DELETE /region-statuses/{region_code}`。

- [ ] 写测试：用户只能读取和修改自己的状态；重复请求幂等；删除恢复无状态。
- [ ] 运行：`cd backend && python -m pytest tests/footprints/test_api.py -v`，预期 FAIL。
- [ ] 实现鉴权路由、响应 DTO 和错误映射。
- [ ] 运行同一测试，预期 PASS。
- [ ] 提交：`git add backend/app/footprints/router.py backend/tests/footprints && git commit -m "feat: expose footprint status API"`。

### Task 4: 地图层级聚合

**Files:**
- Create: `backend/app/map/service.py`
- Create: `backend/app/map/router.py`
- Create: `backend/app/map/schemas.py`
- Create: `backend/tests/map/test_summary.py`

**Interfaces:**
- Produces: `GET /map/summary?parent_code=&status=`；返回直接状态、聚合计数、到访次数和下级区域。

- [ ] 写测试：稻城亚丁记录聚合到县、市、省；直接标记四川不改变下属地点；按 `revisit` 分类只返回对应聚合。
- [ ] 运行：`cd backend && python -m pytest tests/map -v`，预期 FAIL。
- [ ] 实现按行政区祖先链聚合的查询服务和列表降级数据。
- [ ] 运行：`cd backend && python -m pytest tests/map -v`，预期 PASS。
- [ ] 提交：`git add backend/app/map backend/tests/map && git commit -m "feat: add hierarchical map summaries"`。

### Task 5: 阶段集成验证

**Files:**
- Create: `backend/tests/integration/test_travel_flow.py`

**Interfaces:**
- Consumes: 登录、推荐、状态、到访与地图 API。

- [ ] 写端到端测试：登录 → 推荐 → 标记去过并填写日期 → 标记想再去 → 地图省级聚合显示次数 1。
- [ ] 运行：`cd backend && python -m pytest tests/integration/test_travel_flow.py -v`，预期首次 FAIL。
- [ ] 修复测试暴露的接口契约差异，不绕过领域规则。
- [ ] 运行：`cd backend && python -m pytest -v`，预期全部 PASS。
- [ ] 提交：`git add backend && git commit -m "test: cover complete footprint flow"`。

