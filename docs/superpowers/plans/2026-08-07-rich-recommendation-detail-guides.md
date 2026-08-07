# Rich Recommendation Cards and Destination Guides Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Match the HTML v4 recommendation and detail layouts while adding 1–7 day filtering, AI-generated food recommendations, and structured day-by-day itineraries.

**Architecture:** Extend the existing recommendation and guide boundaries instead of adding parallel APIs. Recommendation responses expose compact card metadata; the guide service owns validated food and itinerary structures, cache policy, AI generation, and rule fallback. The mini program keeps explicit filter state, passes a normalized detail context, and renders card/detail view models that never expose missing values to WXML.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy, httpx, pytest, native WeChat Mini Program JavaScript/WXML/WXSS, Vant Weapp, Node.js test runner, PackyAPI OpenAI-compatible Chat Completions.

## Global Constraints

- Use PackyAPI base URL `https://www.packyapi.ai/v1` and model `deepseek-v4-pro`; never log tokens or authorization headers.
- Expose day choices 1–7. An unselected filter sends and displays an internal default of 2 days without adding a summary chip.
- Food output contains 4–6 complete items with `name`, `description`, `area`, and `average_price`.
- Itinerary output contains exactly `days` entries with consecutive `day` values starting at 1 and non-empty `theme`, `morning`, `afternoon`, `evening`, `transport`, and `caution`.
- AI success is accepted only when the end-to-end recommendation response reports `source=ai`; rules fallback is not evidence of AI success.
- AI success caches guides for 30 days. Rules fallback caches for 1 hour. A temporary timeout or 5xx receives one retry after 500 milliseconds.
- Preserve the user's unrelated `miniprogram/project.config.json`, `.superpowers/` artifacts, and SQLite WAL files.
- All new behavior follows TDD: observe a focused RED failure before production changes, then verify focused and full GREEN suites.

---

### Task 1: PackyAPI Model Defaults and Structured Guide Contracts

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/.env.example`
- Modify: `backend/app/guides/schemas.py`
- Modify: `backend/tests/test_config.py`
- Modify: `backend/tests/guides/test_guides.py`
- Modify: `miniprogram/miniprogram/pages/ai-settings/index.js`
- Modify: `miniprogram/tests/pages/ai-settings.test.js`

**Interfaces:**
- Consumes: `TRAVEL_AI_MODEL`, guide generation inputs `month`, `days`, `origin_name`, and `preferences`.
- Produces: `FoodRecommendation`, `ItineraryDay`, and `GuidePayload(foods, itinerary)`; default model `deepseek-v4-pro` across system and personal configuration UI.

- [ ] **Step 1: Write failing configuration and schema tests**

Add literal assertions:

```python
def test_settings_default_to_available_deepseek_model() -> None:
    settings = Settings(_env_file=None)
    assert settings.ai_model == "deepseek-v4-pro"


def test_guide_payload_requires_complete_food_and_consecutive_days() -> None:
    payload = GuidePayload(
        transport=["高铁到杭州东站"], weather=["春季多阵雨"], packing=["雨伞"],
        cautions=["提前预约"], highlights=["苏堤"],
        foods=[
            FoodRecommendation(name="片儿川", description="笋片与雪菜汤面", area="湖滨", average_price="约25元/人"),
            FoodRecommendation(name="东坡肉", description="酥香软糯", area="河坊街", average_price="约60元/人"),
            FoodRecommendation(name="葱包桧", description="酥脆小吃", area="鼓楼", average_price="约10元/人"),
            FoodRecommendation(name="定胜糕", description="软糯米糕", area="南宋御街", average_price="约12元/人"),
        ],
        itinerary=[
            ItineraryDay(day=1, theme="西湖经典", morning="断桥", afternoon="苏堤", evening="湖滨", transport="步行和公交", caution="穿舒适鞋"),
            ItineraryDay(day=2, theme="人文老城", morning="灵隐寺", afternoon="河坊街", evening="南宋御街", transport="地铁和公交", caution="寺院保持安静"),
        ],
    )
    assert [day.day for day in payload.itinerary] == [1, 2]
    assert len(payload.foods) == 4
