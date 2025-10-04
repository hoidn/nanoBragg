#!/usr/bin/env bash
set -euo pipefail

# --- Activate the conda environment required for Claude automation ---
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate pytorch
# --------------------------------------------------------------------

# Sync with remote before starting work
timeout 30 git pull --rebase || {
  echo "WARNING: git pull --rebase failed or timed out. Proceeding with local state."
}

mkdir -p tmp
TS=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="tmp/claudelog${TS}.txt"
ln -sf "${LOG_FILE}" tmp/claudelog-latest.txt

CLAUDE_CMD="/home/ollie/.claude/local/claude"

# Execute debug prompt once per invocation
# Note: Using debug.md per routing guard while AT parity suite incomplete
cat prompts/main.md | "${CLAUDE_CMD}" -p --dangerously-skip-permissions --verbose --output-format stream-json | tee -a "${LOG_FILE}"

# Conditional push: only if there are commits to push and no errors occurred
if git diff --quiet origin/$(git rev-parse --abbrev-ref HEAD)..HEAD 2>/dev/null; then
  echo "No new commits to push."
else
  echo "Pushing commits to remote..."
  git push || {
    echo "WARNING: git push failed. Please push manually."
    exit 1
  }
fi
