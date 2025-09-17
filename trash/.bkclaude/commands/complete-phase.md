# Command: /complete-phase

**Goal:** Manage the end-of-phase transition using a formal review cycle and a hardened, intent-driven Git commit process. This command operates in two distinct modes, determined by the presence of a review file.

---

## 🔴 **CRITICAL: MANDATORY EXECUTION FLOW**

**You MUST operate in one of two modes. You are not allowed to mix them.**

**Mode 1: Request Review (Default)**
*   **Trigger:** No `review_phase_N.md` file exists for the current phase.
*   **Action:** You MUST execute the **Review Request Generation Protocol** below **in its entirety as a single, atomic script**. Do not modify it or run it in pieces. After execution, you MUST HALT.

**Mode 2: Process Review**
*   **Trigger:** A `review_phase_N.md` file EXISTS for the current phase.
*   **Action:** You MUST read the review, parse the `VERDICT`, and then either commit the changes (on `ACCEPT`) using the **Safe Staging and Commit Protocol** or report the required fixes (on `REJECT`).

**DO NOT:**
-   ❌ Commit any code without a `VERDICT: ACCEPT` from a review file.
-   ❌ Use `git add -A` or `git add .`. You must use the explicit, plan-driven staging logic.
-   ❌ **Abandon the provided scripts.** If a script fails, report the complete error message and STOP. Do not attempt to "fix" it by running commands manually; the script's atomicity is essential for safety.

---

## 📋 **YOUR EXECUTION WORKFLOW**

### Step 1: Determine Current Mode
1.  Read `PROJECT_STATUS.md` to find the path and phase number (`N`) of the **current active initiative**.
2.  Check if the file `<path>/review_phase_N.md` exists.
3.  If it exists, proceed to **Mode 2: Process Review**.
4.  If it does not exist, proceed to **Mode 1: Request Review**.

---

### **MODE 1: REQUEST REVIEW**

#### **Review Request Generation Protocol (v3 - Enhanced)**
You will now execute the following shell script block in its entirety. It is designed to be robust against common failures like multi-entry status files and large, untracked repository files.

```bash
#!/bin/bash
set -e
set -o pipefail

# --- START OF ENHANCED PROTOCOL ---

# Function to report errors and exit.
fail() {
    echo "❌ ERROR: $1" >&2
    exit 1
}

# 1. ROBUST PARSING: Find the *active* initiative and get its details.
# This awk script ensures we only parse the block for the current initiative.
read INITIATIVE_PATH PHASE_NUM < <(awk '
  /^### / { in_active = 0 }
  /^### Current Active Initiative/ { in_active = 1 }
  in_active && /^Path:/ { path = $2; gsub(/`/, "", path) }
  in_active && /^Current Phase:/ { phase = $3; sub(":", "", phase) }
  END { if (path && phase) print path, phase }
' PROJECT_STATUS.md)

[ -z "$INITIATIVE_PATH" ] && fail "Could not parse INITIATIVE_PATH from PROJECT_STATUS.md."
[ -z "$PHASE_NUM" ] && fail "Could not parse PHASE_NUM from PROJECT_STATUS.md."

echo "INFO: Preparing review for Phase $PHASE_NUM of initiative at '$INITIATIVE_PATH'."

# Define key file paths
IMPL_FILE="$INITIATIVE_PATH/implementation.md"
CHECKLIST_FILE="$INITIATIVE_PATH/phase_${PHASE_NUM}_checklist.md"
[ ! -f "$IMPL_FILE" ] && fail "Implementation file not found at '$IMPL_FILE'."
[ ! -f "$CHECKLIST_FILE" ] && fail "Checklist file not found at '$CHECKLIST_FILE'."

