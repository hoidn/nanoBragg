# Supervisor Guard Design Memo

**Timestamp (UTC):** 20251009T044254Z
**Git Commit:** f92611b (current HEAD at memo creation)
**Plan Reference:** plans/active/supervisor-loop-guard/plan.md Phase B1
**Related Audit:** reports/routing/20251009T043816Z-supervisor-regression.txt
**Authoritative Commands Source:** docs/development/testing_strategy.md
**Related fix_plan Entry:** [ROUTING-SUPERVISOR-001] Attempt #2 (2025-10-09)

---

## 1. Context & Motivation

### 1.1 Background

The `supervisor.sh` script currently lacks critical automation guards that were previously implemented for `loop.sh` (commit 853cf08). This creates operational risks:

- **Runaway loops:** The script executes 20 iterations by default (`SYNC_LOOPS=20`) with no single-execution mode, violating the automation guard contract specified in `prompts/meta.md`.
- **Rebase failures:** No timeout guard or fallback logic exists for `git pull --rebase`, leaving automation in an inconsistent state when rebases fail or timeout.
- **Unconditional pushes:** The script pushes after every iteration regardless of whether new commits exist or the prompt execution succeeded, potentially propagating failures.
- **Missing Protected Assets coverage:** `docs/index.md` does not list `supervisor.sh`, allowing accidental deletion during repository hygiene operations.

### 1.2 Regression Evidence

The audit log at `reports/routing/20251009T043816Z-supervisor-regression.txt` documents:

1. **Legacy bash path (lines 115-120):** Executes `{1..20}` loop with no single-iteration mode
2. **SYNC mode (lines 126-390):** Implements `SYNC_LOOPS` variable defaulting to 20 iterations
3. **No timeout guard:** The `git_safe_pull()` function exists but was added after the original guard regression; the loop path at lines 117-119 has no pull guard at all
4. **Unconditional push:** Lines 162, 327, 353, 368, 373 show `git push || true` with no commit existence check
5. **Protected Assets gap:** `docs/index.md` lists `loop.sh` and `input.md` but omits `supervisor.sh`

### 1.3 Design Goals

This memo defines guard requirements to bring `supervisor.sh` into compliance with:

- **Single-iteration contract:** Execute `prompts/supervisor.md` exactly once per invocation
- **Timeout & fallback flow:** Timeouted rebase with graceful recovery on failure
- **Conditional push logic:** Only push when new commits exist and prompt execution succeeded
- **Protected Assets policy:** Formalize `supervisor.sh` as a protected file in `docs/index.md`

---

## 2. Guard Parity Analysis

### 2.1 Reference Implementation: loop.sh (commit 853cf08)

The guarded `loop.sh` implements three critical protections:

1. **Timeouted pull with fallback:**
   ```bash
   timeout 30 git pull --rebase || {
     echo "WARNING: git pull --rebase failed or timed out. Proceeding with local state."
   }
   ```

2. **Single prompt execution:**
   ```bash
   cat prompts/debug.md | "${CLAUDE_CMD}" -p --dangerously-skip-permissions --verbose --output-format stream-json | tee -a "${LOG_FILE}"
   ```
   (Exactly one invocation per script run)

3. **Conditional push:**
   ```bash
   if git diff --quiet origin/$(git rev-parse --abbrev-ref HEAD)..HEAD 2>/dev/null; then
     echo "No new commits to push."
   else
     echo "Pushing commits to remote..."
     git push || {
       echo "WARNING: git push failed. Please push manually."
       exit 1
     }
   fi
   ```

### 2.2 Current supervisor.sh Gaps

