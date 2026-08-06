# Phase 1: Backend Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立可运行的 FastAPI、SQLite、微信登录边界及可版本化目的地数据基础。

**Architecture:** 使用应用工厂创建 FastAPI；SQLAlchemy 同步会话承载低并发 SQLite；Pydantic Settings 读取环境变量；认证服务通过可替换的微信客户端换取 `openid`。目的地数据由 JSON 种子文件导入。

**Tech Stack:** Python 3.12、FastAPI、Pydantic 2、pydantic-settings、SQLAlchemy 2、Alembic、PyJWT、httpx、pytest。

## Global Constraints

- 项目根目录为 `/Users/admin/Desktop/游记`。
- SQLite 开启 WAL；应用进程数固定为 1。
- `.env`、数据库文件和任何密钥必须加入 `.gitignore`。
- 代码内不得出现真实 AppSecret 或 AI Token。

---

### Task 1: 应用入口、配置与健康检查

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/main.py`
- Create: `backend/app/core/config.py`
- Create: `backend/tests/test_health.py`
- Create: `.gitignore`

**Interfaces:**
- Produces: `create_app() -> FastAPI`；`settings: Settings`。

- [ ] **Step 1: 写失败测试**

```python
from fastapi.testclient import TestClient
from app.main import create_app

def test_health_returns_ok():
    response = TestClient(create_app()).get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
```

- [ ] **Step 2: 验证测试失败**

Run: `cd backend && python -m pytest tests/test_health.py -v`
Expected: FAIL，`app.main` 尚不存在。

- [ ] **Step 3: 实现最小应用和配置**

```python
def create_app() -> FastAPI:
    app = FastAPI(title='Travel Recommendation API')
    app.get('/health')(lambda: {'status': 'ok'})
    return app
```

`Settings` 必须声明 `database_url`、`jwt_secret`、`wechat_app_id`、`wechat_app_secret`、`ai_base_url`、`ai_model` 和可空 `ai_api_key`，全部支持环境变量覆盖。

- [ ] **Step 4: 验证通过**

Run: `cd backend && python -m pytest tests/test_health.py -v`
Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add .gitignore backend
git commit -m "chore: bootstrap FastAPI backend"
```

### Task 2: SQLite 会话与迁移

**Files:**
- Create: `backend/app/db/session.py`
- Create: `backend/app/db/base.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/tests/db/test_session.py`

**Interfaces:**
- Produces: `get_db() -> Iterator[Session]`；`Base: DeclarativeBase`。

- [ ] **Step 1: 写 WAL 失败测试**

```python
def test_sqlite_uses_wal(db_engine):
    with db_engine.connect() as conn:
        assert conn.exec_driver_sql('PRAGMA journal_mode').scalar().lower() == 'wal'
```

- [ ] **Step 2: 运行并确认失败**

Run: `cd backend && python -m pytest tests/db/test_session.py -v`
Expected: FAIL，数据库引擎 fixture 尚不存在。

- [ ] **Step 3: 实现引擎、会话与 Alembic**

创建 SQLite 引擎时注册连接事件并执行 `PRAGMA journal_mode=WAL`、`PRAGMA foreign_keys=ON`；测试使用临时文件数据库而不是内存数据库。

- [ ] **Step 4: 验证测试和迁移**

Run: `cd backend && python -m pytest tests/db/test_session.py -v && alembic upgrade head`
Expected: PASS，迁移命令退出码为 0。

- [ ] **Step 5: 提交**

```bash
git add backend/app/db backend/alembic.ini backend/alembic backend/tests/db
git commit -m "feat: add SQLite persistence foundation"
```

### Task 3: 用户、行政区与目的地模型

**Files:**
- Create: `backend/app/users/models.py`
- Create: `backend/app/destinations/models.py`
- Create: `backend/app/destinations/schemas.py`
- Create: `backend/alembic/versions/0001_core_tables.py`
- Create: `backend/tests/destinations/test_models.py`

**Interfaces:**
- Produces: `User`、`AdministrativeRegion`、`Destination`；`DestinationRead`。

- [ ] **Step 1: 写唯一约束和关联测试**

