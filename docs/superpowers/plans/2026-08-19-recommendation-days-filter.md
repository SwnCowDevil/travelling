# Recommendation Days Filter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore the recommendation-page play-days selector and preserve the selected day count when opening any generated guide.

**Architecture:** Keep `filters.days` as the single source of truth. Add a small pure `setDays` model operation, derive selected option and summary state from it, and pass `filters.days || 2` through existing detail navigation without changing backend schemas.

**Tech Stack:** Native WeChat Mini Program, JavaScript, WXML, Node.js test runner

**Spec:** `docs/superpowers/specs/2026-08-19-recommendation-days-filter-design.md`

## Global Constraints

- Day options are exactly `1, 2, 3, 5, 7`.
- Selecting the active option clears it.
- Unselected detail navigation uses 2 days.
- Recommendation requests omit `available_days` when no day is selected.
- No backend changes.

---

### Task 1: Add failing model and page tests

**Files:**
- Modify: `miniprogram/tests/pages/recommend.test.js`
- Modify: `miniprogram/tests/pages/recommend-view.test.js`

**Interfaces:**
- Consumes: `setDays(filters, value)`, `filterSummary(filters)`, `filterOptions(filters)`, `buildRequest(filters, origin)`, page `selectDays`, page `openDetail`
- Produces: regression coverage for selector state, API mapping, navigation, and WXML presence

- [ ] **Step 1: Add model assertions**

Assert exact options `[1, 2, 3, 5, 7]`, single-select toggle behavior, `3天` summary, `available_days: 3`, and reset to `null`.

- [ ] **Step 2: Add page assertions**

Assert `selectDays` refreshes state, summary removal clears days, and `openDetail` passes selected days or defaults to 2.

- [ ] **Step 3: Add view assertion**

Assert WXML contains the “游玩天数” title, the day-options loop, and `bindtap="selectDays"`.

- [ ] **Step 4: Verify RED**

Run: `cd miniprogram && node --test tests/pages/recommend.test.js tests/pages/recommend-view.test.js`

Expected: failures because the day model operation, UI, and navigation parameters do not exist.

### Task 2: Restore the day selector

**Files:**
- Modify: `miniprogram/miniprogram/pages/recommend/model.js`
- Modify: `miniprogram/miniprogram/pages/recommend/index.js`
- Modify: `miniprogram/miniprogram/pages/recommend/index.wxml`

**Interfaces:**
- Produces: `DAY_OPTIONS`, `setDays(filters, value)`, derived `filterOptions.days`, page `selectDays`, and day-aware detail URLs

- [ ] **Step 1: Implement model state**

Export `DAY_OPTIONS = [1, 2, 3, 5, 7]` and `setDays`; include selected day state in options, summaries, request mapping, and reset behavior.

- [ ] **Step 2: Implement page events**

Wire `selectDays`, clear day summaries, include days in the “更多” count, and add `days=${filters.days || 2}` to normal detail navigation.

- [ ] **Step 3: Implement WXML controls**

Render the day chips inside “更多”, replace the obsolete “天数可继续扩展” hint, and preserve existing reset/confirm actions.

- [ ] **Step 4: Verify GREEN**

Run: `cd miniprogram && node --test tests/pages/recommend.test.js tests/pages/recommend-view.test.js`

Expected: all selected tests pass.

### Task 3: Verify and commit

**Files:**
- No additional production files

**Interfaces:**
- Verifies the complete Mini Program regression suite

- [ ] **Step 1: Run complete tests**

Run: `cd miniprogram && npm test`

Expected: all tests pass.

- [ ] **Step 2: Check the diff**

Run `git diff --check` and confirm unrelated user files are not staged.

- [ ] **Step 3: Commit**

Commit only the model, page, tests, spec, and plan with `fix: restore recommendation days filter`.
