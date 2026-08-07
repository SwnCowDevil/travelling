# Origin Reverse Geocoding and AI Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Display a concrete POI name after selecting coordinates and verify that the configured PackyAPI system token participates in recommendations.

**Architecture:** Add an authenticated FastAPI location boundary that owns the Amap Web Service key and converts GCJ-02 coordinates into a normalized place response. The mini program requests that boundary after `wx.chooseLocation`, stores both display and administrative fields, and retains a resilient local fallback. AI stays behind the existing recommendation reranker; verification diagnoses configuration/connectivity without exposing tokens.

**Tech Stack:** FastAPI, httpx, Pydantic, pytest, WeChat native JavaScript/WXML, Node.js test runner, Amap Web Service reverse-geocoding v3, existing OpenAI-compatible PackyAPI adapter.

## Global Constraints

- Amap coordinates are sent as `longitude,latitude`, with at most six decimal places.
- Request `extensions=all` so Amap returns nearby POIs.
- Prefer a concrete POI name; fall back through road/building, formatted address, administrative region, then a coordinate label.
- Keep Amap and AI tokens exclusively in ignored backend `.env` files and never print them.
- Use the normalized origin fields `{name,regionName,address,latitude,longitude,source}` on the mini-program side.
- Personal AI profiles override the system token only when their encrypted token can be decrypted.
- AI failure remains non-blocking and returns rule recommendations.
- Preserve the user's unrelated `miniprogram/project.config.json` and SQLite WAL working-tree files.

---

### Task 1: Amap Reverse-Geocoding Client and Authenticated API

**Files:**
- Create: `backend/app/locations/__init__.py`
- Create: `backend/app/locations/amap.py`
- Create: `backend/app/locations/schemas.py`
- Create: `backend/app/locations/router.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/locations/test_amap_reverse.py`
- Create: `backend/tests/locations/test_api.py`

**Interfaces:**
- Consumes: `settings.amap_key`, authenticated user dependency `get_current_user_id`, `httpx.AsyncClient`.
- Produces: `AmapReverseClient.reverse(latitude: float, longitude: float) -> ResolvedLocation`; `GET /locations/reverse-geocode`; JSON `{name,region_name,address,latitude,longitude,source}`.

- [ ] **Step 1: Write failing client parsing tests**

```python
@pytest.mark.asyncio
async def test_reverse_prefers_first_named_poi():
    payload = {"status":"1","regeocode":{"formatted_address":"北京市东城区东长安街", "addressComponent":{"province":"北京市","city":[],"district":"东城区"}, "pois":[{"name":"天安门"}]}}
    result = await client_for(payload).reverse(39.9087, 116.3975)
    assert result.name == "天安门"
    assert result.region_name == "北京市东城区"
```

Add separate tests for missing POIs, Amap `status=0`, malformed payload, and request parameters `location=116.397500,39.908700`, `extensions=all`, `radius=1000`.

- [ ] **Step 2: Run tests and verify RED**

Run: `PYTHONPATH=backend backend/.venv/bin/pytest backend/tests/locations/test_amap_reverse.py -q`

Expected: collection fails because `app.locations.amap` does not exist.

- [ ] **Step 3: Implement normalized Amap parsing**

Define immutable `ResolvedLocation(name, region_name, address, latitude, longitude, source="amap")`. Normalize Amap fields that may be strings or empty arrays. Select `pois[0].name`, then `roads[0].name`, then `formatted_address`, then joined province/city/district. Raise `AmapReverseError` for configuration, transport, upstream status, or invalid-payload failures without including the key.

- [ ] **Step 4: Write failing authenticated API tests**

```python
def test_reverse_geocode_requires_authentication():
    assert TestClient(create_app()).get("/locations/reverse-geocode?latitude=39.9&longitude=116.4").status_code == 403

def test_reverse_geocode_returns_normalized_location(auth_client):
    response = auth_client.get("/locations/reverse-geocode?latitude=39.9&longitude=116.4")
    assert response.json()["name"] == "天安门"
```

Also assert latitude range `[-90,90]`, longitude range `[-180,180]`, missing key maps to `LOCATION_SERVICE_UNAVAILABLE`, and upstream failure maps to `LOCATION_LOOKUP_FAILED`.

- [ ] **Step 5: Implement and register the router**

Use a dependency factory `get_reverse_client()` so tests can override it. Require `get_current_user_id`, return `ResolvedLocationResponse`, and include the router in `create_app()`.

- [ ] **Step 6: Run backend location tests and verify GREEN**

Run: `PYTHONPATH=backend backend/.venv/bin/pytest backend/tests/locations -q`

Expected: all location tests pass.

- [ ] **Step 7: Commit backend location batch**

```bash
git add backend/app/locations backend/app/main.py backend/tests/locations
git commit -m "feat: add authenticated origin reverse geocoding"
```

---

### Task 2: Mini-Program Concrete Place Resolution and Storage

**Files:**
- Modify: `miniprogram/miniprogram/services/location.js`
- Modify: `miniprogram/miniprogram/pages/recommend/index.js`
- Modify: `miniprogram/miniprogram/pages/recommend/model.js`
- Modify: `miniprogram/tests/services/location.test.js`
- Modify: `miniprogram/tests/pages/recommend.test.js`

