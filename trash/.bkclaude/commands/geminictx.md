# Command: /geminictx [query]

**Goal:** Leverage a two-pass AI workflow to provide a comprehensive, context-aware answer to a user's query about the codebase. Pass 1 uses Gemini to identify relevant files, and Pass 2 uses your own (Claude's) synthesis capabilities on the full content of those files.

**Usage:**
- `/geminictx "how does authentication work?"`
- `/geminictx "explain the data loading pipeline"`

---

## 🔴 **CRITICAL: MANDATORY EXECUTION FLOW**

**This command follows a deliberate, non-negotiable two-pass workflow:**
1.  **Setup:** You MUST create a clean, isolated temporary directory for all generated files.
2.  **Context Aggregation:** You MUST run `repomix`, ensuring it ignores the temporary directory.
3.  **Pass 1 (Gemini as Context Locator):** You MUST build a structured prompt file *inside the temporary directory* and execute `gemini -p`.
4.  **Pass 2 (Claude as Synthesizer):** You MUST then read the full content of EVERY file Gemini identified to build your own deep context before providing a synthesized answer.

**DO NOT:**
-   ❌ Create any temporary files or prompts in the project's root directory.
-   ❌ Skip the `repomix` step.
-   ❌ Answer the user's query before completing both passes.

---

## 🤖 **YOUR EXECUTION WORKFLOW**

### Step 1: Setup and Context Aggregation

Create an isolated environment for this run's artifacts and then generate the codebase context.

```bash
set -euo pipefail
IFS=$'\n\t'

# The user's query is passed as $ARGUMENTS
USER_QUERY="$ARGUMENTS"
# Create a unique, isolated directory for this run's artifacts to prevent context pollution.
TEMP_DIR="./tmp/geminictx_run_$(date +%s)"
mkdir -p "$TEMP_DIR"
echo "INFO: Using temporary directory: $TEMP_DIR"

# Use repomix for a complete, single-file context snapshot.
# The --ignore flag for "tmp/**" is critical to prevent feedback loops.
npx repomix@latest . --top-files-len 20 --include "**/*.{js,py,md,sh,json,c,h}" --ignore "build/**,node_modules/**,dist/**,*.lock,.claude/**,PtychoNN/**,torch/**,tmp/**" -o "$TEMP_DIR/repomix-output.xml"

# Verify that the context was created successfully.
if [ ! -s "$TEMP_DIR/repomix-output.xml" ]; then
    echo "❌ ERROR: Repomix failed to generate the codebase context. Aborting."
    exit 1
fi

echo "✅ Codebase context aggregated into $TEMP_DIR/repomix-output.xml."
```

### Step 2: Build and Execute Pass 1 (Gemini as Context Locator)

Now, build a structured prompt in the isolated directory.

#### Step 2.1: Build the Prompt File
```bash
# Define the path for the prompt file inside our isolated directory.
PROMPT_FILE="$TEMP_DIR/gemini-pass1-prompt.md"

# Create the structured prompt using the new template.
# This file contains the core instructions but no dynamic content yet.
cat > "$PROMPT_FILE" << 'PROMPT'
<task>
You are an expert scientist and staff level engineer. Your sole purpose is to analyze the provided codebase context and identify the most relevant files for answering the user's query. Do not answer the query yourself.

<steps>
<0>
Given the codebase context in `<codebase_context>`,
in a <scratchpad>, list the paths of all source code, documentation, test, and configuration files.
</0>

<1>
Analyze the user's `<query>`.
REVIEW PROJECT DOCUMENTATION
 - **Read CLAUDE.md thoroughly** - This contains essential project context, architecture, and known patterns
 - **Read DEVELOPER_GUIDE.md carefully** - This explains the development workflow, common issues, and debugging approaches
 - Review all architecture.md and all other high-level architecture documents
 - **Understand the project structure** from these documents before diving into the code
</1>

<2>
Think step-by-step about the user's query to form a complete understanding of the problem.
- **Hypothesize**: Formulate potential root causes based on the query (e.g., is it a data corruption issue, a configuration error, a logic bug in a specific function, or a regression?).
- **Investigate**: Use your hypotheses to guide a targeted analysis of the codebase, looking for evidence.
- **Synthesize**: Form a complete theory of the problem, identifying the key components, their interactions, and the sequence of events that leads to the failure.
- **Verify**: Review the `<codebase_context>` again to find specific evidence (code snippets, documentation, log messages) that confirms your theory.
</2>

<3>
For each relevant file you identify, provide your output in the strict format specified in `<output_format>`.
</3>
</steps>

<output_format>
Your output must contain the following sections in this exact order:

Section 0:
A list of the at least 25 files that are most relevant to the query (or all files, if there are fewer than 25). Each entry must follow this exact format.

FILE: [exact/path/to/file.ext]
SCORE: [A numeric score from 0.4 to 10.0, where 10 is the most relevant.]

Section 1: Thought Process
A detailed, step-by-step analysis of your reasoning. This section should explicitly include:
- **Initial Hypotheses**: What were your initial theories about the root cause of the problem?
- **Key Evidence**: What specific code snippets, documentation excerpts, or file relationships from the codebase led you to your conclusion?
- **Synthesized Root Cause**: A final, clear explanation of the chain of events causing the issue, referencing the key files involved.

Section 2: Data Flow and Component Analysis
A detailed analysis of all data flows, transformations, and component interactions relevant to the query.
- **Diagrams**: Use Mermaid syntax (e.g., `graph TD` for data flow or `sequenceDiagram` for call flows) to illustrate the problematic workflow.
- **Data Contracts**: Document critical data contracts in markdown tables. The table should include columns for: **Data**, **Source Component**, **Destination Component**, **Shape**, **Dtype**, and **Description**. Focus on the data being passed between the components you identified as most relevant.
- **Formulas/Pseudocode**: Use mathematical formulas or pseudocode to clarify key physical models or data transformations (e.g., `Intensity = |FFT(Probe * Object_patch)|^2`).

Section 3: Curated File List
A curated list of final entries (i.e. a subset of the files in Section 0). Each entry MUST follow this exact format, ending with three dashes on a new line.

FILE: [exact/path/to/file.ext]
RELEVANCE: [A concise, one-sentence explanation of why this file is relevant.]
SCORE: [A numeric score from 0.4 to 10.0, where 10 is the most relevant.]
---

Do not use tools. Your job is to do analysis, not an intervention.
</output_format>

<instructions>
think hard before you answer.
</instructions>
</task>
PROMPT
```

