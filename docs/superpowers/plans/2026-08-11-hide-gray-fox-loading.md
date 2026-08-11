# Hide Gray Fox Loading Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop rendering the gray fox GIF in every page-level Loading state while preserving the shared component, copy, compact variant, and source asset.

**Architecture:** Make the rollback entirely inside `loading-stage`; calling pages remain unchanged. The component renders only its text, so removing one image node prevents all recommendation, guide, and favorite Loading states from decoding the GIF.

**Tech Stack:** WeChat native mini program, WXML/WXSS/JavaScript, Node.js built-in test runner.

## Global Constraints

- Keep `miniprogram/miniprogram/assets/images/loading-gray-fox.gif` unchanged.
- Do not render or reference the GIF from WXML.
- Keep `text` and `compact` component properties.
- Keep all page integrations, button Loading states, skeleton screens, API behavior, and backend code unchanged.

---

### Task 1: Hide the GIF in the Shared Loading Component

**Files:**
- Modify: `miniprogram/tests/components/loading-stage.test.js`
- Modify: `miniprogram/miniprogram/components/loading-stage/index.wxml`
- Modify: `miniprogram/miniprogram/components/loading-stage/index.wxss`

**Interfaces:**
- Consumes: existing `text: string` and `compact: boolean` properties.
- Produces: a text-only `<loading-stage>` with normal and compact typography.

- [ ] **Step 1: Change the component test to require text-only rendering**

```js
test('loading stage temporarily hides the gray fox but keeps text and compact mode',()=>{
  const js=read('index.js')
  const wxml=read('index.wxml')
  const wxss=read('index.wxss')
  const asset=path.resolve(componentDir,'../../assets/images/loading-gray-fox.gif')
  assert.match(js,/compact:\{type:Boolean,value:false\}/)
  assert.match(wxml,/class="loading \{\{compact \? 'compact' : ''\}\}"/)
  assert.match(wxml,/class="loading-copy"/)
  assert.doesNotMatch(wxml,/<image|loading-gray-fox\.gif|loading-fox/)
  assert.doesNotMatch(wxss,/\.loading-fox/)
  assert.equal(fs.readFileSync(asset).subarray(0,3).toString(),'GIF')
})
```

- [ ] **Step 2: Run the targeted test and verify RED**

Run: `cd miniprogram && npm test -- tests/components/loading-stage.test.js`

Expected: FAIL because the current WXML still contains the GIF image.

- [ ] **Step 3: Remove only the image rendering and obsolete styles**

Use this WXML:

```xml
<view class="loading {{compact ? 'compact' : ''}}">
  <text class="loading-copy">{{text}}</text>
</view>
```

Keep the fade-in animation. Change normal padding to `28rpx 24rpx`, compact padding to `18rpx 16rpx`, remove `.loading-fox` rules, and keep normal/compact text sizes at `24rpx` and `22rpx`.

- [ ] **Step 4: Run the targeted test and verify GREEN**

Run: `cd miniprogram && npm test -- tests/components/loading-stage.test.js`

Expected: PASS.

- [ ] **Step 5: Verify all page integrations remain valid**

Run: `cd miniprogram && npm test`

Expected: all tests PASS with zero failures.

- [ ] **Step 6: Verify asset preservation and clean diff**

Run:

```bash
cmp /Users/admin/Downloads/miniprogram_loading_gray_fox_192_v3.gif miniprogram/miniprogram/assets/images/loading-gray-fox.gif
git diff --check
```

Expected: both commands exit 0.

- [ ] **Step 7: Commit the rollback**

```bash
git add miniprogram/miniprogram/components/loading-stage/index.wxml miniprogram/miniprogram/components/loading-stage/index.wxss miniprogram/tests/components/loading-stage.test.js
git commit -m "fix: temporarily hide fox loading animation"
```
