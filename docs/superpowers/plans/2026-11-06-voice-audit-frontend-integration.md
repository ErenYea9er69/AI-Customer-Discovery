# Voice Audit & Copywriting Frontend Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the frontend and supporting server/test layers 100% compatible with the new v3.3.0 prompt/reply audit, multi-tiered voice linter (`voice.py`), and v3.3.1 SQLite storage optimizations without altering the new audit files.

**Architecture:** 
1. Expose voice linting and disclosure phrase generation via `/api/voice/*` endpoints in `app.py`.
2. Update frontend TypeScript definitions in `types.ts` and API client in `api.ts` to support typed `LintReport` and `LintIssue`.
3. Overhaul `ReplyStudioView.tsx` to prevent React runtime object crashes, categorize linter feedback into blocking Errors vs advisory Warnings (slop frames, dashes, banned words, repeated openers, stiff register, etc.), support live debounced linting on the editable textarea, and provide an ethical disclosure phrase selector.
4. Enhance `SettingsView.tsx` with SQLite sync controls and auditor settings.
5. Align `pyproject.toml` and test harness so the entire test suite and frontend build pass 100%.

**Tech Stack:** React 19, TypeScript 5.8+, Vite 8, Lucide React, FastAPI, SQLite3 (WAL/indexes), Pytest.

**Spec:** `PROMPT_AUDIT.md`, `RESOURCE_AUDIT.md`, `agent_reach/discovery/voice.py`, `skills/community-copywriting/SKILL.md`.

---

## Global Constraints

- Do not modify or revert the newly provided audit and optimization files (`agent_reach/discovery/voice.py`, `agent_reach/discovery/storage.py`, `agent_reach/discovery/reply_generator.py`, `agent_reach/discovery/llm_client.py`, `agent_reach/discovery/platform_policy.py`, `skills/community-copywriting/*`, `tests/test_voice_lint.py`, `tests/test_resources.py`, `PROMPT_AUDIT.md`, `RESOURCE_AUDIT.md`, `CHANGELOG.md`).
- Follow the dark/slate design system defined in `frontend/src/App.css` and `index.css`.
- All React child nodes must be primitives (strings/numbers/elements), never raw objects.
- Ensure `npm run build` in `frontend` passes with zero type or bundling errors.
- Ensure all test suites pass with `python -m pytest`.

---

## Review Focus

1. **Linter Object Mapping**: Prevent React crashes where `reply.lint.issues` was mapped as strings instead of `{ code, severity, message }` objects.
2. **Version-Aware Lint Inspection**: Ensure `ReplyStudioView` switches between `value_first`, `product_aware`, and live `custom` lint reports cleanly.
3. **Slop Frame & Error Feedback**: Clearly explain new v3.3 rules (`contrast_frame`, `lead_in`, `empathy_script`, `closing_question`, `dash`, `banned_word`) so the user understands why an AI draft or edit was flagged.
4. **Live Debounced Linting**: As the user edits text in Reply Studio, trigger real-time lint feedback so they don't have to wait until approval to see violations.
5. **Full Harness Green State**: Clean pytest imports and fixtures across all test suites.

---