```

Also add invalid fixtures for 3 foods, duplicate day 1, and an empty evening. Add a Node test asserting the AI settings form starts with `deepseek-v4-pro`.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/pytest backend/tests/test_config.py backend/tests/guides/test_guides.py -q
cd miniprogram && node --test tests/pages/ai-settings.test.js
```

Expected: failures because current defaults use `deepseek-chat`, and `FoodRecommendation`/`ItineraryDay` do not exist.

- [ ] **Step 3: Implement guide value objects and validators**

Define:

```python
class FoodRecommendation(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=300)
    area: str = Field(min_length=1, max_length=120)
    average_price: str = Field(min_length=1, max_length=80)


class ItineraryDay(BaseModel):
    day: int = Field(ge=1, le=7)
    theme: str = Field(min_length=1, max_length=120)
    morning: str = Field(min_length=1, max_length=500)
    afternoon: str = Field(min_length=1, max_length=500)
    evening: str = Field(min_length=1, max_length=500)
    transport: str = Field(min_length=1, max_length=300)
    caution: str = Field(min_length=1, max_length=300)
```

Set `foods: list[FoodRecommendation] = Field(min_length=4, max_length=6)` and `itinerary: list[ItineraryDay] = Field(min_length=1, max_length=7)`. Add a model validator rejecting non-consecutive itinerary days. Change backend, `.env.example`, and mini-program initial model defaults to `deepseek-v4-pro`.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run the Step 2 commands. Expected: all focused tests pass.

- [ ] **Step 5: Commit the contract batch**

```bash
git add backend/app/core/config.py backend/.env.example backend/app/guides/schemas.py backend/tests/test_config.py backend/tests/guides/test_guides.py miniprogram/miniprogram/pages/ai-settings/index.js miniprogram/tests/pages/ai-settings.test.js
git commit -m "feat: define structured food and itinerary guides"
```

---

### Task 2: Guide Generation, Cache Compatibility, Retry, and AI API Path

**Files:**
- Modify: `backend/app/ai/client.py`
- Modify: `backend/app/guides/service.py`
- Modify: `backend/app/guides/router.py`
- Modify: `backend/tests/ai/test_client.py`
- Modify: `backend/tests/guides/test_guides.py`
- Create: `backend/tests/guides/test_api.py`

**Interfaces:**
- Consumes: structured contracts from Task 1 and `GuideGenerationRequest(days: 1..7)`.
- Produces: `GuideService.generate(...) -> GuideResponse` with validated AI/rules payload; `POST /guides/{destination_id}` as the single detail-generation path.

- [ ] **Step 1: Write failing service and API tests**

Add tests proving:

```python
@pytest.mark.asyncio
async def test_rule_guide_matches_requested_days_and_food_shape(db_session):
    result = await GuideService().generate(
        db_session, seed_destination(db_session),
        GuideGenerationRequest(month=4, days=3, origin_name="上海"),
    )
    assert [item.day for item in result.payload.itinerary] == [1, 2, 3]
    assert len(result.payload.foods) == 4
    assert all(item.morning != item.afternoon for item in result.payload.itinerary)


@pytest.mark.asyncio
async def test_old_string_itinerary_cache_is_treated_as_cache_miss(db_session):
    # Insert a non-expired GuideCache whose payload has itinerary=["第一天"]
    # Generate with a valid fake AI generator.
    assert result.cache_hit is False
    assert result.source == "ai"
```

Add tests that an initial `httpx.ReadTimeout` is retried once, a 401 is not retried, a 503 body with `error.code=model_not_found` is not retried, AI cache expiration is approximately 30 days, rule cache expiration is approximately 1 hour, and authenticated `POST /guides/{id}` returns structured foods/days. Add a generator fixture that returns two days for a three-day request and assert the service rejects it and returns a three-day rules payload. The production change each test protects is the retry branch, cache validation branch, requested-day validation branch, or API dependency path—not the fake itself.