| Guard Aspect | loop.sh (853cf08) | supervisor.sh (current) | Required Change |
|--------------|-------------------|------------------------|-----------------|
| **Pull Guard** | `timeout 30 git pull --rebase` with fallback warning | Legacy path: NONE; SYNC path: `git_safe_pull()` exists but needs integration at line 117-119 | Add timeout guard to legacy path (lines 115-120) |
| **Single Execution** | One prompt per script run | Legacy: loops 20×; SYNC: loops `SYNC_LOOPS` times (default 20) | **CRITICAL:** Refactor to single execution per invocation |
| **Conditional Push** | Checks `git diff --quiet origin/HEAD..HEAD` before pushing | Pushes unconditionally via `git push \|\| true` | Add commit existence check; fail on push error instead of `\|\| true` |
| **Exit Code Handling** | Exits non-zero on push failure | Uses `\|\| true` to suppress errors | Remove error suppression; surface failures |
| **Protected Assets** | Listed in `docs/index.md` Core Guides | NOT listed | Add to `docs/index.md` in Phase B5 |

### 2.3 Line-by-Line Commentary

**Legacy Path (lines 115-120):**
- Line 117: `for i in {1..20}; do` — hardcoded 20-iteration loop violates single-execution contract
- Line 118: Direct codex invocation with no pull guard before loop entry
- Line 120: No conditional push logic; script exits after loop without sync

**SYNC Path (lines 126-390):**
- Line 126: `for i in $(seq 1 "$SYNC_LOOPS"); do` — parameterized loop still defaults to 20 iterations
- Line 127: `git_safe_pull` called inside loop (good) but legacy path skips it entirely
- Lines 162, 327, 353, 368, 373: All use `git push || true` pattern, hiding failures
- No commit existence check before any push operation

---

## 3. Timeout & Fallback Flow Design

### 3.1 Required Commands

The guard must implement a two-stage fallback:

```bash
timeout 30 git pull --rebase || {
  echo "WARNING: git pull --rebase failed or timed out. Attempting recovery..." | tee -a "$LOG_FILE"
  git rebase --abort || true
  git pull --no-rebase || true
}
```

### 3.2 Rationale

- **30-second timeout:** Matches `loop.sh` precedent; prevents indefinite hangs on network issues
- **Abort + no-rebase fallback:** Recovers from incomplete rebases by aborting and falling back to merge
- **Logging:** Records warnings in timestamped log for post-mortem analysis

### 3.3 Integration Points

**Legacy path:** Add guard before line 117 (before loop entry)
**SYNC path:** `git_safe_pull()` function already exists (lines 298-304) but must be:
1. Called before legacy loop entry (line 117)
2. Verified to match the spec above (current implementation at lines 298-304 looks correct)

### 3.4 State File Considerations

The SYNC mode manages `sync/state.json` to coordinate galph/ralph turns. The pull guard must:
- Execute BEFORE reading `$STATE_FILE` to ensure latest state is visible
- Handle conflicts in `sync/state.json` via the rebase/merge fallback
- Log state transitions (already implemented at lines 160-162, 350-353, etc.)

---

## 4. Single Iteration Contract Design

### 4.1 Behavioral Requirements

**SYNC_VIA_GIT=0 Mode (Legacy, lines 115-120):**
- MUST execute `prompts/supervisor.md` exactly once
- MUST remove the `for i in {1..20}; do` loop
- SHOULD add pull guard before execution
- MUST add conditional push after execution

**SYNC_VIA_GIT=1 Mode (SYNC, lines 124-390):**
- MUST default to `SYNC_LOOPS=1` instead of 20
- SHOULD retain `SYNC_LOOPS` variable for explicit multi-turn scenarios (e.g., testing)
- MUST document that `SYNC_LOOPS > 1` is for testing only and requires explicit override

### 4.2 Exit Code Handling

Current code (line 165-166):
```bash
set +e
${CODEX_CMD} exec -m gpt-5-codex -c model_reasoning_effort="high" --dangerously-bypass-approvals-and-sandbox < prompts/supervisor.md | tee -a "${LOG_FILE}"
```

Required changes:
```bash
set +e
${CODEX_CMD} exec -m gpt-5-codex -c model_reasoning_effort="high" --dangerously-bypass-approvals-and-sandbox < prompts/supervisor.md | tee -a "${LOG_FILE}"
rc=$?
set -e

if [[ "$rc" -ne 0 ]]; then
  echo "ERROR: Supervisor prompt execution failed (rc=$rc). Halting." | tee -a "$LOG_FILE"
  exit "$rc"
fi
```

