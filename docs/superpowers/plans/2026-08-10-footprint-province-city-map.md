# 足迹页省市点亮地图 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在微信小程序足迹页提供默认地图模式的深色省市点亮地图，并可在不丢失既有足迹列表功能的前提下切换至列表模式。

**Architecture:** 保持 `AdministrativeRegion` 作为行政层级与状态聚合的权威来源。新增独立的区域边界缓存和目的地的可选市级归属；后端按当前层级从高德行政区 Web 服务同步并缓存边界，`/map/summary` 直接返回绘图所需的坐标。小程序使用原生 Canvas 2D 渲染简化多边形、状态色和点击命中，不引入不能在微信小程序运行的高德 JS 地图。

**Tech Stack:** FastAPI、SQLAlchemy/Alembic、httpx、高德 Web 服务行政区域查询 API、微信小程序原生 Canvas 2D、Node.js 内置测试运行器、pytest。

## Global Constraints

- 地图层级仅为中国省级与省内市级；本期不绘制县级边界。
- 不实现卫星底图、地图拖动缩放、轨迹、时间轴、世界视图、角落覆盖率或路线距离统计。
- 不改动既有足迹状态、到访记录、筛选语义、API 鉴权或用户隔离逻辑。
- 高德 Key 仅从后端 `TRAVEL_AMAP_KEY` 读取，禁止下发到小程序或写入测试、日志和提交内容。
- 地图/列表模式仅改变呈现方式，保留当前父级和状态筛选；页面默认地图模式。
- 当边界数据或 Canvas 不可用时，自动展示现有列表，不阻断足迹管理。

---

### Task 1: 持久化省市边界与目的地市级归属

**Files:**
- Create: `backend/alembic/versions/0011_map_region_boundaries.py`
- Modify: `backend/app/destinations/models.py`
- Modify: `backend/app/db/base.py`
- Create: `backend/app/map/models.py`
- Create: `backend/tests/map/test_region_models.py`

**Interfaces:**
- Consumes: `AdministrativeRegion.code` 和既有 `Destination.region_code` 省级外键。
- Produces: `RegionBoundary(region_code, center_longitude, center_latitude, polygons, source)` 与 `Destination.city_region_code`，供地图同步和摘要服务使用。

- [ ] **Step 1: 写入会失败的模型测试**

在 `backend/tests/map/test_region_models.py` 中建立省、市行政区与目的地，要求目的地可保留原省级 `region_code` 并单独关联市级编码；要求边界记录以区域编码作为唯一目标并保存多块多边形：

```python
def test_destination_can_keep_province_and_optional_city_boundary(db_session):
    province = AdministrativeRegion(code="510000", name="四川省", level="province")
    city = AdministrativeRegion(code="510100", name="成都市", level="city", parent_code="510000")
    destination = Destination(code="chengdu", name="成都", summary="测试", latitude=104.06, longitude=30.67, region_code="510000", city_region_code="510100", categories=[], suitable_months=[], season_tags=[], crowd_tags=[], transport_modes=[], climate={}, quality_score=0.5, data_version="test", coordinate_verified=True, coordinate_source="test")
    boundary = RegionBoundary(region_code="510100", center_longitude=104.06, center_latitude=30.67, polygons=[[[104.0, 30.6], [104.1, 30.6], [104.0, 30.7]]], source="amap")
    db_session.add_all([province, city, destination, boundary]); db_session.commit()
    assert db_session.get(Destination, destination.id).city_region_code == "510100"
    assert db_session.get(RegionBoundary, "510100").polygons[0][0] == [104.0, 30.6]
```

- [ ] **Step 2: 运行模型测试，确认因字段与模型不存在而失败**

Run: `.venv/bin/python -m pytest tests/map/test_region_models.py -v`

Expected: FAIL，报 `city_region_code` 或 `RegionBoundary` 未定义。

- [ ] **Step 3: 添加最小模型与迁移**