- [ ] **Step 2: Run guide and AI tests and verify RED**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/pytest backend/tests/ai/test_client.py backend/tests/guides -q
```

Expected: failures from string itinerary fixtures, missing foods, no cache payload validation, and no retry behavior.

- [ ] **Step 3: Implement retry without leaking secrets**

Add a private request loop in `AIClient._post`: two total attempts only for `httpx.TimeoutException` and HTTP 500/502/503/504, with `await asyncio.sleep(0.5)` between attempts. Before retrying a 503, inspect the JSON error code; immediately raise when it equals `model_not_found`, because a retry cannot change an invalid group/model mapping. Immediately raise all 4xx errors. Do not store or format the authorization header in raised custom messages.

- [ ] **Step 4: Implement structured AI prompt and rules generator**

Update the guide system prompt to explicitly require the seven top-level arrays and exact nested field names. Append `destination.name`, `summary`, `categories`, `climate`, `transport_modes`, and requested `days` to the user payload.

Build four deterministic food suggestions from destination category/name seeds and build one `ItineraryDay` per requested day. Rotate highlights and categories so morning, afternoon, and evening fields are not identical. Use `destination.min_budget/max_budget` only for overview metadata, not invented restaurant prices.

After AI payload validation, explicitly require `len(payload.itinerary) == request.days`; treat a mismatched length as an invalid AI response and use the correctly sized rules payload.

- [ ] **Step 5: Validate cached payloads and apply source-specific expiry**

Before returning a cache hit, run `GuidePayload.model_validate(cached.payload)`. Catch `ValidationError` and regenerate instead of returning 500. Store AI payloads with `expires_at=now+30 days`; store rule payloads with `expires_at=now+1 hour`.

- [ ] **Step 6: Run focused tests and verify GREEN**

Run the Step 2 command. Expected: all AI/guide tests pass.

- [ ] **Step 7: Commit the guide generation batch**

```bash
git add backend/app/ai/client.py backend/app/guides backend/tests/ai/test_client.py backend/tests/guides
git commit -m "feat: generate structured AI destination guides"
```

---

### Task 3: Recommendation Days and Compact Card Metadata

**Files:**
- Modify: `backend/app/recommendations/schemas.py`
- Modify: `backend/app/recommendations/service.py`
- Modify: `backend/tests/recommendations/test_api.py`
- Modify: `miniprogram/miniprogram/pages/recommend/model.js`
- Modify: `miniprogram/miniprogram/pages/recommend/index.js`
- Modify: `miniprogram/miniprogram/pages/recommend/index.wxml`
- Modify: `miniprogram/tests/pages/recommend.test.js`
- Modify: `miniprogram/tests/pages/recommend-view.test.js`

**Interfaces:**
- Consumes: filter state and destination fields (`transport_modes`, `climate`, `min_days`, `max_days`, categories/tags).
- Produces: recommendation card metadata `transport`, `weather`, `suggested_days`, `tags`; detail route context `{id, month, days, originName, preferences}`.

- [ ] **Step 1: Write failing backend metadata tests**

Assert a recommendation item literal:

```python
item = response.json()["items"][0]
assert item["transport"] == "高铁 / 地铁"
assert item["weather"] == "春秋温和，雨水较多"
assert item["suggested_days"] == "2–3天"
assert item["tags"] == ["人文", "景色", "旺季", "人多"]
```

Also assert a request with omitted `available_days` defaults to 2 and participates in filtering. Change `RecommendationCreate.available_days` from `None` to `Field(default=2, gt=0, le=7)` so direct API consumers get the same default as the mini program.

- [ ] **Step 2: Write failing mini-program day filter tests**

Add tests that `defaultFilters().days is null`, `buildRequest(...).available_days === 2`, selecting day 5 is single-choice, toggling 5 again clears it, filter summary contains `5天` only when explicit, and `openDetail` navigates to an encoded URL containing the resolved days/origin/month/preferences.

- [ ] **Step 3: Run recommendation tests and verify RED**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/pytest backend/tests/recommendations -q
cd miniprogram && node --test tests/pages/recommend.test.js tests/pages/recommend-view.test.js
```

