# Recommendation, Profile UI, and Location Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore the recommendation and profile pages to the approved HTML v4 design while preserving real APIs, and make current/manual origin selection reliable in WeChat Developer Tools.

**Architecture:** Keep page state and request shaping in focused CommonJS model modules, while native Page/Component files coordinate WeChat APIs and rendering. Extend the existing Vant Weapp/native WXML implementation rather than embedding the HTML mockup. Location permission declarations live in `app.json`; runtime location behavior remains isolated in `services/location.js` and `origin-picker`.

**Tech Stack:** WeChat native mini program, JavaScript CommonJS, WXML/WXSS, Vant Weapp 1.11.7, Node.js built-in test runner, FastAPI API already present.

## Global Constraints

- Match `travel-miniprogram-mockup.html` v4 for the recommendation and profile page hierarchy, color, spacing, cards, and motion.
- Preserve the real recommendation, map summary, visit record, AI settings, avatar, and navigation behaviors.
- Main color is `#1BB28A`; dark main is `#159C77`; soft main is `#E6F7F2`; accent is `#FF9F43`; page background is `#F4F5F7`.
- Do not add WeChat AppSecret, system AI token, Amap server secret, or other secrets to the mini program.
- Local dev auth remains explicitly enabled only by the local startup flow; backend production default remains disabled.
- Do not modify the map page or destination-detail visual design in this batch.
- Use tests first for each behavior change and preserve WeChat WXSS compiler compatibility.

---

## File Structure

- `miniprogram/miniprogram/app.json`: declares location privacy usage and registers page-level platform configuration.
- `miniprogram/miniprogram/services/location.js`: classifies location failures, resolves current/saved origins, requests settings authorization, and selects a manual origin.
- `miniprogram/miniprogram/components/origin-picker/*`: renders the HTML-v4-style origin row and coordinates retry/manual selection UI.
- `miniprogram/miniprogram/pages/recommend/model.js`: owns filter constants, immutable filter transitions, summaries, and backend request shaping.
- `miniprogram/miniprogram/pages/recommend/index.{js,wxml,wxss,json}`: owns recommendation-page orchestration and HTML-v4 page rendering.
- `miniprogram/miniprogram/components/recommend-card/*`: renders result cards and emits open/status events without owning API state.
- `miniprogram/miniprogram/pages/me/model.js`: maps map-summary API data into the three profile counters and menu definitions.
- `miniprogram/miniprogram/pages/me/index.{js,wxml,wxss,json}`: owns avatar, counters, navigation, and HTML-v4 profile rendering.
- `miniprogram/tests/**`: Node tests for behavior, configuration, WXML structure, and WXSS compatibility.

---

### Task 1: Reliable Origin Permission and Selection

**Files:**
- Modify: `miniprogram/miniprogram/app.json`
- Modify: `miniprogram/miniprogram/services/location.js`
- Modify: `miniprogram/miniprogram/components/origin-picker/index.js`
- Modify: `miniprogram/miniprogram/components/origin-picker/index.wxml`
- Modify: `miniprogram/miniprogram/components/origin-picker/index.wxss`
- Modify: `miniprogram/tests/services/location.test.js`
- Modify: `miniprogram/tests/components/origin-picker.test.js`
- Create: `miniprogram/tests/config/location-permission.test.js`

**Interfaces:**
- Consumes: WeChat `getLocation`, `chooseLocation`, `getSetting`, `openSetting`, `showModal`, and storage APIs.
- Produces: `classifyLocationFailure(error): 'cancel'|'permission'|'unavailable'`; `createLocationService(wxApi).resolveOrigin()`; `chooseManualOrigin()`; `requestLocationPermission()`; component event `change` with `{type,name,latitude,longitude}`.

- [ ] **Step 1: Write failing permission and failure-classification tests**