### 4.3 Pseudo-Code for Refactored Legacy Path

```bash
# Legacy async mode (single execution)
if [[ "$SYNC_VIA_GIT" -eq 0 ]]; then
  # Pull guard
  timeout 30 git pull --rebase || {
    echo "WARNING: git pull --rebase failed or timed out. Proceeding with local state."
  }

  # Single execution
  set +e
  ${CODEX_CMD} exec -m gpt-5-codex -c model_reasoning_effort="high" --dangerously-bypass-approvals-and-sandbox < prompts/supervisor.md | tee -a "${LOG_FILE}"
  rc=$?
  set -e

  # Conditional push
  if [[ "$rc" -eq 0 ]]; then
    if git diff --quiet origin/$(git rev-parse --abbrev-ref HEAD)..HEAD 2>/dev/null; then
      echo "No new commits to push."
    else
      echo "Pushing commits to remote..."
      git push || {
        echo "ERROR: git push failed. Please push manually."
        exit 1
      }
    fi
  else
    echo "ERROR: Supervisor prompt failed (rc=$rc). Skipping push."
    exit "$rc"
  fi

  exit 0
fi
```

---

## 5. Conditional Push Logic Design

### 5.1 Detection Strategy

The guard must check three conditions before pushing:

1. **New commits exist:** Compare local HEAD to remote tracking branch
2. **Prompt succeeded:** Exit code from codex invocation is 0
3. **Push attempt succeeds:** Propagate push failures instead of suppressing with `|| true`

### 5.2 Implementation Pattern

```bash
# After successful prompt execution (rc=0)
if git diff --quiet origin/$(git rev-parse --abbrev-ref HEAD)..HEAD 2>/dev/null; then
  echo "No new commits to push." | tee -a "$LOG_FILE"
else
  echo "Pushing commits to remote..." | tee -a "$LOG_FILE"
  if ! git push; then
    echo "ERROR: git push failed. Please push manually." | tee -a "$LOG_FILE"
    exit 1
  fi
  echo "Push successful." | tee -a "$LOG_FILE"
fi
```

### 5.3 Parity with loop.sh

The `loop.sh` guard (commit 853cf08) uses this exact pattern. Key differences to preserve:

- **Error propagation:** `loop.sh` exits 1 on push failure; `supervisor.sh` currently suppresses errors with `|| true`
- **Logging:** Both scripts log to timestamped files; `supervisor.sh` must maintain `tee -a "${LOG_FILE}"` pattern
- **Branch detection:** `loop.sh` uses `$(git rev-parse --abbrev-ref HEAD)` to get current branch name

### 5.4 SYNC Mode Adjustments

The SYNC mode (lines 126-390) has additional state management. The conditional push must:

1. **Check commit existence** before lines 162, 327, 353, 368, 373
2. **Update state file** only if push succeeds (already implemented at line 160-162 pattern)
3. **Halt on push failure** instead of continuing to next iteration

Example for line 162 region:
```bash
# Current (lines 159-162):
write_state "galph" "running-galph" 0 ""
git add "$STATE_FILE"
git commit -m "[SYNC i=${ITER}] actor=galph status=running" || true
git push || true

# Required:
write_state "galph" "running-galph" 0 ""
git add "$STATE_FILE"
if ! git commit -m "[SYNC i=${ITER}] actor=galph status=running"; then
  echo "WARNING: No changes to commit for state update." | tee -a "$LOG_FILE"
fi
if git diff --quiet origin/$(git rev-parse --abbrev-ref HEAD)..HEAD 2>/dev/null; then
  echo "No new commits to push (state update)." | tee -a "$LOG_FILE"
else
  if ! git push; then
    echo "ERROR: Failed to push state update. Halting SYNC loop." | tee -a "$LOG_FILE"
    exit 1
  fi
fi
```

---

## 6. Protected Assets Update Plan

