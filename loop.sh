#!/usr/bin/env bash
set -euo pipefail

# --- THE FIX: ACTIVATE THE CONDA ENVIRONMENT ---
# Replace 'conda' with the full path to your conda installation if needed.
# Find it with 'which conda' -> e.g., /home/ollie/miniconda3/bin/conda
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate pytorch
# -----------------------------------------------

# Ensure tmp directory exists
mkdir -p tmp

# Create a timestamped log file and update the 'latest' symlink
TS=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="tmp/claudelog${TS}.txt"
ln -sf "${LOG_FILE}" tmp/claudelog-latest.txt

CLAUDE_CMD="/home/ollie/.claude/local/claude"

# Default: run prompt a few times
for i in {1..10}; do
  cat prompts/debug.md | ${CLAUDE_CMD} -p --dangerously-skip-permissions --verbose --output-format stream-json | tee -a "${LOG_FILE}"
  #cat prompts/main.md | ${CLAUDE_CMD} -p --dangerously-skip-permissions --verbose --output-format stream-json | tee -a "${LOG_FILE}"
done
