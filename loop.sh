#!/usr/bin/env bash
set -euo pipefail

# --- Activate the conda environment required for Claude automation ---
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate pytorch
# --------------------------------------------------------------------

mkdir -p tmp
TS=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="tmp/claudelog${TS}.txt"
ln -sf "${LOG_FILE}" tmp/claudelog-latest.txt

CLAUDE_CMD="/home/ollie/.claude/local/claude"

for i in {1..20}; do
  cat prompts/main.md | "${CLAUDE_CMD}" -p --dangerously-skip-permissions --verbose --output-format stream-json | tee -a "${LOG_FILE}"
  git push || true
  sleep 1
done