### 6.1 Required docs/index.md Change

**Current Core Guides section (lines 17-24):**
```markdown
### Core Project Guides
* **[CLAUDE.md](../CLAUDE.md)** - The primary instruction set for the AI agent.
* **[README.md](../README.md)** - The main project entry point.
* **[README_PYTORCH.md](../README_PYTORCH.md)** - Comprehensive user guide for the PyTorch implementation.
* **[PROJECT_STATUS.md](../PROJECT_STATUS.md)** - Tracks the current active development initiative.
* **[loop.sh](../loop.sh)** - Supervisory automation harness for Claude loops; treat as a protected asset.
* **[supervisor.sh](../supervisor.sh)** - Supervisor (galph) runner. Supports `--sync-via-git` for cross-machine turn taking; treat as a protected asset.
* **[input.md](../input.md)** - Supervisor→Engineer steering memo. Rewritten and committed each supervisor run; treat as a protected asset.
```

**Analysis:**
- **GOOD NEWS:** `supervisor.sh` is already listed at line 22!
- **ACTION:** Verify this entry exists during Phase B5 hygiene check
- **NO CHANGE NEEDED** to docs/index.md listing

### 6.2 Protected Assets Policy Compliance

The existing entry already includes the required "treat as a protected asset" annotation. Phase B5 verification must confirm:

1. Entry exists at docs/index.md:22
2. Annotation "treat as a protected asset" is present
3. Description mentions `--sync-via-git` functionality (already present)

### 6.3 Additional Documentation Updates

**CLAUDE.md:** No changes required (already references supervisor.sh via docs/index.md)

**prompts/meta.md:** Should be reviewed to ensure routing rules mention supervisor.sh guard requirements (out of scope for this memo; note for future)

---

## 7. Verification Checklist for Phases B3/B4

### 7.1 Phase B3: Guarded Dry Run

**Command:**
```bash
CODEX_CMD=printf ./supervisor.sh > reports/routing/20251009T044254Z-supervisor-dry-run.log 2>&1
```

**Expected Log Contents:**
- Single iteration (not 20×)
- Pull guard timeout warning path demonstrated (if rebase fails)
- No actual push attempt (dry run mode)
- Timestamped log file created under `tmp/`

**Success Criteria:**
- Log shows exactly one prompt invocation
- `printf` substitution for `${CODEX_CMD}` works correctly
- No `git push` commands executed
- Log file under 1KB (no repetition)

### 7.2 Phase B4: Hygiene Verification

**Shell Syntax Check:**
```bash
bash -n supervisor.sh > reports/routing/20251009T044254Z-supervisor-hygiene.txt 2>&1
echo "Exit code: $?" >> reports/routing/20251009T044254Z-supervisor-hygiene.txt
```

**Optional ShellCheck:**
```bash
if command -v shellcheck &>/dev/null; then
  shellcheck supervisor.sh >> reports/routing/20251009T044254Z-supervisor-hygiene.txt 2>&1
fi
```

**Git Status Verification:**
```bash
git status --short >> reports/routing/20251009T044254Z-supervisor-hygiene.txt
```

**Expected Output:**
- Syntax check exit code: 0
- ShellCheck warnings (if any): reviewed and documented
- Git status: Only `supervisor.sh` (and possibly this memo) modified

### 7.3 Test Collection (Authoritative Command)

Per `docs/development/testing_strategy.md` §1.5, docs-only loops must verify test collection:

```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q > reports/routing/20251009T044254Z-pytest-collect.log 2>&1
echo "Exit code: $?" >> reports/routing/20251009T044254Z-pytest-collect.log
```

**Success Criteria:**
- Exit code: 0
- No import errors
- Test count matches pre-change baseline (~500-600 tests)

---

## 8. Risks & Open Questions

### 8.1 Python Orchestrator Interaction

**Issue:** Lines 11-14 implement a Python orchestrator fallback:
```bash
if [[ "${ORCHESTRATION_PYTHON:-1}" == "1" ]]; then
  PYTHON_BIN=${PYTHON_BIN:-python3}
  exec "$PYTHON_BIN" -m scripts.orchestration.supervisor "$@"
fi
```

