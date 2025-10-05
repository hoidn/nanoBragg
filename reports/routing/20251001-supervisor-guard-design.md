# Supervisor.sh Guard Design Note

**Date:** 2025-10-01
**Author:** Ralph (automation guard implementation)
**Reference:** loop.sh guard implementation (commit 853cf08)
**Plan:** plans/active/supervisor-loop-guard/plan.md Phase B1

## Context

The `supervisor.sh` automation script currently runs supervisor loops without the required safety guards that are already implemented in `loop.sh`. This design note specifies the guard elements needed to bring `supervisor.sh` up to the same safety standard.

## Reference Implementation (loop.sh)

The `loop.sh` script at commit 853cf08 implements three critical guards:

1. **Timeouted Git Pull with Fallback**
   ```bash
   timeout 30 git pull --rebase || {
     echo "WARNING: git pull --rebase failed or timed out. Proceeding with local state."
   }
   ```
   - Prevents indefinite hangs on network issues or rebase conflicts
   - Provides graceful fallback to continue with local state
   - 30-second timeout is sufficient for typical rebase operations

2. **Single Prompt Execution**
   ```bash
   # Execute debug prompt once per invocation
   cat prompts/debug.md | "${CLAUDE_CMD}" -p --dangerously-skip-permissions ...
   ```
   - No loops - script executes exactly once per invocation
   - External orchestration (e.g., cron, manual runs) controls repetition
   - Prevents runaway automation

3. **Conditional Push Guard**
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
   - Only pushes when there are actual commits
   - Fails gracefully if push fails
   - Provides clear user guidance on manual recovery

## Required Changes to supervisor.sh

### Current State Issues

The current `supervisor.sh` has four critical violations:

1. **No timeout on git pull** - commented out pull entirely (line 15)
2. **Multi-iteration loop** - runs 20 times (`for i in {1..20}`)
3. **No conditional push guard** - no push logic at all
4. **Missing conda env activation** - not activating pytorch environment

### Guard Design

#### 1. Timeouted Pull with Fallback

Add before the main execution:
```bash
# Sync with remote before starting work
timeout 30 git pull --rebase || {
  echo "WARNING: git pull --rebase failed or timed out. Proceeding with local state."
}
```

**Fallback Logic for Timeout:**
- If timeout occurs during rebase, the repository may be in a dirty state
- The script should attempt cleanup before continuing:
  ```bash
  timeout 30 git pull --rebase || {
    # Check if we're in mid-rebase
    if [ -d .git/rebase-merge ] || [ -d .git/rebase-apply ]; then
      echo "WARNING: Rebase in progress detected after timeout. Aborting rebase..."
      git rebase --abort 2>/dev/null || true
      echo "WARNING: Attempting non-rebase pull as fallback..."
      git pull --no-rebase || {
        echo "WARNING: Both rebase and merge pulls failed. Proceeding with local state."
      }
    else
      echo "WARNING: git pull --rebase failed or timed out. Proceeding with local state."
    fi
  }
  ```

#### 2. Single Execution

Replace the for-loop with single execution:
```bash
# Execute supervisor prompt once per invocation
${CODEX_CMD} exec -m gpt-5-codex -c model_reasoning_effort="high" --dangerously-bypass-approvals-and-sandbox < prompts/supervisor.md | tee -a "${LOG_FILE}"
SUPERVISOR_EXIT=$?
```

Capture exit code for conditional push logic.

#### 3. Conditional Push

Add after execution:
```bash
# Conditional push: only if there are commits to push and execution succeeded
if [ $SUPERVISOR_EXIT -eq 0 ]; then
  if git diff --quiet origin/$(git rev-parse --abbrev-ref HEAD)..HEAD 2>/dev/null; then
    echo "No new commits to push."
  else
    echo "Pushing commits to remote..."
    git push || {
      echo "WARNING: git push failed. Please push manually."
      exit 1
    }
  fi
else
  echo "WARNING: Supervisor execution failed (exit code: $SUPERVISOR_EXIT). Skipping push."
  exit $SUPERVISOR_EXIT
fi
```

#### 4. Conda Environment Activation

Add at the beginning (after shebang and set):
```bash
# --- Activate the conda environment required for supervisor automation ---
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate pytorch
# -----------------------------------------------------------------------
```

## Protected Assets Policy

The `supervisor.sh` file must be added to `docs/index.md` Core Project Guides section alongside `loop.sh` to formalize its protected status. This prevents accidental deletion during repository hygiene operations.

## Testing & Verification

1. **Dry Run Test:** Execute with `CODEX_CMD=printf ./supervisor.sh` to verify:
   - Single iteration occurs
   - Fallback warning paths work correctly
   - No push attempt on dry run

2. **Hygiene Check:** Run `bash -n supervisor.sh` to validate syntax

3. **Compliance Snapshot:** Capture final script state for audit trail

## Exit Criteria

- Script implements all four guard elements
- Dry run produces expected single-iteration behavior
- Script passes bash syntax check
- supervisor.sh added to docs/index.md Protected Assets list
- All artifacts stored in reports/routing/ with timestamps
