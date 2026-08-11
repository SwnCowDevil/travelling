# Profile Avatar and Filter Button Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep the profile avatar circular in flexible layouts and vertically center the recommendation filter action button labels.

**Architecture:** Both fixes are isolated WXSS corrections. Avatar sizing becomes non-shrinkable with a border-box square, while filter action buttons use Flexbox rather than line-height to center their text.

**Tech Stack:** WeChat native mini program, WXSS, Node.js built-in test runner.

## Global Constraints

- Keep all page structures, event handlers, colors, dimensions, and animations unchanged unless required for alignment.
- Preserve the avatar image `aspectFill` behavior and avatar selection flow.
- Preserve the 76rpx filter action button height.
- Do not modify backend code.

---

### Task 1: Lock Avatar Geometry and Button Text Alignment

**Files:**
- Modify: `miniprogram/tests/pages/me-view.test.js`
- Modify: `miniprogram/tests/pages/recommend-view.test.js`
- Modify: `miniprogram/miniprogram/pages/me/index.wxss`
- Modify: `miniprogram/miniprogram/pages/recommend/index.wxss`

**Interfaces:**
- Consumes: `.avatar` and `.panel-actions button` style selectors.
- Produces: a non-shrinkable square avatar and flex-centered filter action buttons.

- [ ] **Step 1: Write failing static style tests**

Add assertions to the profile view test:

```js
assert.match(wxss,/\.avatar\{[^}]*flex:0 0 132rpx/)
assert.match(wxss,/\.avatar\{[^}]*min-width:132rpx/)
assert.match(wxss,/\.avatar\{[^}]*min-height:132rpx/)
assert.match(wxss,/\.avatar\{[^}]*box-sizing:border-box/)
```

Add assertions to the recommendation view test:

```js
assert.match(wxss,/\.panel-actions button\{[^}]*display:flex/)
assert.match(wxss,/\.panel-actions button\{[^}]*align-items:center/)
assert.match(wxss,/\.panel-actions button\{[^}]*justify-content:center/)
assert.match(wxss,/\.panel-actions button\{[^}]*padding:0/)
assert.doesNotMatch(wxss,/\.panel-actions button\{[^}]*line-height:76rpx/)
```

- [ ] **Step 2: Run targeted tests and verify RED**

Run: `cd miniprogram && npm test -- tests/pages/me-view.test.js tests/pages/recommend-view.test.js`

Expected: FAIL because the avatar can shrink and action buttons use line-height.

- [ ] **Step 3: Implement the smallest WXSS fixes**

Extend `.avatar` with:

```css
flex:0 0 132rpx;
min-width:132rpx;
min-height:132rpx;
box-sizing:border-box;
```

Replace the `.panel-actions button` text alignment declarations with:

```css
display:flex;
align-items:center;
justify-content:center;
padding:0;
box-sizing:border-box;
```

Keep `height:76rpx`, remove `line-height:76rpx`, and retain all existing color, radius, and border rules.

- [ ] **Step 4: Run targeted tests and verify GREEN**

Run: `cd miniprogram && npm test -- tests/pages/me-view.test.js tests/pages/recommend-view.test.js`

Expected: PASS.

- [ ] **Step 5: Run the full mini-program suite**

Run: `cd miniprogram && npm test`

Expected: all tests PASS with zero failures.

- [ ] **Step 6: Verify whitespace and commit**

Run: `git diff --check`

Expected: exit 0.

```bash
git add miniprogram/miniprogram/pages/me/index.wxss miniprogram/miniprogram/pages/recommend/index.wxss miniprogram/tests/pages/me-view.test.js miniprogram/tests/pages/recommend-view.test.js
git commit -m "fix: align profile avatar and filter buttons"
```