### Task 1: TypeScript Types and API Client Extensions

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api.ts`

- [x] **Step 1: Add typed Linting interfaces in `frontend/src/types.ts`**
  Add `LintSeverity`, `LintIssue`, `LintReport` types matching `agent_reach/discovery/voice.py`. Update `GeneratedReply.lint` from generic `Record<string, any>` to structured map `{ value_first?: LintReport; product_aware?: LintReport; final?: LintReport; [key: string]: any }`.
- [x] **Step 2: Add `lintText` and `getDisclosures` API methods in `frontend/src/api.ts`**
  Implement `api.lintText(text: string, kind?: string, platform?: string, leadId?: string): Promise<LintReport>` and `api.getDisclosures(): Promise<{ phrases: string[] }>`.
- [x] **Step 3: Run `npm run build` in `frontend/` to verify types**

---

### Task 2: Backend Voice & Linter Endpoints

**Files:**
- Modify: `agent_reach/server/app.py`
- Test: `tests/test_dashboard_team_api.py`

- [x] **Step 1: Add request model and `/api/voice/lint` endpoint to `agent_reach/server/app.py`**
  Accept `{ text: str, kind: Optional[str], platform: Optional[str], lead_id: Optional[str] }` and return `voice.lint_reply(...).to_dict()`.
- [x] **Step 2: Add `/api/voice/disclosures` endpoint to `agent_reach/server/app.py`**
  Fetch current business profile and return formatted disclosure phrases from `skillpack.disclosure_phrases()`.
- [x] **Step 3: Wire profile validation into `POST /api/replies/{lead_id}/approve`**
  Pass current `profile` to `reply_generator.approve_reply` so approving a custom reply checks rules and attaches the `final` lint report.

---

### Task 3: Interactive Reply Studio Overhaul (`ReplyStudioView.tsx`)

**Files:**
- Modify: `frontend/src/components/ReplyStudioView.tsx`
- Modify: `frontend/src/App.css`

- [x] **Step 1: Fix `reply.lint.issues` mapping and object rendering bug**
  Safely resolve the active `LintReport` based on `selectedVersion` (`value_first`, `product_aware`, or live `custom`).
- [x] **Step 2: Build categorized Error vs Warning Linter UI**
  Split issues into blocking **Errors** (red badge with rule name, explanation, and rewrite hint) and advisory **Warnings** (amber badge for style improvements: repeated openers, stacked triples, missing contractions, etc.).
- [x] **Step 3: Add debounced live linting on custom edits**
  When editing in the textarea, debounce (400ms) a call to `api.lintText` to provide immediate feedback before the user clicks Approve.
- [x] **Step 4: Add Ethical Disclosure Phrase selector**
  Allow the user to browse approved natural disclosure phrases and click to insert them into their reply draft.
- [x] **Step 5: Add platform word limit progress bar and badges**
  Visual indicator of word count vs maximum word limit for Reddit (150), Twitter/X (45), GitHub (120), etc.

---

### Task 4: Settings View & Storage Optimizations UI

**Files:**
- Modify: `frontend/src/components/SettingsView.tsx`

- [x] **Step 1: Add SQLite Sync Mode option (`AGENT_REACH_DB_SYNC`)**
  Provide dropdown with `NORMAL` (faster writes, standard durability), `EXTRA` (maximum durability), and `OFF` (development/testing).
- [x] **Step 2: Add Auditor Model Settings**
  Inputs for `AGENT_REACH_AUDITOR_PROVIDER` and `AGENT_REACH_AUDITOR_MODEL` with help text explaining independent verifier checks.

---

### Task 5: Python Test Suite & Harness Alignment

**Files:**
- Modify: `pyproject.toml`
- Modify: `tests/conftest.py`

- [x] **Step 1: Add `pythonpath = ["tests", "."]` to `pyproject.toml`**
  Ensure test files can import `conftest` without `ModuleNotFoundError`.
- [x] **Step 2: Restore missing legacy fixtures in `tests/conftest.py`**
  Add `now`, `VALUE_FIRST`, `PRODUCT_AWARE`, `make_lead`, and `lead` fixtures so unit tests in `test_reply_generator.py`, `test_orchestrator_cli.py`, `test_publisher.py`, `test_qualifier_planner.py`, and `test_accounts_threads.py` run cleanly.
- [x] **Step 3: Run full pytest suite to verify 100% green status**

---

### Task 6: End-to-End Build and Verification

- [x] **Step 1: Run `npm run build` in `frontend/`**
- [x] **Step 2: Run all backend tests and verify clean exit**
- [x] **Step 3: Verify stdio/MCP compatibility**
