# DeepSeek 官方接入、AI 标识与隐私授权实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将系统 AI 切换为 DeepSeek 官方 V4，并为快速/深度生成配置不同思考策略，在推荐、攻略和收藏中可靠标识 AI 来源，同时补齐定位隐私授权门禁和微信后台隐私指引。

**Architecture:** 继续使用现有 OpenAI Chat Completions 兼容客户端，在独立策略模块中决定模型、思考模式和输出上限。后端将 AI 来源随收藏持久化；小程序只根据后端 `source` 渲染标识。隐私服务独立封装微信隐私协议授权，定位服务在调用私有 API 前通过该门禁。

**Tech Stack:** Python 3.12、FastAPI、Pydantic、SQLAlchemy、Alembic、httpx、pytest、微信原生小程序、Node.js Test Runner

## Global Constraints

- 系统 DeepSeek API Key 只能进入 `backend/.env` 与服务器 `/etc/travelling/travel-api.env`，不得进入 Git、前端、文档、测试快照或日志。
- 只有后端明确返回 `source === "ai"` 的内容才显示 AI 生成标识。
- 规则兜底不得显示 AI 标识；历史收藏来源未知时不得推断来源。
- DeepSeek 厂商专用 `thinking` 字段只能发送给 `api.deepseek.com`。
- 保留个人 AI 配置的现有优先级，不静默覆盖用户个人 Token。
- 保留现有开发版/体验版/正式版 API 地址切换逻辑。
- 不覆盖工作区中与本任务无关的用户修改。

---

### Task 1: DeepSeek 请求策略

**Files:**
- Create: `backend/app/ai/policy.py`
- Modify: `backend/app/ai/client.py`
- Modify: `backend/tests/ai/test_client.py`
- Create: `backend/tests/ai/test_policy.py`

**Interfaces:**
- Produces: `AIRequestPolicy(thinking_enabled: bool | None, max_tokens: int)`
- Produces: `request_policy(base_url: str, purpose: Literal["rerank", "guide_fast", "guide_deep"]) -> AIRequestPolicy`
- Produces: `AIClient(..., thinking_enabled: bool | None = None, max_tokens: int | None = None)`

- [ ] **Step 1: 写 DeepSeek 与第三方地址的失败测试**

在 `backend/tests/ai/test_policy.py` 验证：

```python
from app.ai.policy import request_policy


def test_deepseek_official_policies_split_fast_and_deep() -> None:
    fast = request_policy("https://api.deepseek.com", "guide_fast")
    deep = request_policy("https://api.deepseek.com", "guide_deep")
    rerank = request_policy("https://api.deepseek.com", "rerank")

    assert (fast.thinking_enabled, fast.max_tokens) == (False, 6000)
    assert (deep.thinking_enabled, deep.max_tokens) == (True, 12000)
    assert (rerank.thinking_enabled, rerank.max_tokens) == (False, 1200)


def test_non_deepseek_provider_omits_vendor_thinking_field() -> None:
    policy = request_policy("https://provider.example/v1", "guide_fast")
    assert policy.thinking_enabled is None
    assert policy.max_tokens == 6000
```

- [ ] **Step 2: 运行策略测试确认失败**

Run:

```bash
cd backend && PYTHONPATH=.:.. .venv/bin/python -m pytest tests/ai/test_policy.py -q
```

Expected: FAIL，提示 `app.ai.policy` 不存在。

- [ ] **Step 3: 实现最小策略模块**

在 `backend/app/ai/policy.py` 实现冻结 dataclass、严格的目的枚举，以及使用 `urllib.parse.urlparse` 对主机名 `api.deepseek.com` 做精确匹配。第三方地址返回 `thinking_enabled=None`，但仍保留标准 `max_tokens` 上限。

- [ ] **Step 4: 运行策略测试确认通过**

Run 同 Step 2。

Expected: 2 tests PASS。

- [ ] **Step 5: 写客户端请求体失败测试**

在 `backend/tests/ai/test_client.py` 增加两个异步测试：

