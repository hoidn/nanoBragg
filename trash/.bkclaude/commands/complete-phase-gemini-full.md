# Command: /complete-phase-gemini-full <initiative-path>

**Goal:** Autonomously verify the completion of the current project phase, report the verdict, and prepare for the next phase by delegating all analysis and decision-making to Gemini.

**Usage:**
- `/complete-phase-gemini-full plans/active/real-time-notifications`

**Prerequisites:**
- An `implementation.md` and `PROJECT_STATUS.md` must exist.
- The command should be run after a phase's checklist is believed to be complete.

---

## 🔴 **CRITICAL: MANDATORY EXECUTION FLOW**

**YOUR ROLE IS AN AUTONOMOUS ORCHESTRATOR AND FILE MANAGER. YOU MAKE NO DECISIONS.**
1.  You MUST identify the current phase and its success criteria from the project files.
2.  You MUST run `repomix` to create a complete, fresh snapshot of the codebase, including the recent changes.
3.  You MUST build a structured prompt file (`tmp/verify-prompt.md`) using the XML format.
4.  You MUST execute `gemini -p "@tmp/verify-prompt.md"` to delegate the entire verification process.
5.  You MUST parse Gemini's verdict from the response.
6.  You MUST execute the correct file management actions (advance phase or create fix-list) based **only** on Gemini's verdict.

**DO NOT:**
-   ❌ Make any judgment calls on whether a phase is complete.
-   ❌ Modify, interpret, or enhance Gemini's analysis.
-   ❌ Skip any step.

---

## 🤖 **YOUR EXECUTION WORKFLOW**

### Step 1: Prepare Context from Project State

```bash
# Parse arguments
INITIATIVE_PATH="$1"
IMPLEMENTATION_PLAN_PATH="$INITIATIVE_PATH/implementation.md"
PROJECT_STATUS_PATH="PROJECT_STATUS.md"

# Verify required files exist
if [ ! -f "$IMPLEMENTATION_PLAN_PATH" ] || [ ! -f "$PROJECT_STATUS_PATH" ]; then
    echo "❌ ERROR: Required project files (implementation.md or PROJECT_STATUS.md) not found."
    exit 1
fi

# Extract current phase number and info
CURRENT_PHASE_NUMBER=$(grep 'Current Phase:' "$PROJECT_STATUS_PATH" | sed 's/Current Phase: Phase \([0-9]*\).*/\1/')
CURRENT_PHASE_INFO=$(awk "/### \*\*Phase $CURRENT_PHASE_NUMBER:/{f=1} f && /^### \*\*Phase|## 📊 PROGRESS TRACKING/{if (!/Phase $CURRENT_PHASE_NUMBER/) f=0} f" "$IMPLEMENTATION_PLAN_PATH")
CURRENT_PHASE_CHECKLIST_PATH="$INITIATIVE_PATH/phase_${CURRENT_PHASE_NUMBER}_checklist.md"
CURRENT_PHASE_CHECKLIST=$(cat "$CURRENT_PHASE_CHECKLIST_PATH")

if [ -z "$CURRENT_PHASE_NUMBER" ] || [ -z "$CURRENT_PHASE_INFO" ]; then
    echo "❌ ERROR: Could not determine current phase from project files."
    exit 1
fi
echo "✅ Loaded context for current Phase $CURRENT_PHASE_NUMBER."
```

### Step 2: Aggregate Codebase Context with Repomix

```bash
# Use repomix for a complete, single-file context snapshot.
npx repomix@latest . \
  --include "**/*.{js,py,md,sh,json,c,h,log,yml,toml}" \
  --ignore "build/**,node_modules/**,dist/**,*.lock,tmp/**"

if [ ! -s ./repomix-output.xml ]; then
    echo "❌ ERROR: Repomix failed to generate the codebase context. Aborting."
    exit 1
fi
echo "✅ Codebase context aggregated into repomix-output.xml."
```

### Step 3: MANDATORY - Build the Prompt File

