#!/usr/bin/env bash
set -euo pipefail

# --- Activate the conda environment required for supervisor automation ---
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate pytorch
# -----------------------------------------------------------------------

# Sync with remote before starting work
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

# Prepare a timestamped log for supervisor runs.
mkdir -p tmp
TS=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="tmp/supervisorlog${TS}.txt"
ln -sf "${LOG_FILE}" tmp/supervisorlog-latest.txt

CODEX_CMD="codex"

# Execute supervisor prompt once per invocation
# Note: External orchestration (e.g., cron, manual runs) controls repetition
${CODEX_CMD} exec -m gpt-5-codex -c model_reasoning_effort="high" --dangerously-bypass-approvals-and-sandbox < prompts/supervisor.md | tee -a "${LOG_FILE}"
SUPERVISOR_EXIT=$?

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