在 `Destination` 增加可空 `city_region_code: Mapped[str | None]` 外键到 `administrative_regions.code`，不替换 `region_code`。新建 `RegionBoundary`：`region_code` 为主键和级联外键，两个中心点 Float，`polygons` JSON 默认空列表，`source` String(20) 默认 `amap`，`updated_at` 服务端更新时间。将 `app.map.models` 导入 `import_models()`。

迁移 `0011_map_region_boundaries` 依赖 `0010_custom_favorite_targets`：给 `destinations` 增加可空 `city_region_code` 和外键；创建 `region_boundaries` 与上述字段、主键、外键。SQLite 使用 `batch_alter_table` 添加目的地外键。

```python
class RegionBoundary(Base):
    __tablename__ = "region_boundaries"
    region_code: Mapped[str] = mapped_column(ForeignKey("administrative_regions.code", ondelete="CASCADE"), primary_key=True)
    center_longitude: Mapped[float] = mapped_column(Float)
    center_latitude: Mapped[float] = mapped_column(Float)
    polygons: Mapped[list[list[list[float]]]] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(20), default="amap")
```

- [ ] **Step 4: 运行模型测试，确认通过**

Run: `.venv/bin/python -m pytest tests/map/test_region_models.py -v`

Expected: PASS。

- [ ] **Step 5: 提交数据模型任务**

```bash
git add backend/alembic/versions/0011_map_region_boundaries.py backend/app/destinations/models.py backend/app/db/base.py backend/app/map/models.py backend/tests/map/test_region_models.py
git commit -m "feat: store map region boundaries"
```

### Task 2: 同步高德省市边界并返回可绘制地图摘要

**Files:**
- Create: `backend/app/map/amap.py`
- Modify: `backend/app/map/schemas.py`
- Modify: `backend/app/map/service.py`
- Modify: `backend/app/map/router.py`
- Create: `backend/scripts/sync_map_regions.py`
- Modify: `backend/tests/map/test_summary.py`
- Create: `backend/tests/map/test_amap_regions.py`

**Interfaces:**
- Consumes: Task 1 的 `RegionBoundary` 与 `Destination.city_region_code`；`Settings.amap_key`。
- Produces: `GET /map/summary?parent_code=<province-code>&status=<optional-status>`，每项新增 `center`、`polygons`、`map_status`；`AmapDistrictClient.fetch_region(adcode)` 与一次性同步脚本。

- [ ] **Step 1: 写入会失败的高德行政区解析测试**

在 `backend/tests/map/test_amap_regions.py` 使用 `httpx.MockTransport` 返回一条高德 `districts` 响应，验证 `AmapDistrictClient.fetch_region("510000")` 解析当前区域边界、中心点与直属市级元数据；多面边界 `|` 分隔必须解析为多条坐标路径：

```python
async def test_fetch_region_parses_polyline_and_children():
    region = await client.fetch_region("510000")
    assert region.code == "510000"
    assert region.polygons == [[[104.0, 30.0], [105.0, 30.0]], [[106.0, 31.0], [107.0, 31.0]]]
    assert region.children[0].code == "510100"
```

同时在 `test_summary.py` 扩展现有层级测试，写入省、市 `RegionBoundary` 和目的地 `city_region_code`，要求根层省份、下钻层市均返回各自的多边形及优先状态：

```python
assert root[0].map_status == "revisit"
assert root[0].center == [102.0, 30.0]
assert city[0].region_code == "513300"
assert city[0].polygons
```

- [ ] **Step 2: 运行新测试，确认因为客户端、地图字段和市级聚合尚不存在而失败**

Run: `.venv/bin/python -m pytest tests/map/test_amap_regions.py tests/map/test_summary.py -v`

Expected: FAIL，缺少 `AmapDistrictClient`、`center`、`polygons` 或 `map_status`。

- [ ] **Step 3: 实现高德客户端、缓存同步与摘要字段**

创建 `AmapDistrictClient`，只向 `https://restapi.amap.com/v3/config/district` 发送服务端请求，固定 `subdistrict=1`、`extensions=all`、`keywords=<adcode>`。缺 Key、HTTP/JSON 错误、状态非 `1` 或无当前 district 时抛明确的 `AmapDistrictError`，不泄露 Key。

