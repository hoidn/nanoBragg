# Workflow Rules for General Triclinic Cell Parameters Initiative

*Created: 2025-07-29*  
*Initiative: General Triclinic Cell Parameters*

This document codifies the workflow patterns and best practices established during the implementation of this initiative.

## 📋 Initiative Workflow Structure

### 1. Initiative Creation (`/customplan`)
- **Always create a feature branch**: `feature/<initiative-name>`
- **Directory structure**: `plans/active/<initiative-name>/`
- **Required files**:
  - `plan.md` - R&D plan with objectives and validation criteria
  - `implementation.md` - Phased breakdown with Git tracking
  - `phase_X_checklist.md` - Detailed task lists per phase
  - `workflow_rules.md` - Initiative-specific patterns (this file)

### 2. Phase Management (`/phase-checklist`)
- **Leverage existing work**: Check `plans/<similar-feature>/` for reusable checklists
- **Checklist format**: Use table format with ID, Task, State, and Guidance columns
- **Task states**: `[ ]` → `[P]` → `[D]`
- **Task granularity**: 15-60 minutes per task, 8-20 tasks per phase

### 3. Implementation Workflow

#### Phase Execution Pattern
1. **Start phase**: Update todo list to track phase and current tasks
2. **Section 0**: Always review documents and identify target files first
3. **Progressive implementation**: Complete sections in order
4. **Continuous validation**: Test after each major change
5. **Commit at phase end**: Single atomic commit per phase

#### Todo Management Rules
- **Track phases**: One todo per phase showing overall progress
- **Track active tasks**: Add todos for current section/task being worked on
- **Update immediately**: Mark todos complete as soon as task finishes
- **Clean up**: Remove completed task todos, keep phase todos

## 🛠️ Technical Implementation Rules

### 1. Golden Data Generation
- **Create reproducible scripts**: Always include `regenerate_golden.sh`
- **Document parameters**: Store exact parameters in `params.json`
- **Save orientation**: For random orientations, save the values for reproducibility
- **Use defaults**: When HKL files are problematic, use `-default_F` parameter

### 2. Configuration Updates
- **Extend dataclasses**: Add new parameters with sensible defaults
- **Import types**: Add `Optional` when adding nullable fields
- **Maintain compatibility**: Default values should preserve existing behavior

### 3. Documentation Updates
- **CLAUDE.md**: Add domain-specific conventions (e.g., crystallographic)
- **Golden README**: Document new test cases with exact commands
- **Inline updates**: Update checklists to mark completed tasks

### 4. Git Workflow
- **Stage carefully**: Only add files related to current phase
- **Descriptive commits**: Use conventional commits with clear messages
- **Include attribution**: Add Claude Code attribution in commit messages
- **Update status**: Keep PROJECT_STATUS.md current

## 🔍 Quality Assurance Rules

### 1. Testing Infrastructure
- **Create placeholder tests**: Even in Phase 1, create test file structure
- **Environment variables**: Always set `KMP_DUPLICATE_LIB_OK=TRUE` for PyTorch
- **Verify paths**: Double-check file paths before operations

### 2. Code Quality
- **Format before commit**: Run `black` on modified Python files
- **Handle missing tools**: Check if formatters/linters exist before running
- **Fix imports**: Update imports when adding new types (e.g., `Optional`)

### 3. Validation Steps
- **Check file creation**: Verify files exist after creation
- **Test commands**: Run golden data generation commands to ensure they work
- **Preserve output**: Save command output in trace logs for debugging
- **C-code references**: For ported functions, verify docstring contains mandatory C-code quote

## 📝 Documentation Patterns

### 1. Phase Checklists
```markdown
| ID | Task Description | State | How/Why & API Guidance |
| :--- | :--- | :--- | :--- |
| 0.A | **Review Key Documents** | `[ ]` | **Why:** Context needed. <br> **Docs:** List specific files. |
```

#### For Functions Porting C-Code Logic:
Break implementation into separate stub creation and implementation tasks:
```markdown
| X.A | **Create function_name stub with C-code reference** | `[ ]` | **Why:** Mandatory traceability per CLAUDE.md Rule #11. <br> **How:** Create function with docstring containing C-code quote BEFORE implementation. |
| X.B | **Implement function_name logic** | `[ ]` | **Why:** Core functionality. <br> **How:** Now implement the Python version, referencing the C-code in the docstring above. |
| X.C | **Verify C-code reference completeness** | `[ ]` | **Why:** Ensure compliance with Rule #11. <br> **How:** Confirm docstring includes line numbers and verbatim C-code. |
```

### 2. Commit Messages
```
feat(geometry): Phase N - Brief description

- Bullet points of key changes
- Reference to specifications
- Note any important decisions

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 3. Status Updates
- Update PROJECT_STATUS.md after each phase
- Show progress with visual bars: `████████████████ 100% ✅`
- Update phase history with completion status

## ⚠️ Common Pitfalls & Solutions

### 1. Path Issues
- **Problem**: Assuming `src/` directory exists at root
- **Solution**: Use `find` to locate actual paths before operations

### 2. Test Infrastructure
- **Problem**: No existing test framework in early phases
- **Solution**: Create minimal test structure, skip regression tests if needed

### 3. HKL File Issues
- **Problem**: Simple HKL files rejected by nanoBragg
- **Solution**: Use `-default_F` parameter or generate comprehensive P1.hkl

### 4. Reproducibility
- **Problem**: Random orientations make tests non-reproducible
- **Solution**: Save random values and use them explicitly in commands

## 🚀 Efficiency Tips

### 1. Reuse Existing Work
- Check similar initiatives in `plans/` directory
- Adapt existing checklists rather than writing from scratch
- Copy patterns from related features

### 2. Batch Operations
- Update multiple checklist items with `MultiEdit`
- Stage related files together in git
- Run related commands in sequence

### 3. Progressive Development
- Complete Phase 1 setup before starting implementation
- Test each component before integration
- Document as you go, not at the end

## 📋 Phase Transition Checklist

Before moving to the next phase:
- [ ] All tasks in current phase marked `[D]`
- [ ] Phase success criteria verified
- [ ] Code formatted and linted
- [ ] Changes committed with descriptive message
- [ ] PROJECT_STATUS.md updated
- [ ] Todo list updated for next phase

---

*This workflow was established during the implementation of the General Triclinic Cell Parameters initiative and should be adapted as needed for future features.*