**Interfaces:**
- Consumes: `api.request({path:'/locations/reverse-geocode?...'})`, `authReady`, `wx.chooseLocation`.
- Produces: `resolveSelectedOrigin(api, selected): Promise<Origin>`; stored origin `{type,name,regionName,address,latitude,longitude,source}`; recommendation `origin_name=origin.name`.

- [ ] **Step 1: Write failing normalized-origin tests**

```js
test('selected coordinates are enriched with a concrete POI name', async () => {
  const api = { request: async () => ({ name:'天安门', region_name:'北京市东城区', address:'北京市东城区东长安街', latitude:39.9, longitude:116.4, source:'amap' }) }
  const result = await resolveSelectedOrigin(api, { name:'', address:'', latitude:39.9, longitude:116.4 })
  assert.equal(result.name, '天安门')
  assert.equal(result.regionName, '北京市东城区')
})
```

Add a failure test proving WeChat `name`, then `address`, then the coordinate label remains usable when the backend lookup fails.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `cd miniprogram && node --test tests/services/location.test.js tests/pages/recommend.test.js`

Expected: FAIL because `resolveSelectedOrigin` is missing and page selection does not call the API.

- [ ] **Step 3: Implement enrichment and one storage owner**

Change `chooseManualOrigin()` to return the raw WeChat selection without storing it. Implement `resolveSelectedOrigin(api, selected)` to call the backend, convert snake_case to camelCase, and fall back locally on error. Add `saveOrigin(origin)` to write `ORIGIN_KEY` only after enrichment, preventing the temporary coordinate label from overwriting a real name.

- [ ] **Step 4: Wire recommendation page selection**

After `chooseManualOrigin`, wait for `authReady` and retry authentication if required, enrich via `globalData.api`, save, then call `onOrigin`. Show `正在识别地点…` during lookup. If the user initiated one-click recommendation, continue automatically after the concrete name is assigned.

- [ ] **Step 5: Add request-shaping defense**

Make `buildRequest` trim `origin.name` and fall back to `origin.address`, `origin.regionName`, then a stable coordinate label. This prevents a future platform payload change from sending an empty `origin_name`.

- [ ] **Step 6: Run focused tests and verify GREEN**

Run: `cd miniprogram && node --test tests/services/location.test.js tests/pages/recommend.test.js`

Expected: all focused tests pass.

- [ ] **Step 7: Commit mini-program origin batch**

```bash
git add miniprogram/miniprogram/services/location.js miniprogram/miniprogram/pages/recommend miniprogram/tests/services/location.test.js miniprogram/tests/pages/recommend.test.js
git commit -m "feat: display concrete selected place names"
```

---

### Task 3: AI Connectivity, Source Diagnostics, and Final Verification

**Files:**
- Modify only if tests expose a defect: `backend/app/ai/client.py`, `backend/app/recommendations/service.py`, corresponding tests.
- Modify: `miniprogram/miniprogram/pages/recommend/index.wxml`
- Modify: `miniprogram/tests/pages/recommend-view.test.js`

**Interfaces:**
- Consumes: ignored `.env` system AI settings and existing `/recommendations` source response.
- Produces: verified `source=ai` when PackyAPI succeeds; precise fallback copy `AI 未参与，已使用可靠规则推荐` when source is `rules`.

- [ ] **Step 1: Validate loaded configuration without printing secrets**

Run a backend command that prints only booleans for `ai_api_key`, `amap_key`, `ai_encryption_key`, plus `ai_base_url` and `ai_model`. Expected: system AI key and Amap key are true; personal-token encryption may remain false.

- [ ] **Step 2: Run a direct AI connectivity probe**

Call the existing `AIClient.rerank` with one minimal candidate and print only HTTP/result status, selected ID count, base URL, and model. Never print headers, token, request dump, or exception objects that may contain authorization data.

Expected: a valid structured rerank response. If the probe fails, classify whether it is base URL, model, authorization, response schema, or timeout before changing code.

- [ ] **Step 3: Verify the full recommendation endpoint source**

Start the backend with the local script after reloading `.env`, authenticate via `/auth/dev`, post a valid recommendation, and print only `{status,source,item_count}`. Expected: `status=201`, `source=ai`, and at least one item. If upstream is unavailable, `source=rules` is acceptable only with a documented sanitized reason.

- [ ] **Step 4: Update fallback copy under test**

Write a WXML test expecting `AI 未参与，已使用可靠规则推荐`; verify RED against the old copy, update the text, and verify GREEN.

- [ ] **Step 5: Run full verification**

Run:

```bash
cd miniprogram && npm test
PYTHONPATH=backend backend/.venv/bin/pytest backend/tests -q
rg --files miniprogram/miniprogram -g '*.wxss' | while IFS= read -r f; do /Applications/wechatwebdevtools.app/Contents/Resources/app.asar.unpacked/node_modules/wcc-exec/wcsc -lc "$f" >/dev/null || exit 1; done
git diff --check
```

Expected: all tests pass, all WXSS files compile, and no whitespace errors occur.

- [ ] **Step 6: Commit any AI/copy correction**

```bash
git add miniprogram/miniprogram/pages/recommend/index.wxml miniprogram/tests/pages/recommend-view.test.js backend/app/ai backend/app/recommendations backend/tests/ai backend/tests/recommendations
git commit -m "fix: verify AI recommendation source and fallback status"
```

Stage only paths that actually changed; do not create an empty commit.
