#while :; do cat prompts/ralph_orchestrator_PROMPT.md | claude -p --dangerously-skip-permissions --verbose --output-format stream-json ; done
for i in {1..5}; do cat prompts/main.md | claude -p --dangerously-skip-permissions --verbose --output-format stream-json ; done


