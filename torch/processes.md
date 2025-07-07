# `processes.md`: Claude Code Standard Operating Procedures

**Purpose:** This document is my primary playbook. It contains a set of standardized, step-by-step processes for executing different types of software engineering tasks. When given a high-level goal, I will first consult this document to select the appropriate Standard Operating Procedure (SOP) to follow.

**Core Principles:**
1.  **Checklist-Driven:** Every complex task is managed via a checklist. I will create, update, and complete checklists to track my progress and manage context.
2.  **Plan Before Acting:** For non-trivial tasks, I will always create a detailed plan before writing implementation code.
3.  **Verify, Then Commit:** I will always run tests to verify my changes before committing them.
4.  **Scale with Subagents:** For tasks that are complex or parallelizable, I will act as a supervising agent, spawning specialized subagents to handle discrete sub-problems.

---

## Process Directory

1.  **SOP-1: Task Planning & Decomposition:** For high-level or ambiguous goals (e.g., "implement feature X," "refactor the logging system").
2.  **SOP-2: Focused Code Implementation:** For executing a clear, pre-defined plan.
3.  **SOP-3: Test-Driven Development (TDD):** For creating new functionality with a strong verification contract.
4.  **SOP-4: Bug Fix & Verification:** For resolving a specific bug from a ticket or report.
5.  **SOP-5: Documentation Update:** For updating project documentation based on recent code changes.
6.  **SOP-6: Interface Definition (IDL) Creation:** For reverse-engineering a formal contract from existing code.
7.  **SOP-7: Large-Scale Automated Refactoring:** For applying a consistent change across many files.

---

### **SOP-1: Task Planning & Decomposition**

**Goal:** To transform a high-level objective into a detailed, actionable checklist.

| ID | Task Description | State | Details & Guidance |
| :--- | :--- | :--- | :--- |
| **Phase 0: Scoping & Research** |
| 0.A | **Consult `CLAUDE.md`** | `[ ]` | Read `CLAUDE.md` in the current and parent directories to understand project-specific rules, commands, and context. |
| 0.B | **Initial Codebase Exploration** | `[ ]` | Identify potentially relevant files and directories based on the task description. Use file search and read the contents of 2-3 key files to build initial context. |
| 0.C | **Spawn Research Subagents (If Needed)** | `[ ]` | If the task involves complex APIs or unclear areas, spawn subagents for focused investigation. **Example:** "Subagent, read `ExecutionFactory.ts` and its `git log`. Summarize its purpose and evolution." |
| 0.D | **Synthesize Findings** | `[ ]` | Consolidate my own findings and the reports from any subagents into a brief summary of the current state and the core problem to be solved. |
| **Phase 1: Plan Generation** |
| 1.A | **Engage Extended Thinking** | `[ ]` | Use the command `think hard` to formulate a comprehensive plan. If the problem is exceptionally complex, use `ultrathink`. |
| 1.B | **Generate Implementation Checklist** | `[ ]` | Create a detailed, step-by-step checklist for the implementation. The checklist should be broken into logical phases (e.g., Setup, Implementation, Testing, Cleanup). |
| 1.C | **Identify Parallelizable Tasks** | `[ ]` | Review the checklist and identify any steps that can be performed in parallel. Mark these explicitly in the plan for potential subagent execution later. |
| **Phase 2: Finalization** |
| 2.A | **Save Plan to a Scratchpad** | `[ ]` | Save the generated checklist to a new file (e.g., `PLAN.md`) or a new GitHub issue. This scratchpad will be the source of truth for the implementation phase. |
| 2.B | **Request User Approval** | `[ ]` | Present the summary and the link to the plan. State: "I have completed the planning phase. Please review the plan at `PLAN.md`. Shall I proceed with implementation by executing **SOP-2**?" |

---

### **SOP-2: Focused Code Implementation**

**Goal:** To execute a pre-existing plan from a checklist.

| ID | Task Description | State | Details & Guidance |
| :--- | :--- | :--- | :--- |
| 0.A | **Load Plan** | `[ ]` | Read the specified checklist from the `PLAN.md` file or GitHub issue. |
| 1.A | **Execute Checklist Item 1** | `[ ]` | Perform the first task as described. This may involve file edits, running commands, or other actions. |
| 1.B | **Update Checklist** | `[ ]` | Mark the item as complete in my internal state. |
| 1.C | **Execute Next Item...** | `[ ]` | Continue sequentially through the checklist until all items are complete. |
| 2.A | **Final Verification** | `[ ]` | Run all relevant tests (unit, integration) as specified in the plan or `CLAUDE.md`. |
| 2.B | **Report Completion** | `[ ]` | State: "Implementation complete and all tests are passing. Ready for commit." |

---

### **SOP-3: Test-Driven Development (TDD)**

**Goal:** To implement a new feature by writing tests first.

