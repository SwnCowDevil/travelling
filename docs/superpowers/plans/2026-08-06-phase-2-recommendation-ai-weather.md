# Phase 2: Recommendation, AI, Weather Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付不会因 AI 或天气服务失败而失效的推荐与攻略 API。

**Architecture:** 纯函数负责距离、硬筛选和评分；AI 适配器只重排候选并返回结构化结果；天气适配器区分近期预报和历史气候；推荐会话与攻略缓存持久化到 SQLite。

**Tech Stack:** FastAPI、SQLAlchemy 2、Pydantic 2、httpx、pytest、Open-Meteo、OpenAI 兼容 API。

## Global Constraints

- AI 只能返回传入候选的稳定 ID。
- 距离使用 Haversine 直线距离并明确标注。
- AI 超时默认 20 秒，失败必须降级到规则结果。
- Open-Meteo 失败必须回退本地气候字段。

---

### Task 1: 距离、硬筛选与评分

**Files:**
- Create: `backend/app/recommendations/domain.py`
- Create: `backend/app/recommendations/scoring.py`
- Create: `backend/tests/recommendations/test_scoring.py`

**Interfaces:**
- Produces: `haversine_km(origin, target) -> float`；`filter_candidates(query, destinations, statuses) -> list[Destination]`；`score_candidate(query, destination) -> ScoreBreakdown`。

- [ ] 写测试：上海到杭州距离落在 150–190km；超距、不想去、默认已去过被排除；想再去保留；各权重之和为 1。
- [ ] 运行：`cd backend && python -m pytest tests/recommendations/test_scoring.py -v`，预期 FAIL。
- [ ] 实现 Haversine、硬约束和六项评分；由近到远/由远到近使用距离主排序键。
- [ ] 运行同一测试，预期 PASS。
- [ ] 提交：`git add backend/app/recommendations backend/tests/recommendations && git commit -m "feat: add deterministic recommendation engine"`。

### Task 2: AI 配置加密与适配器

**Files:**
- Create: `backend/app/ai/models.py`
- Create: `backend/app/ai/crypto.py`
- Create: `backend/app/ai/client.py`
- Create: `backend/app/ai/router.py`
- Create: `backend/tests/ai/test_profile.py`
- Create: `backend/tests/ai/test_client.py`

**Interfaces:**
- Produces: `TokenCipher.encrypt/decrypt`；`AIClient.rerank(request) -> RerankResult`；`GET/PUT/DELETE /ai-profile`；`POST /ai-profile/test`。

- [ ] 写测试：密文不含明文、掩码只暴露末四位、连接失败不覆盖旧配置、未知目的地 ID 被拒绝。
- [ ] 运行：`cd backend && python -m pytest tests/ai -v`，预期 FAIL。
- [ ] 使用 AES-GCM 和环境变量主密钥实现加密；用 httpx 调用可配置 OpenAI Chat Completions；Pydantic 严格校验三项候选结果。
- [ ] 运行同一测试，预期 PASS。
- [ ] 提交：`git add backend/app/ai backend/tests/ai backend/alembic && git commit -m "feat: add secure configurable AI adapter"`。

### Task 3: 推荐会话 API 与降级

**Files:**
- Create: `backend/app/recommendations/models.py`
- Create: `backend/app/recommendations/schemas.py`
- Create: `backend/app/recommendations/service.py`
- Create: `backend/app/recommendations/router.py`
- Create: `backend/tests/recommendations/test_api.py`

**Interfaces:**
- Produces: `POST /recommendations`；`POST /recommendations/{id}/next`；`GET /recommendations/history`。

- [ ] 写测试：默认返回三项；AI 超时仍返回规则前三；换一批排除已展示集合；候选不足时不突破硬约束。
- [ ] 运行：`cd backend && python -m pytest tests/recommendations/test_api.py -v`，预期 FAIL。
- [ ] 实现会话持久化、AI 重排、规则降级和稳定业务错误码。
- [ ] 运行同一测试，预期 PASS。
- [ ] 提交：`git add backend/app/recommendations backend/tests/recommendations backend/alembic && git commit -m "feat: expose resilient recommendation API"`。

### Task 4: 天气与历史气候适配器

**Files:**
- Create: `backend/app/weather/client.py`
- Create: `backend/app/weather/service.py`
- Create: `backend/app/weather/router.py`
- Create: `backend/tests/weather/test_service.py`

**Interfaces:**
- Produces: `WeatherService.get(destination, date_range) -> ForecastWeather | ClimateReference`；`GET /weather/{destination_id}`。

- [ ] 写测试：预报范围内返回 `forecast`；远期返回 `climate_reference`；Open-Meteo 错误回退 `local_climate`。
- [ ] 运行：`cd backend && python -m pytest tests/weather -v`，预期 FAIL。
- [ ] 实现 Open-Meteo forecast/archive 请求、缓存、来源和更新时间字段。
- [ ] 运行同一测试，预期 PASS。
- [ ] 提交：`git add backend/app/weather backend/tests/weather && git commit -m "feat: add weather and climate fallback"`。

### Task 5: 攻略生成与缓存

**Files:**
- Create: `backend/app/guides/models.py`
- Create: `backend/app/guides/schemas.py`
- Create: `backend/app/guides/service.py`
- Create: `backend/app/guides/router.py`
- Create: `backend/tests/guides/test_guides.py`

**Interfaces:**
- Produces: `GET /guides/{destination_id}`；`POST /guides/{destination_id}`。

- [ ] 写测试：结构包含交通、天气解读、行李、注意事项、玩法和分日行程；相同缓存键复用；数据版本变化使缓存失效；AI 失败返回基础详情。
- [ ] 运行：`cd backend && python -m pytest tests/guides -v`，预期 FAIL。
- [ ] 实现结构化生成、缓存键和按模块来源标记。
- [ ] 运行完整测试：`cd backend && python -m pytest -v`，预期全部 PASS。
- [ ] 提交：`git add backend/app/guides backend/tests/guides backend/alembic && git commit -m "feat: add cached destination guides"`。

