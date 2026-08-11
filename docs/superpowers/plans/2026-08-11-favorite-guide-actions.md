# 收藏攻略操作按钮 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将收藏攻略详情页的操作按钮升级为横向等宽矩形主次操作。

**Architecture:** 保留已有的 `.actions` 与按钮事件，只通过 WXSS 的 Flex 布局和编辑态类区分视觉层级。测试读取视图源码，锁定关键布局与危险操作样式。

**Tech Stack:** 微信小程序 WXML/WXSS、Node.js 内置测试运行器。

## Global Constraints

- 不修改编辑、保存、取消、删除的 JavaScript 行为。
- 非编辑态的编辑与删除按钮横向等宽，非胶囊外观。
- 删除按钮保持红色描边；主操作保持绿色实心。

---

### Task 1: 收藏详情操作区样式

**Files:**
- Modify: `miniprogram/miniprogram/pages/favorite-guide-detail/index.wxss:1`
- Test: `miniprogram/tests/pages/favorite-guide-detail.test.js`

**Interfaces:**
- Consumes: `.actions`、`.primary`、`.danger` 与已有的 `bindtap` 事件。
- Produces: 76rpx 高、两列等宽、Flex 居中且有明确主次层级的按钮。

- [x] **Step 1: Write the failing test**

```js
test('favorite guide actions use rectangular two-column primary and danger styles', () => {
  const css = fs.readFileSync(path.join(dir, 'index.wxss'), 'utf8')
  assert.match(css, /\.actions\{[^}]*display:flex/)
  assert.match(css, /\.actions button\{[^}]*height:76rpx/)
  assert.match(css, /\.actions button\{[^}]*flex:1/)
  assert.match(css, /\.actions \.danger\{[^}]*border:2rpx solid #d76060/)
})
```

- [x] **Step 2: Run test to verify it fails**

Run: `npm test -- tests/pages/favorite-guide-detail.test.js`

Expected: failure because the old action layout is Flex with pill-shaped buttons.

- [x] **Step 3: Write minimal implementation**

```css
.actions{display:flex;flex-wrap:wrap;gap:16rpx}
.actions button{display:flex;align-items:center;justify-content:center;height:76rpx;border-radius:18rpx}
.actions .primary{background:#1bb28a;color:#fff}
.actions .danger{border:2rpx solid #d76060;background:#fff;color:#d76060}
```

- [x] **Step 4: Run focused and full tests**

Run: `npm test -- tests/pages/favorite-guide-detail.test.js && npm test`

Expected: all tests pass.

- [x] **Step 5: Commit**

```bash
git add miniprogram/miniprogram/pages/favorite-guide-detail/index.wxss miniprogram/tests/pages/favorite-guide-detail.test.js
git commit -m "style: refine favorite guide actions"
```