实现多边形解析：先按 `|` 切块，再按 `;` 切点、每点按 `,` 转换 `[longitude, latitude]`；过滤不含至少 3 个点的路径。仅当前查询 district 含边界，子级只解析名称、adcode、level、center。

在地图服务增加：

新增 `sync_region_layer(session, client, parent_code) -> SyncResult`：读取 `parent_code` 对应区域（根层为全部已存在的省份），写入当前区域和直属子级的 `AdministrativeRegion` 元数据与当前区域边界；返回 `SyncResult(regions_created, boundaries_cached, failures)`。新增 `resolve_map_status(item) -> str | None`，按 `visited`、`revisit`、`want`、`avoid` 依次选择非零聚合状态。

根层同步所有已存在省级记录的边界；省级下钻时先同步其直属市级行政区，再同步每个市边界。已有 `RegionBoundary` 时不重复请求。网络失败不清除已有缓存；没有缓存时摘要返回空 `polygons`，让前端安全回退。城市写入的 `AdministrativeRegion.parent_code` 为省级编码，直辖市没有市级子项时保持地图终点。

`build_map_summary` 对每个目的地优先使用 `city_region_code`、否则使用原 `region_code` 向上聚合；新增 `map_status`，优先级为 `visited`、`revisit`、`want`、`avoid`，其中直接设置仍在 `direct_status` 原字段返回。`RegionMapSummary` 增加 `center: list[float] | None`、`polygons: list[list[list[float]]]` 和 `map_status: str | None`。

路由注入一个短生命周期 `httpx.Client(timeout=15)`；若高德同步失败仍返回现有摘要，另通过 `geometry_available` 响应字段标记该层是否至少有一条有效边界。

`scripts/sync_map_regions.py` 导出 `run_sync(session, api_key, province_codes) -> SyncResult` 并提供 `--province <adcode>` 与 `--all-provinces` 命令行入口；同步前检查 `TRAVEL_AMAP_KEY`，运行后输出只包含同步区域数量、边界数量及未匹配目的地数量。脚本对既有目的地调用逆地理编码，按省下的市名匹配并写入 `city_region_code`；无法匹配和直辖市保留空值。

- [ ] **Step 4: 运行地图后端测试，确认通过**

Run: `.venv/bin/python -m pytest tests/map/test_amap_regions.py tests/map/test_summary.py -v`

Expected: PASS。

- [ ] **Step 5: 运行全部后端测试**

Run: `.venv/bin/python -m pytest`

Expected: PASS，所有后端测试无失败。

- [ ] **Step 6: 提交地图数据服务任务**

```bash
git add backend/app/map/amap.py backend/app/map/schemas.py backend/app/map/service.py backend/app/map/router.py backend/scripts/sync_map_regions.py backend/tests/map/test_amap_regions.py backend/tests/map/test_summary.py
git commit -m "feat: provide province city map layers"
```

### Task 3: 形成可测试的 Canvas 地图数据模型

**Files:**
- Modify: `miniprogram/miniprogram/pages/map/model.js`
- Modify: `miniprogram/tests/pages/map.test.js`

**Interfaces:**
- Consumes: `/map/summary` 条目中的 `center`、`polygons`、`map_status` 和既有 `status_counts`。
- Produces: `mapColor(item)`、`projectMapItems(items, width, height, padding)`、`hitRegion(projected, x, y)` 与 `visibleMapItems(items, status)`，供页面渲染和点击下钻使用。

- [ ] **Step 1: 写入会失败的小程序模型测试**

在 `map.test.js` 增加状态颜色、投影和命中测试：

```js
assert.equal(mapColor({map_status:'visited'}), '#20d8cf')
assert.equal(mapColor({map_status:'avoid'}), '#1b3440')
const projected = projectMapItems([{region_code:'510000', polygons:[[[100,30],[110,30],[100,40]]]}], 300, 200, 16)
assert.equal(projected[0].paths[0].length, 3)
assert.equal(hitRegion(projected, 20, 180).region_code, '510000')
```