```python
@pytest.mark.asyncio
async def test_client_sends_configured_thinking_and_max_tokens() -> None:
    seen = {}
    async def handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        await AIClient(
            "https://api.deepseek.com", "sk-test", "deepseek-v4-flash",
            thinking_enabled=False, max_tokens=6000, http=http,
        ).complete_json("system", "user")
    assert seen["thinking"] == {"type": "disabled"}
    assert seen["max_tokens"] == 6000


@pytest.mark.asyncio
async def test_client_omits_thinking_when_policy_is_none() -> None:
    seen = {}
    async def handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        await AIClient(
            "https://provider.example/v1", "sk-test", "model",
            thinking_enabled=None, max_tokens=6000, http=http,
        ).complete_json("system", "user")
    assert "thinking" not in seen
    assert seen["max_tokens"] == 6000
```

- [ ] **Step 6: 运行客户端测试确认失败**

Run:

```bash
cd backend && PYTHONPATH=.:.. .venv/bin/python -m pytest tests/ai/test_client.py -q
```

Expected: FAIL，提示构造器不接受新参数或请求体缺字段。

- [ ] **Step 7: 最小实现客户端选项**

在 `AIClient.__init__` 保存两个可选字段；新增 `_apply_generation_options(payload)`，仅当值非空时添加 `max_tokens` 和 `thinking: {"type": "enabled" | "disabled"}`。`rerank` 与 `complete_json` 在 `_post` 前调用该方法；`test_connection` 保持自身 `max_tokens=1` 且不强制厂商字段。

- [ ] **Step 8: 运行 AI 测试并提交**

Run:

```bash
cd backend && PYTHONPATH=.:.. .venv/bin/python -m pytest tests/ai -q
```

Expected: 全部 PASS。

Commit:

```bash
git add backend/app/ai/policy.py backend/app/ai/client.py backend/tests/ai/test_policy.py backend/tests/ai/test_client.py
git commit -m "feat: add DeepSeek request policies"
```

### Task 2: 官方模型配置与调用路由

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/.env.example`
- Modify: `backend/app/guides/router.py`
- Modify: `backend/app/recommendations/router.py`
- Modify: `backend/app/guides/service.py`
- Modify: `backend/tests/test_config.py`
- Modify: `backend/tests/guides/test_guides.py`
- Modify: `backend/tests/recommendations/test_api.py`

**Interfaces:**
- Consumes: Task 1 的 `request_policy`
- Produces: 系统默认 `https://api.deepseek.com`、`deepseek-v4-pro`、`deepseek-v4-flash`

- [ ] **Step 1: 写默认配置与路由策略失败测试**

修改 `backend/tests/test_config.py`，断言系统默认地址为 `https://api.deepseek.com` 且快速模型为 `deepseek-v4-flash`。在攻略与推荐测试中通过依赖函数或可观察构造参数断言：快速攻略使用 Flash/关闭思考/6000，深度攻略使用 Pro/开启思考/12000，推荐使用 Pro/关闭思考/1200。

- [ ] **Step 2: 运行目标测试确认失败**

Run:

```bash
cd backend && PYTHONPATH=.:.. .venv/bin/python -m pytest tests/test_config.py tests/guides tests/recommendations -q
```

Expected: FAIL，至少默认地址仍为 PackyAPI，路由未传入策略。

- [ ] **Step 3: 更新系统默认配置**

将 `Settings.ai_base_url` 和 `backend/.env.example` 改为 `https://api.deepseek.com`；在 `.env.example` 显式增加：

```dotenv
TRAVEL_AI_MODEL=deepseek-v4-pro
TRAVEL_AI_FAST_MODEL=deepseek-v4-flash
```

真实 Key 保持空白。

- [ ] **Step 4: 接入路由策略**

攻略路由根据 `generation_mode` 调用 `request_policy(base_url, "guide_fast" | "guide_deep")`，将结果传入 `AIClient`。推荐路由使用 `request_policy(base_url, "rerank")`。个人第三方地址由策略自动省略 `thinking`，个人官方 DeepSeek 地址获得相同模式控制。

- [ ] **Step 5: 使旧攻略缓存失效**

将 `GUIDE_CONTENT_VERSION` 从 `rich-v2` 升为 `rich-v3-deepseek-policy`，确保旧中转站缓存不被当成新版本结果。

- [ ] **Step 6: 运行目标测试并提交**

Run 同 Step 2。

Expected: 全部 PASS。

Commit:

