#!/usr/bin/env bash
set -euo pipefail

# Simple re-run loop to show pytest status with colors in-place.
# - Respects TEST_PATH (default: tests)
# - Respects PYTEST_ARGS for extra flags
# - Respects SLEEP_SECS between runs (default: 5)

TEST_PATH="${TEST_PATH:-tests}"
PYTEST_ARGS="${PYTEST_ARGS:-}" 
SLEEP_SECS="${SLEEP_SECS:-5}"

# Some environments need this to avoid MKL/KMP warnings when using torch/numpy
export KMP_DUPLICATE_LIB_OK=TRUE

while :; do
  # Clear screen but preserve scrollback in tmux pane
  printf "\033c"
  echo "[pytest] $(date '+%H:%M:%S') — running…"
  echo
  # Ensure colored output even when not attached to a TTY directly
  pytest --color=yes ${PYTEST_ARGS} "$TEST_PATH" || true
  echo
  echo "[pytest] cycle complete. Sleeping ${SLEEP_SECS}s. Press Ctrl-C to stop."
  sleep "$SLEEP_SECS"
done
