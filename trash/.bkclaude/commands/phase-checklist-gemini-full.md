# Command: /phase-checklist-gemini-full <phase-number> <initiative-path>

**Goal:** Autonomously generate a complete, highly-detailed, code-aware implementation checklist for a specific project phase using Gemini for analysis and generation.

**Usage:**
- `/phase-checklist-gemini-full 2 plans/active/my-project`

**Prerequisites:**
- An `implementation.md` file must exist at the specified `<initiative-path>`.
- The file must contain a clearly defined section for the given `<phase-number>`.

---

## 🔴 **CRITICAL: MANDATORY EXECUTION FLOW**

**YOUR ROLE IS TO ORCHESTRATE, NOT TO AUTHOR.**
1.  You MUST parse the phase information from the specified `implementation.md` file.
2.  You MUST run `repomix` to create a complete, fresh snapshot of the codebase context.
3.  You MUST build a structured prompt file (`tmp/checklist-prompt.md`) using the XML format.
4.  You MUST execute `gemini -p "@tmp/checklist-prompt.md"` to delegate the checklist generation.
5.  You MUST save Gemini's response **exactly as provided** to the correct output file.

**DO NOT:**
-   ❌ Modify, interpret, or add comments to Gemini's output. You are a file manager.
-   ❌ Create the checklist yourself. Your job is to run the process.
-   ❌ Skip any step.

---

## 🤖 **YOUR EXECUTION WORKFLOW**

### Step 1: Prepare Context from Local Files

