# Pyrefly Static Analysis Baseline - 20251008T053652Z

## Purpose
STATIC-PYREFLY-001 Phase A: Pre-flight verification for pyrefly static analysis tooling.

## Execution Context
- **Date**: 2025-10-08 05:36:52 UTC
- **Branch**: feature/spec-based-2
- **Plan**: `plans/active/static-pyrefly.md`
- **Fix Plan Entry**: `docs/fix_plan.md` line 2943-2957

## Phase A Results ✅

### A1: Configuration Verification ✅
- **pyproject.toml**: `[tool.pyrefly]` found at line 11
- **Tool Version**: pyrefly 0.35.0
- **Availability**: CONFIRMED

### A2: Artifact Directory ✅
- **Location**: `reports/pyrefly/20251008T053652Z/`
- **Files Created**:
  - `commands.txt` - Detailed command log with outputs and exit codes
  - `README.md` - This file

### A3: Fix Plan Update ✅
Status: Completed in Attempt #1 (see `docs/fix_plan.md:2954-2968`)

## Phase B Results ✅

### B1: Baseline Scan Execution ✅
- **Command**: `pyrefly check src | tee reports/pyrefly/20251008T053652Z/pyrefly.log`
- **Exit Code**: 1 (violations detected)
- **Total Errors**: 78 errors (3 ignored)
- **Timestamp**: 2025-10-08T05:46:01Z

### B2: Environment Snapshot ✅
- **File**: `env.json`
- **Python**: 3.13.7
- **Pyrefly**: 0.35.0
- **Git Commit**: 8ca885f95dfca23d8a3e3867af3f5aefff7f40a3
- **Git Branch**: feature/spec-based-2

### B3: Diagnostics Summary ✅
- **File**: `summary.md`
- **Grouped by**: Severity (Blocker/High/Medium/Low), Rule ID, File
- **Top Issues**:
  - 29 unsupported-operation errors (None arithmetic, Tensor `**` operations)
  - 26 bad-argument-type errors (Tensor vs scalar mismatches)
  - 8 read-only errors (device property assignments)
  - 7 missing-attribute errors (NoneType access)

## Next Steps
- Phase C: Triage and prioritize findings (classify blocker/high/medium/defer)
- Phase D: Update `docs/fix_plan.md` Attempt #2 and prepare Ralph delegation
- Phase E: Post-fix validation (after Ralph completes fixes)

## Artifacts
- `commands.txt` - Command execution log with Phase A & B entries
- `README.md` - This overview
- `pyrefly.log` - Full pyrefly output (78 errors)
- `env.json` - Environment snapshot (Python, pyrefly versions, git state)
- `summary.md` - Comprehensive analysis with severity grouping and recommendations
