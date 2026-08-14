# DeepSeek Guide Transport Normalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent valid DeepSeek guides from failing when a daily itinerary `transport` value is returned as a string array.

**Architecture:** Normalize the known provider variation at the `ItineraryDay` schema boundary while retaining all existing length and structure validation. Strengthen both guide prompts so the model is explicitly asked for string-valued itinerary fields.

**Tech Stack:** Python 3.12, FastAPI, Pydantic 2, pytest

## Global Constraints

- Top-level `GuidePayload.transport` remains `list[str]`.
- Only a non-empty `list[str]` is normalized for `ItineraryDay.transport`.
- Other invalid values continue to raise Pydantic validation errors.
- No frontend or database migration changes.

---

### Task 1: Add regression coverage

**Files:**
- Modify: `backend/tests/guides/test_guides.py`

**Interfaces:**
- Consumes: `GuidePayload.model_validate(dict)`, `_guide_prompt(mode: str) -> str`
- Produces: regression assertions for list normalization and prompt field types

- [ ] **Step 1: Write a failing schema test**

Add a test that assigns `["高铁", "景区公交"]` to `itinerary[0].transport`, validates the payload, and expects `"高铁；景区公交"`.

- [ ] **Step 2: Write a failing prompt test**

Assert that both fast and deep prompts state that all daily itinerary text fields must be strings.

- [ ] **Step 3: Verify RED**

Run: `cd backend && PYTHONPATH=.:.. .venv/bin/python -m pytest tests/guides/test_guides.py -q`

Expected: the transport-array test fails with a Pydantic string-type validation error and the prompt test fails because the explicit constraint is absent.

### Task 2: Implement minimal compatibility

**Files:**
- Modify: `backend/app/guides/schemas.py`
- Modify: `backend/app/guides/router.py`

**Interfaces:**
- Produces: `ItineraryDay.transport: str` after validation for either a string or a valid non-empty string array input

- [ ] **Step 1: Add a pre-validation normalizer**

Use a Pydantic `field_validator` on `ItineraryDay.transport` that strips and joins a non-empty list of non-empty strings with `；`; return all other values unchanged so existing validation rejects them.

- [ ] **Step 2: Strengthen both prompts**

State that `theme`, `morning`, `afternoon`, `evening`, `transport`, and `caution` must each be a string and must not be an array or object.

- [ ] **Step 3: Verify GREEN**

Run: `cd backend && PYTHONPATH=.:.. .venv/bin/python -m pytest tests/guides/test_guides.py -q`

Expected: all guide tests pass.

### Task 3: Regression verification

**Files:**
- No additional files

**Interfaces:**
- Verifies: all backend behavior remains compatible

- [ ] **Step 1: Run the backend suite**

Run: `cd backend && PYTHONPATH=.:.. .venv/bin/python -m pytest -q`

Expected: all tests pass without warnings or errors.

- [ ] **Step 2: Review the diff**

Confirm only the schema boundary, guide prompts, tests, and these documents changed.

- [ ] **Step 3: Commit the fix**

Stage only the files from this plan and commit with `fix: normalize DeepSeek guide transport fields`.
