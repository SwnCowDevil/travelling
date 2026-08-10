# 足迹地图按需下载包 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将全国省市边界改为版本化静态地图包，仅在用户主动进入地图模式时下载并本地缓存，消除足迹首屏卡顿。

**Architecture:** 后端脚本从 `region_boundaries` 原始缓存生成 `backend/data/map-packs/china-v1.json`，输出已简化的行政区边界。`/map/summary` 只返回状态摘要；新地图包元信息和下载接口提供版本、MD5 校验值和静态 JSON。小程序地图页默认列表模式，在用户确认后用 `wx.downloadFile` 下载、校验、保存文件，再合并状态摘要到 Canvas 模型。

**Tech Stack:** FastAPI、SQLAlchemy、Python JSON/哈希、微信小程序原生 API、Canvas 2D、Node/Pytest 测试。

## Global Constraints

- 原始 `region_boundaries.polygons` 仅用于构建资源，绝不写回简化结果。
- 静态包每个行政区至多 12 条路径、360 个坐标点；`/map/summary` 不得返回 `polygons`。
- 首次下载必须经用户确认并展示进度；取消和失败必须留在列表模式。
- 同一版本地图包仅下载一次；使用 `wx.getFileInfo` 校验本地文件的版本、字节数与 MD5。
- 不在接口、日志、资源或测试中写入高德 Key。

---

### Task 1: 生成并提供版本化静态地图包

**Files:**
- Create: `backend/app/map/pack.py`
- Create: `backend/scripts/build_map_pack.py`
- Modify: `backend/app/map/router.py`
- Modify: `backend/app/map/schemas.py`
- Modify: `backend/app/map/service.py`
- Modify: `docs/deployment/server-setup.md`
- Test: `backend/tests/map/test_pack.py`
- Test: `backend/tests/map/test_summary.py`

**Interfaces:**
- Produces `build_map_pack(session: Session, destination: Path) -> MapPackMetadata`.
- Produces `load_map_pack_metadata(path: Path) -> MapPackMetadata`.
- Adds `GET /map/pack` returning `{version, byte_size, md5, download_path}`.
- Adds `GET /map/pack/download` returning the JSON file as `application/json`.
- Changes `build_map_summary(...)` so `RegionMapSummary.polygons == []` for all normal summary calls.

- [ ] **Step 1: Write failing backend tests**

```python
def test_build_map_pack_writes_simplified_versioned_geometry(db_session, tmp_path):
    metadata = build_map_pack(db_session, tmp_path / "china-v1.json")
    payload = json.loads((tmp_path / "china-v1.json").read_text())
    assert metadata.byte_size > 0
    assert payload["version"] == metadata.version
    assert sum(len(path) for path in payload["regions"][0]["polygons"]) <= 360

def test_map_summary_never_returns_raw_polygons(client, auth_headers):
    response = client.get("/map/summary", headers=auth_headers)
    assert response.status_code == 200
    assert all(item["polygons"] == [] for item in response.json()["items"])
```

- [ ] **Step 2: Run tests to verify failure**

Run: `cd backend && .venv/bin/python -m pytest tests/map/test_pack.py tests/map/test_summary.py -v`

Expected: FAIL because pack module/endpoints do not exist and summaries still return polygons.

- [ ] **Step 3: Implement the generator and FastAPI download endpoints**

```python
@dataclass(frozen=True)
class MapPackMetadata:
    version: str
    byte_size: int
    md5: str

def build_map_pack(session: Session, destination: Path) -> MapPackMetadata:
    regions = list(session.execute(select(AdministrativeRegion, RegionBoundary).join(RegionBoundary)).all())
    payload = {"version": MAP_PACK_VERSION, "regions": simplified_regions}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    return metadata_for(destination)
```

Use `simplify_map_polygons` from `app.map.service`, retain only region code/name/level/center/polygons, and compute MD5 from the bytes written. Return HTTP 404 with a clear “build map pack first” message when the file is absent. Update deployment documentation to run the builder after `sync_map_regions`.

