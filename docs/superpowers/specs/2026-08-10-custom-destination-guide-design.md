# 任意地点主动生成攻略设计

## 目标

用户可在推荐页主动输入全国任意旅行地点，经高德地点搜索和明确选择后，直接进入现有目的地详情生成攻略，并复用快速/深度生成、天气、收藏和收藏编辑能力。

## 范围

- 推荐页增加“想去哪里？”输入、候选地点列表和“生成攻略”操作。
- 后端用现有高德 Web 服务 API 搜索 POI，并返回最多 5 条名称、地址、行政区、经纬度。
- 用户选择候选后创建或复用仅属于该用户的自定义目的地，再跳转现有详情页。
- 攻略请求继承推荐页当前月份、游玩天数、出发地和偏好筛选。

不包含手动地图选点、未搜索到 POI 时由 AI 猜测地点、将自定义地点加入公共推荐库或公开给其他用户。

## 数据模型

新增 `custom_destinations`：`id`、`user_id`、`amap_poi_id`、`name`、`address`、`region_name`、`latitude`、`longitude`、`created_at`、`updated_at`。`(user_id, amap_poi_id)` 唯一。

自定义目的地不复用公共 `destinations` 表：公共表的内容质量、推荐评分与筛选数据不适用于临时 POI。新增 `custom-guides` 路由直接用自定义目的地信息生成 `GuidePayload`；它有自己的用户作用域缓存。天气端点可接受自定义目的地 ID 并使用其坐标。

收藏表迁移为多态目标：将现有 `favorite_guides.destination_id` 改为可空，新增可空 `custom_destination_id` 和必填 `destination_type`（`public` 或 `custom`）。记录必须且只能填写一个目标 ID；公共记录继续引用 `destinations`，自定义记录引用 `custom_destinations`。公共收藏维持 `(user_id, destination_id)` 唯一性；自定义收藏新增 `(user_id, custom_destination_id)` 唯一性。收藏快照保存名称、摘要和 emoji，因此列表不依赖目标表查询。

## API

- `GET /custom-destinations/search?keyword=...`：使用高德搜索，关键词至少 2 字，最多返回 5 条候选；没有高德密钥时返回稳定的服务不可用错误。
- `POST /custom-destinations`：接受高德候选的 POI ID、名称、地址、地区和坐标；按用户和 POI ID 幂等创建。
- `GET /custom-destinations/{id}`：仅创建者可读取。
- `POST /custom-guides/{custom_destination_id}`：接受现有 `GuideGenerationRequest`，使用自定义目的地和模式生成攻略。

任何跨用户读取或生成都返回 404；所有自定义地点请求使用既有 Bearer 认证。

## 小程序体验

推荐页在筛选摘要和一键推荐区之间增加主动地点卡片。输入不少于 2 个字后，点击“搜索地点”加载候选；候选展示名称和地址。选中后调用创建接口，跳转 `destination-detail`，URL 携带 `custom_id`、当前月份、天数、出发地和偏好。

详情页检测 `custom_id` 后，改为请求自定义地点资料、坐标天气和 `/custom-guides/{id}`；快速/深度按钮、收藏、已收藏回显与收藏详情保持同样行为。我的收藏列表使用快照名称和 `destination_type`，无需访问公共目的地。

## 错误处理

- 输入不足两字：前端提示补全地点名称，不请求后端。
- 无候选：展示“未找到具体地点，请换一个更完整的名称”。
- 高德服务失败或未配置：提示地点搜索暂不可用。
- 创建/生成失败：保留输入和候选；不跳转详情。
- 自定义地点删除不属于第一版范围，已创建的地点保留以支持其收藏与历史攻略。

## 验收

- 高德候选被验证并按用户 POI 唯一保存。
- 自定义地点不会出现在公共推荐结果中，也不会被其他用户读取。
- 选中地点会继承推荐页筛选，并能快速/深度生成、收藏、编辑。
- 前后端测试覆盖关键词校验、幂等创建、跨用户 404、跳转参数与无结果状态。
