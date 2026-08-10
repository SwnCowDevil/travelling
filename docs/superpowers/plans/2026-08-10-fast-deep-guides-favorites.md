# 快速/深度攻略与收藏编辑 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 支持快速/深度两种 AI 攻略，并保存可独立编辑的个人收藏副本。

**Architecture:** `GuideGenerationRequest` 增加模式并进入缓存键，路由按模式创建 AI 客户端。新增 `favorites` 模块保存用户专属的 `GuidePayload` 快照；小程序详情页发起模式请求和收藏，新增收藏列表、详情与编辑页。

**Tech Stack:** FastAPI、SQLAlchemy、Alembic、Pydantic、微信原生小程序、pytest、Node Test。

## Global Constraints

- 快速模型为 `TRAVEL_AI_FAST_MODEL`，默认 `deepseek-v4-flash`；深度模型为现有系统/个人深度模型。
- `generation_mode` 必须是 `fast` 或 `deep`，并参与缓存键。
- 收藏按用户隔离，同一用户同一目的地仅一条；编辑不修改 AI 缓存。
- 收藏快照和保存更新均由 `GuidePayload` 校验。

---

### Task 1: 模式化攻略服务

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/guides/schemas.py`
- Modify: `backend/app/guides/router.py`
- Modify: `backend/app/guides/service.py`
- Test: `backend/tests/guides/test_guides.py`

**Interfaces:** `GuideGenerationRequest.generation_mode: Literal["fast", "deep"] = "fast"`; `guide_client_for_mode(profile, mode) -> AIClient`。

- [ ] **Step 1: Write failing tests**

```python
async def test_fast_and_deep_do_not_share_cache(db_session):
    await service.generate(db_session, destination, GuideGenerationRequest(..., generation_mode="fast"))
    result = await service.generate(db_session, destination, GuideGenerationRequest(..., generation_mode="deep"))
    assert result.cache_hit is False
```

- [ ] **Step 2: Run RED test**

Run: `cd backend && PYTHONPATH=.:.. .venv/bin/pytest tests/guides/test_guides.py -q`

Expected: FAIL because the request has no generation mode.

- [ ] **Step 3: Implement mode resolver and cache separation**

```python
class GuideGenerationRequest(BaseModel):
    generation_mode: Literal["fast", "deep"] = "fast"

def guide_model_for_mode(profile, mode):
    return settings.ai_fast_model if mode == "fast" else (profile.model if profile else settings.ai_model)
```

Set fast timeout to 45 seconds and deep timeout to 90 seconds; use a concise fast prompt but keep schema validation.

- [ ] **Step 4: Run GREEN test and commit**

Run: `cd backend && PYTHONPATH=.:.. .venv/bin/pytest tests/guides/test_guides.py -q`

Commit: `git add backend/app/core/config.py backend/app/guides backend/tests/guides/test_guides.py && git commit -m "feat: add fast and deep guide modes"`

### Task 2: 收藏攻略数据库与 API

**Files:**
- Create: `backend/app/favorites/{__init__,models,schemas,service,router}.py`
- Create: `backend/alembic/versions/0008_favorite_guides.py`
- Modify: `backend/app/db/base.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/favorites/test_favorites.py`

**Interfaces:** `POST/GET /favorite-guides`, `GET/PUT/DELETE /favorite-guides/{id}`；`FavoriteGuide` 含 user、destination、mode、payload、destination_snapshot、时间戳。

- [ ] **Step 1: Write failing API tests**

```python
def test_save_favorite_is_idempotent_for_user_and_destination(client):
    assert client.post("/favorite-guides", json=body).status_code == 201
    assert client.post("/favorite-guides", json=body).json()["id"] == 1

def test_other_user_cannot_edit_favorite(client):
    assert client.put("/favorite-guides/1", headers=other_user, json=payload).status_code == 404