```bash
git add backend/app/core/config.py backend/.env.example backend/app/guides/router.py backend/app/recommendations/router.py backend/app/guides/service.py backend/tests/test_config.py backend/tests/guides backend/tests/recommendations
git commit -m "feat: route AI requests to official DeepSeek"
```

### Task 3: 收藏攻略来源与编辑状态

**Files:**
- Create: `backend/alembic/versions/0012_favorite_ai_provenance.py`
- Modify: `backend/app/favorites/models.py`
- Modify: `backend/app/favorites/schemas.py`
- Modify: `backend/app/favorites/service.py`
- Modify: `backend/app/favorites/router.py`
- Modify: `backend/tests/favorites/test_favorites.py`

**Interfaces:**
- Produces: `FavoriteGuide.source: Literal["ai", "rules", "unknown"]`
- Produces: `FavoriteGuide.user_edited: bool`
- `FavoriteGuideCreate` 必须携带 `source`
- `FavoriteGuideUpdate` 不允许修改来源，成功编辑后后端设置 `user_edited=True`

- [ ] **Step 1: 写来源持久化失败测试**

扩展收藏测试：创建 AI 收藏后 `source == "ai"` 且 `user_edited is False`；更新后 `source` 不变且 `user_edited is True`；规则收藏保留 `rules`；迁移后的旧行默认 `unknown`。

- [ ] **Step 2: 运行收藏测试确认失败**

Run:

```bash
cd backend && PYTHONPATH=.:.. .venv/bin/python -m pytest tests/favorites -q
```

Expected: FAIL，模型和响应没有来源字段。

- [ ] **Step 3: 创建迁移**

`0012_favorite_ai_provenance.py` 以 `0011_map_region_boundaries` 为上一个 revision，新增：

```python
source = sa.Column("source", sa.String(10), nullable=False, server_default="unknown")
user_edited = sa.Column("user_edited", sa.Boolean(), nullable=False, server_default=sa.false())
```

不对历史行推断 AI 来源。

- [ ] **Step 4: 更新模型、Schema、服务与路由**

创建时从请求保存 `source`；更新收藏内容时只把 `user_edited` 设为 `True`，不接受客户端修改来源；所有列表和详情响应返回两个字段。并发幂等回查仍返回数据库中已有来源。

- [ ] **Step 5: 运行迁移和收藏测试**

Run:

```bash
cd backend && .venv/bin/alembic upgrade head && PYTHONPATH=.:.. .venv/bin/python -m pytest tests/favorites -q
```

Expected: 迁移成功，收藏测试全部 PASS。

- [ ] **Step 6: 提交**

```bash
git add backend/alembic/versions/0012_favorite_ai_provenance.py backend/app/favorites backend/tests/favorites
git commit -m "feat: preserve AI provenance in favorite guides"
```

### Task 4: 小程序 AI 生成标识

**Files:**
- Modify: `miniprogram/miniprogram/pages/recommend/index.js`
- Modify: `miniprogram/miniprogram/pages/recommend/index.wxml`
- Modify: `miniprogram/miniprogram/pages/recommend/index.wxss`
- Modify: `miniprogram/miniprogram/pages/destination-detail/model.js`
- Modify: `miniprogram/miniprogram/pages/destination-detail/index.js`
- Modify: `miniprogram/miniprogram/pages/destination-detail/index.wxml`
- Modify: `miniprogram/miniprogram/pages/destination-detail/index.wxss`
- Modify: `miniprogram/miniprogram/pages/favorite-guide-detail/index.js`
- Modify: `miniprogram/miniprogram/pages/favorite-guide-detail/index.wxml`
- Modify: `miniprogram/miniprogram/pages/favorite-guide-detail/index.wxss`
- Modify: `miniprogram/miniprogram/pages/favorite-guides/index.wxml`
- Modify: `miniprogram/tests/pages/recommend.test.js`
- Modify: `miniprogram/tests/pages/recommend-view.test.js`
- Modify: `miniprogram/tests/pages/destination-detail.test.js`
- Modify: `miniprogram/tests/pages/destination-detail-view.test.js`
- Modify: `miniprogram/tests/pages/favorite-guide-detail.test.js`

**Interfaces:**
- Consumes: 推荐/攻略响应 `source`
- Consumes: 收藏响应 `source`、`user_edited`
- Produces: 互斥且持久的 AI/规则/未知来源文案

