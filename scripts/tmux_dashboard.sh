#!/usr/bin/env bash
set -euo pipefail

# Create a tmux dashboard with two panes ready for manual commands:
#  - Pane 0: intended for pytest loop
#  - Pane 1: intended for loop.sh stream-json pretty-printer
#
# Usage:
#  scripts/tmux_dashboard.sh            # create/attach session
#  TEST_PATH=tests SLEEP_SECS=3 scripts/tmux_dashboard.sh

SESSION="${SESSION:-nbdash}"
ATTACH="${ATTACH:-1}"

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is required. Install via brew install tmux" >&2
  exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  if [[ "$ATTACH" == "1" ]]; then
    exec tmux attach -t "$SESSION"
  else
    exit 0
  fi
fi

# Create new session detached with a window named 'dash'
tmux new-session -d -s "$SESSION" -n dash

# Split window to create two panes for manual commands
tmux split-window -h -t "$SESSION":dash

# Store useful defaults inside the session environment for manual use
tmux set-environment -t "$SESSION" NB_DASH_LOG "tmp/claudelog-latest.txt"
tmux set-environment -t "$SESSION" NB_DASH_WAIT_SECS "${WAIT_SECS:-1}"

# Provide quick guidance in panes; user will run commands manually
tmux send-keys -t "$SESSION":dash.0 "clear && echo 'Pane 0: run scripts/run_pytest_loop.sh (or your pytest command).'" C-m
tmux send-keys -t "$SESSION":dash.1 "clear && echo 'Pane 1: run scripts/pretty_claudelog_tail.sh or ./loop.sh | python3 scripts/pretty_stream_json.py .'" C-m

# Optional: enable mouse navigation
tmux set -t "$SESSION" -g mouse on >/dev/null 2>&1 || true

if [[ "$ATTACH" == "1" ]]; then
  exec tmux attach -t "$SESSION"
fi

exit 0
