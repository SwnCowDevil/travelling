# 小程序运行环境接口切换 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 开发版自动连接本地 FastAPI，体验版和正式版自动连接 `https://api.sunks.cc`，且线上环境始终关闭开发登录。

**Architecture:** 新建独立运行时配置模块，将环境识别和配置映射与 `app.js` 解耦。`app.js` 启动时读取一次配置，将接口地址和登录模式存入 `globalData`，再创建 API 客户端。

**Tech Stack:** 微信原生小程序、CommonJS、Node.js 内置测试运行器。

## Global Constraints

- `develop` 使用 `http://127.0.0.1:8000` 和开发登录。
- `trial`、`release` 使用 `https://api.sunks.cc` 并关闭开发登录。
- 读取失败、缺失或未知环境按 `develop` 处理。
- 配置中不得包含 Token、AppSecret 或 API Key。

---

### Task 1: 运行环境配置解析与应用启动集成

**Files:**
- Create: `miniprogram/miniprogram/config/runtime.js`
- Modify: `miniprogram/miniprogram/app.js`
- Delete: `miniprogram/miniprogram/config/local.js`
- Create: `miniprogram/tests/config/runtime.test.js`
- Delete: `miniprogram/tests/config/local.test.js`
- Modify: `miniprogram/tests/app.test.js`

**Interfaces:**
- Consumes: `wx.getAccountInfoSync(): { miniProgram?: { envVersion?: string } }`
- Produces: `resolveRuntimeConfig(envVersion): { apiBaseUrl: string, useDevAuth: boolean }`
- Produces: `getRuntimeConfig(wxApi): { apiBaseUrl: string, useDevAuth: boolean }`

- [ ] **Step 1: 写运行时配置的失败测试**

创建 `miniprogram/tests/config/runtime.test.js`：

```js
const test = require('node:test')
const assert = require('node:assert/strict')
const { resolveRuntimeConfig, getRuntimeConfig } = require('../../miniprogram/config/runtime')

test('develop uses the local API and development authentication', () => {
  assert.deepEqual(resolveRuntimeConfig('develop'), {
    apiBaseUrl: 'http://127.0.0.1:8000',
    useDevAuth: true
  })
})

test('trial and release use the production API and real authentication', () => {
  for (const envVersion of ['trial', 'release']) {
    assert.deepEqual(resolveRuntimeConfig(envVersion), {
      apiBaseUrl: 'https://api.sunks.cc',
      useDevAuth: false
    })
  }
})

test('missing, unknown, and unreadable environments fall back to develop', () => {
  assert.equal(resolveRuntimeConfig().apiBaseUrl, 'http://127.0.0.1:8000')
  assert.equal(resolveRuntimeConfig('unknown').useDevAuth, true)
  assert.equal(getRuntimeConfig({ getAccountInfoSync() { throw new Error('unavailable') } }).useDevAuth, true)
})

test('runtime configuration exposes no credential fields', () => {
  const keys = Object.keys(resolveRuntimeConfig('release')).join(' ').toLowerCase()
  assert.doesNotMatch(keys, /token|secret|api.?key/)
})
```

- [ ] **Step 2: 运行测试并确认因模块缺失而失败**

Run: `cd miniprogram && node --test tests/config/runtime.test.js`

Expected: FAIL，错误包含 `Cannot find module '../../miniprogram/config/runtime'`。

- [ ] **Step 3: 实现最小运行时配置模块**

创建 `miniprogram/miniprogram/config/runtime.js`：

