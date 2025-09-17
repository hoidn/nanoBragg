# Command: /phase-checklist <phase-number>

**Goal:** Generate a detailed, context-aware checklist for a specific phase by parsing the implementation plan and providing actionable guidance.

---

## 🔴 **CRITICAL: MANDATORY EXECUTION FLOW**

**THIS COMMAND MUST FOLLOW THIS EXACT SEQUENCE:**
1.  You MUST parse the phase number from the command arguments.
2.  You MUST read `PROJECT_STATUS.md` to identify the current initiative path.
3.  You MUST read the corresponding `<path>/implementation.md` file.
4.  You MUST extract the **Goal**, **Deliverable**, **Key Tasks**, **Key Modules & APIs**, and **Potential Gotchas** for the specified phase number.
5.  You MUST use this extracted information to populate the new, enhanced checklist template.
6.  You MUST save the generated checklist to `<path>/phase_<n>_checklist.md`.
7.  You MUST present the saved file path and its full content to the user.

**DO NOT:**
-   ❌ Generate a generic checklist. You must use the specific context from `implementation.md`.
-   ❌ Leave the "Critical Context" section empty. If the `implementation.md` is missing this information, you must report an error.
-   ❌ Execute any of the tasks in the checklist you generate. Your role is to create the plan, not execute it.

---

## 🤖 **CONTEXT: YOU ARE CLAUDE CODE**

You are Claude Code, an autonomous command-line tool. You will execute the file operations described below to create a detailed and context-aware checklist for the user or another AI agent to follow.

---

## 📋 **YOUR EXECUTION WORKFLOW**

### Step 1: Parse Arguments and Read Context
-   Parse the `<phase-number>` from the command.
-   Read `PROJECT_STATUS.md` to get the current initiative path.
-   Read `<path>/implementation.md`.

### Step 2: Extract Phase-Specific Information
-   Using a robust parsing method (like `awk` or a Python script), extract all the relevant sections for the specified phase from `implementation.md`:
    -   Phase Name, Goal, Deliverable
    -   The list of "Key Tasks"
    -   The content of "Key Modules & APIs to Touch"
    -   The content of "Potential Gotchas & Critical Conventions"

### Step 3: Generate and Save the Checklist
-   Generate the full content for the checklist using the "ENHANCED CHECKLIST TEMPLATE" below.
-   Populate all sections with the information you extracted in Step 2.
-   For the main task list, create a row for each "Key Task" you extracted and use the context to generate specific, actionable prompts in the "How/Why & API Guidance" column.
-   Save the final content to `<initiative-path>/phase_<phase-number>_checklist.md`.

### Step 4: Confirm and Present
-   Announce that the detailed checklist has been created.
-   Present the full content of the generated checklist file for the user's review.

---

## 템플릿 & 가이드라인 (Templates & Guidelines)

### **ENHANCED CHECKLIST TEMPLATE (for non-Gemini `/phase-checklist`)**
*This is the template for the content of `phase_<n>_checklist.md`.*
```markdown
# Phase <N>: <Phase Name> Checklist

**Initiative:** <Initiative name from plan>
**Created:** <Today's date YYYY-MM-DD>
**Phase Goal:** <Extracted from implementation.md>
**Deliverable:** <Extracted from implementation.md>

---
## 🧠 **Critical Context for This Phase**

**Key Modules & APIs Involved:**
<*Content from "Key Modules & APIs" in implementation.md is inserted here*>

**⚠️ Potential Gotchas & Conventions to Respect:**
<*Content from "Potential Gotchas" in implementation.md is inserted here*>
---

## ✅ Task List

### Instructions:
1.  Work through tasks in order. Dependencies are noted in the guidance column.
2.  The **"How/Why & API Guidance"** column contains all necessary details for implementation.
3.  Update the `State` column as you progress: `[ ]` (Open) -> `[P]` (In Progress) -> `[D]` (Done).

---

| ID  | Task Description                                   | State | How/Why & API Guidance                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       -
| :-- | :------------------------------------------------- | :---- | :-------------------------------------------------
| **Section 0: Preparation & Analysis**
| 0.A | **Review Critical Context**                        | `[ ]` | **Why:** To prevent common errors by understanding the specific challenges of this phase. <br> **Action:** Carefully read the "Critical Context for This Phase" section above. Acknowledge that you understand the potential gotchas before proceeding.
| 0.B | **Analyze Source Code**                            | `[ ]` | **Why:** To understand the existing code before modification. <br> **Action:** Open and read the files listed in the "Key Modules & APIs" section. Pay close attention to the function signatures, data flow, and any existing comments.
| **Section 1: Implementation Tasks**
| 1.A | **Implement: <Task 1 from implementation.md>**     | `[ ]` | **Why:** [Agent fills in based on goal] <br> **File:** `[Agent fills in based on context]` <br> **API Guidance:** **[Agent: Based on your analysis of the source code and the gotchas, what is the exact code snippet or API call needed here? Be specific.]**
| 1.B | **Implement: <Task 2 from implementation.md>**     | `[ ]` | **Why:** [Agent fills in based on goal] <br> **File:** `[Agent fills in based on context]` <br> **API Guidance:** **[Agent: Based on your analysis of the source code and the gotchas, what is the exact code snippet or API call needed here? Be specific.]**
| ... | ...                                                | ...   | ...
| **Section 2: Testing & Validation**
| 2.A | **Write Unit/Integration Tests**                   | `[ ]` | **Why:** To verify the new implementation is correct and does not introduce regressions. <br> **File:** `[Agent: Suggest a new or existing test file]` <br> **Guidance:** Write tests that specifically cover the changes made in this phase. Refer to the "Success Test" for this phase in `implementation.md`.
| 2.B | **Run All Tests**                                  | `[ ]` | **Why:** To confirm the changes are working and have not broken other parts of the application. <br> **Command:** `python -m unittest discover -s tests -p "test_*.py"` <br> **Verify:** All tests must pass.
| **Section 3: Finalization**
| 3.A | **Code Formatting & Linting**                      | `[ ]` | **Why:** To maintain code quality and project standards. <br> **How:** Review code for consistent indentation, remove any debug prints, ensure proper docstrings for new functions.
| 3.B | **Update Function Docstrings**                     | `[ ]` | **Why:** To document new parameters and functionality. <br> **How:** Update docstrings for any modified functions to reflect the changes made in this phase.

---

## 🎯 Success Criteria

**This phase is complete when:**
1.  All tasks in the table above are marked `[D]` (Done).
2.  The phase success test passes: `<specific command from implementation.md>`
3.  No regressions are introduced in the existing test suite.
