# Command: /implementation

**Goal:** Generate and save a phased implementation plan document, including Git state tracking, based on the most recent R&D plan and established decomposition principles. This enhanced version requires the identification of key modules and potential risks for each phase.

---

## 🔴 **CRITICAL: MANDATORY EXECUTION FLOW**

**THIS COMMAND MUST FOLLOW THIS EXACT SEQUENCE:**
1.  You MUST read `PROJECT_STATUS.md` to identify the current initiative.
2.  You MUST read the corresponding `plan.md`.
3.  You MUST execute the Git commands in the "State Persistence Logic" section to capture the feature branch, baseline branch, and baseline commit hash.
4.  You MUST decompose the work into logical phases, following the "PHASE DECOMPOSITION GUIDELINES".
5.  **NEW:** For each phase, you MUST analyze the codebase to identify the **"Key Modules & APIs to Touch"** and any **"Potential Gotchas & Critical Conventions"**.
6.  You MUST generate the `implementation.md` file using the provided template, populating all fields correctly.
7.  You MUST update `PROJECT_STATUS.md` to advance the initiative to Phase 1.

**DO NOT:**
-   ❌ Generate the implementation plan without first capturing the Git state.
-   ❌ Leave the "Key Modules" or "Potential Gotchas" sections empty. This indicates insufficient analysis.
-   ❌ Use complex or untested shell commands.

**EXECUTION CHECKPOINT:** Before saving the `implementation.md` file, you must verify that the `Baseline Commit Hash` field contains a valid Git commit hash and that the new analysis sections are populated.

---

## 🤖 **CONTEXT: YOU ARE CLAUDE CODE**

You are Claude Code, an autonomous command-line tool. You will execute the Git commands and file operations described below directly and without human intervention to create the implementation plan.

---

## 📋 **YOUR EXECUTION WORKFLOW**

### Step 1: Read Context
-   Read `PROJECT_STATUS.md` to get the current initiative path.
-   Read `<path>/plan.md` to understand the project goals and technical details.

### Step 2: 🔴 MANDATORY - Capture Git State
-   Execute the shell commands provided in the "State Persistence Logic" section below to determine the feature branch, baseline branch, and baseline commit hash.

### Step 3: Decompose Work into Phases & Perform Deeper Analysis
-   Analyze the "Core Capabilities" and "Technical Implementation Details" from the `plan.md`.
-   Using the **"PHASE DECOMPOSITION GUIDELINES"** below, break the work down into a sequence of 2-5 logical phases.
-   **For each phase you define, perform a targeted analysis of the codebase to identify and document:**
    1.  The specific files, functions, and classes that will be modified or created.
    2.  Any non-obvious technical details, API contracts, or data conventions that a developer must know to implement the phase correctly (e.g., "the offset tensor uses [y, x] order").

### Step 4: Generate and Save Implementation Plan
-   Generate the full content for the implementation plan using the "IMPLEMENTATION PLAN TEMPLATE" below.
-   Populate all sections, including the new analysis sections for each phase, with the information you gathered.
-   Save the content to `<initiative-path>/implementation.md`.

### Step 5: Update Project Status
-   Update the `PROJECT_STATUS.md` file using the "PROJECT STATUS UPDATE" section as a guide.

### Step 6: Confirm and Present
-   Announce that the implementation plan has been created and the project status has been updated.
-   Present the full content of the generated `implementation.md` for the user's review.

---

## 🔒 **State Persistence Logic (Revised for Robustness)**

You must execute the following shell commands. This robust, sequential approach is tested to work in your environment.

```bash
# 1. Get the current feature branch name
feature_branch=$(git rev-parse --abbrev-ref HEAD)

# 2. Extract baseline branch from PROJECT_STATUS.md
# Format: **Branch:** `feature/name` (baseline: branch-name)
baseline_branch=$(grep "Branch:" PROJECT_STATUS.md | sed 's/.*baseline: \(.*\))/\1/')
if [ -z "$baseline_branch" ]; then
    echo "❌ ERROR: Could not determine baseline branch from PROJECT_STATUS.md"
    exit 1
fi
echo "Baseline branch determined as: $baseline_branch"

# 3. Get the commit hash of that baseline branch
baseline_hash=$(git rev-parse "$baseline_branch")
echo "Baseline commit hash: $baseline_hash"
```

---

## 💡 **PHASE DECOMPOSITION GUIDELINES**

When breaking work into phases, you **MUST** follow these principles:

1.  **Each phase must produce a verifiable deliverable.**
2.  **Phases should be logically independent when possible.**
3.  **Consider natural boundaries in the work:** Data First, Foundation First, Backend then Frontend.
4.  **Size phases appropriately:** Aim for phases that represent approximately 1-2 days of focused work.
5.  **The final phase is always "Validation & Documentation".**

---

## 템플릿 & 가이드라인 (Templates & Guidelines)

