#!/usr/bin/env bash
set -euo pipefail

# Create a tmux dashboard with two panes:
#  - Left: pytest loop (colored output)
#  - Right: loop.sh pretty-printed JSON stream
#
# Usage:
#  scripts/tmux_dashboard.sh            # create/attach session
#  TEST_PATH=tests SLEEP_SECS=3 scripts/tmux_dashboard.sh

SESSION="${SESSION:-nbdash}"

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is required. Install via brew install tmux" >&2
  exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  exec tmux attach -t "$SESSION"
fi

# Create new session detached with a window named 'dash'
tmux new-session -d -s "$SESSION" -n dash

# Left pane (pane 0): pytest loop
tmux send-keys -t "$SESSION":dash.0 "chmod +x scripts/run_pytest_loop.sh 2>/dev/null || true" C-m
tmux send-keys -t "$SESSION":dash.0 "scripts/run_pytest_loop.sh" C-m

# Right pane: split horizontally and run loop pretty-printer (follows newest log)
tmux split-window -h -t "$SESSION":dash
tmux send-keys -t "$SESSION":dash.1 "chmod +x scripts/pretty_claudelog_tail.sh 2>/dev/null || true" C-m
tmux send-keys -t "$SESSION":dash.1 "scripts/pretty_claudelog_tail.sh" C-m

# Optional: enable mouse navigation
tmux set -t "$SESSION" -g mouse on >/dev/null 2>&1 || true

exec tmux attach -t "$SESSION"
