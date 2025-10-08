#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

LOG_NAME_RE = re.compile(r"^iter-(\d+)_.*\.log$")


def find_logs(root: Path) -> Dict[int, Path]:
    """Scan a role directory for iter-*.log files and return {iter: path}."""
    found: Dict[int, Path] = {}
    if not root.exists():
        return found
    for p in sorted(root.glob("iter-*.log")):
        m = LOG_NAME_RE.match(p.name)
        if not m:
            continue
        try:
            it = int(m.group(1))
        except ValueError:
            continue
        found[it] = p
    return found


def interleave_last(prefix: Path, count: int, out) -> int:
    """Print last N interleaved galph & ralph logs under logs/<prefix>/*.

    Output uses XML-like tags per log with CDATA wrapping.
    Returns 0 on success, non-zero otherwise.
    """
    galph_dir = Path("logs") / prefix / "galph"
    ralph_dir = Path("logs") / prefix / "ralph"

    galph_logs = find_logs(galph_dir)
    ralph_logs = find_logs(ralph_dir)

    if not galph_logs and not ralph_logs:
        print(f"No logs found under {galph_dir} or {ralph_dir}", file=sys.stderr)
        return 2

    # Build union of iterations and take last N by numeric iteration
    all_iters = sorted(set(galph_logs.keys()) | set(ralph_logs.keys()))
    if not all_iters:
        print(f"No iter-*.log files found under {prefix}", file=sys.stderr)
        return 3
    tail_iters = all_iters[-count:]

    # Emit a header for clarity
    out.write(f"<logs prefix=\"{prefix}\" count=\"{count}\">\n")

    for it in tail_iters:
        # Supervisor first, then Loop for each iteration
        if it in galph_logs:
            p = galph_logs[it]
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                content = f"<error reading {p}: {e}>\n"
            out.write(f"  <log role=\"galph\" iter=\"{it}\" path=\"{p}\">\n")
            out.write("    <![CDATA[\n")
            out.write(content)
            if not content.endswith("\n"):
                out.write("\n")
            out.write("    ]]>\n")
            out.write("  </log>\n")

        if it in ralph_logs:
            p = ralph_logs[it]
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                content = f"<error reading {p}: {e}>\n"
            out.write(f"  <log role=\"ralph\" iter=\"{it}\" path=\"{p}\">\n")
            out.write("    <![CDATA[\n")
            out.write(content)
            if not content.endswith("\n"):
                out.write("\n")
            out.write("    ]]>\n")
            out.write("  </log>\n")

    out.write("</logs>\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Interleave the last N galph/ralph logs with matching iteration numbers.")
    ap.add_argument("prefix", type=str, help="Branch prefix under logs/ (e.g., 'feature-spec-based-2')")
    ap.add_argument("-n", "--count", type=int, default=5, help="How many iterations to include (default: 5)")
    args = ap.parse_args()

    prefix = Path(args.prefix)
    if prefix.parts and (prefix.parts[0] == "logs"):
        # Accept both 'feature-...' and 'logs/feature-...'
        prefix = Path(*prefix.parts[1:])

    return interleave_last(prefix, args.count, sys.stdout)


if __name__ == "__main__":
    raise SystemExit(main())