- [ ] **Step 1: 写推荐来源状态失败测试**

验证首次推荐与“换一批”都会设置 `aiGenerated = data.source === "ai"` 和 `fallback = data.source === "rules"`；AI 与规则状态互斥。静态视图测试要求出现“AI 生成建议”“行程与实时信息请核验”和现有规则提示。

- [ ] **Step 2: 运行推荐测试确认失败**

Run:

```bash
cd miniprogram && npm test -- tests/pages/recommend.test.js tests/pages/recommend-view.test.js
```

Expected: FAIL，`aiGenerated` 和 AI 提示条不存在。

- [ ] **Step 3: 实现推荐标识**

在页面 data 增加 `aiGenerated:false`；两条响应路径同时更新 `aiGenerated` 与 `fallback`。WXML 在结果标题下按状态展示互斥提示条，WXSS 使用非胶囊、易读的浅紫/绿色信息卡样式。

- [ ] **Step 4: 写详情来源失败测试并实现**

`buildDetailView` 增加 `isAIGenerated`、`guideSourceLabel` 与 `sourceNotice`。AI 文案为“AI 生成”和“AI 生成内容｜景区开放、票价、交通和天气请以官方信息为准”；规则文案为“规则参考”和“规则参考内容｜AI 未参与”。详情 WXML 在 meta 后显示独立提示条。

- [ ] **Step 5: 写收藏来源失败测试并实现**

收藏创建请求加入 `source:this.guideResponse.source`。收藏详情增加纯函数 `favoriteSourceLabel(source, userEdited)`，映射四种文案；编辑保存后使用后端返回的 `user_edited` 立即刷新。收藏列表同样显示来源标签。

- [ ] **Step 6: 运行页面测试并提交**

Run:

```bash
cd miniprogram && npm test -- tests/pages/recommend.test.js tests/pages/recommend-view.test.js tests/pages/destination-detail.test.js tests/pages/destination-detail-view.test.js tests/pages/destination-detail-regenerate.test.js tests/pages/favorite-guide-detail.test.js tests/pages/favorite-guides.test.js
```

Expected: 全部 PASS。

Commit:

```bash
git add miniprogram/miniprogram/pages/recommend miniprogram/miniprogram/pages/destination-detail miniprogram/miniprogram/pages/favorite-guide-detail miniprogram/miniprogram/pages/favorite-guides miniprogram/tests/pages
git commit -m "feat: label AI generated travel content"
```

### Task 5: 微信隐私授权门禁与指引

**Files:**
- Create: `miniprogram/miniprogram/services/privacy.js`
- Modify: `miniprogram/miniprogram/services/location.js`
- Modify: `miniprogram/miniprogram/app.json`
- Create: `miniprogram/tests/services/privacy.test.js`
- Modify: `miniprogram/tests/services/location.test.js`
- Modify: `miniprogram/tests/config/location-permission.test.js`
- Create: `docs/deployment/wechat-privacy-guide.md`

**Interfaces:**
- Produces: `ensurePrivacyAuthorized(wxApi) -> Promise<boolean>`
- `createLocationService(wxApi)` 在 `getLocation`、`chooseLocation` 前调用隐私门禁

- [ ] **Step 1: 写隐私服务失败测试**

测试三条路径：无需授权直接返回 true；需要授权且 `requirePrivacyAuthorize` 成功返回 true；拒绝返回 false；API 不存在时为兼容旧基础库返回 true。

- [ ] **Step 2: 运行隐私测试确认失败**

Run:

```bash
cd miniprogram && npm test -- tests/services/privacy.test.js
```

Expected: FAIL，模块不存在。

- [ ] **Step 3: 实现隐私服务**

使用 Promise 封装回调 API。`getPrivacySetting` 失败时返回 false；只有两个隐私 API 都不存在时走兼容 true。不得循环调用授权弹窗。

- [ ] **Step 4: 写定位门禁失败测试**

为 `getLocation` 和 `chooseLocation` 分别验证：隐私授权成功才调用实际接口；拒绝时接口调用次数为 0。拒绝自动定位返回 `{type:"manual_required"}`；拒绝地图选点以 `errMsg` 含 `privacy deny` 的错误结束。

- [ ] **Step 5: 接入定位门禁并更新 app.json**

