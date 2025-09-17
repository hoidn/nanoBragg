# Command: /prime-context

**Goal:** To load the project's essential, authoritative documentation into your working context. This command MUST be run before starting any new implementation or refactoring task to ensure all subsequent actions are aligned with the project's established architecture and conventions.

---

## 🔴 **CRITICAL: MANDATORY EXECUTION FLOW**

**YOUR ROLE IS AN AUTONOMOUS LEARNER. YOUR ONLY TASK IS TO READ AND CONFIRM.**
1.  You MUST read the full content of the three specified core documentation files.
2.  You MUST NOT analyze any other code or files during this process.
3.  You MUST confirm that you have read and understood the contents by providing a structured summary.

**DO NOT:**
-   ❌ Skim the documents. You must read them in their entirety.
-   ❌ Suggest any code changes or start any implementation. This is a read-only task.
-   ❌ Proceed with any other task until this priming is complete and you have provided the confirmation summary.

---

## 🤖 **YOUR EXECUTION WORKFLOW**

### Step 1: Read Authoritative Documentation

You will now execute the following steps to load the project's core principles into your context.

```bash
# Announce the start of the priming process.
echo "Initializing context priming. Reading core architectural and conventional documents..."

# Read the three core documents.
# We will use cat and store the output in variables for later processing.
# This ensures the content is fully loaded into your context.

DOC_ARCHITECTURE=$(cat docs/architecture/pytorch_design.md)
DOC_CONVENTIONS=$(cat docs/architecture/conventions.md)
DOC_CLAUDE=$(cat CLAUDE.md)

# Verify that the files were read successfully.
if [ -z "$DOC_ARCHITECTURE" ] || [ -z "$DOC_CONVENTIONS" ] || [ -z "$DOC_CLAUDE" ]; then
    echo "❌ ERROR: One or more core documentation files are missing or empty. Halting."
    exit 1
fi

echo "✅ Successfully loaded all core documentation into context."
```

### Step 2: Generate Confirmation Summary

After successfully reading the files in Step 1, you MUST generate and present the following summary. This confirms to the user that you have successfully primed your context.

**Do not proceed until you have outputted this exact format.**

---

## ✅ **Context Priming Complete: Confirmation Report**

I have successfully read and loaded the following core project documents into my working context:

1.  **`docs/architecture/pytorch_design.md`**
2.  **`docs/architecture/conventions.md`**
3.  **`CLAUDE.md`**

### My Understanding of the Core Principles:

*   **Architectural Pattern:** The project follows a vectorized, object-oriented design (`Simulator`, `Crystal`, `Detector`) that replaces C-style loops with PyTorch tensor broadcasting. All configuration is managed via dataclasses.
*   **Unit System Convention:**
    *   **Internal:** All calculations MUST use **Angstroms (Å)** for length and **radians** for angles.
    *   **User-Facing:** Configuration (`.Config` classes) MUST accept **millimeters (mm)** and **degrees**.
    *   **C-Trace Interface:** I am aware that C-trace logs may use other units (e.g., **meters** for `PIX0_VECTOR`) and I must handle these conversions during testing.
*   **Coordinate System Convention:**
    *   **Lab Frame:** Right-handed, with the beam along the `+X` axis.
    *   **Pixel Indexing:** `(slow, fast)` order, with integer indices referring to the **pixel's leading edge/corner**, not its center. All `meshgrid` calls must use `indexing="ij"`.
*   **Crystallographic Convention:** Miller indices (h,k,l) are calculated via dot product of the scattering vector with the **real-space lattice vectors (a, b, c)**.
*   **Differentiability:** The computation graph must be preserved. I will avoid `.item()`, `.numpy()`, and `torch.linspace` on tensors that require gradients. I will use the "Boundary Enforcement Pattern" for type safety.
*   **Debugging:** All physics debugging must start with a **Parallel Trace Comparison** against the C-code golden traces, as detailed in `docs/development/debugging.md`.

My context is now primed. I am ready to proceed with the next task.