### **IMPLEMENTATION PLAN TEMPLATE (Updated)**
*This is the template for the content of `implementation.md`.*
```markdown
<!-- ACTIVE IMPLEMENTATION PLAN -->
<!-- DO NOT MISTAKE THIS FOR A TEMPLATE. THIS IS THE OFFICIAL SOURCE OF TRUTH FOR THE PROJECT'S PHASED PLAN. -->

# Phased Implementation Plan

**Project:** <Name from R&D Plan>
**Initiative Path:** `plans/active/<initiative-name>/`

---
## Git Workflow Information
**Feature Branch:** <Value of $feature_branch from logic above>
**Baseline Branch:** <Value of $baseline_branch from logic above>
**Baseline Commit Hash:** <Value of $baseline_hash from logic above>
**Last Phase Commit Hash:** <Value of $baseline_hash from logic above>
---

**Created:** <Current Date, e.g., 2025-07-20>
**Core Technologies:** Python, NumPy, TensorFlow, scikit-image

---

## 📄 **DOCUMENT HIERARCHY**

This document orchestrates the implementation of the objective defined in the main R&D plan. The full set of documents for this initiative is:

- **`plan.md`** - The high-level R&D Plan
  - **`implementation.md`** - This file - The Phased Implementation Plan
    - `phase_1_checklist.md` - Detailed checklist for Phase 1
    - `phase_2_checklist.md` - Detailed checklist for Phase 2
    - `phase_final_checklist.md` - Checklist for the Final Phase

---

## 🎯 **PHASE-BASED IMPLEMENTATION**

**Overall Goal:** <Synthesize a one-sentence summary from the R&D Plan's objective.>

**Total Estimated Duration:** <Sum of phase estimates, e.g., 3 days>

---

## 📋 **IMPLEMENTATION PHASES**

### **Phase 1: Core Logic Implementation**

**Goal:** To implement the foundational data structures and core algorithms for the new feature.
**Deliverable:** A new module `src/core/new_feature.py` with passing unit tests for all public functions.
**Estimated Duration:** 1 day

**Key Modules & APIs to Touch:**
- `ptycho/raw_data.py`: `get_image_patches`
- `ptycho/tf_helper.py`: `translate`
- `ptycho/config/config.py`: `ModelConfig`

**Potential Gotchas & Critical Conventions:**
- The `offsets_f` tensor in `raw_data.py` stores coordinates in `[y, x]` order.
- The `hh.translate` function in `tf_helper.py` expects its `translations` argument in `[dx, dy]` order.
- A coordinate swap will be necessary to ensure correctness.

**Implementation Checklist:** `phase_1_checklist.md`
**Success Test:** `pytest tests/core/test_new_feature.py` completes with 100% pass rate.

---

### **Phase 2: Integration with Main Application**

**Goal:** To integrate the new core logic into the main application workflow.
**Deliverable:** An updated `src/main.py` that correctly calls the new module and produces the expected output.
**Estimated Duration:** 1 day

**Key Modules & APIs to Touch:**
- `src/main.py`: Main application loop
- `src/config.py`: Add new feature flag

**Potential Gotchas & Critical Conventions:**
- Ensure the new feature flag is `False` by default to maintain backward compatibility.
- The main application expects data in a specific format; a data transformation step may be needed.

**Implementation Checklist:** `phase_2_checklist.md`
**Success Test:** Running `python src/main.py --enable-new-feature --input data.txt` produces a valid output file.

---

### **Final Phase: Validation & Documentation**

**Goal:** Validate the complete implementation, update all relevant documentation, and ensure performance meets requirements.
**Deliverable:** A fully tested and documented feature, ready for production use.
**Estimated Duration:** 1 day

**Key Modules & APIs to Touch:**
- `README.md`: User-facing documentation
- `docs/features.md`: Detailed feature documentation

**Potential Gotchas & Critical Conventions:**
- All public-facing documentation must be updated with clear examples.
- Performance benchmarks must be run and documented before the feature is considered complete.

**Implementation Checklist:** `phase_final_checklist.md`
**Success Test:** All R&D plan success criteria are verified as complete.

---

## 📊 **PROGRESS TRACKING**

### Phase Status:
- [ ] **Phase 1:** Core Logic Implementation - 0% complete
- [ ] **Phase 2:** Integration with Main Application - 0% complete
- [ ] **Final Phase:** Validation & Documentation - 0% complete

**Current Phase:** Phase 1: Core Logic Implementation
**Overall Progress:** ░░░░░░░░░░░░░░░░ 0%

---

## 🚀 **GETTING STARTED**

1.  **Generate Phase 1 Checklist:** Run `/phase-checklist 1` to create the detailed checklist.
2.  **Begin Implementation:** Follow the checklist tasks in order.
3.  **Track Progress:** Update task states in the checklist as you work.
4.  **Request Review:** Run `/complete-phase` when all Phase 1 tasks are done to generate a review request.

---

## ⚠️ **RISK MITIGATION**

**Potential Blockers:**
- **Risk:** The external API dependency might have a lower rate limit than expected.
  - **Mitigation:** Implement client-side caching and exponential backoff for retries.
- **Risk:** The new algorithm may be too computationally expensive.
  - **Mitigation:** Profile the code early in Phase 1 and identify optimization opportunities.

**Rollback Plan:**
- **Git:** Each phase will be a separate, reviewed commit on the feature branch, allowing for easy reverts.
- **Feature Flag:** The `--enable-new-feature` flag allows the new code to be disabled in production if issues arise.
```

### **PROJECT STATUS UPDATE**
*Update these fields in `PROJECT_STATUS.md`.*
```markdown
**Current Phase:** Phase 1: Core Logic Implementation
**Progress:** ░░░░░░░░░░░░░░░░ 0%
**Next Milestone:** A new module `src/core/new_feature.py` with passing unit tests.
**Implementation Plan:** `plans/active/<initiative-name>/implementation.md`
```
