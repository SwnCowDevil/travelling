# Gray Fox Loading Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the provided gray fox GIF to all page-level loading states while preserving compact native button spinners.

**Architecture:** Keep request state ownership in each page and make the existing `loading-stage` component presentation-only. The component renders a local GIF plus caller-provided text and size variant; pages conditionally mount it from their existing `loading` or `regenerating` booleans.

**Tech Stack:** WeChat native mini program, WXML/WXSS/JavaScript, Vant Weapp, Node.js built-in test runner.

## Global Constraints

- Use `/Users/admin/Downloads/miniprogram_loading_gray_fox_192_v3.gif` unchanged as the source asset.
- Publish the GIF inside the mini-program package; no network request may be required to render it.
- Use the GIF only for page-level waiting states.
- Keep native/Vant loading indicators for save, search, delete, and AI settings buttons.
- Do not change backend APIs, database models, or request timeouts.
- If the image cannot render, the loading copy must remain visible.

---

### Task 1: Reusable Gray Fox Loading Component

**Files:**
- Create: `miniprogram/miniprogram/assets/images/loading-gray-fox.gif`
- Modify: `miniprogram/miniprogram/components/loading-stage/index.js`
- Modify: `miniprogram/miniprogram/components/loading-stage/index.json`
- Modify: `miniprogram/miniprogram/components/loading-stage/index.wxml`
- Modify: `miniprogram/miniprogram/components/loading-stage/index.wxss`
- Create: `miniprogram/tests/components/loading-stage.test.js`

**Interfaces:**
- Consumes: component properties `text: string` and `compact: boolean`.
- Produces: `<loading-stage text="..." compact="{{true|false}}"/>`, rendering `/assets/images/loading-gray-fox.gif` and a separate text node.

- [ ] **Step 1: Write the failing component test**

```js
test('loading stage renders the local gray fox gif and supports compact mode',()=>{
  const js=read('index.js')
  const wxml=read('index.wxml')
  const wxss=read('index.wxss')
  const asset=path.resolve(componentDir,'../../assets/images/loading-gray-fox.gif')
  assert.match(js,/compact:\{type:Boolean,value:false\}/)
  assert.match(wxml,/src="\/assets\/images\/loading-gray-fox\.gif"/)
  assert.match(wxml,/class="loading \{\{compact \? 'compact' : ''\}\}"/)
  assert.match(wxml,/class="loading-fox"/)
  assert.match(wxml,/loading-copy/)
  assert.match(wxss,/\.loading-fox/)
  assert.equal(fs.readFileSync(asset).subarray(0,3).toString(),'GIF')
})
```

- [ ] **Step 2: Run the test and verify RED**

Run: `cd miniprogram && npm test -- tests/components/loading-stage.test.js`

Expected: FAIL because the component still renders `van-loading` and the local GIF does not exist.

- [ ] **Step 3: Copy the asset and implement the component**

Copy the source GIF byte-for-byte to `miniprogram/miniprogram/assets/images/loading-gray-fox.gif`. Define the properties as:

```js
Component({
  properties:{
    text:{type:String,value:'正在加载…'},
    compact:{type:Boolean,value:false},
  },
})
```

Render the image and copy independently:

```xml
<view class="loading {{compact ? 'compact' : ''}}">
  <image class="loading-fox" src="/assets/images/loading-gray-fox.gif" mode="aspectFit"/>
  <text class="loading-copy">{{text}}</text>
</view>
```

Remove the unused `van-loading` component registration. Style the default image at `160rpx × 160rpx`, compact image at `112rpx × 112rpx`, and retain the existing fade-in animation.

- [ ] **Step 4: Run the component test and verify GREEN**

Run: `cd miniprogram && npm test -- tests/components/loading-stage.test.js`

Expected: PASS.

- [ ] **Step 5: Commit the component deliverable**

```bash
git add miniprogram/miniprogram/assets/images/loading-gray-fox.gif miniprogram/miniprogram/components/loading-stage miniprogram/tests/components/loading-stage.test.js
git commit -m "feat: add gray fox loading component"
```

---

### Task 2: Recommendation and Guide Generation Loading

**Files:**
- Modify: `miniprogram/miniprogram/pages/recommend/index.json`
- Modify: `miniprogram/miniprogram/pages/recommend/index.wxml`
- Modify: `miniprogram/miniprogram/pages/recommend/index.wxss`
- Modify: `miniprogram/miniprogram/pages/destination-detail/index.json`
- Modify: `miniprogram/miniprogram/pages/destination-detail/index.wxml`
- Modify: `miniprogram/miniprogram/pages/destination-detail/index.wxss`
- Modify: `miniprogram/tests/pages/recommend-view.test.js`
- Modify: `miniprogram/tests/pages/destination-detail-view.test.js`

**Interfaces:**
- Consumes: `loading-stage` from Task 1 and existing page state `loading`, `stage`, `regenerating`, and `generationMode`.
- Produces: visible gray fox feedback for recommendation requests, initial detail loading, and fast/deep guide regeneration.

- [ ] **Step 1: Write failing page integration tests**

Add assertions that both page JSON files register `loading-stage`, recommendation WXML renders `<loading-stage wx:if="{{loading}}" text="{{stage}}"/>`, and detail WXML renders it for initial loading and regeneration. Keep assertions that `loading="{{searchingCustom}}"`, `loading="{{savingFavorite}}"`, and generation button disabling remain present.

