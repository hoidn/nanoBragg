#!/usr/bin/env bash
set -euo pipefail

# Ensure the conda environment used for Claude loops is active.
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate pytorch

# Prepare a timestamped log for supervisor runs.
mkdir -p tmp
TS=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="tmp/supervisorlog${TS}.txt"
ln -sf "${LOG_FILE}" tmp/supervisorlog-latest.txt

CLAUDE_CMD="/home/ollie/.claude/local/claude"

# Run the supervisor prompt repeatedly to manage Ralph's loops.
for i in {1..20}; do
  cat prompts/supervisor.md | ${CLAUDE_CMD} -p --dangerously-skip-permissions --verbose --output-format stream-json | tee -a "${LOG_FILE}"
done