- [ ] **Step 4: Run backend tests to verify pass**

Run: `cd backend && .venv/bin/python -m pytest tests/map/test_pack.py tests/map/test_summary.py -v`

Expected: PASS; generated geometry is bounded and summary responses have no raw points.

- [ ] **Step 5: Commit**

```bash
git add backend/app/map/pack.py backend/scripts/build_map_pack.py backend/app/map/router.py backend/app/map/schemas.py backend/app/map/service.py backend/tests/map/test_pack.py backend/tests/map/test_summary.py docs/deployment/server-setup.md
git commit -m "feat: publish compact footprint map pack"
```

### Task 2: 下载、验证并缓存地图包的小程序模块

**Files:**
- Create: `miniprogram/miniprogram/pages/map/pack.js`
- Test: `miniprogram/tests/pages/map-pack.test.js`

**Interfaces:**
- Produces `ensureMapPack(api, wxApi, onProgress) -> Promise<{version: string, regions: MapRegion[]}>`.
- Uses storage key `travel.map-pack.meta.v1` with `{version, filePath, byteSize, md5}`.
- Throws `MapPackDownloadError` for cancellation, invalid JSON, checksum mismatch, status code failure, or unavailable file.

- [ ] **Step 1: Write failing Node tests**

```javascript
test('uses a saved map pack when its version matches metadata', async()=>{
  const pack=await ensureMapPack(api,wxApi,onProgress)
  assert.equal(pack.version,'china-v1')
  assert.equal(wxApi.downloadCalls,0)
})

test('downloads and saves a newer map pack while reporting progress', async()=>{
  const pack=await ensureMapPack(api,wxApi,onProgress)
  assert.equal(pack.regions.length,2)
  assert.deepEqual(progress,[20,100])
})
```

- [ ] **Step 2: Run tests to verify failure**

Run: `cd miniprogram && npm test -- tests/pages/map-pack.test.js`

Expected: FAIL because `pack.js` does not exist.

- [ ] **Step 3: Implement file-cache lifecycle**

```javascript
async function ensureMapPack(api,wxApi,onProgress){
  const metadata=await api.request({path:'/map/pack'})
  const cached=readCachedPack(wxApi,metadata)
  if(cached)return cached
  const tempPath=await downloadWithProgress(wxApi,getApp().globalData.apiBaseUrl+metadata.download_path,onProgress)
  const content=wxApi.getFileSystemManager().readFileSync(tempPath,'utf8')
  const pack=validatePack(content,metadata)
  const saved=await saveFile(wxApi,tempPath)
  wxApi.setStorageSync(MAP_PACK_META_KEY,{version:metadata.version,filePath:saved,byteSize:metadata.byte_size,md5:metadata.md5})
  return pack
}
```

Validate version, byte size and MD5 with `wx.getFileInfo({digestAlgorithm:'md5'})` before caching. If metadata cannot be requested but a locally validated file exists, use that file. Do not persist parsed JSON; persist only the downloaded file path and metadata.

- [ ] **Step 4: Run Node tests to verify pass**

Run: `cd miniprogram && npm test -- tests/pages/map-pack.test.js`

Expected: PASS for cache hit, progress download, invalid file, and offline cache fallback.

- [ ] **Step 5: Commit**

```bash
git add miniprogram/miniprogram/pages/map/pack.js miniprogram/tests/pages/map-pack.test.js
git commit -m "feat: cache downloadable footprint map pack"
```

### Task 3: 让足迹页按需加载离线地图

**Files:**
- Modify: `miniprogram/miniprogram/pages/map/index.js`
- Modify: `miniprogram/miniprogram/pages/map/index.wxml`
- Modify: `miniprogram/miniprogram/pages/map/index.wxss`
- Modify: `miniprogram/miniprogram/pages/map/model.js`
- Test: `miniprogram/tests/pages/map-view.test.js`

**Interfaces:**
- Consumes `ensureMapPack` and page state `mapPack`, `mapDownloading`, `mapProgress`.
- Combines `summary.items` status data with pack regions by `region_code` before `projectMapItems`.
- `requestMapMode()` owns confirmation; `toggleMode()` only changes between ready map and list.