Expected: missing metadata fields and missing day filter rendering/navigation context.

- [ ] **Step 4: Implement recommendation metadata**

Extend `RecommendationItem` with `transport: str`, `weather: str`, `suggested_days: str`, and `tags: list[str]`. In `_response_items`, join transport modes with `" / "`, read `climate.summary`, format `min_days/max_days` as `2天` or `2–3天`, and deduplicate categories + season tags + crowd tags while preserving order.

- [ ] **Step 5: Implement explicit day filter and detail navigation context**

Add `dayOptions = [1,2,3,4,5,6,7]`, `selectDays(event)` with single-choice toggle semantics, render the chips at the top of the “more” panel, include explicit days in `filterSummary`, and set `available_days: filters.days || 2` in every recommendation request.

Build the detail URL using `encodeURIComponent` for origin/preferences:

```js
const days = this.data.filters.days || 2
const preferences = encodeURIComponent(JSON.stringify([
  ...this.data.filters.preferences,
  ...this.data.filters.categories
]))
wx.navigateTo({
  url: `/pages/destination-detail/index?id=${id}&month=${this.data.filters.month}&days=${days}&origin_name=${encodeURIComponent(this.data.origin.name)}&preferences=${preferences}`
})
```

- [ ] **Step 6: Run focused tests and verify GREEN**

Run the Step 3 commands. Expected: all recommendation tests pass.

- [ ] **Step 7: Commit recommendation context batch**

```bash
git add backend/app/recommendations backend/tests/recommendations miniprogram/miniprogram/pages/recommend miniprogram/tests/pages/recommend.test.js miniprogram/tests/pages/recommend-view.test.js
git commit -m "feat: add trip days and recommendation card metadata"
```

---

### Task 4: HTML-v4 Recommendation Card and Button Hierarchy

**Files:**
- Modify: `miniprogram/miniprogram/components/recommend-card/model.js`
- Modify: `miniprogram/miniprogram/components/recommend-card/index.js`
- Modify: `miniprogram/miniprogram/components/recommend-card/index.wxml`
- Modify: `miniprogram/miniprogram/components/recommend-card/index.wxss`
- Modify: `miniprogram/tests/components/recommend-card.test.js`

**Interfaces:**
- Consumes: Task 3 `RecommendationItem` metadata.
- Produces: `toCardView(item)` and events `open({id})`, `status({destinationId,status})` with main “查看攻略” action and lightweight status controls.

- [ ] **Step 1: Write failing card view and interaction tests**

Use a complete literal item and assert:

```js
assert.equal(view.transport, '高铁 / 地铁')
assert.equal(view.weather, '春秋温和，雨水较多')
assert.equal(view.suggestedDays, '2–3天')
assert.deepEqual(view.tags.map(item => item.label), ['人文', '景色', '旺季', '人多'])
```

Exercise `open` and `setStatus` separately and assert each emits only its own event. Extend the WXML/WXSS view test to require `查看攻略`, lightweight status classes, v4 color tokens, and no default button pseudo-border.

- [ ] **Step 2: Run card tests and verify RED**

Run:

```bash
cd miniprogram && node --test tests/components/recommend-card.test.js
```

Expected: metadata and “查看攻略” assertions fail against the old card.

- [ ] **Step 3: Implement the v4 card view model and markup**

Map backend metadata directly with safe string fallbacks. Render a compact top row, a green rounded “查看攻略 ›” action, a three-column `怎么去 / 天气 / 建议天数` grid, and three non-button or reset-style lightweight status actions using `catchtap`.

- [ ] **Step 4: Implement card styles and motion**

