#!/usr/bin/env bash
set -euo pipefail

# Tail the newest tmp/claudelog*.txt (or tmp/claudelog-latest.txt symlink) and pretty-print.

LATEST_SYMLINK="tmp/claudelog-latest.txt"
WAIT_SECS=${WAIT_SECS:-1}

echo "Waiting for loop output… (run ./loop.sh to start logging)" >&2

while :; do
  if [[ -L "$LATEST_SYMLINK" || -f "$LATEST_SYMLINK" ]]; then
    echo "Following via symlink: $LATEST_SYMLINK" >&2
    exec tail -n +1 -F "$LATEST_SYMLINK" | python3 scripts/pretty_stream_json.py
  fi

  latest_file=$(ls -t tmp/claudelog*.txt 2>/dev/null | head -n1 || true)
  if [[ -n "${latest_file:-}" ]]; then
    echo "Following latest file: $latest_file" >&2
    exec tail -n +1 -F "$latest_file" | python3 scripts/pretty_stream_json.py
  fi

  sleep "$WAIT_SECS"
done