- [ ] **Step 1: Write failing page tests**

```javascript
test('first map switch asks before downloading and keeps list mode when cancelled', async()=>{
  await definition.requestMapMode.call(page)
  assert.equal(page.data.mode,'list')
  assert.equal(page.data.mapDownloading,false)
})

test('confirmed map download exposes progress then draws merged pack geometry', async()=>{
  await definition.requestMapMode.call(page)
  assert.equal(page.data.mode,'map')
  assert.equal(page.data.mapProgress,100)
  assert.equal(page.data.items[0].polygons.length>0,true)
})
```

- [ ] **Step 2: Run tests to verify failure**

Run: `cd miniprogram && npm test -- tests/pages/map-view.test.js`

Expected: FAIL because map mode is still driven by geometry returned by `/map/summary`.

- [ ] **Step 3: Implement confirmation, progress, and geometry merge**

```javascript
async requestMapMode(){
  if(!await confirmDownload())return
  this.setData({mapDownloading:true,mapProgress:0})
  try{
    const pack=await ensureMapPack(api,wx,progress=>this.setData({mapProgress:progress}))
    this.mapPack=pack
    this.setData({mode:'map',mapDownloading:false,items:mergeMapGeometry(this.data.summaryItems,pack.regions)},()=>this.initCanvas())
  }catch(_){this.setData({mode:'list',mapDownloading:false});wx.showToast({title:'地图包下载失败，可稍后重试',icon:'none'})}
}
```

Use `wx.showModal` for confirmation and show an inline loading card with percentage while downloading. Preserve the current filter and parent code when entering or leaving map mode. In list mode only render summary items.

- [ ] **Step 4: Run full frontend tests to verify pass**

Run: `cd miniprogram && npm test`

Expected: PASS; initial list mode, cancellation, progress, cached map, province/city drill and return country all remain covered.

- [ ] **Step 5: Commit**

```bash
git add miniprogram/miniprogram/pages/map/index.js miniprogram/miniprogram/pages/map/index.wxml miniprogram/miniprogram/pages/map/index.wxss miniprogram/miniprogram/pages/map/model.js miniprogram/tests/pages/map-view.test.js
git commit -m "feat: load footprint map on demand"
```

### Task 4: 生成本地资源并进行交付验证

**Files:**
- Modify: `scripts/start-local.sh`
- Test: `backend/tests/map/test_pack.py`

**Interfaces:**
- Local startup invokes `.venv/bin/python -m scripts.build_map_pack` after migrations when boundaries exist.
- The generated `backend/data/map-packs/china-v1.json` remains runtime data and is not committed.

- [ ] **Step 1: Write failing startup/pack test**

```python
def test_pack_metadata_matches_downloaded_file(client, auth_headers):
    metadata=client.get('/map/pack',headers=auth_headers).json()
    response=client.get(metadata['download_path'],headers=auth_headers)
    assert hashlib.md5(response.content).hexdigest()==metadata['md5']
```

- [ ] **Step 2: Run test to verify failure**

Run: `cd backend && .venv/bin/python -m pytest tests/map/test_pack.py -v`

Expected: FAIL until startup resource generation and download file response are connected.

- [ ] **Step 3: Generate the local pack and verify actual size**

```bash
cd backend
.venv/bin/python -m scripts.build_map_pack
.venv/bin/python -c "from pathlib import Path; print(Path('data/map-packs/china-v1.json').stat().st_size)"
```

Confirm the pack is far smaller than the previous 18 MB root payload and does not contain a Key.

- [ ] **Step 4: Run all checks**

Run: `cd backend && .venv/bin/python -m pytest && cd ../miniprogram && npm test && cd .. && git diff --check`

Expected: all tests pass and no whitespace errors.

- [ ] **Step 5: Commit**

```bash
git add scripts/start-local.sh backend/tests/map/test_pack.py
git commit -m "chore: build local footprint map pack"
```