Use `#1bb28a`, `#159c77`, `#ff9f43`, 28–32rpx radii, subtle shadow, gradient thumbnail, clamped metadata, `transform:scale(.95)` press feedback, and staggerable `card-in` animation. Ensure `.action-button::after{border:0}` for any remaining WeChat button element.

- [ ] **Step 5: Run focused card tests and compile WXSS**

Run:

```bash
cd miniprogram && node --test tests/components/recommend-card.test.js
/Applications/wechatwebdevtools.app/Contents/Resources/app.asar.unpacked/node_modules/wcc-exec/wcsc -lc miniprogram/miniprogram/components/recommend-card/index.wxss >/dev/null
```

Expected: tests pass and compiler exits 0.

- [ ] **Step 6: Commit the card visual batch**

```bash
git add miniprogram/miniprogram/components/recommend-card miniprogram/tests/components/recommend-card.test.js
git commit -m "feat: match recommendation cards to v4 design"
```

---

### Task 5: Rich Destination Detail View Model and Page

**Files:**
- Modify: `miniprogram/miniprogram/pages/destination-detail/model.js`
- Modify: `miniprogram/miniprogram/pages/destination-detail/index.js`
- Modify: `miniprogram/miniprogram/pages/destination-detail/index.wxml`
- Modify: `miniprogram/miniprogram/pages/destination-detail/index.wxss`
- Modify: `miniprogram/miniprogram/pages/destination-detail/index.json`
- Modify: `miniprogram/tests/pages/destination-detail.test.js`
- Create: `miniprogram/tests/pages/destination-detail-view.test.js`

**Interfaces:**
- Consumes: destination, weather, structured `GuideResponse`, and encoded detail query from Task 3.
- Produces: `buildDetailView(destination, weather, guide, context)` with safe hero/meta/transport/weather/packing/cautions/highlights/foods/itinerary sections.

- [ ] **Step 1: Write failing detail model tests**

Create complete and sparse fixtures. Assert that a 3-day payload yields exactly three view days, food values never contain `undefined`, overview days reflect 3, source label is `AI 攻略`, and sparse rule data still produces safe display strings.

```js
const view = buildDetailView(destination, weather, guide, { days: 3 })
assert.equal(view.daysText, '3天')
assert.equal(view.itinerary.length, 3)
assert.equal(view.foods[0].averagePrice, '约25元/人')
assert.equal(view.guideSourceLabel, 'AI 攻略')
assert.ok(!JSON.stringify(view).includes('undefined'))
```

- [ ] **Step 2: Write failing page loading tests**

Capture `Page(...)`, invoke `onLoad` with encoded month/days/origin/preferences, and assert the guide request is:

```js
{
  method: 'POST',
  path: '/guides/7',
  data: { month: 8, days: 3, origin_name: '上海', preferences: ['景色'] }
}
```

Assert destination/weather requests run, `loading` finishes on success, and a guide failure sets a retryable guide error without discarding destination/weather.

- [ ] **Step 3: Run detail tests and verify RED**

Run:

```bash
cd miniprogram && node --test tests/pages/destination-detail.test.js tests/pages/destination-detail-view.test.js
```

Expected: missing view model, hard-coded GET guide request, and incomplete WXML.

- [ ] **Step 4: Implement query parsing and parallel page loading**

Parse integer month/days with safe defaults and bounds, decode origin, parse preferences JSON with an empty-array fallback, then load destination, weather, and POST guide data. Keep independent `loadingBase`, `loadingWeather`, and `loadingGuide` flags plus `guideError`. Add `retryGuide()` using the same normalized context.

- [ ] **Step 5: Implement the detail view model**

Derive hero gradient/emoji deterministically, best season from `suitable_months`, budget from `min_budget/max_budget`, rating from `quality_score`, weather cards from forecast periods, and safe copies of every guide array. Map food snake_case `average_price` to `averagePrice`.

- [ ] **Step 6: Build the v4 WXML structure**

