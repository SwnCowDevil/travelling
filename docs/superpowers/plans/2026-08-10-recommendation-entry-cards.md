# 推荐页双入口卡片 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将推荐页的“想去哪里”和“一键推荐”做成共享筛选条件的、同时展开的同级白色入口卡片，并缩短一键推荐加载文案。

**Architecture:** 仅调整推荐页 WXML 和 WXSS，不改变现有的 `recommend`、`searchCustomDestination` 或筛选状态。视图静态测试负责锁定入口结构、文案和关键样式，以防后续又将一键推荐放回卡片之外。

**Tech Stack:** 微信小程序原生 WXML/WXSS、Node.js 内置测试运行器（`node --test`）。

## Global Constraints

- 共享的出发地、月份、游玩天数和偏好筛选条件不得复制或重置。
- 两个入口必须同时展开；不添加标签页、收起逻辑或后端接口变更。
- 一键推荐加载态文案必须是“正在推荐”，不得保留“正在为你推荐”。
- 只改动 `miniprogram` 前端，不改后端或数据库。

---

### Task 1: 锁定双入口卡片的视图契约

**Files:**
- Modify: `miniprogram/tests/pages/recommend-view.test.js`
- Modify: `miniprogram/miniprogram/pages/recommend/index.wxml`

**Interfaces:**
- Consumes: 既有 `customKeyword`、`customCandidates`、`searchingCustom`、`loading` 和事件处理器。
- Produces: 可由小程序直接渲染的 `custom-guide-card` 与 `quick-recommend-card` 两个相邻入口卡片。

- [ ] **Step 1: 写入会失败的视图测试**

在 `recommend-view.test.js` 中扩展推荐页断言，要求 WXML 同时包含两个明确的卡片类、提示文案和短加载文案：

```js
for (const token of ['custom-guide-card', 'quick-recommend-card', '不知道去哪？试试一键推荐', '正在推荐']) {
  assert.match(wxml, new RegExp(token))
}
assert.doesNotMatch(wxml, /正在为你推荐/)
```

- [ ] **Step 2: 运行测试，确认因新入口结构尚不存在而失败**

Run: `npm test -- tests/pages/recommend-view.test.js`

Expected: FAIL，缺少 `quick-recommend-card` 或“正在推荐”断言。

- [ ] **Step 3: 最小化调整 WXML 结构与文案**

保留现有“想去哪里”卡片的输入、候选地点与提示内容。将现有一键推荐按钮及其加载阶段文案移入紧随其后的白色卡片，并添加标题和说明：

```xml
<view class="quick-recommend-card">
  <text class="quick-recommend-title">✨ 一键推荐</text>
  <text class="quick-recommend-hint">不知道去哪？试试一键推荐</text>
  <button id="recommend-cta" class="recommend-cta {{loading ? 'loading' : ''}}" disabled="{{loading}}" bindtap="recommend">
    <view wx:if="{{loading}}" class="cta-spinner"></view>
    <text>{{loading ? '正在推荐' : '🚀 一键推荐'}}</text>
  </button>
  <text wx:if="{{loading}}" class="loading-stage-copy">{{stage}}</text>
</view>
```

- [ ] **Step 4: 运行目标测试，确认结构契约通过**

Run: `npm test -- tests/pages/recommend-view.test.js`

Expected: PASS。

### Task 2: 统一双卡片的视觉层级与加载态

**Files:**
- Modify: `miniprogram/tests/pages/recommend-view.test.js`
- Modify: `miniprogram/miniprogram/pages/recommend/index.wxss`

**Interfaces:**
- Consumes: Task 1 产出的 `custom-guide-card`、`quick-recommend-card`、`recommend-cta`、`loading-stage-copy` 类名。
- Produces: 两张同级白底卡片和不溢出的紧凑加载按钮样式。

- [ ] **Step 1: 写入会失败的样式测试**

在同一视图测试中读取 WXSS 后，断言两个入口卡片都有白底、圆角与阴影，且加载按钮禁止文字间距扩大：

```js
assert.match(wxss, /\.quick-recommend-card\{[^}]*background:#fff[^}]*border-radius:[^}]*box-shadow/)
assert.match(wxss, /\.custom-guide-card\{[^}]*background:#fff[^}]*border-radius:[^}]*box-shadow/)
assert.match(wxss, /\.recommend-cta\.loading\{[^}]*letter-spacing:0/)
```

- [ ] **Step 2: 运行测试，确认新卡片样式断言失败**

Run: `npm test -- tests/pages/recommend-view.test.js`

Expected: FAIL，缺少 `quick-recommend-card` 的样式规则。

- [ ] **Step 3: 最小化调整 WXSS**

让 `.cta-wrap` 仅负责纵向间距；为 `.custom-guide-card` 和 `.quick-recommend-card` 提供一致的白底、24rpx 圆角、轻阴影和内边距。为一键推荐卡片增加标题、说明和按钮顶部间距；保持绿色渐变主按钮、转圈动画与禁用状态。加载态增加 `letter-spacing:0`，让“正在推荐”在小屏中自然居中。

```css
.quick-recommend-card{padding:22rpx;border-radius:24rpx;background:#fff;box-shadow:0 6rpx 20rpx rgba(0,0,0,.05);text-align:left}
.quick-recommend-title,.quick-recommend-hint{display:block}
.quick-recommend-hint{margin-top:8rpx;color:#71807b;font-size:22rpx}
.quick-recommend-card .recommend-cta{margin-top:20rpx}
.recommend-cta.loading{opacity:.86;letter-spacing:0}
```

- [ ] **Step 4: 运行推荐页视图测试，确认通过**

Run: `npm test -- tests/pages/recommend-view.test.js`

Expected: PASS。

- [ ] **Step 5: 运行小程序全量测试**

Run: `npm test`

Expected: PASS，所有小程序测试无失败。

- [ ] **Step 6: 提交实现**

```bash
git add miniprogram/miniprogram/pages/recommend/index.wxml miniprogram/miniprogram/pages/recommend/index.wxss miniprogram/tests/pages/recommend-view.test.js
git commit -m "feat: unify recommendation entry cards"
```