**Risk:** This memo only addresses the bash codepath (lines 17-390). The Python orchestrator may have separate guard requirements.

**Mitigation:**
- Document in memo that Python path is out of scope for Phase B
- Create follow-up fix_plan item if Python orchestrator is actively used
- Verify `ORCHESTRATION_PYTHON=0` during dry run to test bash path

### 8.2 Environment Variable Defaults

**Current Defaults:**
- `SYNC_VIA_GIT=0` (legacy async mode, 20× loop)
- `SYNC_LOOPS=20` (SYNC mode iteration count)
- `POLL_INTERVAL=5` (seconds)
- `MAX_WAIT_SEC=0` (no timeout)

**Question:** Should `SYNC_LOOPS` default be changed to 1 as part of this guard implementation?

**Recommendation:** YES. Change line 218 from:
```bash
SYNC_LOOPS=${SYNC_LOOPS:-20}
```
to:
```bash
SYNC_LOOPS=${SYNC_LOOPS:-1}
```

Rationale: Single-iteration contract requires `SYNC_LOOPS=1` by default. Users needing multi-turn testing must explicitly override.

### 8.3 State File Rotation

**Observation:** `sync/state.json` grows indefinitely with timestamps in `last_update` field.

**Risk:** Not a guard issue, but may cause eventual file bloat.

**Action:** Out of scope for this guard design; note for future state management improvements.

### 8.4 Logging Expectations

**Current Pattern:** Timestamped logs under `tmp/supervisorlog*.txt` with symlink to `tmp/supervisorlog-latest.txt`

**Question:** Should logs be rotated after N runs?

**Recommendation:** Out of scope for guard implementation. Existing pattern is acceptable for operational hygiene.

---

## 9. Implementation Roadmap

### 9.1 Phase B2: Implement Guarded Script

**Task List:**

1. **Lines 115-120 (Legacy Path):**
   - [ ] Add pull guard before line 117
   - [ ] Remove `for i in {1..20}; do` loop
   - [ ] Add single execution of `prompts/supervisor.md`
   - [ ] Capture exit code and implement conditional push
   - [ ] Exit 0 after single execution

2. **Line 218 (SYNC Loop Default):**
   - [ ] Change `SYNC_LOOPS=${SYNC_LOOPS:-20}` to `SYNC_LOOPS=${SYNC_LOOPS:-1}`

3. **Lines 159-162, 327, 353, 368, 373 (Conditional Push Sites):**
   - [ ] Add commit existence check before each `git push`
   - [ ] Remove `|| true` error suppression
   - [ ] Add explicit error logging and exit 1 on push failure
   - [ ] Preserve state file update logic

4. **Lines 126-390 (SYNC Mode Loop Refactoring):**
   - [ ] Consider removing loop entirely (execute once per invocation)
   - [ ] OR: Document that `SYNC_LOOPS > 1` requires explicit override
   - [ ] Update logging to clarify single-turn vs multi-turn modes

**Estimated Diff Size:** ~50 lines changed, ~30 lines added, ~15 lines removed

### 9.2 Phase B3: Dry Run Evidence

**Command:**
```bash
CODEX_CMD=printf ./supervisor.sh > reports/routing/20251009T044254Z-supervisor-dry-run.log 2>&1
```

**Artifacts:**
- `reports/routing/20251009T044254Z-supervisor-dry-run.log`

**Success Criteria:**
- Log shows single iteration
- No git push executed
- No errors from printf substitution

### 9.3 Phase B4: Hygiene Verification

**Commands:**
```bash
bash -n supervisor.sh > reports/routing/20251009T044254Z-supervisor-hygiene.txt 2>&1
git status --short >> reports/routing/20251009T044254Z-supervisor-hygiene.txt
KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q >> reports/routing/20251009T044254Z-pytest-collect.log 2>&1
```