将两条定位方法改为 async/Promise 流程，在隐私门禁成功后才调用微信接口。`app.json` 增加：

```json
"__usePrivacyCheck__": true
```

保留现有 `permission.scope.userLocation` 和 `requiredPrivateInfos`。

- [ ] **Step 6: 编写微信后台隐私指引**

`docs/deployment/wechat-privacy-guide.md` 必须按实际代码描述位置信息、微信登录标识、足迹/收藏/到访记录、个人 AI Token、高德/DeepSeek/阿里云第三方处理、保存方式和用户删除路径。明确头像当前不上传后端；账号级数据删除入口尚未提供，提交正式审核前需提供联系渠道或删除入口。

- [ ] **Step 7: 运行隐私与定位测试并提交**

Run:

```bash
cd miniprogram && npm test -- tests/services/privacy.test.js tests/services/location.test.js tests/config/location-permission.test.js
```

Expected: 全部 PASS。

Commit:

```bash
git add miniprogram/miniprogram/services/privacy.js miniprogram/miniprogram/services/location.js miniprogram/miniprogram/app.json miniprogram/tests/services/privacy.test.js miniprogram/tests/services/location.test.js miniprogram/tests/config/location-permission.test.js docs/deployment/wechat-privacy-guide.md
git commit -m "feat: gate private location APIs behind consent"
```

### Task 6: 官方 Key 配置、全量验证与部署

**Files:**
- Modify, ignored: `backend/.env`
- Modify on server: `/etc/travelling/travel-api.env`
- Execute on server: `/opt/travelling/scripts/restart-backend.sh`

**Interfaces:**
- Consumes: 用户持有的 DeepSeek 官方 API Key，通过终端隐藏输入
- Produces: 本地和线上系统模式直连 `api.deepseek.com`

- [ ] **Step 1: 运行本地全量测试和迁移**

Run:

```bash
cd backend && .venv/bin/alembic upgrade head && PYTHONPATH=.:.. .venv/bin/python -m pytest -q
cd ../miniprogram && npm test
cd .. && git diff --check
```

Expected: 后端、小程序全部 PASS，迁移和 diff 检查成功。

- [ ] **Step 2: 检查秘密未进入 Git**

从被忽略的 `.env` 读取 Key 到临时 shell 变量，用 `git grep -F` 扫描跟踪文件；只输出 clean/leak 状态，不输出 Key。确认 `git check-ignore backend/.env` 成功。

- [ ] **Step 3: 更新本地私密配置**

将本地 `backend/.env` 的地址、两个模型和 API Key 更新为 DeepSeek 官方值。Key 通过终端隐藏输入或受控补丁写入，任何验证只打印是否配置与长度。

- [ ] **Step 4: 部署后端代码与迁移**

按现有挂载式部署流程同步后端代码及迁移到 `/opt/travelling/backend`，不重新打业务镜像。先备份 `/etc/travelling/travel-api.env`，再由用户在服务器终端隐藏输入官方 Key，同时更新：

```dotenv
TRAVEL_AI_BASE_URL=https://api.deepseek.com
TRAVEL_AI_MODEL=deepseek-v4-pro
TRAVEL_AI_FAST_MODEL=deepseek-v4-flash
```

- [ ] **Step 5: 重启并脱敏验证**

Run on server:

```bash
/opt/travelling/scripts/restart-backend.sh
curl -fsS http://127.0.0.1:8000/health
```

Expected: `{"status":"ok"}`。额外脱敏检查只确认地址、模型和 Key 长度，不显示 Key。

- [ ] **Step 6: 恢复系统默认并真机验证**

在“我的 → AI 设置”点击“恢复系统默认”，避免旧个人 PackyAPI 配置继续覆盖系统。ICP、HTTPS 和 request 合法域名生效后，体验版验证一键推荐、快速攻略、深度攻略、收藏编辑、AI 标识、隐私授权同意/拒绝路径。

- [ ] **Step 7: 交付剩余后台操作**

依据 `docs/deployment/wechat-privacy-guide.md` 填写微信公众平台隐私保护指引；补充账号级数据删除或联系渠道；核对 DeepSeek 模型备案号/上线编号和生成式 AI 应用登记要求；正式发布前轮换任何曾在聊天中出现的密钥。