```bash
# Parse arguments
PHASE_NUMBER="$1"
INITIATIVE_PATH="$2"
IMPLEMENTATION_PLAN_PATH="$INITIATIVE_PATH/implementation.md"

# Verify the implementation plan exists
if [ ! -f "$IMPLEMENTATION_PLAN_PATH" ]; then
    echo "❌ ERROR: Implementation plan not found at '$IMPLEMENTATION_PLAN_PATH'."
    exit 1
fi

# Extract the entire section for the specified phase.
PHASE_INFO_CONTENT=$(awk "/### \*\*Phase $PHASE_NUMBER:/{f=1} f && /^### \*\*Phase|## 📊 PROGRESS TRACKING/{if (!/Phase $PHASE_NUMBER/) f=0} f" "$IMPLEMENTATION_PLAN_PATH")

if [ -z "$PHASE_INFO_CONTENT" ]; then
    echo "❌ ERROR: Could not find or extract content for Phase $PHASE_NUMBER in '$IMPLEMENTATION_PLAN_PATH'."
    exit 1
fi
echo "✅ Successfully extracted info for Phase $PHASE_NUMBER."
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
rm -f ./tmp/checklist-prompt.md 2>/dev/null

# Create the structured prompt
cat > ./tmp/checklist-prompt.md << 'PROMPT'
<task>
You are an expert software engineer and project manager. Your task is to create a complete, ultra-detailed, step-by-step implementation checklist for a given project phase.

The checklist must be so detailed that a developer can execute it by copying and pasting code and commands directly. You must analyze the provided codebase context to inform your guidance, referencing existing patterns, APIs, and potential gotchas.

<steps>
<1>
Analyze the `<phase_info>` to understand the goals, deliverables, and critical context (especially "Potential Gotchas") for this phase.
</1>
<2>
Thoroughly analyze the entire `<codebase_context>` to find the exact files, functions, and code patterns relevant to the phase goal.
</2>
<3>
Generate the complete checklist. The final output must strictly adhere to the Markdown table format specified in `<output_format>`. The "How/Why & API Guidance" column is the most important part and must contain specific, actionable details.
</3>
</steps>

<context>
<phase_info>
[Placeholder for the Phase N section from implementation.md]
</phase_info>

<codebase_context>
<!-- Placeholder for content from repomix-output.xml -->
</codebase_context>
</context>

<output_format>
Your entire response must be a single Markdown block containing the checklist. Do not include any conversational text before or after the checklist. The format is non-negotiable.

# Phase [N]: [Phase Name] Checklist

**Initiative:** [Initiative Name]
**Created:** [Current Date]
**Phase Goal:** [Goal from phase_info]
**Deliverable:** [Deliverable from phase_info]

## ✅ Task List

### Instructions:
1.  Work through tasks in order. Dependencies are noted in the guidance column.
2.  The **"How/Why & API Guidance"** column contains all necessary details for implementation.
3.  Update the `State` column as you progress: `[ ]` (Open) -> `[P]` (In Progress) -> `[D]` (Done).

---

| ID  | Task Description                                   | State | How/Why & API Guidance                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            -
| :-- | :------------------------------------------------- | :---- | :-------------------------------------------------
| **Section 0: Preparation & Analysis**
| 0.A | **Review Critical Context**                        | `[ ]` | **Why:** To prevent common errors by understanding the specific challenges of this phase. <br> **Action:** [Gemini: Based on the 'Potential Gotchas' section of the phase_info, write a specific instruction here. e.g., "Carefully review the coordinate system mismatch between `raw_data.py` and `tf_helper.py`."]
| 0.B | **Analyze Source Code**                            | `[ ]` | **Why:** To understand the existing code before modification. <br> **Action:** [Gemini: Based on the 'Key Modules & APIs' section, list the exact files to be read. e.g., "Open and read `ptycho/raw_data.py` and `ptycho/tf_helper.py`."]
| **Section 1: Implementation Tasks**
| 1.A | **Implement: [Task 1 from phase_info]**            | `[ ]` | **Why:** [Gemini: Synthesize the reason from the phase goal.] <br> **File:** `[Gemini: Identify the exact file path]` <br> **API Guidance:** [Gemini: Provide a specific, actionable code snippet or API call, incorporating any necessary fixes for the 'Potential Gotchas'. e.g., "**CRITICAL:** You must swap the coordinates... Use this code: `offsets_xy = tf.gather(offsets_yx, [1, 0], axis=1)`"]
| ... | ...                                                | ...   | ...
| **Section 2: Testing & Validation**
| 2.A | **Write Unit/Integration Tests**                   | `[ ]` | **Why:** To verify the new implementation is correct. <br> **File:** `[Gemini: Suggest a new or existing test file]` <br> **Guidance:** [Gemini: Describe the specific test cases needed to validate the changes and the success criteria from the phase_info.]
| ... | ...                                                | ...   | ...

---

## 🎯 Success Criteria
... (Standard success criteria section) ...

</output_format>
</task>
PROMPT

# Inject the dynamic context
echo "$PHASE_INFO_CONTENT" > ./tmp/phase_info.txt
sed -i.bak -e '/\[Placeholder for the Phase N section from implementation.md\]/r ./tmp/phase_info.txt' -e '//d' ./tmp/checklist-prompt.md

echo -e "\n<codebase_context>" >> ./tmp/checklist-prompt.md
cat ./repomix-output.xml >> ./tmp/checklist-prompt.md
echo -e "\n</codebase_context>" >> ./tmp/checklist-prompt.md

echo "✅ Successfully built structured prompt file: ./tmp/checklist-prompt.md"
```

### Step 4: MANDATORY - Execute Gemini Analysis

```bash
# Execute Gemini with the fully-formed prompt file
GEMINI_RESPONSE=$(gemini -p "@./tmp/checklist-prompt.md")
```

### Step 5: Save Gemini's Checklist

```bash
# Define the output path
OUTPUT_PATH="$INITIATIVE_PATH/phase_${PHASE_NUMBER}_checklist.md"

# Save the checklist exactly as received.
echo "$GEMINI_RESPONSE" > "$OUTPUT_PATH"

# Verify the file was saved
if [ ! -s "$OUTPUT_PATH" ]; then
    echo "❌ ERROR: Failed to save Gemini's output to '$OUTPUT_PATH'."
    exit 1
fi

# Announce completion to the user
echo "✅ Saved Gemini's complete Phase $PHASE_NUMBER checklist to: $OUTPUT_PATH"
echo ""
echo "The checklist is ready for execution and contains highly detailed, code-aware tasks."