# 2. PARSE THE PLAN: Identify all files intended for this phase.
# This is the source of truth for what should be in the diff.
intended_files_str=$(python -c "
import re, sys
try:
    with open('$CHECKLIST_FILE', 'r') as f: content = f.read()
    files = re.findall(r'\`([a-zA-Z0-9/._-]+)\`', content)
    valid_files = sorted(list({f for f in files if '/' in f and '.' in f}))
    print(' '.join(valid_files))
except FileNotFoundError:
    sys.exit(1)
")
[ -z "$intended_files_str" ] && fail "Could not parse any intended file paths from '$CHECKLIST_FILE'."
echo "INFO: Plan indicates the following files should be modified:"
echo "$intended_files_str" | tr ' ' '\n' | sed 's/^/ - /'
read -r -a intended_files_array <<< "$intended_files_str"

# 3. FAST & TARGETED VERIFICATION: Check that all intended files are present in git status.
# By passing the file list to git status, we avoid scanning the entire repo,
# which prevents timeouts from large, untracked files.
all_changed_planned_files=$(git status --porcelain -- "${intended_files_array[@]}" | awk '{print $2}')
for intended_file in "${intended_files_array[@]}"; do
    if ! echo "$all_changed_planned_files" | grep -q "^${intended_file}$"; then
        fail "A planned file is missing from git's changed files list: $intended_file. Please ensure it was created/modified as per the checklist."
    fi
done
echo "✅ INFO: All planned files are present in git status."

# 4. STAGE NEW FILES FOR REVIEW: Add only the untracked files that were part of the plan.
untracked_files=$(git status --porcelain -- "${intended_files_array[@]}" | grep '^??' | awk '{print $2}' || true)
if [ -n "$untracked_files" ]; then
    for file in $untracked_files; do
        echo "INFO: Staging new planned file for review diff: $file"
        git add "$file"
    done
fi

# 5. GENERATE TARGETED DIFF: Create a diff including ONLY the intended files.
# This is the critical step that prevents large, unplanned files from corrupting the review.
mkdir -p ./tmp
DIFF_FILE="./tmp/phase_diff.txt"
diff_base=$(grep 'Last Phase Commit Hash:' "$IMPL_FILE" | awk '{print $4}')
[ -z "$diff_base" ] && fail "Could not find 'Last Phase Commit Hash:' in $IMPL_FILE."

echo "INFO: Generating targeted diff against baseline '$diff_base' for intended files only..."
# Generate a combined diff for all intended files, excluding notebooks.
git diff --staged "$diff_base" -- "${intended_files_array[@]}" ':(exclude)*.ipynb' > "$DIFF_FILE"
git diff HEAD -- "${intended_files_array[@]}" ':(exclude)*.ipynb' >> "$DIFF_FILE"
echo "INFO: Targeted diff generated."

# 6. SANITY CHECK: Verify the diff is not excessively large.
diff_lines=$(wc -l < "$DIFF_FILE")
MAX_DIFF_LINES=5000 # Set a reasonable limit
if [ "$diff_lines" -gt "$MAX_DIFF_LINES" ]; then
    echo "⚠️ WARNING: The generated diff is very large ($diff_lines lines)."
    echo "This may indicate that a data file or unintended large file was included in the plan."
    echo "Please double-check the file list in '$CHECKLIST_FILE'."
    # This is a warning, not an error, to allow for legitimate large changes.
fi

# 7. GENERATE REVIEW FILE: Programmatically build the review request.
PHASE_NAME=$(awk -F': ' "/### \\*\\*Phase $PHASE_NUM:/{print \$2}" "$IMPL_FILE" | head -n 1)
INITIATIVE_NAME=$(grep 'Name:' PROJECT_STATUS.md | head -n 1 | sed 's/Name: //')
REVIEW_FILE="$INITIATIVE_PATH/review_request_phase_$PHASE_NUM.md"
PLAN_FILE="$INITIATIVE_PATH/plan.md"

# Create the review file from components
{
    echo "# Review Request: Phase $PHASE_NUM - $PHASE_NAME"
    echo ""
    echo "**Initiative:** $INITIATIVE_NAME"
    echo "**Generated:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "## Instructions for Reviewer"
    echo "1.  Analyze the planning documents and the code changes (\`git diff\`) below."
    echo "2.  Create a new file named \`review_phase_${PHASE_NUM}.md\` in this same directory (\`$INITIATIVE_PATH/\`)."
    echo "3.  In your review file, you **MUST** provide a clear verdict on a single line: \`VERDICT: ACCEPT\` or \`VERDICT: REJECT\`."
    echo "4.  If rejecting, you **MUST** provide a list of specific, actionable fixes under a \"Required Fixes\" heading."
    echo ""
    echo "---"
    echo "## 1. Planning Documents"
    echo ""
    echo "### R&D Plan (\`plan.md\`)"
    echo '```markdown'
    cat "$PLAN_FILE"
    echo '```'
    echo ""
    echo "### Implementation Plan (\`implementation.md\`)"
    echo '```markdown'
    cat "$IMPL_FILE"
    echo '```'
    echo ""
    echo "### Phase Checklist (\`phase_${PHASE_NUM}_checklist.md\`)"
    echo '```markdown'
    cat "$CHECKLIST_FILE"
    echo '```'
    echo ""
    echo "---"
    echo "## 2. Code Changes for This Phase"
    echo ""
    echo "**Baseline Commit:** $diff_base"
    echo ""
    echo '```diff'
    cat "$DIFF_FILE"
    echo '```'
} > "$REVIEW_FILE"

echo "✅ Review request file generated at: $REVIEW_FILE"

# 8. UNSTAGE FILES: Reset the index to leave the repository clean for the user.
if [ -n "$untracked_files" ]; then
    echo "INFO: Unstaging new files. They will be re-staged during the commit process after review."
    git reset > /dev/null
fi

# --- END OF ENHANCED PROTOCOL ---
```

#### **Final Step: Notify and Halt**
-   Inform the user that the review request is ready at `<path>/review_request_phase_N.md`.
-   **HALT.** Your task for this run is complete.

---

### **MODE 2: PROCESS REVIEW**

#### Step 2.1: Read and Parse Review File
-   Read the file `<path>/review_phase_N.md`.
-   Find the line starting with `VERDICT:`. Extract the verdict (`ACCEPT` or `REJECT`).
-   If no valid verdict is found, report an error and stop.

#### Step 2.2: 🔴 MANDATORY - Conditional Execution (On `ACCEPT`)
-   If `VERDICT: ACCEPT`, you MUST execute the **Safe Staging and Commit Protocol** below.

#### Step 2.3: Conditional Execution (On `REJECT`)
-   If `VERDICT: REJECT`, extract all lines from the "Required Fixes" section of the review file.
-   Present these fixes clearly to the user.
-   **HALT.** Make no changes to Git or status files.

---

## 🔒 **Safe Staging and Commit Protocol (For `ACCEPT` Verdict)**

#### **Safe Staging and Commit Protocol (v3 - Enhanced)**
If `VERDICT: ACCEPT`, you MUST execute this precise sequence of commands as a single script.

```bash
#!/bin/bash
set -e
set -o pipefail

fail() {
    echo "❌ ERROR: $1" >&2
    exit 1
}

# 1. ROBUST PARSING
read INITIATIVE_PATH PHASE_NUM < <(awk '
  /^### / { in_active = 0 }
  /^### Current Active Initiative/ { in_active = 1 }
  in_active && /^Path:/ { path = $2; gsub(/`/, "", path) }
  in_active && /^Current Phase:/ { phase = $3; sub(":", "", phase) }
  END { if (path && phase) print path, phase }
' PROJECT_STATUS.md)

[ -z "$INITIATIVE_PATH" ] && fail "Could not parse INITIATIVE_PATH."
[ -z "$PHASE_NUM" ] && fail "Could not parse PHASE_NUM."

CHECKLIST_FILE="$INITIATIVE_PATH/phase_${PHASE_NUM}_checklist.md"
IMPL_FILE="$INITIATIVE_PATH/implementation.md"
[ ! -f "$CHECKLIST_FILE" ] && fail "Checklist file not found: $CHECKLIST_FILE."
[ ! -f "$IMPL_FILE" ] && fail "Implementation file not found: $IMPL_FILE."

# 2. PARSE THE PLAN
intended_files_str=$(python -c "
import re, sys
try:
    with open('$CHECKLIST_FILE', 'r') as f: content = f.read()
    files = re.findall(r'\`([a-zA-Z0-9/._-]+)\`', content)
    valid_files = sorted(list({f for f in files if '/' in f and '.' in f}))
    print(' '.join(valid_files))
except FileNotFoundError:
    sys.exit(1)
")
[ -z "$intended_files_str" ] && fail "Could not parse any intended files from checklist."
read -r -a intended_files_array <<< "$intended_files_str"
echo "INFO: Staging files according to plan:"
printf " - %s\n" "${intended_files_array[@]}"

# 3. FAST & TARGETED STAGING: Explicitly stage ONLY intended files.
git add "${intended_files_array[@]}"
echo "✅ INFO: Staged all planned files."

# 4. HALT ON UNPLANNED CHANGES: Verify no other files were modified.
# We check the status of the *entire repo* here, but EXCLUDE the files we just staged.
# This is the one place a full 'git status' is required, to ensure repo cleanliness.
unintended_changes=$(git status --porcelain | grep -v '^A[ M]')
if [ -n "$unintended_changes" ]; then
    echo "Unplanned changes detected:"
    echo "$unintended_changes"
    fail "The repository contains modified or untracked files not in the phase plan. Please revert them or add them to the checklist."
fi

# 5. COMMIT
phase_deliverable=$(awk -F': ' "/^\\*\\*Deliverable\\*\\*/{print \$2}" "$IMPL_FILE" | head -n 1)
commit_message="feat: Phase $PHASE_NUM - $phase_deliverable"
echo "INFO: Committing with message: '$commit_message'"
git commit -m "$commit_message"
new_hash=$(git rev-parse HEAD)
echo "✅ Commit successful. New commit hash: $new_hash"

# 6. UPDATE STATE FILES
echo "INFO: Updating state files..."

# Update implementation.md with new commit hash
sed -i "s/Last Phase Commit Hash: .*/Last Phase Commit Hash: $new_hash/" "$IMPL_FILE"

# Update PROJECT_STATUS.md
# First, calculate next phase
NEXT_PHASE=$((PHASE_NUM + 1))
TOTAL_PHASES=$(grep -c "^### \*\*Phase [0-9]" "$IMPL_FILE")

if [ "$NEXT_PHASE" -le "$TOTAL_PHASES" ]; then
    # Update to next phase
    sed -i "/^### Current Active Initiative/,/^###/ {
        s/Current Phase: Phase [0-9]*/Current Phase: Phase $NEXT_PHASE/
    }" PROJECT_STATUS.md
    echo "✅ Advanced to Phase $NEXT_PHASE"
else
    # Initiative complete
    sed -i "/^### Current Active Initiative/,/^###/ {
        s/Status: .*/Status: Completed/
        s/Current Phase: .*/Current Phase: Completed/
    }" PROJECT_STATUS.md
    echo "✅ Initiative completed!"
fi

echo "✅ State files updated successfully."
```