```js
assert.equal(config.usingComponents['loading-stage'],'/components/loading-stage/index')
assert.match(wxml,/<loading-stage wx:if="\{\{loading\}\}" text="\{\{stage\}\}"\/>/)
assert.match(detailWxml,/<loading-stage wx:if="\{\{regenerating\}\}"/)
assert.match(detailWxml,/loading="\{\{savingFavorite\}\}"/)
```

- [ ] **Step 2: Run the page tests and verify RED**

Run: `cd miniprogram && npm test -- tests/pages/recommend-view.test.js tests/pages/destination-detail-view.test.js`

Expected: FAIL because neither page registers or renders the component.

- [ ] **Step 3: Implement recommendation loading**

Register `loading-stage` in `pages/recommend/index.json`. Remove the standalone stage-copy line from the quick-recommend card and render one `loading-stage` above the skeleton cards in the results area. Retain the compact button spinner and “正在推荐” copy so the pressed control still communicates its disabled state without showing the GIF twice.

- [ ] **Step 4: Implement detail and guide generation loading**

Register `loading-stage` in `pages/destination-detail/index.json`. Replace the initial skeleton-only branch with a wrapper containing `loading-stage text="正在准备目的地攻略…"` plus the existing skeleton. Inside the regenerate card, render `loading-stage` when `regenerating`, with text selected from `generationMode`:

```xml
<loading-stage wx:if="{{regenerating}}" compact="{{true}}" text="{{generationMode==='deep'?'正在深度生成攻略…':'正在快速生成攻略…'}}"/>
```

Keep both buttons disabled during regeneration and keep the previously rendered guide sections visible.

- [ ] **Step 5: Run the page tests and verify GREEN**

Run: `cd miniprogram && npm test -- tests/pages/recommend-view.test.js tests/pages/destination-detail-view.test.js`

Expected: PASS.

- [ ] **Step 6: Commit the recommendation/detail deliverable**

```bash
git add miniprogram/miniprogram/pages/recommend miniprogram/miniprogram/pages/destination-detail miniprogram/tests/pages/recommend-view.test.js miniprogram/tests/pages/destination-detail-view.test.js
git commit -m "feat: show fox animation during guide generation"
```

---

### Task 3: Favorite Guide Page Loading

**Files:**
- Modify: `miniprogram/miniprogram/pages/favorite-guides/index.json`
- Modify: `miniprogram/miniprogram/pages/favorite-guides/index.wxml`
- Modify: `miniprogram/miniprogram/pages/favorite-guide-detail/index.json`
- Modify: `miniprogram/miniprogram/pages/favorite-guide-detail/index.wxml`
- Modify: `miniprogram/tests/pages/favorite-guides.test.js`
- Modify: `miniprogram/tests/pages/favorite-guide-detail.test.js`

**Interfaces:**
- Consumes: Task 1 component and each page's existing `loading` boolean.
- Produces: compact gray fox feedback only during initial favorite data loads.

- [ ] **Step 1: Write failing favorite-page tests**

Assert both JSON files register `loading-stage`, and replace the expected pure loading copy with:

```js
assert.match(wxml,/<loading-stage wx:if="\{\{loading\}\}" compact="\{\{true\}\}" text="正在加载收藏攻略…"\/>/)
```

For the detail page, expect `text="正在加载攻略详情…"`. Retain assertions for empty/error copy and the save button's native `loading="{{saving}}"` behavior.

- [ ] **Step 2: Run the favorite page tests and verify RED**

Run: `cd miniprogram && npm test -- tests/pages/favorite-guides.test.js tests/pages/favorite-guide-detail.test.js`

Expected: FAIL because both pages render `正在加载…` in a plain view.

- [ ] **Step 3: Implement favorite loading states**

Register `loading-stage` in both JSON files. Replace only the first `wx:if="{{loading}}"` view in each WXML file with the compact component. Do not change the error, empty-list, edit, save, cancel, or delete branches.

- [ ] **Step 4: Run the favorite page tests and verify GREEN**

Run: `cd miniprogram && npm test -- tests/pages/favorite-guides.test.js tests/pages/favorite-guide-detail.test.js`

Expected: PASS.

- [ ] **Step 5: Commit the favorite-page deliverable**

```bash
git add miniprogram/miniprogram/pages/favorite-guides miniprogram/miniprogram/pages/favorite-guide-detail miniprogram/tests/pages/favorite-guides.test.js miniprogram/tests/pages/favorite-guide-detail.test.js
git commit -m "feat: animate favorite guide loading states"
```

---

### Task 4: Full Verification

**Files:**
- Verify only; no production files should be added in this task.

**Interfaces:**
- Consumes: all deliverables from Tasks 1–3.
- Produces: fresh evidence that the mini-program behavior and package remain valid.

- [ ] **Step 1: Verify the asset is unchanged**

Run:

```bash
cmp /Users/admin/Downloads/miniprogram_loading_gray_fox_192_v3.gif miniprogram/miniprogram/assets/images/loading-gray-fox.gif
file miniprogram/miniprogram/assets/images/loading-gray-fox.gif
```

Expected: `cmp` exits 0 and `file` reports `GIF image data, version 89a, 192 x 192`.

- [ ] **Step 2: Run the complete mini-program test suite**

Run: `cd miniprogram && npm test`

Expected: all tests PASS with zero failures.

- [ ] **Step 3: Check whitespace and intended scope**

Run: `git diff --check && git status --short`

Expected: no whitespace errors; only the user's pre-existing local files remain unstaged.

- [ ] **Step 4: Inspect the final commit range**

Run: `git log --oneline -5 && git status --short`

Expected: the three implementation commits are present, and `miniprogram/project.config.json`, `.superpowers/`, and SQLite WAL/SHM files were not committed.
