# Command: /new-initiative

**Goal:** To formally begin a new development initiative by creating a structured R&D plan, optionally informed by a high-level architectural document.

**Usage:** `/new-initiative "A descriptive name for the new initiative" [optional path to planning_doc.md]`

**Example:**
*   `/new-initiative "Fix Data Pipeline"`
*   `/new-initiative "Refactor Voxelization Module" docs/proposals/voxel_refactor_v2.md`

**Architectural Guidance (from user input):**
$ARGUMENTS

---
## 🚀 **EXECUTION STRATEGY**

**As the AI agent, follow these steps precisely:**

1.  **Identify Initiative Name and Architectural Guidance:**
    *   The initiative name is the first line of the `$ARGUMENTS` block above.
    *   The architectural guidance is the entire content of the `$ARGUMENTS` block. This may be a simple path to a file or a more detailed free-text description.

2.  **Create Initiative Slug:**
    *   Convert the initiative name into a file-safe "slug" (e.g., `"Refactor Voxelization Module"` becomes `refactor_voxelization_module`).

3.  **Determine File Paths:**
    *   **Template Path:** `customplan.md` (in the root directory).
    *   **Output Directory:** `docs/studies/`.
    *   **Output Filename:** `plan_<initiative_slug>.md`.
    *   **Example Output Path:** `docs/studies/plan_refactor_voxelization_module.md`.

4.  **Read Template and Gather Context:**
    *   Read the entire content of the `customplan.md` template file into memory.
    *   If the architectural guidance in `$ARGUMENTS` contains a file path, read the content of that file.

5.  **Generate New R&D Plan Content:**
    *   **If the `$ARGUMENTS` block is empty or contains only the initiative name:** The content for the new R&D plan is simply the content of the `customplan.md` template.
    *   **If the `$ARGUMENTS` block contains architectural guidance:**
        *   Use the provided guidance to intelligently pre-fill the `customplan.md` template.
        *   **Objective & Hypothesis:** Summarize the core problem and proposed solution from the guidance.
        *   **Scope & Deliverables:** Extract the key deliverables mentioned.
        *   **Technical Implementation Details:** List the key modules and dependencies identified.
        *   **Validation & Verification Plan:** List the key tests and success criteria mentioned.
        *   **IMPORTANT:** The final output must still follow the structure of the `customplan.md` template.

6.  **Create New R&D Plan File:**
    *   Use the `Edit` tool to create a new file at the determined output path.
    *   Write the generated (and possibly pre-filled) content into this new file.

7.  **Update Project Status Tracker:**
    *   Read `docs/PROJECT_STATUS.md`.
    *   Add a new entry under the "Planned Initiatives" section. If this section doesn't exist, create it.
    *   The entry must include the initiative name and a link to the new R&D plan. If the guidance included a file path, link to that as well.
    *   **Example Entry (with architectural doc):**
        ```markdown
        - **Refactor Voxelization Module**
          - **Architectural Plan:** `docs/proposals/voxel_refactor_v2.md`
          - **R&D Plan:** `docs/studies/plan_refactor_voxelization_module.md`
        ```

8.  **Engage User for Next Steps:**
    *   Announce that the new R&d plan has been created and the project status has been updated.
    *   Use the "USER ENGAGEMENT SCRIPT" below to prompt the user for the next action.

---

## 🤔 **USER ENGAGEMENT SCRIPT**

**Announce the following to the user:**

"I have created the new R&D plan for the initiative: **<Initiative Name>**."

"The plan is located at: **`<path/to/new/plan.md>`**"

"I have pre-filled it based on the architectural guidance you provided. Please review and complete the plan with any remaining details."

"Once the plan is finalized, run the `/implementation` command to generate the phased implementation plan."

---

## 📤 **OUTPUTS**

This command will produce the following artifacts:

1.  **A new R&D plan file:** Located at `docs/studies/plan_<initiative_slug>.md`. This will be either a direct copy of the template or an intelligently pre-filled version based on the user's input.
2.  **An updated project status tracker:** The `docs/PROJECT_STATUS.md` file will be modified to include the new initiative and links to its planning documents.