```bash
# Clean start for the prompt file
mkdir -p ./tmp
rm -f ./tmp/verify-prompt.md 2>/dev/null

# Create the structured prompt
cat > ./tmp/verify-prompt.md << 'PROMPT'
<task>
You are an automated, rigorous Quality Assurance and Verification system. Your task is to perform a complete verification of a software development phase and determine if it is complete. You must be strict and objective.

<steps>
<1>
Analyze the provided context: `<phase_info>`, `<phase_checklist>`, and the full `<codebase_context>`.
</1>
<2>
Perform all verification checks as detailed in the `<output_format>` section. This includes implementation review, test analysis, and quality checks.
</2>
<3>
Execute the success test command defined in the `<phase_info>` and compare the actual output to the expected outcome.
</3>
<4>
Provide a definitive, overall verdict: `COMPLETE` or `INCOMPLETE`. This is the most critical part of your output.
</4>
<5>
If the verdict is `INCOMPLETE`, provide a list of all `BLOCKER` issues.
</5>
<6>
If the verdict is `COMPLETE`, provide a detailed preparation plan for the next phase.
</6>
</steps>

<context>
<phase_info>
[Placeholder for the current phase info from implementation.md]
</phase_info>

<phase_checklist>
[Placeholder for the current phase's checklist.md]
</phase_checklist>

<codebase_context>
<!-- Placeholder for content from repomix-output.xml -->
</codebase_context>
</context>

<output_format>
Your entire response must be a single Markdown block.
The most important line of your output MUST be `OVERALL_VERDICT: [COMPLETE|INCOMPLETE]`.
Do not include any conversational text before or after your analysis.

OVERALL_VERDICT: [COMPLETE|INCOMPLETE]

## 1. IMPLEMENTATION VERIFICATION
- **Checklist Completion:** [Analyze the checklist. Are all items marked as done? Report status.]
- **Code Review:** [Review the code changes relevant to this phase. Do they correctly implement the goals? Are there any obvious bugs, anti-patterns, or style violations?]
- **Deliverable Check:** [Does the deliverable specified in the phase_info exist and is it correct?]

## 2. TEST VERIFICATION
- **Test Execution:** [Simulate running the `Success Test` command from the phase_info. Report the expected outcome.]
- **Test Coverage:** [Analyze the tests. Do they adequately cover the new or modified code?]
- **Regression Check:** [Does the implementation introduce any obvious regressions or break existing functionality described in the codebase context?]

## 3. QUALITY & DOCUMENTATION
- **Code Quality:** [Assess the quality of the new code. Is it clean, readable, and maintainable?]
- **Documentation:** [Are docstrings, comments, and any relevant external documentation updated?]

## 4. BLOCKERS (if INCOMPLETE)
- **Blocker 1:** [A specific, actionable reason why the phase is not complete.]
- **Blocker 2:** [Another specific, actionable reason.]

## 5. NEXT PHASE PREPARATION (if COMPLETE)
- **Next Phase Goal:** [Based on the implementation plan, what is the goal of the next phase?]
- **Key Modules for Next Phase:** [Identify files/modules that will be important for the next phase.]
- **Potential Challenges:** [Anticipate any risks or challenges for the next phase.]

## 6. GEMINI VERIFICATION SUMMARY
- **Overall Assessment:** [A brief summary of your findings.]
- **Confidence Score:** [HIGH | MEDIUM | LOW]

END OF VERIFICATION
</output_format>
</task>
PROMPT

# Inject the dynamic context
echo "$CURRENT_PHASE_INFO" > ./tmp/phase_info.txt
echo "$CURRENT_PHASE_CHECKLIST" > ./tmp/phase_checklist.txt
sed -i.bak -e '/\[Placeholder for the current phase info from implementation.md\]/r ./tmp/phase_info.txt' -e '//d' ./tmp/verify-prompt.md
sed -i.bak -e '/\[Placeholder for the current phase.s checklist.md\]/r ./tmp/phase_checklist.txt' -e '//d' ./tmp/verify-prompt.md

echo -e "\n<codebase_context>" >> ./tmp/verify-prompt.md
cat ./repomix-output.xml >> ./tmp/verify-prompt.md
echo -e "\n</codebase_context>" >> ./tmp/verify-prompt.md

echo "✅ Successfully built structured prompt file: ./tmp/verify-prompt.md"
```

### Step 4: MANDATORY - Execute Gemini Verification

```bash
# Execute Gemini with the fully-formed prompt file
GEMINI_RESPONSE=$(gemini -p "@./tmp/verify-prompt.md")
```

### Step 5: Process Gemini's Verdict and Manage Files

```bash
# Parse the verdict from the first line of the response.
VERDICT=$(echo "$GEMINI_RESPONSE" | grep '^OVERALL_VERDICT: ' | sed 's/^OVERALL_VERDICT: //')
REPORT_CONTENT=$(echo "$GEMINI_RESPONSE" | sed '1d') # Get the rest of the content

if [ "$VERDICT" == "COMPLETE" ]; then
    echo "✅ Phase $CURRENT_PHASE_NUMBER VERIFIED COMPLETE by Gemini."
    echo "$REPORT_CONTENT" # Display the full successful report

    # Update implementation.md and PROJECT_STATUS.md
    echo "Updating project tracking files..."
    # (Logic to mark phase complete and update status would go here)

    # Check if this was the final phase
    # If final, archive the project.
    # If not final, announce next step.
    echo "Next step: Run \`/phase-checklist-gemini-full $((CURRENT_PHASE_NUMBER + 1)) $INITIATIVE_PATH\` to generate the detailed checklist for the next phase."

elif [ "$VERDICT" == "INCOMPLETE" ]; then
    echo "❌ Phase $CURRENT_PHASE_NUMBER verification FAILED."
    
    # Extract and save the list of blockers
    BLOCKERS=$(echo "$REPORT_CONTENT" | awk '/## 4. BLOCKERS/,/## 5. NEXT PHASE PREPARATION/' | grep 'Blocker')
    FIX_LIST_PATH="$INITIATIVE_PATH/phase_${CURRENT_PHASE_NUMBER}_fixes.md"
    echo "# Phase $CURRENT_PHASE_NUMBER Fix-List (Blockers Only)" > "$FIX_LIST_PATH"
    echo "Generated on $(date)" >> "$FIX_LIST_PATH"
    echo "$BLOCKERS" >> "$FIX_LIST_PATH"

    echo "Gemini found BLOCKERS that must be fixed:"
    echo "$BLOCKERS"
    echo ""
    echo "A detailed fix-list has been saved to: $FIX_LIST_PATH"
    echo "After fixing all blockers, run this command again to re-verify."

else
    echo "❌ ERROR: Could not determine phase verdict from Gemini's output."
    echo "--- Gemini's Raw Output ---"
    echo "$GEMINI_RESPONSE"
    exit 1
fi
```
