# Recommendation Distance Ranges Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users select one fixed distance interval from their selected origin and apply it as a hard recommendation filter.

**Architecture:** The mini-program stores one `distanceRange` key and maps it to optional minimum/maximum kilometre parameters. The backend adds `min_distance_km` to its request and domain query, and applies it with existing Haversine distances; paired min/max filters are left-closed/right-open, while max-only requests retain their previous inclusive behavior.

**Tech Stack:** WeChat native mini program, WXML/WXSS/JavaScript, FastAPI, Pydantic, SQLAlchemy, pytest, Node.js built-in test runner.

## Global Constraints

- Expose distance options only in the existing “更多” filter panel.
- Use one selected interval at a time; default and reset are “不限”.
- Map interval boundaries to `[min_distance_km, max_distance_km)`.
- Preserve compatibility for callers that send only the existing `max_distance_km` field.
- Do not alter AI ranking, cache, custom destination search, or route-distance behavior.

---

### Task 1: Backend Min/Max Distance Contract and Filter

**Files:**
- Modify: `backend/app/recommendations/schemas.py`
- Modify: `backend/app/recommendations/domain.py`
- Modify: `backend/app/recommendations/service.py`
- Modify: `backend/app/recommendations/scoring.py`
- Modify: `backend/tests/recommendations/test_scoring.py`
- Modify: `backend/tests/recommendations/test_api.py`

**Interfaces:**
- Consumes: `RecommendationCreate.min_distance_km: float | None` and existing `max_distance_km`.
- Produces: `RecommendationQuery(min_distance_km=..., max_distance_km=...)` and exact range filtering.

- [ ] **Step 1: Write failing scoring and API tests**

Add a candidate filter test using distances near 50km, 100km, 150km, and 200km. Assert a query with `min_distance_km=100` and `max_distance_km=200` keeps the 100km/150km candidates but excludes 50km and 200km. Add API coverage posting both parameters and asserting every response item satisfies `100 <= distance_km < 200`.

```python
assert [item.code for item in result] == ["at-lower-bound", "inside-range"]
assert all(100 <= item["distance_km"] < 200 for item in response.json()["items"])
```

Add schema validation cases for `min_distance_km=-1`, `min_distance_km=200, max_distance_km=200`, and `min_distance_km=300, max_distance_km=200`, expecting validation errors.

- [ ] **Step 2: Run backend tests and verify RED**

Run: `cd backend && .venv/bin/python -m pytest tests/recommendations/test_scoring.py tests/recommendations/test_api.py -v`

Expected: FAIL because `min_distance_km` is not accepted or propagated.

- [ ] **Step 3: Add request and domain fields**

Add `min_distance_km: float | None = Field(default=None, ge=0)` to `RecommendationCreate`; validate the paired bounds using a Pydantic model validator that raises when `min_distance_km >= max_distance_km`. Add the same field to `RecommendationQuery` and pass it in `service._query`.

- [ ] **Step 4: Apply left-closed/right-open filtering**

In `filter_candidates`, compute Haversine distance once when either bound is set. Apply:

```python
if query.min_distance_km is not None and distance < query.min_distance_km:
    continue
if query.max_distance_km is not None:
    if query.min_distance_km is not None and distance >= query.max_distance_km:
        continue
    if query.min_distance_km is None and distance > query.max_distance_km:
        continue
```

Continue excluding unverified coordinates whenever either bound is supplied.

- [ ] **Step 5: Run backend tests and verify GREEN**

Run: `cd backend && .venv/bin/python -m pytest tests/recommendations/test_scoring.py tests/recommendations/test_api.py -v`

Expected: PASS.

- [ ] **Step 6: Commit backend deliverable**

```bash
git add backend/app/recommendations backend/tests/recommendations/test_scoring.py backend/tests/recommendations/test_api.py
git commit -m "feat: filter recommendations by distance range"
```

---

### Task 2: Frontend Distance Range State and Request Mapping

**Files:**
- Modify: `miniprogram/miniprogram/pages/recommend/model.js`
- Modify: `miniprogram/tests/pages/recommend.test.js`

**Interfaces:**
- Consumes: `filters.distanceRange: string | null`.
- Produces: `DISTANCE_RANGES`, `setDistanceRange(filters, value)`, `filterOptions(filters).distance`, distance summary chips, and `buildRequest` min/max parameters.

- [ ] **Step 1: Write failing model tests**

Add a test that selects `100-200`, checks it is the only range, and expects:

```js
assert.equal(request.min_distance_km,100)
assert.equal(request.max_distance_km,200)
assert.deepEqual(filterSummary(filters).map(item=>item.label),['8月','100–200km'])
```

Assert `setDistanceRange(filters, null)` makes both request fields `undefined`, and `resetOptionalFilters` restores `distanceRange` to `null`.

- [ ] **Step 2: Run the model tests and verify RED**

Run: `cd miniprogram && npm test -- tests/pages/recommend.test.js`

