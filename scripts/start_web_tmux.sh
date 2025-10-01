#!/usr/bin/env bash
set -euo pipefail

# Expose the tmux dashboard session over the web using ttyd or gotty, if available.
#
# Usage:
#  PORT=7681 SESSION=nbdash scripts/start_web_tmux.sh

PORT="${PORT:-7681}"
SESSION="${SESSION:-nbdash}"

# Ensure tmux session exists
if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session '$SESSION' not found; creating with scripts/tmux_dashboard.sh" >&2
  ATTACH=0 scripts/tmux_dashboard.sh >/dev/null 2>&1 || true
fi

if command -v ttyd >/dev/null 2>&1; then
  echo "Starting ttyd on http://localhost:${PORT} (attach to tmux:$SESSION)"
  exec ttyd -p "$PORT" tmux attach -t "$SESSION" || tmux new -s "$SESSION"
fi

if command -v gotty >/dev/null 2>&1; then
  echo "Starting gotty on http://localhost:${PORT} (attach to tmux:$SESSION)"
  exec gotty -p "$PORT" -w tmux attach -t "$SESSION" || tmux new -s "$SESSION"
fi

cat >&2 <<EOF
Neither 'ttyd' nor 'gotty' is installed.

Install one of:
  brew install ttyd
or
  brew install yudai/gotty/gotty

Then run again:
  PORT=${PORT} SESSION=${SESSION} scripts/start_web_tmux.sh
EOF
exit 1