Render: gradient hero; four-cell meta row; transport timeline; horizontal weather deck; packing chips; numbered cautions; highlight chips; 4–6 food cards with a price-reference note; day cards with morning/afternoon/evening/transport/caution; source label; quote; fixed safe-area action bar. Use skeleton blocks matching section heights while loading.

- [ ] **Step 7: Build the v4 WXSS and optimized actions**

Port the HTML design tokens to rpx, including white section cards, 28–32rpx radii, green section bars, weather horizontal scroll, orange warnings, timeline dots, food two-column layout that collapses to one column when needed, and bottom safe area. Use the selected “main action + lightweight status” button hierarchy and remove all default WeChat button borders.

- [ ] **Step 8: Run detail tests and official WXSS compilation**

Run:

```bash
cd miniprogram && node --test tests/pages/destination-detail.test.js tests/pages/destination-detail-view.test.js
/Applications/wechatwebdevtools.app/Contents/Resources/app.asar.unpacked/node_modules/wcc-exec/wcsc -lc miniprogram/miniprogram/pages/destination-detail/index.wxss >/dev/null
```

Expected: tests pass and compiler exits 0.

- [ ] **Step 9: Commit the detail visual batch**

```bash
git add miniprogram/miniprogram/pages/destination-detail miniprogram/tests/pages/destination-detail.test.js miniprogram/tests/pages/destination-detail-view.test.js
git commit -m "feat: add rich food and daily itinerary detail page"
```

---

### Task 6: End-to-End AI and Full Visual Verification

**Files:**
- Verify: implementation and test files from Tasks 1–5.
- Do not modify: `miniprogram/project.config.json`, `.superpowers/`, or secret `.env` values unless the user separately edits their ignored local configuration.

**Interfaces:**
- Consumes: all prior task outputs and ignored local `.env` with `deepseek-v4-pro`.
- Produces: verified real `source=ai` recommendation, structured AI guide, compilable WXSS, and clean committed feature branch.

- [ ] **Step 1: Run full automated suites**

Run:

```bash
cd miniprogram && npm test
PYTHONPATH=backend backend/.venv/bin/pytest backend/tests -q
sh scripts/tests/local-service-scripts.sh
```

Expected: zero failures.

- [ ] **Step 2: Compile every WXSS file with the WeChat compiler**

Run:

```bash
rg --files miniprogram/miniprogram -g '*.wxss' | while IFS= read -r file; do
  /Applications/wechatwebdevtools.app/Contents/Resources/app.asar.unpacked/node_modules/wcc-exec/wcsc -lc "$file" >/dev/null || exit 1
done
```

Expected: exit 0 with no compiler error.

- [ ] **Step 3: Restart local backend and run sanitized end-to-end AI probes**

Restart using `./scripts/stop-local.sh` then `./scripts/start-local.sh`. Authenticate with `/auth/dev`, post an August recommendation with `available_days=3`, and post a 3-day guide for the first returned destination. Print only:

```json
{
  "recommendation_status": 201,
  "recommendation_source": "ai",
  "recommendation_items": 3,
  "guide_status": 200,
  "guide_source": "ai",
  "food_count": 4,
  "itinerary_days": [1, 2, 3]
}
```

Never print the bearer token, authorization header, or raw third-party response.

- [ ] **Step 4: Verify the original UI symptoms in WeChat Developer Tools**

Compile the mini program, choose a location, choose 3 days, run one-click recommendation, confirm styled cards show “查看攻略”, open detail, and confirm all sections render with three daily cards and 4–6 foods. Check iPhone narrow viewport and bottom safe area. If CLI automation cannot inspect the simulator visually, provide these exact manual checks to the user without claiming them complete.

- [ ] **Step 5: Run repository hygiene checks**

Run:

```bash
git diff --check
git status --short
```

Expected: no whitespace errors; only known user-owned `miniprogram/project.config.json`, `.superpowers/`, or SQLite WAL artifacts may remain outside committed feature changes.

- [ ] **Step 6: Commit any verification-only fixes**

Stage only files actually changed by a verified defect fix. Do not create an empty commit.
