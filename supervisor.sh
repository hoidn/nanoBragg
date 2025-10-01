#!/usr/bin/env bash
set -euo pipefail


# Prepare a timestamped log for supervisor runs.
mkdir -p tmp
TS=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="tmp/supervisorlog${TS}.txt"
ln -sf "${LOG_FILE}" tmp/supervisorlog-latest.txt

CODEX_CMD="codex"

# Run the supervisor prompt repeatedly to manage Ralph's loops.
for i in {1..20}; do
  #git pull
  ${CODEX_CMD} exec -m gpt-5-codex -c model_reasoning_effort="high" --dangerously-bypass-approvals-and-sandbox < prompts/supervisor.md | tee -a "${LOG_FILE}"
done