```

- [ ] **Step 2: Run RED test**

Run: `cd backend && PYTHONPATH=.:.. .venv/bin/pytest tests/favorites/test_favorites.py -q`

Expected: FAIL because favorites routes do not exist.

- [ ] **Step 3: Implement model, migration, service and routes**

```python
__table_args__ = (UniqueConstraint("user_id", "destination_id"),)
payload: Mapped[dict] = mapped_column(JSON)
destination_snapshot: Mapped[dict] = mapped_column(JSON)
```

Validate `GuidePayload` on create/update; duplicate `POST` returns the existing item; list sorts by `updated_at DESC`; all item queries include `user_id`; delete returns 204.

- [ ] **Step 4: Run migration, GREEN test and commit**

Run: `cd backend && .venv/bin/alembic upgrade head && PYTHONPATH=.:.. .venv/bin/pytest tests/favorites/test_favorites.py -q`

Commit: `git add backend/app/favorites backend/app/db/base.py backend/app/main.py backend/alembic/versions/0008_favorite_guides.py backend/tests/favorites && git commit -m "feat: add favorite guide API"`

### Task 3: 详情页双模式与收藏入口

**Files:**
- Modify: `miniprogram/miniprogram/pages/destination-detail/{index.js,index.wxml,index.wxss,model.js}`
- Test: `miniprogram/tests/pages/destination-detail-regenerate.test.js`
- Test: `miniprogram/tests/pages/destination-detail-view.test.js`

**Interfaces:** `generateGuide(mode)` 调用 `/guides/{id}`；`saveFavorite()` 调用 `/favorite-guides`。

- [ ] **Step 1: Write failing page tests**

```js
test('deep mode sends generation_mode and preserves old guide during loading', async () => {
  await page.generateGuide('deep')
  assert.equal(request.data.generation_mode, 'deep')
})
test('favorite sends current payload and mode once', async () => {
  await page.saveFavorite()
  assert.equal(request.path, '/favorite-guides')
})
```

- [ ] **Step 2: Run RED test**

Run: `cd miniprogram && node --test tests/pages/destination-detail-regenerate.test.js tests/pages/destination-detail-view.test.js`

Expected: FAIL because mode controls and favorite action do not exist.

- [ ] **Step 3: Implement controls and state**

Default initial request to fast. Show quick/deep buttons, current-mode label and deep “约 1 分钟” hint. Preserve `guideResponse` for exact favorite submission. Use 60 seconds for fast and 120 seconds for deep. Add a bottom `收藏攻略` / `已收藏` button; duplicate response saves the returned ID and a second tap opens favorite detail.

- [ ] **Step 4: Run GREEN test and commit**

Run: `cd miniprogram && node --test tests/pages/destination-detail-regenerate.test.js tests/pages/destination-detail-view.test.js`

Commit: `git add miniprogram/miniprogram/pages/destination-detail miniprogram/tests/pages/destination-detail-*.test.js && git commit -m "feat: add guide modes and favorite action"`

### Task 4: 我的页收藏列表与编辑页

**Files:**
- Create: `miniprogram/miniprogram/pages/favorite-guides/{index.js,index.json,index.wxml,index.wxss}`
- Create: `miniprogram/miniprogram/pages/favorite-guide-detail/{index.js,index.json,index.wxml,index.wxss}`
- Modify: `miniprogram/miniprogram/app.json`
- Modify: `miniprogram/miniprogram/pages/me/{index.js,index.wxml,model.js}`
- Test: `miniprogram/tests/pages/favorite-guides.test.js`
- Test: `miniprogram/tests/pages/favorite-guide-detail.test.js`
- Test: `miniprogram/tests/pages/me.test.js`

- [ ] **Step 1: Write failing tests**

```js
test('profile shows favorite count and opens favorite list', () => {
  assert.match(wxml, /收藏攻略/)
  assert.equal(view.favorites, 3)
})
test('failed favorite save keeps editor draft', async () => {
  await page.save()
  assert.equal(page.data.editing, true)
  assert.equal(page.data.draft.payload.highlights[0], '修改后的玩法')
})
```

- [ ] **Step 2: Run RED tests**

Run: `cd miniprogram && node --test tests/pages/favorite-guides.test.js tests/pages/favorite-guide-detail.test.js tests/pages/me.test.js`

Expected: FAIL because the menu and pages do not exist.

- [ ] **Step 3: Implement pages and editor**

Add both paths to `app.json`. List by latest update with destination, mode and time. In detail maintain separate `saved` and `draft`; edit transport, weather, packing, cautions, highlights, each food field, and each itinerary field. Save with `PUT`; retain draft on failure. Confirm before delete with `wx.showModal`; return to list after success. Add favorite count and menu action to 我的页.

- [ ] **Step 4: Run GREEN tests and commit**

Run: `cd miniprogram && node --test tests/pages/favorite-guides.test.js tests/pages/favorite-guide-detail.test.js tests/pages/me.test.js`

Commit: `git add miniprogram/miniprogram/app.json miniprogram/miniprogram/pages/me miniprogram/miniprogram/pages/favorite-guides miniprogram/miniprogram/pages/favorite-guide-detail miniprogram/tests/pages && git commit -m "feat: add editable favorite guide pages"`

### Task 5: Full verification

**Files:** all task-owned source, tests and migration files.

- [ ] **Step 1: Run backend verification**

Run: `cd backend && .venv/bin/alembic upgrade head && PYTHONPATH=.:.. .venv/bin/pytest -q`

Expected: PASS.

- [ ] **Step 2: Run mini-program verification**

Run: `cd miniprogram && npm test`

Expected: PASS.

- [ ] **Step 3: Restart and manually verify**

Run: `./scripts/stop-local.sh && ./scripts/start-local.sh`

In WeChat DevTools: compile, open a detail, generate fast, generate deep, favorite it, edit food and one day plan, save, reopen it from 我的页.

- [ ] **Step 4: Commit boundary check**

Run: `git diff --check && git status --short`

Commit only source, tests, docs and migration files; leave user-local project config and SQLite WAL files unstaged.
