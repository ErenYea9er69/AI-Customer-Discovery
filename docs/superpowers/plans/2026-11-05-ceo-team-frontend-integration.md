# CEO & Autonomous Team Frontend Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the new Agent Reach Company & CEO orchestration layer (`v3.2.0`) into the web dashboard, providing a first-class CEO Command Center, interactive task DAG visualizer, human-in-the-loop checkpoint resolver, verified report inspector, and company memory manager.

**Architecture:** Extend the React/TypeScript frontend with full `/api/team/*` API client methods, TypeScript interfaces matching the Python Pydantic models in `agent_reach/team/models.py`, and build `TeamView.tsx` with responsive sub-components for directives, DAG pipeline progress, checkpoints, verified reports, and standing memory preferences. Embed mission progress into `OverviewView.tsx` and sidebar navigation.

**Tech Stack:** React 19, TypeScript 5.8+, Vite 8, Lucide React, FastAPI backend.

---

## Global Constraints

- Never modify the backend company layer files (`agent_reach/team/*`, `agent_reach/server/app.py`, `skills/company-operations/*`) as they serve as the ground truth.
- Follow the existing dark/slate design system in `frontend/src/App.css` and `index.css`.
- All checkpoint decisions submitted from the dashboard must record channel `via: "dashboard"`.
- Ensure clean TypeScript build (`npm run build` passes with zero errors or warnings).

---

## Review Focus

1. **Directive Polling & Reactivity**: Background runs must update progress without page reloads while a directive is in state `running` or `open`.
2. **Checkpoint Resolution**: When a task enters `needs_owner`, prompt the user with clear context (profile summary or info request) and send approve/reject with owner words.
3. **Empty States**: Friendly, instructive empty state when no directive has been launched yet with actionable starter prompts.
4. **Verified Report Trust Visualization**: Prominently display trust level (`high`, `medium`, `low`, `none`, `partial`) and verbatim evidence quotes.
5. **Synergy with Leads & Replies**: Links from team lead cards directly open the lead in Leads Inbox or Reply Studio.

---

### Task 1: Type Definitions and API Client Extensions

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api.ts`

- [ ] **Step 1: Add Team and Directive TypeScript types to `frontend/src/types.ts`**
  Add `Directive`, `DirectiveStatus`, `Task`, `TaskStatus`, `Verdict`, `Evidence`, `TeamReport`, `InspectionRow`, `LeadCard`, `RoleSpec`, `Playbook`, `MemoryItem`, `NextStep`, `AskCeoResponse`, `TeamRoster`.
- [ ] **Step 2: Add Team API methods to `frontend/src/api.ts`**
  Implement `api.team` with `ask`, `listDirectives`, `getDirective`, `runDirective`, `getReport`, `resolveCheckpoint`, `getNextStep`, `cancelDirective`, `getMemory`, `addMemory`, `deleteMemory`, and `getRoster`.
- [ ] **Step 3: Run `npm run build` in `frontend` to verify type checking**

---

### Task 2: Build the CEO & Team Command Center Component (`TeamView.tsx`)

**Files:**
- Create: `frontend/src/components/TeamView.tsx`

- [ ] **Step 1: Create CEO Command Bar with starter prompts**
  Provide input field with submit handler, loading indicator, and quick starter buttons.
- [ ] **Step 2: Create Directive Mission Pipeline (DAG / Task Cards)**
  Show directive progress bar, status badges, and expandable task cards with role tags, attempts, dependencies, and verification status.
- [ ] **Step 3: Create Checkpoint Resolver Card**
  Render when tasks have `status === "needs_owner"`, showing question, textarea for feedback, and Approve / Reject buttons.
- [ ] **Step 4: Create Verified Report Modal / Viewer**
  Display headline, trust badge, lead cards with verified quotes and gate inspection pills, tried queries, quality numbers, and owner next actions.
- [ ] **Step 5: Create Roster & Memory Preferences Panel**
  Allow viewing active specialists/tools and managing persistent company memory rules.

---

### Task 3: Global Styling & Design System Integration

**Files:**
- Modify: `frontend/src/App.css`

- [ ] **Step 1: Add styles for TeamView layout, CEO bar, and prompt chips**
- [ ] **Step 2: Add styles for Directive pipeline, task nodes, and checkpoint callout**
- [ ] **Step 3: Add styles for Report drawer, trust badges (high/med/low), and inspection badges**
- [ ] **Step 4: Add styles for Memory preferences list and delete controls**

---

### Task 4: Navigation, Overview Bridge, and Polish

**Files:**
- Modify: `frontend/src/components/Sidebar.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/OverviewView.tsx`

- [ ] **Step 1: Add "CEO & Team" navigation tab in `Sidebar.tsx`**
  Add nav entry with `Users` icon, pending checkpoint badge counter, and bump footer version to `Engine v3.2.0`.
- [ ] **Step 2: Wire up `/team` routing and checkpoint badge in `App.tsx`**
- [ ] **Step 3: Embed active team directive status card in `OverviewView.tsx`**
  Shows active autonomous directive progress and quick button to open Team View.

---

### Task 5: End-to-End Build and Verification

**Files:**
- Build check: `frontend/`
- Backend check: `agent_reach/server/app.py`

- [ ] **Step 1: Run `npm run build` in `frontend/` to ensure clean build and asset generation**
- [ ] **Step 2: Verify all endpoints and test suite pass**

