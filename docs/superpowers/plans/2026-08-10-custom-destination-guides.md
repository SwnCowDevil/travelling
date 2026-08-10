# 任意地点主动生成攻略 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在推荐页支持高德搜索全国任意地点，继承当前筛选条件生成并收藏可编辑攻略。

**Architecture:** 新增用户隔离的 `custom_destinations` 和 `custom-guides` 模块；对公共与自定义地点使用统一的攻略展示和收藏快照。推荐页搜索并创建自定义地点后通过 `custom_id` 跳转详情，详情按目标类型调用不同 API。

**Tech Stack:** FastAPI、SQLAlchemy、Alembic、Pydantic、现有高德 Web 服务 API、微信原生小程序、pytest、Node Test。

## Global Constraints

- 自定义地点只属于创建用户，绝不进入公共推荐库。
- 必须从高德搜索候选中选择，关键词至少 2 字。
- 自定义攻略继承推荐页已有月份、天数、出发地和偏好。
- 收藏记录必须且只能关联公共目的地或自定义目的地之一。

---

### Task 1: 高德候选与自定义地点持久化

**Files:**
- Modify: `backend/app/destinations/amap.py`
- Create: `backend/app/custom_destinations/{__init__,models,schemas,service,router}.py`
- Create: `backend/alembic/versions/0009_custom_destinations.py`
- Modify: `backend/app/db/base.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/custom_destinations/test_custom_destinations.py`

- [ ] Write failing tests for two-character keyword validation, candidate parsing, user+POI idempotent create, and cross-user 404.
- [ ] Run: `cd backend && PYTHONPATH=.:.. .venv/bin/pytest tests/custom_destinations/test_custom_destinations.py -q` (expect RED).
- [ ] Extend `AmapClient` with `search_candidates(keyword)` returning name, address, region, POI ID and coordinates. Implement authenticated search/create/read routes and migration with `UniqueConstraint(user_id, amap_poi_id)`.
- [ ] Run migration and test command above (expect GREEN).
- [ ] Commit: `feat: add custom destination search`.

### Task 2: 自定义天气、攻略与收藏兼容

**Files:**
- Create: `backend/app/custom_guides/router.py`
- Modify: `backend/app/guides/service.py`
- Modify: `backend/app/favorites/{models,schemas,service,router}.py`
- Create: `backend/alembic/versions/0010_custom_favorite_targets.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/custom_destinations/test_custom_guides.py`
- Test: `backend/tests/favorites/test_favorites.py`

- [ ] Write failing tests proving custom guide cache is user-scoped, custom payload has correct name/coordinates context, custom favorite is idempotent, and a favorite cannot contain both target IDs.
- [ ] Run targeted pytest commands (expect RED).
- [ ] Add custom guide route that constructs the same `GuideGenerationRequest` and model selection path from custom data. Migrate favorite target to nullable public/custom IDs plus `destination_type`, with exclusive-target validation and separate user-target unique constraints. Store custom snapshot and preserve existing public favorites.
- [ ] Run migrations and targeted tests (expect GREEN).
- [ ] Commit: `feat: support custom guide favorites`.

### Task 3: 推荐页地点输入与候选选择

**Files:**
- Modify: `miniprogram/miniprogram/pages/recommend/{index.js,index.wxml,index.wxss,model.js}`
- Test: `miniprogram/tests/pages/recommend.test.js`

- [ ] Write failing tests: short input does not request search; selected candidate creates custom destination and URL contains current filters; empty result displays the no-result state.
- [ ] Run: `cd miniprogram && node --test tests/pages/recommend.test.js` (expect RED).
- [ ] Add search card above CTA, candidate state, debounced/manual search, create request and navigation to detail with encoded month/days/origin/preferences.
- [ ] Run the targeted test command (expect GREEN).
- [ ] Commit: `feat: search custom destinations from recommend`.

### Task 4: 详情页自定义目标与收藏显示

**Files:**
- Modify: `miniprogram/miniprogram/pages/destination-detail/{index.js,model.js,index.wxml}`
- Modify: `miniprogram/miniprogram/pages/favorite-guides/index.wxml`
- Test: `miniprogram/tests/pages/destination-detail-regenerate.test.js`
- Test: `miniprogram/tests/pages/favorite-guides.test.js`

- [ ] Write failing tests for custom ID route selection, inherited generation fields, and custom favorite payload.
- [ ] Run targeted Node tests (expect RED).
- [ ] Resolve `custom_id` on load; use custom destination and guide paths while retaining fast/deep/favorite behavior. Render custom items in favorite list from snapshot.
- [ ] Run targeted Node tests (expect GREEN).
- [ ] Commit: `feat: generate guides for custom destinations`.

### Task 5: Final verification

- [ ] Run `cd backend && .venv/bin/alembic upgrade head && PYTHONPATH=.:.. .venv/bin/pytest -q`.
- [ ] Run `cd miniprogram && npm test`.
- [ ] Restart local backend and use WeChat DevTools to search a POI, create fast/deep guide, favorite, edit, save and reopen it.
- [ ] Run `git diff --check`; commit only task files and leave local config/WAL files unstaged.
