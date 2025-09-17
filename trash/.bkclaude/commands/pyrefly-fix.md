# Command: /pyrefly-fix-local <target-directory>

**Goal:** Autonomously run `pyrefly check` on a specified directory, analyze the reported errors, and fix each identified issue sequentially.

**Usage:**
- `/pyrefly-fix-local src/nanobrag_torch/models/`
- `/pyrefly-fix-local tests/`

---

## 🔴 **CRITICAL: MANDATORY EXECUTION FLOW**

**YOUR ROLE IS AN AUTONOMOUS DEVELOPER.**
1.  You MUST run `pyrefly check` on the user-provided target directory and capture its output.
2.  You MUST parse the `pyrefly` output to create a structured list of errors to fix.
3.  You MUST enter a loop, fixing **one error at a time**.
4.  After each fix, you MUST run `pyrefly check` again on the *modified file* to verify that the specific error was resolved and no new errors were introduced. If the fix is not perfect, you must revert it and try again.
5.  After the loop completes, you MUST run `pyrefly check` a final time on the entire target directory to confirm all issues are resolved.
6.  You MUST then commit the changes with a detailed message.

**DO NOT:**
-   ❌ Attempt to fix all errors at once. You must work sequentially, one error at a time.
-   ❌ Commit any changes until the final verification scan passes with zero errors.
-   ❌ Modify any code unrelated to the specific error you are currently fixing.

---

## 🤖 **YOUR EXECUTION WORKFLOW**

### **Phase 1: Analysis & Task Generation**

*(You will execute these commands directly to analyze the code and generate the task list.)*

| ID | Task Description | State | How/Why & API Guidance |
| :-- | :--- | :--- | :--- |
| 1.A | **Run `pyrefly check`** | `[ ]` | **Why:** To get the ground-truth list of all static analysis errors that need to be fixed. <br> **How:** Execute the following command now. <br> ```bash <br> # The user's target directory is in $ARGUMENTS <br> TARGET_DIR="$ARGUMENTS" <br> <br> # Ensure the target directory exists <br> if [ ! -d "$TARGET_DIR" ]; then <br>     echo "❌ ERROR: Target directory '$TARGET_DIR' not found. Aborting." <br>     exit 1 <br> fi <br> <br> # Run pyrefly and save the output to a file <br> echo "Running pyrefly check on '$TARGET_DIR'..." <br> pyrefly check "$TARGET_DIR" > ./tmp/pyrefly_errors.log <br> <br> # Check if there were any errors <br> if [ ! -s ./tmp/pyrefly_errors.log ]; then <br>     echo "✅ No pyrefly errors found in '$TARGET_DIR'. Nothing to do." <br>     exit 0 <br> fi <br> <br> echo "✅ Found pyrefly errors. Report saved to ./tmp/pyrefly_errors.log." <br> ``` |
| 1.B | **Parse Errors into a Task List** | `[ ]` | **Why:** To create a structured, machine-readable list of tasks for the orchestration loop. <br> **How:** Write and execute a script (e.g., Python) to parse `pyrefly_errors.log` into a JSON file `tmp/pyrefly_tasks.json`. Each entry should contain the file path, line number, error code, and error message. <br> **Example JSON entry:** <br> ```json <br> { <br>   "file_path": "src/nanobrag_torch/models/crystal.py", <br>   "line_number": 38, <br>   "error_code": "bad-function-definition", <br>   "error_message": "Default `None` is not assignable to parameter `config` with type `CrystalConfig`" <br> } <br> ``` |

---

### **Phase 2: Sequential Fixing Loop**

*(You will now begin the execution loop, fixing one error at a time.)*

| ID | Task Description | State | How/Why & API Guidance |
| :-- | :--- | :--- | :--- |
| 2.A | **Iterate Through Each Error** | `[ ]` | **Why:** To process each error independently, ensuring each fix is correct and isolated. <br> **How:** Begin a loop. For each error object in `tmp/pyrefly_tasks.json`: <br> 1. **Read the File:** Read the content of the `file_path` for the current error. <br> 2. **Formulate the Fix:** Based on the `error_message` and `line_number`, determine the minimal code change required. <br> 3. **Apply the Fix:** Modify the file with your change. <br> 4. **Verify the Fix:** Run `pyrefly check` **only on the modified file**. Check that the original error is gone and no new errors have appeared in that file. <br> 5. **Revert if Necessary:** If the verification fails, revert the changes to that file (`git checkout -- <file_path>`) and log the failure before moving to the next error. |

---

### **Phase 3: Final Verification & Commit**

*(You will execute these final steps after the loop in Phase 2 is complete.)*

| ID | Task Description | State | How/Why & API Guidance |
| :-- | :--- | :--- | :--- |
| 3.A | **Run Final Verification Scan** | `[ ]` | **Why:** To ensure that all fixes have been applied correctly and no new errors were introduced across the entire target directory. <br> **How:** Run `pyrefly check` one last time on the original target directory. <br> ```bash <br> echo "Running final verification scan on '$TARGET_DIR'..." <br> pyrefly check "$TARGET_DIR" > ./tmp/pyrefly_final_check.log <br> <br> if [ -s ./tmp/pyrefly_final_check.log ]; then <br>     echo "❌ ERROR: Final verification failed. Some errors remain:" <br>     cat ./tmp/pyrefly_final_check.log <br>     echo "Please review the failed fixes and remaining errors." <br>     exit 1 <br> fi <br> echo "✅ Final verification passed. All pyrefly errors have been resolved." <br> ``` |
| 3.B | **Final Code Commit** | `[ ]` | **Why:** To save the completed refactoring work. <br> **How:** Stage all the modified Python files and commit them with a detailed message. <br> ```bash <br> git add "$TARGET_DIR/**/*.py" <br> git commit -m "refactor(typing): Resolve pyrefly static analysis errors" -m "Ran pyrefly check and fixed all identified type safety and code quality issues in the '$TARGET_DIR' directory. This improves code correctness and maintainability." <br> ``` |
