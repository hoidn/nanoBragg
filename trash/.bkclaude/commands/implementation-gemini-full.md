# Command: /implementation-gemini-full <initiative-path>

**Goal:** Autonomously generate a complete, code-aware, phased implementation plan by delegating the analysis and authoring to Gemini, then saving the resulting artifacts to the project structure.

**Usage:**
- `/implementation-gemini-full plans/active/real-time-notifications`

**Prerequisites:**
- An R&D plan (`plan.md`) must exist at the specified `<initiative-path>`.

---

## 🔴 **CRITICAL: MANDATORY EXECUTION FLOW**

**YOUR ROLE IS AN AUTONOMOUS ORCHESTRATOR AND FILE MANAGER.**
1.  You MUST parse the R&D plan from the specified `<initiative-path>/plan.md`.
2.  You MUST run `repomix` to create a complete, fresh snapshot of the codebase context.
3.  You MUST build a structured prompt file (`tmp/impl-prompt.md`) using the XML format.
4.  You MUST execute `gemini -p "@tmp/impl-prompt.md"` to delegate the implementation plan generation.
5.  You MUST save Gemini's response **exactly as provided** to the correct output file.
6.  You MUST update `PROJECT_STATUS.md` with the new phase information.

**DO NOT:**
-   ❌ Modify, interpret, or enhance Gemini's output in any way.
-   ❌ Create the implementation plan yourself. Your job is to run the process.
-   ❌ Skip any step. The workflow is non-negotiable.

---

## 🤖 **YOUR EXECUTION WORKFLOW**

### Step 1: Prepare Context from the R&D Plan

```bash
# Parse arguments
INITIATIVE_PATH="$1"
RD_PLAN_PATH="$INITIATIVE_PATH/plan.md"

# Verify the R&D plan exists
if [ ! -f "$RD_PLAN_PATH" ]; then
    echo "❌ ERROR: R&D plan not found at '$RD_PLAN_PATH'."
    echo "Please run /customplan-gemini-full first."
    exit 1
fi

# Read the entire content of the R&D plan.
RD_PLAN_CONTENT=$(cat "$RD_PLAN_PATH")
echo "✅ Successfully loaded R&D plan from '$RD_PLAN_PATH'."
```

### Step 2: Aggregate Codebase Context with Repomix