```js
const DEVELOP_CONFIG = Object.freeze({
  apiBaseUrl: 'http://127.0.0.1:8000',
  useDevAuth: true
})

const PRODUCTION_CONFIG = Object.freeze({
  apiBaseUrl: 'https://api.sunks.cc',
  useDevAuth: false
})

function resolveRuntimeConfig(envVersion) {
  const selected = envVersion === 'trial' || envVersion === 'release'
    ? PRODUCTION_CONFIG
    : DEVELOP_CONFIG
  return { ...selected }
}

function getRuntimeConfig(wxApi) {
  try {
    const account = wxApi && typeof wxApi.getAccountInfoSync === 'function'
      ? wxApi.getAccountInfoSync()
      : null
    return resolveRuntimeConfig(account && account.miniProgram && account.miniProgram.envVersion)
  } catch (_) {
    return resolveRuntimeConfig('develop')
  }
}

module.exports = { resolveRuntimeConfig, getRuntimeConfig }
```

- [ ] **Step 4: 运行配置测试并确认通过**

Run: `cd miniprogram && node --test tests/config/runtime.test.js`

Expected: 4 tests PASS。

- [ ] **Step 5: 写 App 集成的失败断言**

在 `miniprogram/tests/app.test.js` 的微信模拟对象中增加：

```js
getAccountInfoSync: () => ({ miniProgram: { envVersion: 'trial' } }),
login: ({ success }) => success({ code: 'wx-code' }),
```

在 `definition.onLaunch.call(app)` 后增加：

```js
assert.equal(app.globalData.apiBaseUrl, 'https://api.sunks.cc')
assert.equal(app.globalData.useDevAuth, false)
```

Run: `cd miniprogram && node --test tests/app.test.js`

Expected: FAIL，因为 `app.js` 仍固定使用本地配置。

- [ ] **Step 6: 将 App 启动流程接入运行时配置**

将 `miniprogram/miniprogram/app.js` 改为：

```js
const { createApiClient } = require('./services/api')
const { login } = require('./services/auth')
const { getRuntimeConfig } = require('./config/runtime')

App({
  globalData: {
    apiBaseUrl: '',
    useDevAuth: false,
    api: null,
    authReady: null
  },
  onLaunch() {
    const runtimeConfig = getRuntimeConfig(wx)
    this.globalData.apiBaseUrl = runtimeConfig.apiBaseUrl
    this.globalData.useDevAuth = runtimeConfig.useDevAuth
    this.globalData.api = createApiClient(wx, runtimeConfig.apiBaseUrl)
    this.ensureAuthenticated()
  },
  ensureAuthenticated() {
    const attempt = login(wx, this.globalData.api, { useDevAuth: this.globalData.useDevAuth })
      .then(() => true)
      .catch(() => {
        wx.showToast({ title: this.globalData.useDevAuth ? '本地登录失败' : '微信登录失败', icon: 'none' })
        return false
      })
    this.globalData.authReady = attempt
    return attempt
  }
})
```

删除已不再使用的 `miniprogram/miniprogram/config/local.js` 与 `miniprogram/tests/config/local.test.js`。

- [ ] **Step 7: 运行小程序全量测试**

Run: `cd miniprogram && npm test`

Expected: 全部测试 PASS，且不再有代码引用 `config/local`。

Run: `rg -n "config/local|127\\.0\\.0\\.1:8000" miniprogram/miniprogram miniprogram/tests`

Expected: 只在 `config/runtime.js` 和对应测试中找到本地地址，不再找到 `config/local`。

- [ ] **Step 8: 提交实现**

```bash
git add miniprogram/miniprogram/app.js \
  miniprogram/miniprogram/config/runtime.js \
  miniprogram/tests/app.test.js \
  miniprogram/tests/config/runtime.test.js \
  miniprogram/miniprogram/config/local.js \
  miniprogram/tests/config/local.test.js
git commit -m "feat: switch mini program API by runtime environment"
```

- [ ] **Step 9: 真机发布前验证**

在微信公众平台将 `https://api.sunks.cc` 加入 request 合法域名，并在 ECS 的 `/etc/travelling/travel-api.env` 补齐 `TRAVEL_WECHAT_APP_ID`、`TRAVEL_WECHAT_APP_SECRET`。上传体验版后验证登录、推荐、攻略生成和收藏；开发者工具中的 `develop` 版本继续连接本地服务。