#### Step 2.2: Append Dynamic Context
```bash
# Now, append the dynamic content (user query and repomix context) to the prompt file.
# This append-only method is robust and follows the new template structure.

# Append the user query, wrapped in tags
echo -e "\n<query>\n$USER_QUERY\n</query>\n" >> "$PROMPT_FILE"

# Append the full codebase context, wrapped in tags
echo -e "<codebase_context>\n" >> "$PROMPT_FILE"
cat "$TEMP_DIR/repomix-output.xml" >> "$PROMPT_FILE"
echo -e "\n</codebase_context>" >> "$PROMPT_FILE"

echo "✅ Built final structured prompt for Pass 1: $PROMPT_FILE"
```

#### Step 2.3: Execute Gemini
```bash
# Execute Gemini with the single, clean prompt file.
# The response is saved to a file for reliable parsing.
GEMINI_RESPONSE_FILE="$TEMP_DIR/gemini-pass1-response.txt"
gemini -p "@$PROMPT_FILE" > "$GEMINI_RESPONSE_FILE"

if [ ! -s "$GEMINI_RESPONSE_FILE" ]; then
    echo "❌ ERROR: Gemini command failed or produced no output."
    exit 1
fi
```

### Step 3: Process Gemini's Response & Prepare for Pass 2

Parse the response file from the temporary directory.

```bash
# Read response
GEMINI_RESPONSE_FILE="$TEMP_DIR/gemini-pass1-response.txt"
GEMINI_RESPONSE="$(cat "$GEMINI_RESPONSE_FILE")"

# Extract only the "Curated File List" (Section 3), keep full path after "FILE: "
FILE_LIST="$(
  awk '
    BEGIN{capture=0}
    /^Section 3: Curated File List/ {capture=1; next}
    capture && /^Section [0-9]+:/ {capture=0}
    capture && /^FILE: / { sub(/^FILE:[[:space:]]*/,""); print }
  ' "$GEMINI_RESPONSE_FILE"
)"

if [ -z "$FILE_LIST" ]; then
  echo "⚠️ Gemini did not identify any files in Section 3. The analysis may be incomplete."
  exit 0
fi

echo "Gemini identified these files:"
printf '%s\n' "$FILE_LIST"

# Safe, space-tolerant iteration
mapfile -t FILES < <(printf '%s\n' "$FILE_LIST")
```

### Step 4: Execute Pass 2 (Claude as Synthesizer)

This is your primary role. Read the full content of the identified files to build deep context.

```bash
# Announce what you are doing for transparency.
echo "Now reading the full content of each identified file to build a deep understanding..."

for file in "${FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "Reading: $file"
    # cat "$file"  # or your ingestion logic
  else
    echo "WARN: Not found: $file"
  fi
done

# After reading all files, you are ready to synthesize the answer.
```

### Step 5: Present Your Synthesized Analysis

Your final output to the user should follow this well-structured format.

```markdown
Based on your query, Gemini identified the following key files, which I have now read and analyzed in their entirety:

-   `path/to/relevant/file1.ext`
-   `path/to/relevant/file2.ext`
-   `docs/relevant_guide.md`

Here is a synthesized analysis of how they work together to address your question.

### Summary
[Provide a 2-3 sentence, high-level answer to the user's query based on your comprehensive analysis of the files.]

### Detailed Breakdown

#### **Core Logic in `path/to/relevant/file1.ext`**
[Explain the role of this file. Reference specific functions or classes you have read.]

**Key Code Snippet:**
\`\`\`[language]
[Quote a critical code block from the file that you have read.]
\`\`\`

#### **Workflow Orchestration in `path/to/relevant/file2.ext`**
[Explain how this file uses or connects to the core logic from the first file.]

**Key Code Snippet:**
\`\`\`[language]
[Quote a relevant snippet showing the interaction.]
\`\`\`

### How It All Connects
[Provide a brief narrative explaining the data flow or call chain between the identified components.]

### Conclusion
[End with a concluding thought or a question to guide the user's next step.]
```