Expected: FAIL because the model has no range constants, state setter, summary, or parameter mapping.

- [ ] **Step 3: Implement state, options, summary, and mapping**

Define a `DISTANCE_RANGES` array with fixed values:

```js
[
  {value:null,label:'不限'},
  {value:'under-100',label:'<100km',min:0,max:100},
  {value:'100-200',label:'100–200km',min:100,max:200},
  {value:'200-300',label:'200–300km',min:200,max:300},
  {value:'300-400',label:'300–400km',min:300,max:400},
  {value:'400-500',label:'400–500km',min:400,max:500},
  {value:'over-500',label:'>500km',min:500},
]
```

Store `distanceRange: null` in defaults and reset. `filterOptions` returns `distance` entries with a `selected` boolean. Add a single `{key:'distanceRange', value, label}` summary entry when non-null. `buildRequest` finds the selected range and writes only defined `min_distance_km` / `max_distance_km` fields.

- [ ] **Step 4: Run the model tests and verify GREEN**

Run: `cd miniprogram && npm test -- tests/pages/recommend.test.js`

Expected: PASS.

- [ ] **Step 5: Commit frontend model deliverable**

```bash
git add miniprogram/miniprogram/pages/recommend/model.js miniprogram/tests/pages/recommend.test.js
git commit -m "feat: add recommendation distance range state"
```

---

### Task 3: More-Panel Distance Controls

**Files:**
- Modify: `miniprogram/miniprogram/pages/recommend/index.js`
- Modify: `miniprogram/miniprogram/pages/recommend/index.wxml`
- Modify: `miniprogram/tests/pages/recommend-view.test.js`

**Interfaces:**
- Consumes: `DISTANCE_RANGES`, `setDistanceRange`, `filterOptions(filters).distance`, and current `filters.distanceRange`.
- Produces: one selectable distance range in the “更多” panel, a matching More count, and removable summary chip behavior.

- [ ] **Step 1: Write failing page-view and page-behavior tests**

Assert the WXML includes “距离所在地区”, `data-value="{{item.value}}"`, `bindtap="selectDistanceRange"`, and `filterOptions.distance`. Add a behavior test that invokes `selectDistanceRange` with `100-200` and verifies `refreshFilterView` receives a filter with `distanceRange: '100-200'`. Add a test that invokes `removeSummary` with `key: 'distanceRange'` and expects `distanceRange: null`.

- [ ] **Step 2: Run the frontend page tests and verify RED**

Run: `cd miniprogram && npm test -- tests/pages/recommend-view.test.js tests/pages/recommend.test.js`

Expected: FAIL because no distance controls or handlers exist.

- [ ] **Step 3: Render and wire the single-select controls**

Import `setDistanceRange` into `index.js`. Add:

```js
selectDistanceRange(event) {
  this.refreshFilterView(setDistanceRange(this.data.filters, event.currentTarget.dataset.value || null))
}
```

Extend `removeSummary` to set `distanceRange: null` when its key is `distanceRange`. In the “更多” WXML block, add the distance title and options before “最推荐”:

```xml
<text class="panel-title">距离所在地区</text>
<view class="option-grid">
  <view wx:for="{{filterOptions.distance}}" wx:key="label" class="option {{item.selected ? 'selected' : ''}}" data-value="{{item.value}}" bindtap="selectDistanceRange">{{item.label}}</view>
</view>
```

Update the More count expression to include `filters.distanceRange ? 1 : 0`, and replace the hint with `预算、天数与交通条件可继续在此扩展`.

- [ ] **Step 4: Run the frontend page tests and verify GREEN**

Run: `cd miniprogram && npm test -- tests/pages/recommend-view.test.js tests/pages/recommend.test.js`

Expected: PASS.

- [ ] **Step 5: Commit the UI deliverable**

```bash
git add miniprogram/miniprogram/pages/recommend/index.js miniprogram/miniprogram/pages/recommend/index.wxml miniprogram/tests/pages/recommend-view.test.js miniprogram/tests/pages/recommend.test.js
git commit -m "feat: add distance range recommendation filter"
```

---

### Task 4: Full Verification

**Files:**
- Verify only; no production files are added in this task.

**Interfaces:**
- Consumes: Tasks 1–3.
- Produces: fresh evidence that distance range filtering preserves existing recommendation behavior.

- [ ] **Step 1: Run full backend suite**

Run: `cd backend && .venv/bin/python -m pytest`

Expected: all backend tests PASS.

- [ ] **Step 2: Run full mini-program suite**

Run: `cd miniprogram && npm test`

Expected: all mini-program tests PASS.

- [ ] **Step 3: Inspect working tree scope**

Run: `git diff --check && git status --short && git log --oneline -6`

Expected: no whitespace errors; pre-existing `miniprogram/project.config.json`, `.superpowers/`, and SQLite WAL/SHM files remain uncommitted.