| ID | Task Description | State | Details & Guidance |
| :--- | :--- | :--- | :--- |
| 1.A | **Write Failing Tests** | `[ ]` | Create new test cases for the target functionality. The tests should cover success cases and edge cases. Do not write any implementation code. |
| 1.B | **Run Tests and Confirm Failure (Red)** | `[ ]` | Execute the new tests and verify that they fail as expected (e.g., `NotImplementedError`, `AssertionError`). |
| 1.C | **Commit Tests** | `[ ]` | Create a commit with the message "test: Add failing tests for [feature name]". |
| 2.A | **Write Minimal Implementation (Green)** | `[ ]` | Write the simplest possible implementation code required to make the new tests pass. Do not modify the tests. |
| 2.B | **Run Tests and Confirm Success** | `[ ]` | Execute the full test suite and confirm all tests now pass. Iterate on the implementation if needed. |
| 3.A | **Refactor Implementation** | `[ ]` | With the tests providing a safety net, refactor the implementation for clarity, performance, and adherence to code style. The tests must continue to pass after each change. |
| 3.B | **Commit Final Code** | `[ ]` | Create a final commit with the message "feat: Implement [feature name] and pass tests". |

---

### **SOP-4: Bug Fix & Verification**

**Goal:** To diagnose, fix, and verify a bug.

| ID | Task Description | State | Details & Guidance |
| :--- | :--- | :--- | :--- |
| 1.A | **Understand the Bug** | `[ ]` | Read the GitHub issue or bug report. Use `gh issue view {issue_number}`. |
| 1.B | **Create a Failing Test** | `[ ]` | **This is the most critical step.** Write a new test case that specifically reproduces the bug. Run the test and confirm it fails. This proves I have understood and replicated the problem. |
| 2.A | **Diagnose Root Cause** | `[ ]` | Use tools like `git blame` and `git log` on the relevant files to understand the history. Read the code to identify the logical flaw. |
| 2.B | **Implement the Fix** | `[ ]` | Modify the code to correct the flaw. |
| 3.A | **Verify the Fix** | `[ ]` | Run the new failing test and confirm it now passes. |
| 3.B | **Verify No Regressions** | `[ ]` | Run the *entire* project test suite to ensure the fix has not introduced any new problems. |
| 3.C | **Commit and Create PR** | `[ ]` | Commit the fix and the new test. Use `gh pr create` and reference the issue number in the PR description (e.g., "Fixes #{issue_number}"). |

---

### **SOP-5: Documentation Update**

**Goal:** To update documentation to reflect recent code changes.

| ID | Task Description | State | Details & Guidance |
| :--- | :--- | :--- | :--- |
| 1.A | **Analyze Code Changes** | `[ ]` | Use `git diff main` to get a list of all changed files and their modifications. |
| 1.B | **Spawn Subagent for Analysis** | `[ ]` | Spawn a subagent with the `git diff` output. **Prompt:** "Subagent, review this diff and identify all changes to public-facing APIs, user-visible behavior, or command-line arguments. List the affected files and a summary of each change." |
| 2.A | **Update Documentation Files** | `[ ]` | Based on the subagent's report, edit the relevant documentation files (`README.md`, `CLAUDE.md`, docstrings, etc.) to reflect the changes. |
| 2.B | **Commit Documentation** | `[ ]` | Create a commit with the message "docs: Update documentation for [feature name]". |

---

### **SOP-6: Interface Definition (IDL) Creation**

**Goal:** To create a formal contract (`_IDL.md`) for an existing code module.

| ID | Task Description | State | Details & Guidance |
| :--- | :--- | :--- | :--- |
| 1.A | **Analyze Source Code** | `[ ]` | Read the target source file (`.py`, `.ts`, etc.) in its entirety. |
| 1.B | **Identify Public Interface** | `[ ]` | List all public classes, functions, and methods. Ignore private members (e.g., those prefixed with `_`). |
| 1.C | **Extract Signatures** | `[ ]` | For each public item, document its signature, including parameters (and their types) and return values (and their types). |
| 1.D | **Infer Behavior** | `[ ]` | Read the code logic for each function/method to summarize its core behavior, preconditions, and postconditions. |
| 1.E | **Identify Error Conditions** | `[ ]` | Look for `raise` statements or error-handling blocks to document potential exceptions. |
| 2.A | **Draft IDL File** | `[ ]` | Assemble the collected information into a new `_IDL.md` file, following the project's standard IDL format. |
| 2.B | **Commit IDL** | `[ ]` | Commit the new file with the message "docs: Add IDL for [module name]". |

---

### **SOP-7: Large-Scale Automated Refactoring**

**Goal:** To apply a single, consistent change across a large number of files.

| ID | Task Description | State | Details & Guidance |
| :--- | :--- | :--- | :--- |
| 1.A | **Generate Task List** | `[ ]` | Write a script or use shell commands to generate a list of all files that need to be modified. Save this list to a scratchpad file, `refactor_checklist.md`. |
| 2.A | **Process Checklist** | `[ ]` | Begin a loop to process each file listed in `refactor_checklist.md`. |
| 2.B | **Spawn Refactoring Subagent** | `[ ]` | For each file in the list, spawn a dedicated subagent with a highly focused prompt. **Example:** "Subagent, your only task is to refactor the file `{filename}`. Replace all instances of `old_api()` with `new_api()`. Do not modify any other files. Report 'SUCCESS' or 'FAILURE'." |
| 2.C | **Update Master Checklist** | `[ ]` | As each subagent reports back, update the status of the corresponding item in `refactor_checklist.md`. Log any failures for later manual review. |
| 3.A | **Final Verification** | `[ ]` | After the loop is complete, run the linter and the full test suite to verify the entire refactoring effort. |
| 3.B | **Commit Changes** | `[ ]` | Commit all changes with a comprehensive message describing the refactoring task. |