```js
test('app declares both location private APIs', () => {
  const app = readJson('miniprogram/app.json')
  assert.match(app.permission['scope.userLocation'].desc, /距离|出发地/)
  assert.deepEqual(new Set(app.requiredPrivateInfos), new Set(['getLocation', 'chooseLocation']))
})

test('location failures distinguish cancellation from permission denial', () => {
  assert.equal(classifyLocationFailure({ errMsg: 'chooseLocation:fail cancel' }), 'cancel')
  assert.equal(classifyLocationFailure({ errMsg: 'getLocation:fail auth deny' }), 'permission')
})
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `cd miniprogram && node --test tests/config/location-permission.test.js tests/services/location.test.js tests/components/origin-picker.test.js`

Expected: FAIL because privacy declarations and `classifyLocationFailure` are missing and denied permission is still swallowed/generic.

- [ ] **Step 3: Add declarations and implement classified recovery**

Add to `app.json`:

```json
"permission": {
  "scope.userLocation": {
    "desc": "你的位置将用于选择出发地和计算旅行距离"
  }
},
"requiredPrivateInfos": ["getLocation", "chooseLocation"]
```

Implement failure classification by matching `cancel`, `auth deny`, `authorize`, and `permission`; expose permission recovery as a Promise around `wx.openSetting`. In the component, cancellation clears pending recommendation without alarming copy, permission denial opens a modal with a settings action, and other failures show `暂时无法选择地点`.

- [ ] **Step 4: Render the HTML-v4 origin row**

Use one tappable row with location icon, `所在地区：`, bold current name or `请选择`, and a right-aligned `切换定位` pill. Ensure the tappable region covers the entire row and the component emits a `cancel` event when a pending recommendation must be stopped.

- [ ] **Step 5: Run focused tests and verify GREEN**

Run: `cd miniprogram && node --test tests/config/location-permission.test.js tests/services/location.test.js tests/components/origin-picker.test.js`

Expected: all focused tests PASS.

- [ ] **Step 6: Commit the location batch**

```bash
git add miniprogram/miniprogram/app.json miniprogram/miniprogram/services/location.js miniprogram/miniprogram/components/origin-picker miniprogram/tests/config/location-permission.test.js miniprogram/tests/services/location.test.js miniprogram/tests/components/origin-picker.test.js
git commit -m "fix: restore reliable origin selection"
```

---

### Task 2: Recommendation Filter State and HTML-v4 Page Shell

**Files:**
- Modify: `miniprogram/miniprogram/pages/recommend/model.js`
- Modify: `miniprogram/miniprogram/pages/recommend/index.js`
- Modify: `miniprogram/miniprogram/pages/recommend/index.wxml`
- Modify: `miniprogram/miniprogram/pages/recommend/index.wxss`
- Modify: `miniprogram/miniprogram/pages/recommend/index.json`
- Modify: `miniprogram/tests/pages/recommend.test.js`
- Create: `miniprogram/tests/pages/recommend-view.test.js`

**Interfaces:**
- Consumes: origin component `change`/`cancel`, existing API client, existing `loadingStages` and backend `/recommendations` contract.
- Produces: `FILTER_GROUPS`; `toggleFilter(filters, group, value)`; `setMonth(filters, month)`; `resetOptionalFilters(filters)`; `filterSummary(filters)`; Page methods `togglePanel`, `selectMonth`, `toggleOption`, `removeSummary`, `resetFilters`, `closeFilters`.

- [ ] **Step 1: Write failing filter-model and view-structure tests**

```js
test('optional recommendation filters toggle independently', () => {
  let filters = defaultFilters(new Date('2026-08-07'))
  filters = toggleFilter(filters, 'categories', '山川')
  filters = toggleFilter(filters, 'categories', '古城')
  assert.deepEqual(filters.categories, ['山川', '古城'])
  assert.deepEqual(filterSummary(filters).map(x => x.label), ['8月', '山川', '古城'])
})