并验证 `visibleMapItems` 保持现有状态筛选，地图模式下只给有有效三点路径的区域作图。

- [ ] **Step 2: 运行模型测试，确认新增导出尚不存在而失败**

Run: `npm test -- tests/pages/map.test.js`

Expected: FAIL，`mapColor`、`projectMapItems` 或 `hitRegion` 未定义。

- [ ] **Step 3: 实现纯函数地图模型**

实现上述函数且不依赖 `wx`：用所有点的 min/max 经度纬度计算等比缩放和居中偏移；纬度投影采用上下翻转；空/无效路径被移除；点在多边形内判断用射线法。`mapColor` 使用固定调色板：`visited #20d8cf`、`revisit #159c9a`、`want #83d9cb`、`avoid #1b3440`、未设置 `#294451`。保留现有 `nextParent`、`filterItems`，并以 `map_status` 为首选、`direct_status` 和 `status_counts` 为回退。

- [ ] **Step 4: 运行地图模型测试，确认通过**

Run: `npm test -- tests/pages/map.test.js`

Expected: PASS。

- [ ] **Step 5: 提交地图模型任务**

```bash
git add miniprogram/miniprogram/pages/map/model.js miniprogram/tests/pages/map.test.js
git commit -m "feat: add footprint map canvas model"
```

### Task 4: 构建默认地图模式与列表回退页面

**Files:**
- Modify: `miniprogram/miniprogram/pages/map/index.json`
- Modify: `miniprogram/miniprogram/pages/map/index.js`
- Modify: `miniprogram/miniprogram/pages/map/index.wxml`
- Modify: `miniprogram/miniprogram/pages/map/index.wxss`
- Create: `miniprogram/tests/pages/map-view.test.js`

**Interfaces:**
- Consumes: Task 2 的 `geometry_available` 和区域几何字段，Task 3 的纯函数。
- Produces: 默认地图界面、`mode` 为 `map | list`、`drawMap()`、`tapMap(event)`、地图/列表切换以及无几何时的安全回退。

- [ ] **Step 1: 写入会失败的视图与行为测试**

创建 `map-view.test.js` 静态检查默认地图模式和必要控件：

```js
assert.match(wxml, /footprint-canvas/)
assert.match(wxml, /mode === 'map'/)
assert.match(wxml, /bindtap="toggleMode"/)
assert.match(wxml, /地图/)
assert.match(wxml, /列表/)
assert.match(wxml, /bindtap="tapMap"/)
assert.match(wxss, /\.map-stage\{[^}]*background:#0b1d2b/)
```

通过模拟 `Page` 注册，验证 `toggleMode` 在 `map` 与 `list` 间切换且保留 `parentCode`、`status`；验证 `tapMap` 对命中区域调用现有 `drill`，未命中不触发请求。

- [ ] **Step 2: 运行页面测试，确认 Canvas、切换或事件尚不存在而失败**

Run: `npm test -- tests/pages/map-view.test.js`

Expected: FAIL，缺少 Canvas 容器或 `toggleMode`。

- [ ] **Step 3: 实现页面结构与 Canvas 渲染**

将地图页 `data` 扩展为 `mode:'map'`、`geometryAvailable:false`、`canvasReady:false`、`projected:[]` 和已有层级/筛选字段。`load()` 请求 `/map/summary` 时同时写入 `geometryAvailable`，再在地图模式调用 `drawMap()`。当请求失败、`geometryAvailable` 为 false、Canvas 节点不可得或可绘制区域为空时，自动设置 `mode:'list'` 和 `mapAvailable:false`，保留 `visible` 列表。