```bash
# Use repomix for a complete, single-file context snapshot.
npx repomix@latest . \
  --include "**/*.{js,py,md,sh,json,c,h,log,yml,toml}" \
  --ignore "build/**,node_modules/**,dist/**,*.lock,tmp/**"

# Verify that the context was created successfully.
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
rm -f ./tmp/impl-prompt.md 2>/dev/null

# Create the structured prompt with placeholders
cat > ./tmp/impl-prompt.md << 'PROMPT'
<task>
You are an expert Lead Software Engineer. Your task is to create a complete, phased implementation plan based on a high-level R&D plan.

Your implementation plan must be deeply informed by an analysis of the provided codebase. You will break the project down into logical, testable phases, and for each phase, you will define the goals, tasks, and potential risks.

<steps>
<1>
Analyze the `<rd_plan_context>` to understand the project's overall objectives, scope, and technical specifications.
</1>
<2>
Thoroughly analyze the entire `<codebase_context>` to identify natural boundaries for phasing, dependencies, existing code patterns, and potential risks. This analysis is critical for creating a safe and effective plan.
</2>
<3>
Generate the complete, phased implementation plan. The plan must strictly adhere to the format specified in `<output_format>`. All sections, especially "Key Modules & APIs" and "Potential Gotchas," must be filled out based on your analysis.
</3>
</steps>

<context>
<rd_plan_context>
[Placeholder for the content of plan.md]
</rd_plan_context>

<codebase_context>
<!-- Placeholder for content from repomix-output.xml -->
</codebase_context>
</context>

<output_format>
Your entire response must be a single Markdown block containing the implementation plan. Do not include any conversational text before or after the plan. The format is non-negotiable.

<!-- ACTIVE IMPLEMENTATION PLAN -->
<!-- DO NOT MISTAKE THIS FOR A TEMPLATE. THIS IS THE OFFICIAL SOURCE OF TRUTH FOR THE PROJECT'S PHASED PLAN. -->

# Phased Implementation Plan

**Project:** [Name from R&D Plan]
**Initiative Path:** `[Initiative Path]`

---
## Git Workflow Information
**Feature Branch:** [Value of current git branch]
**Baseline Branch:** [Value of baseline branch from PROJECT_STATUS.md]
**Baseline Commit Hash:** [Commit hash of baseline branch]
**Last Phase Commit Hash:** [Commit hash of baseline branch]
---

**Created:** [Current Date, e.g., 2025-08-03]
**Core Technologies:** [List of technologies from your analysis]

---

## 📄 **DOCUMENT HIERARCHY**
... (Standard hierarchy section) ...

---

## 🎯 **PHASE-BASED IMPLEMENTATION**

**Overall Goal:** [Synthesize a one-sentence summary from the R&D Plan's objective.]

**Total Estimated Duration:** [Sum of phase estimates, e.g., 3 days]

---

## 📋 **IMPLEMENTATION PHASES**

### **Phase 1: [Descriptive Phase Name]**

**Goal:** [Clear, concise goal for this phase.]
**Deliverable:** [A specific, verifiable artifact, e.g., "A new module `src/core/new_feature.py` with passing unit tests."]
**Estimated Duration:** [e.g., 1 day]

**Key Modules & APIs to Touch:**
- `[path/to/module1.py]`: [Brief reason]
- `[path/to/module2.py]`: [Brief reason]

**Potential Gotchas & Critical Conventions:**
- [A specific, code-aware warning, e.g., "The `offsets_f` tensor in `raw_data.py` stores coordinates in `[y, x]` order."]
- [Another warning, e.g., "The `hh.translate` function expects `[dx, dy]` order. A coordinate swap will be necessary."]

**Implementation Checklist:** `phase_1_checklist.md`
**Success Test:** [A specific command to run to verify completion, e.g., `pytest tests/core/test_new_feature.py` completes with 100% pass rate.]

---

### **Phase 2: [Descriptive Phase Name]**
... (Repeat for all necessary phases) ...

---

### **Final Phase: Validation & Documentation**
... (Standard final phase section) ...

---

## 📊 **PROGRESS TRACKING**
... (Standard progress tracking section) ...

---

## 🚀 **GETTING STARTED**
... (Standard getting started section) ...

---

## ⚠️ **RISK MITIGATION**
... (Standard risk mitigation section) ...

</output_format>
</task>
PROMPT

# Inject the dynamic context
echo "$RD_PLAN_CONTENT" > ./tmp/rd_plan.txt
sed -i.bak -e '/\[Placeholder for the content of plan.md\]/r ./tmp/rd_plan.txt' -e '//d' ./tmp/impl-prompt.md

echo -e "\n<codebase_context>" >> ./tmp/impl-prompt.md
cat ./repomix-output.xml >> ./tmp/impl-prompt.md
echo -e "\n</codebase_context>" >> ./tmp/impl-prompt.md

echo "✅ Successfully built structured prompt file: ./tmp/impl-prompt.md"
```

### Step 4: MANDATORY - Execute Gemini Analysis

```bash
# Execute Gemini with the fully-formed prompt file
GEMINI_RESPONSE=$(gemini -p "@./tmp/impl-prompt.md")
```

### Step 5: Save Implementation Plan and Update Project Status

```bash
# Define the output path
OUTPUT_PATH="$INITIATIVE_PATH/implementation.md"

# Save the plan exactly as received.
echo "$GEMINI_RESPONSE" > "$OUTPUT_PATH"

# Verify the file was saved
if [ ! -s "$OUTPUT_PATH" ]; then
    echo "❌ ERROR: Failed to save Gemini's output to '$OUTPUT_PATH'."
    exit 1
fi
echo "✅ Saved Gemini's implementation plan to: $OUTPUT_PATH"

# Update PROJECT_STATUS.md
echo "Updating PROJECT_STATUS.md with new phase information..."
# (Logic to parse $GEMINI_RESPONSE for phase count, duration, etc., and update PROJECT_STATUS.md would go here)
echo "✅ Updated PROJECT_STATUS.md"

# Announce completion to the user
echo ""
echo "Next step: Run \`/phase-checklist-gemini-full 1 $INITIATIVE_PATH\` to have Gemini create the detailed Phase 1 checklist."
```

