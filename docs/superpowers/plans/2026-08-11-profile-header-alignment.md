# 个人页头部左对齐 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 使个人页头像左侧固定，资料文字以 20rpx 间距紧邻头像右侧并始终左对齐。

**Architecture:** 仅调整个人页已有的 Flex 样式，不改变 WXML 结构、头像选择行为或数据绑定。视图测试通过断言关键 CSS 声明，防止后续样式回退。

**Tech Stack:** 微信小程序 WXML/WXSS、Node.js 内置测试运行器。

## Global Constraints

- 不修改头像上传交互、页面数据或其他页面。
- 头像仍使用 132rpx 的不可收缩圆形尺寸。
- 文字区与头像的视觉间距固定为 20rpx。

---

### Task 1: 个人资料头部对齐

**Files:**
- Modify: `miniprogram/miniprogram/pages/me/index.wxss:1-3`
- Test: `miniprogram/tests/pages/me-view.test.js`

**Interfaces:**
- Consumes: `.me-hero` 内既有的 `.avatar` 与 `.profile-copy` 结构。
- Produces: 左侧头像、右侧 20rpx 间距且左对齐的资料文字。

- [ ] **Step 1: Write the failing test**

```js
test('profile copy stays left aligned beside the avatar with a compact gap', () => {
  const wxss = fs.readFileSync(path.join(pageDir, 'index.wxss'), 'utf8')
  assert.match(wxss, /\\.me-hero\\{[^}]*gap:20rpx/)
  assert.match(wxss, /\\.profile-copy\\{[^}]*flex:0 1 auto/)
  assert.match(wxss, /\\.profile-copy\\{[^}]*text-align:left/)
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- tests/pages/me-view.test.js`

Expected: failure because the current gap is `30rpx` and profile copy has no explicit compact left-alignment declarations.

- [ ] **Step 3: Write minimal implementation**

```css
.me-hero{...;gap:20rpx;...}
.profile-copy{...;min-width:0;flex:0 1 auto;text-align:left}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- tests/pages/me-view.test.js`

Expected: PASS.

- [ ] **Step 5: Run the full mini-program suite**

Run: `npm test`

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add miniprogram/miniprogram/pages/me/index.wxss miniprogram/tests/pages/me-view.test.js
git commit -m "fix: align profile header content"
```