WXML 顶部使用普通 `view` 作为右上角分段控件而非新依赖：地图、列表均绑定 `toggleMode`。地图模式展示层级面包屑、点亮数量、状态筛选、`<canvas type="2d" id="footprint-canvas" canvas-id="footprint-canvas" bindtap="tapMap">` 和紧凑图例；列表模式渲染现有区域卡片、到访记录入口和回退提示。市级为终点：`drill` 只在项目 `level === 'province'` 时进入其城市层，点击市级显示轻提示并不请求县级。

在 `onReady` 调用 `initCanvas()`，使用 `wx.createSelectorQuery().select('#footprint-canvas').fields({node:true,size:true})` 获取 2D context；`drawMap()` 清空后用 `projectMapItems` 绘制深色底、每条路径、名称和状态色，按 DPR 放大画布以保证清晰。`tapMap` 把触点换算为画布坐标，经 `hitRegion` 找到项目后调用 `drill({currentTarget:{dataset:{code:item.region_code, level:item.level}}})`。

- [ ] **Step 4: 运行地图页面测试，确认通过**

Run: `npm test -- tests/pages/map-view.test.js && npm test -- tests/pages/map.test.js`

Expected: PASS。

- [ ] **Step 5: 运行小程序全量测试**

Run: `npm test`

Expected: PASS，所有小程序测试无失败。

- [ ] **Step 6: 提交地图 UI 任务**

```bash
git add miniprogram/miniprogram/pages/map/index.json miniprogram/miniprogram/pages/map/index.js miniprogram/miniprogram/pages/map/index.wxml miniprogram/miniprogram/pages/map/index.wxss miniprogram/tests/pages/map-view.test.js
git commit -m "feat: render footprint map and list modes"
```

### Task 5: 同步本地地图数据并验证回退行为

**Files:**
- Modify: `docs/deployment/server-setup.md`
- Test: `backend/tests/map/test_amap_regions.py`
- Test: `miniprogram/tests/pages/map-view.test.js`

**Interfaces:**
- Consumes: Task 2 脚本 `python -m scripts.sync_map_regions --all-provinces` 与任务 4 的回退界面。
- Produces: 本地与部署环境可重复执行的行政区同步说明。

- [ ] **Step 1: 写入会失败的文档/配置视图断言**

在 `map-view.test.js` 增加断言：当 `geometry_available` 为 false 时页面渲染“地图数据暂不可用，已切换为列表模式”；在 `test_amap_regions.py` 增加无 Key 时 `sync_map_regions` 以配置错误退出且不会写入数据库的测试。

- [ ] **Step 2: 运行目标测试，确认回退文案与无 Key 保护尚不存在而失败**

Run: `.venv/bin/python -m pytest tests/map/test_amap_regions.py -v && npm test -- tests/pages/map-view.test.js`

Expected: FAIL，缺少无 Key 保护或回退文案。

- [ ] **Step 3: 补齐保护、运行文档与本地同步**

脚本在打开数据库事务前检查 `settings.amap_key`，无 Key 抛出 `SystemExit("TRAVEL_AMAP_KEY is required")`；页面使用固定回退文案。更新 `server-setup.md`，增加迁移后的两条命令：

```bash
alembic upgrade head
python -m scripts.sync_map_regions --all-provinces
```

说明该命令只使用服务器 `.env` 内的高德 Web 服务 Key、可安全重跑、首次会请求省市边界并缓存；不在文档中写入实际 Key。开发机配置了 Key 时运行一次同步，然后用 `GET /map/summary` 与开发者工具验证省级地图和省内城市地图；没有 Key 时验证自动列表回退。

- [ ] **Step 4: 运行目标测试，确认通过**

Run: `.venv/bin/python -m pytest tests/map/test_amap_regions.py -v && npm test -- tests/pages/map-view.test.js`

Expected: PASS。

- [ ] **Step 5: 运行全量验证并提交任务**

Run: `.venv/bin/python -m pytest && npm test`

Expected: 后端与小程序全量测试均 PASS。

```bash
git add docs/deployment/server-setup.md backend/tests/map/test_amap_regions.py miniprogram/tests/pages/map-view.test.js
git commit -m "docs: document footprint map data sync"
```