test('recommend page contains v4 hero, five filter triggers, summary, CTA, and results', () => {
  const wxml = read('miniprogram/pages/recommend/index.wxml')
  for (const marker of ['recommend-hero', 'filter-month', 'filter-season', 'filter-crowd', 'filter-pref', 'filter-more', 'filter-summary', 'recommend-cta', 'recommend-results']) assert.match(wxml, new RegExp(marker))
})
```

- [ ] **Step 2: Run focused tests and verify RED**

Run: `cd miniprogram && node --test tests/pages/recommend.test.js tests/pages/recommend-view.test.js`

Expected: FAIL because filter transitions and the v4 structure do not exist.

- [ ] **Step 3: Implement immutable filter transitions**

Define exact options:

```js
const FILTER_GROUPS = {
  season: ['旺季', '淡季'],
  crowd: ['人少', '人多'],
  preferences: ['人文', '景色'],
  categories: ['海岛', '古城', '山川', '草原', '城市', '沙漠']
}
```

Map both `preferences` (`人文`, `景色`) and destination `categories` into the existing `preferred_categories` request array without changing the backend API. Summary entries must include `{key,value,label}` so each chip can be removed deterministically.

- [ ] **Step 4: Implement the HTML-v4 page shell**

Build the hero, five-column filter bar, one active panel below it, dismissible mask, summary chips, gradient CTA, loading skeleton, fallback notice, and results heading. Keep Vant only where it improves native behavior; implement the filter panel directly in WXML to control exact HTML-v4 spacing.

- [ ] **Step 5: Wire page interactions and origin cancellation**

Keep `pendingRecommend`; after a successful origin selection, continue automatically. On origin `cancel`, set `pendingRecommend:false`. While loading, disable the CTA and show a spinner plus the current loading-stage copy. Preserve `authReady`, error toast, session ID, fallback source, and next-batch behavior.

- [ ] **Step 6: Run focused tests and verify GREEN**

Run: `cd miniprogram && node --test tests/pages/recommend.test.js tests/pages/recommend-view.test.js`

Expected: all focused tests PASS.

- [ ] **Step 7: Commit the recommendation shell batch**

```bash
git add miniprogram/miniprogram/pages/recommend miniprogram/tests/pages/recommend.test.js miniprogram/tests/pages/recommend-view.test.js
git commit -m "feat: align recommendation filters with v4 design"
```

---

### Task 3: HTML-v4 Recommendation Cards and Status Actions

**Files:**
- Modify: `miniprogram/miniprogram/components/recommend-card/index.js`
- Modify: `miniprogram/miniprogram/components/recommend-card/index.wxml`
- Modify: `miniprogram/miniprogram/components/recommend-card/index.wxss`
- Modify: `miniprogram/miniprogram/components/recommend-card/index.json`
- Create: `miniprogram/miniprogram/components/recommend-card/model.js`
- Create: `miniprogram/tests/components/recommend-card.test.js`
- Modify: `miniprogram/miniprogram/pages/recommend/index.js`

**Interfaces:**
- Consumes: recommendation response item; `PUT /destination-statuses/{destinationId}`; Page handler `onCardStatus`.
- Produces: `toCardView(item)` returning stable `{destinationId,code,name,emoji,ratingText,tags,badge,transport,weather,note,distanceText}`; component events `open` and `status` with `{destinationId,status}`.

- [ ] **Step 1: Write failing card-view and event tests**

```js
test('card view never renders undefined for missing guide fields', () => {
  const view = toCardView({ destination_id: 7, code: 'x', name: '桂林', score: 87 })
  assert.equal(view.transport, '查看详情')
  assert.equal(view.weather, '暂无天气数据')
  assert.equal(view.note, '出发前查看当地提示')
  assert.ok(!JSON.stringify(view).includes('undefined'))
})
```

Add a component-method test that confirms a status-button tap emits `status` and does not emit `open`.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `cd miniprogram && node --test tests/components/recommend-card.test.js`

Expected: FAIL because `model.js` and status events are missing.

- [ ] **Step 3: Implement the normalized card view**

Use backend fields when present and deterministic placeholders otherwise. Convert numeric score to a five-star visual label, classify warning tags (`淡季`, `人多`), and derive a stable emoji/gradient from category or code without remote image dependencies.

- [ ] **Step 4: Implement HTML-v4 card markup and styling**

Render thumbnail, title, stars, tags, best badge, three-column details, and three status buttons. Use `catchtap` on buttons to prevent card navigation. Emit open only from the card body. Apply stagger-friendly fade-up classes and selected-state colors matching v4.

- [ ] **Step 5: Persist status from the recommendation page**

Handle `status` by calling:

```js
api.request({
  method: 'PUT',
  path: `/destination-statuses/${destinationId}`,
  data: { status }
})
```

The three v4 buttons send exact backend enum values: `visited`, `want`, and `avoid`. On success update only the matching card status and show `已保存`; on `REVISIT_REQUIRES_VISIT`, preserve the existing visit-record guidance; on other failures show the API error message.

- [ ] **Step 6: Run focused and recommendation tests**

Run: `cd miniprogram && node --test tests/components/recommend-card.test.js tests/pages/recommend.test.js tests/pages/recommend-view.test.js`

Expected: all tests PASS.

- [ ] **Step 7: Commit the card batch**

```bash
git add miniprogram/miniprogram/components/recommend-card miniprogram/miniprogram/pages/recommend/index.js miniprogram/tests/components/recommend-card.test.js
git commit -m "feat: restore v4 recommendation cards"
```

---

### Task 4: HTML-v4 Profile Page with Real Counters and Navigation

**Files:**
- Create: `miniprogram/miniprogram/pages/me/model.js`
- Modify: `miniprogram/miniprogram/pages/me/index.js`
- Modify: `miniprogram/miniprogram/pages/me/index.wxml`
- Modify: `miniprogram/miniprogram/pages/me/index.wxss`
- Modify: `miniprogram/miniprogram/pages/me/index.json`
- Create: `miniprogram/tests/pages/me.test.js`
- Create: `miniprogram/tests/pages/me-view.test.js`

**Interfaces:**
- Consumes: `GET /map/summary`, `authReady`, `chooseAvatar`, `switchTab`, and `navigateTo`.
- Produces: `toProfileStats(summary): {visited,want,no}`; menu actions `openMap`, `openVisits`, `openAI`, `showComingSoon`; profile view state `{avatar,name,subtitle,stats,loading}`.

- [ ] **Step 1: Write failing stats and view-structure tests**

```js
test('profile counters aggregate map summary statuses safely', () => {
  const summary = { items: [
    { status_counts: { visited: 2, revisit: 1, want: 3, avoid: 1 } },
    { status_counts: { visited: 1, want: 2, avoid: 1 } }
  ] }
  assert.deepEqual(toProfileStats(summary), { visited: 4, want: 5, avoid: 2 })
  assert.deepEqual(toProfileStats({}), { visited: 0, want: 0, avoid: 0 })
})
```

Assert the WXML contains `me-hero`, `me-stats`, all three counter labels, `我的旅行地图`, `到访记录`, `AI 设置`, and both `待扩展` items.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `cd miniprogram && node --test tests/pages/me.test.js tests/pages/me-view.test.js`

Expected: FAIL because the model and v4 structure are absent.

- [ ] **Step 3: Implement stats loading and navigation**

On `onShow`, await `authReady`, request `/map/summary`, aggregate every item's `status_counts`; count both `visited` and `revisit` under the displayed `去过` number, map `want` to `想去`, and map `avoid` to `不想去`. Fall back to zeros on failure without blocking menus. Use exact navigation:

```js
openMap() { wx.switchTab({ url: '/pages/map/index' }) }
openVisits() { wx.navigateTo({ url: '/pages/visit-records/index' }) }
openAI() { wx.navigateTo({ url: '/pages/ai-settings/index' }) }
showComingSoon() { wx.showToast({ title: '敬请期待', icon: 'none' }) }
```

- [ ] **Step 4: Implement the HTML-v4 profile view**

Build the gradient avatar hero, three-column counter card, two white menu groups, emoji/icon columns, arrows, divider lines, and `待扩展` pills. Preserve `chooseAvatar`; use the default person silhouette when no avatar exists.

- [ ] **Step 5: Run focused tests and verify GREEN**

Run: `cd miniprogram && node --test tests/pages/me.test.js tests/pages/me-view.test.js`

Expected: all tests PASS.

- [ ] **Step 6: Commit the profile batch**

```bash
git add miniprogram/miniprogram/pages/me miniprogram/tests/pages/me.test.js miniprogram/tests/pages/me-view.test.js
git commit -m "feat: align profile page with v4 design"
```

---

### Task 5: Full Verification and Developer-Tool Handoff

**Files:**
- Modify only if verification exposes a defect in files already in scope.
- Preserve the user's unrelated `miniprogram/project.config.json` newline-only working-tree change.

**Interfaces:**
- Consumes: all deliverables from Tasks 1-4.
- Produces: verified mini-program package and exact WeChat Developer Tools validation steps.

- [ ] **Step 1: Run all front-end tests**

Run: `cd miniprogram && npm test`

Expected: zero failures.

- [ ] **Step 2: Run all backend tests**

Run: `PYTHONPATH=backend backend/.venv/bin/pytest backend/tests -q`

Expected: zero failures.

- [ ] **Step 3: Run repository hygiene checks**

Run: `git diff --check`

Expected: no whitespace errors in scoped changes. Do not stage or overwrite `miniprogram/project.config.json` unless the user explicitly asks.

- [ ] **Step 4: Compile-check custom WXSS with the installed WeChat compiler**

Resolve the installed developer-tools compiler path and run the same `wcsc`/`wcsc-exec` syntax already proven for all custom `.wxss` files. Expected: exit 0 and no unsupported-rule error.

- [ ] **Step 5: Inspect the final diff and runtime instructions**

Confirm no secret is present, `requiredPrivateInfos` contains both location APIs, local auth is still backend-default-off, recommendation request remains `/recommendations`, and profile navigation paths match `app.json`.

- [ ] **Step 6: Commit any verification-only correction**

If no correction was needed, do not create an empty commit. If a scoped correction was needed, stage the explicit corrected paths and commit them; for example, when correcting the recommendation page and its test:

```bash
git add miniprogram/miniprogram/pages/recommend/index.js miniprogram/tests/pages/recommend.test.js
git commit -m "fix: complete mini program UI verification"
```

- [ ] **Step 7: Provide manual acceptance steps**

Tell the user to run `./scripts/start-local.sh` in their own terminal, clear all cache, rebuild npm if prompted, compile, accept or deny/retry location, choose a point, verify `POST /auth/dev` then `POST /recommendations`, and inspect the recommendation/profile layouts against the HTML v4 file.