**Artifacts:**
- `reports/routing/20251009T044254Z-supervisor-hygiene.txt`
- `reports/routing/20251009T044254Z-pytest-collect.log`

**Success Criteria:**
- Syntax check passes (exit 0)
- Only expected files modified in git status
- Test collection passes (exit 0)

### 9.4 Phase B5: Protected Assets Verification

**Task:**
- [ ] Verify `docs/index.md` line 22 contains `supervisor.sh` entry
- [ ] Confirm "treat as a protected asset" annotation present
- [ ] Document verification in `reports/routing/20251009T044254Z-supervisor-protected-asset.md`

**Expected Outcome:** No changes needed (already compliant)

---

## 10. Appendix: References

### 10.1 Plan & Tracking

- **Plan:** `plans/active/supervisor-loop-guard/plan.md` (Phase B1 row)
- **Fix Plan Entry:** `docs/fix_plan.md` § [ROUTING-SUPERVISOR-001] (lines 407-434)
- **Audit Log:** `reports/routing/20251009T043816Z-supervisor-regression.txt`
- **galph Memory:** `galph_memory.md` (supervisor notes, latest entry 2025-10-13)

### 10.2 Reference Implementation

- **loop.sh Guard:** Commit 853cf08
- **Reference Plan:** `plans/active/routing-loop-guard/plan.md`
- **Loop Audit:** `reports/routing/20251001-loop-audit.txt`
- **Loop Compliance:** `reports/routing/20251001-compliance-verified.txt`

### 10.3 Policies & SOPs

- **Routing Rules:** `prompts/meta.md` (lines 1-200, automation policy)
- **Protected Assets Policy:** `docs/index.md` § Core Project Guides (lines 17-24)
- **Testing Strategy:** `docs/development/testing_strategy.md` § 1.5 (loop execution notes)
- **Authoritative Commands:** `docs/development/testing_strategy.md` (pytest collection command)

### 10.4 File:Line Anchors

- `supervisor.sh:11-14` — Python orchestrator fallback
- `supervisor.sh:17-20` — Timestamped log setup
- `supervisor.sh:115-120` — Legacy async mode (20× loop)
- `supervisor.sh:126-390` — SYNC mode implementation
- `supervisor.sh:218` — `SYNC_LOOPS` default (currently 20)
- `supervisor.sh:298-304` — `git_safe_pull()` function
- `docs/index.md:22` — `supervisor.sh` Protected Assets entry
- `plans/active/supervisor-loop-guard/plan.md:35` — Phase B1 task definition
- `docs/fix_plan.md:407-434` — [ROUTING-SUPERVISOR-001] tracking entry

---

## 11. Completion Checklist

**Phase B1 Deliverables:**

- [x] Memo drafted with UTC timestamp (20251009T044254Z)
- [x] Context section summarizes regression findings (§1)
- [x] Guard Parity Table included with line-by-line commentary (§2)
- [x] Timeout & Fallback Flow documented (§3)
- [x] Single Iteration Contract specified for both modes (§4)
- [x] Conditional Push Logic detailed with pseudo-code (§5)
- [x] Protected Assets update plan prepared (§6)
- [x] Verification Checklist for B3/B4 provided (§7)
- [x] Risks & Open Questions catalogued (§8)
- [x] Implementation Roadmap with task list (§9)
- [x] References appendix with file:line anchors (§10)

**Next Actions (Implementation Loops):**

1. Execute Phase B2 tasks (implement guard in supervisor.sh)
2. Run Phase B3 dry run and capture log
3. Execute Phase B4 hygiene checks
4. Verify Phase B5 Protected Assets (already compliant)
5. Update `docs/fix_plan.md` Attempts History with Phase B outcomes
6. Update `plans/active/supervisor-loop-guard/plan.md` to mark B1 [D] (done)

**Memo Status:** ✅ COMPLETE — Ready for implementation (Phase B2)

---

**End of Memo**
*Generated by: ralph (engineer loop, docs-only mode)*
*Approved for: Phase B2 implementation*
