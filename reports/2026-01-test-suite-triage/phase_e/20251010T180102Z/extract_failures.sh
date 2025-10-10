#!/bin/bash
# Extract failures from pytest log for Phase E

LOGFILE="logs/pytest_full.log"
OUTFILE="failures_raw.txt"
MDFILE="failures_raw.md"

# Extract raw FAILED lines
grep '^FAILED ' "$LOGFILE" | sed 's/^FAILED //' > "$OUTFILE"

# Convert to markdown
{
  echo "# Phase E Failures"
  echo ""
  echo "**Timestamp:** 2025-10-10T18:01:02Z"
  echo "**Log:** logs/pytest_full.log"
  echo ""
  echo "## Failed Tests"
  echo ""
  while IFS= read -r line; do
    echo "- \`$line\`"
  done < "$OUTFILE"
} > "$MDFILE"

echo "Extracted $(wc -l < "$OUTFILE") failures"
echo "Created: $MDFILE"
