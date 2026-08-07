# 出发地具体名称反查与 AI 配置设计

## 1. 目标

- 微信选址只返回坐标或名称为空时，使用后端高德逆地理编码获取具体 POI 名称并回显。
- 经纬度、具体地点名、行政区名和完整地址分开保存，推荐请求使用具体地点名。
- 系统 AI Token 配置正常时使用 AI 重排；仅在 AI 未配置或调用失败时降级为规则推荐。
- 明确 `.env` 在本地、个人 Token 和正式部署三种场景下的必填项。

## 2. 地点数据结构

前端统一使用以下结构：

```js
{
  type: 'manual',
  name: '天安门',
  regionName: '北京市东城区',
  address: '北京市东城区长安街',
  latitude: 39.9087,
  longitude: 116.3975,
  source: 'amap'
}
```

- `name` 优先使用距坐标最近的 POI 名称，用于页面回显和 `origin_name`。
- `regionName` 使用省、市、区县组合文本。
- `address` 使用高德格式化地址。
- `source` 记录名称来源，便于后续诊断。

## 3. 逆地理编码架构

### 3.1 后端

- 新增需要登录的 `GET /locations/reverse-geocode?latitude=...&longitude=...` API。
- 后端使用 `TRAVEL_AMAP_KEY` 调用高德逆地理编码 Web API，高德 Key 不下发到小程序。
- 响应为 `{name, region_name, address, latitude, longitude, source}`。
- POI 名选择顺序：返回列表第一个有效 POI 名称 → 道路/建筑名 → 格式化地址 → 行政区名。
- 高德未配置、超时或返回异常时，API 返回稳定错误码，不暴露 Key 或上游响应。

### 3.2 前端

1. 调用 `wx.chooseLocation` 获得坐标。
2. 等待 `authReady`，调用后端逆地理编码。
3. 成功后同时设置页面 `origin` 并保存最近出发地。
4. 高德调用失败时，优先使用微信返回的 `name`，其次使用 `address`，最后使用行政区或坐标占位；不阻断用户发起推荐。
5. 已存储的旧结构仍可读取，下次手动选址时自动升级为新结构。

## 4. AI 配置与降级

- 系统 Token 来自后端 `.env` 的 `TRAVEL_AI_API_KEY`。
- 系统 API 地址和模型分别来自 `TRAVEL_AI_BASE_URL` 与 `TRAVEL_AI_MODEL`。
- 用户在“我的 → AI 设置”保存个人 Token 后，个人 Token 优先于系统 Token；该能力要求 `TRAVEL_AI_ENCRYPTION_KEY`。
- 调用 AI 成功时响应 `source=ai`，前端不显示降级提示。
- AI 未配置或请求失败时响应 `source=rules`，前端显示“AI 未参与，已使用可靠规则推荐”。
- 开发时的连通性检查只输出 HTTP 状态、模型名和结果类型，不输出 Token。

## 5. `.env` 要求

### 5.1 当前本地调试必填

- `TRAVEL_AMAP_KEY`：具体地点反查必填。
- `TRAVEL_DATABASE_URL`：数据库地址；可使用当前 SQLite 值。
- `TRAVEL_AI_BASE_URL`、`TRAVEL_AI_MODEL`、`TRAVEL_AI_API_KEY`：要求 AI 参与推荐时必填。

### 5.2 按功能必填

- `TRAVEL_AI_ENCRYPTION_KEY`：使用“我的页保存个人 Token”时必填。
- `TRAVEL_WECHAT_APP_ID`、`TRAVEL_WECHAT_APP_SECRET`：使用正式微信静默登录时必填；本地 `/auth/dev` 不需要。
- `TRAVEL_AMAP_SECRET`：当高德控制台为 Web API 开启数字签名校验时才必填。

### 5.3 正式部署必填

- `TRAVEL_JWT_SECRET`：必须使用强随机值，不能使用开发默认值。
- `TRAVEL_DATABASE_URL`：改为正式数据库连接。
- 正式微信登录与对应功能的上述密钥。

## 6. 测试与验收

- 后端单元测试覆盖 POI 优先级、无 POI 回退、高德错误和未配置 Key。
- API 测试覆盖登录鉴权、坐标校验与稳定响应。
- 前端测试覆盖具体名称回显、新结构存储、反查失败回退和推荐请求的 `origin_name`。
- AI 连通性测试确认当前系统配置能产生 `source=ai`；若上游拒绝，记录脱敏原因并保留规则降级。
- 全量前后端测试和微信 WXSS 编译检查通过后提交。
