#!/usr/bin/env bash
set -euo pipefail

# Ensure tmp directory exists
mkdir -p tmp

# Create a timestamped log file and update the 'latest' symlink
TS=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="tmp/claudelog${TS}.txt"
ln -sf "${LOG_FILE}" tmp/claudelog-latest.txt

# Optional alternative prompt
# while :; do cat prompts/ralph_orchestrator_PROMPT.md | claude -p --dangerously-skip-permissions --verbose --output-format stream-json | tee -a "${LOG_FILE}" ; done

# Default: run prompt a few times to generate stream-json, teeing to the log file
for i in {1..10}; do
  cat prompts/main.md | claude -p --dangerously-skip-permissions --verbose --output-format stream-json | tee -a "${LOG_FILE}"
done