```python
def test_destination_links_stable_region_code(db_session):
    region = AdministrativeRegion(code='510000', name='四川省', level='province')
    place = Destination(code='sc-daocheng-yading', name='稻城亚丁', latitude=28.37, longitude=100.35, region_code='510000')
    db_session.add_all([region, place]); db_session.commit()
    assert place.region.name == '四川省'
```

- [ ] **Step 2: 验证失败**

Run: `cd backend && python -m pytest tests/destinations/test_models.py -v`
Expected: FAIL，模型尚不存在。

- [ ] **Step 3: 实现模型与迁移**

`Destination` 使用稳定 `code` 唯一键，保存坐标、分类 JSON、适宜月份 JSON、季节、人流、预算区间、建议天数区间、交通方式和基础质量分；名称不得作为外键。

- [ ] **Step 4: 验证**

Run: `cd backend && alembic upgrade head && python -m pytest tests/destinations/test_models.py -v`
Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add backend/app/users backend/app/destinations backend/alembic backend/tests/destinations
git commit -m "feat: model users regions and destinations"
```

### Task 4: 目的地种子导入

**Files:**
- Create: `backend/data/destinations.v1.json`
- Create: `backend/app/destinations/seed.py`
- Create: `backend/tests/destinations/test_seed.py`

**Interfaces:**
- Produces: `seed_destinations(session: Session, path: Path) -> SeedResult`。

- [ ] **Step 1: 写幂等测试**

```python
def test_seed_is_idempotent(db_session, seed_path):
    first = seed_destinations(db_session, seed_path)
    second = seed_destinations(db_session, seed_path)
    assert first.created > 0
    assert second.created == 0
    assert second.updated == first.created
```

- [ ] **Step 2: 验证失败**

Run: `cd backend && python -m pytest tests/destinations/test_seed.py -v`
Expected: FAIL，导入器尚不存在。

- [ ] **Step 3: 实现校验和 upsert**

种子文件顶层包含 `version` 和 `destinations`；导入前验证稳定编码、经纬度范围、行政区存在、月份为 1–12。先提交覆盖各省级区域的最小测试集，再按同一模式扩充到约 150 个经人工校验的地点。

- [ ] **Step 4: 验证**

Run: `cd backend && python -m pytest tests/destinations/test_seed.py -v`
Expected: PASS，重复导入不新增重复记录。

- [ ] **Step 5: 提交**

```bash
git add backend/data backend/app/destinations/seed.py backend/tests/destinations/test_seed.py
git commit -m "feat: add versioned destination seed import"
```

### Task 5: 微信登录边界与会话令牌

**Files:**
- Create: `backend/app/auth/wechat.py`
- Create: `backend/app/auth/service.py`
- Create: `backend/app/auth/router.py`
- Create: `backend/app/auth/schemas.py`
- Create: `backend/tests/auth/test_wechat_login.py`

**Interfaces:**
- Produces: `WechatClient.exchange(code: str) -> WechatSession`；`POST /auth/wechat`。

- [ ] **Step 1: 写客户端替身测试**

```python
def test_login_creates_user_and_returns_bearer(client, fake_wechat):
    fake_wechat.openid = 'openid-1'
    response = client.post('/auth/wechat', json={'code': 'wx-code'})
    assert response.status_code == 200
    assert response.json()['token_type'] == 'bearer'
    assert response.json()['access_token']
```

- [ ] **Step 2: 验证失败**

Run: `cd backend && python -m pytest tests/auth/test_wechat_login.py -v`
Expected: FAIL，路由尚不存在。

- [ ] **Step 3: 实现登录**

用 `httpx.AsyncClient` 调用微信 `jscode2session`；将客户端作为依赖注入以便测试；按 `openid` 创建或读取用户；JWT 只包含内部用户 ID 和过期时间，不包含 AppSecret 或 session key。

- [ ] **Step 4: 验证**

Run: `cd backend && python -m pytest tests/auth/test_wechat_login.py -v`
Expected: PASS，微信错误码映射为稳定业务错误。

- [ ] **Step 5: 提交与阶段验收**

```bash
git add backend/app/auth backend/tests/auth backend/app/main.py
git commit -m "feat: add WeChat login boundary"
```

Run: `cd backend && python -m pytest -v && alembic upgrade head`
Expected: 全部通过；`GET /health` 返回 200；种子数据可重复导入。

