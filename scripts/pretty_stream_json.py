#!/usr/bin/env python3
import sys
import json
import os
import re
from typing import Any, Dict, Iterable

RESET = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"


def clamp(s: str, max_chars: int = 1200) -> str:
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 1] + "…"


def lines(s: str, max_lines: int = 40) -> str:
    splitted = s.splitlines()
    if len(splitted) <= max_lines:
        return s
    head = "\n".join(splitted[:max_lines])
    return f"{head}\n{DIM}… {len(splitted) - max_lines} more lines hidden …{RESET}"


def fmt_tool_input(name: str, inp: Any) -> str:
    try:
        if not isinstance(inp, dict):
            return clamp(str(inp))
        # Common shapes
        if name.lower() in {"bash", "bashoutput"}:
            cmd = inp.get("command") or inp.get("cmd")
            if cmd:
                return "$ " + (" ".join(cmd) if isinstance(cmd, list) else str(cmd))
        if name.lower() in {"edit", "multiedit", "write", "notebookedit"}:
            path = inp.get("file_path") or inp.get("path")
            desc = inp.get("description")
            return " ".join(x for x in [str(path) if path else None, f"— {desc}" if desc else None] if x)
        if name.lower() in {"task"}:
            return clamp(str(inp.get("description") or ""), 400)
        # Fallback: compact JSON
        return clamp(json.dumps(inp, ensure_ascii=False))
    except Exception:
        return clamp(str(inp))


def render(obj: Dict[str, Any]) -> str:
    t = obj.get("type")
    if t == "system":
        st = obj.get("subtype")
        if st == "init":
            cwd = obj.get("cwd", "")
            model = obj.get("model", "")
            tools = obj.get("tools", [])
            return f"{DIM}{MAGENTA}⟲ session init{RESET} {DIM}cwd={cwd} model={model} tools={len(tools)}{RESET}"
        return f"{DIM}{MAGENTA}system · {st or 'event'}{RESET}"

    if t == "assistant":
        msg = obj.get("message") or {}
        content = msg.get("content") or []
        parts = []
        model = msg.get("model") or "assistant"
        for c in content:
            ctype = c.get("type")
            if ctype == "text":
                txt = c.get("text") or ""
                parts.append(f"{GREEN}assistant[{model}]:{RESET} {lines(txt)}")
            elif ctype == "tool_use":
                name = c.get("name") or "tool"
                inp = c.get("input")
                summary = fmt_tool_input(name, inp)
                parts.append(f"{CYAN}→ tool:{name}{RESET} {summary}")
        if not parts:
            return f"{GREEN}assistant[{model}]{RESET}"
        return "\n".join(parts)

    if t == "user":
        msg = obj.get("message") or {}
        content = msg.get("content") or []
        parts = []
        for c in content:
            ctype = c.get("type")
            if ctype == "tool_result":
                inner = c.get("content")
                # tool outputs are often long; trim
                if isinstance(inner, str):
                    shown = lines(clamp(inner, 4000), 40)
                else:
                    shown = clamp(json.dumps(inner, ensure_ascii=False), 1200)
                parts.append(f"{YELLOW}⇐ tool_result{RESET}\n{shown}")
            elif ctype == "text":
                parts.append(f"{YELLOW}user:{RESET} {lines(clamp(str(c.get('text') or ''), 1200))}")
        return "\n".join(parts) if parts else f"{YELLOW}user event{RESET}"

    # Unknown types fall back to compact JSON
    return f"{DIM}{json.dumps(obj, ensure_ascii=False)}{RESET}"


def iter_lines(stream: Iterable[str]) -> Iterable[str]:
    for raw in stream:
        # Some tools emit ANSI control codes even in JSON streams, strip them
        clean = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", raw).strip()
        if not clean:
            continue
        yield clean


def main() -> int:
    # Read JSON-lines from stdin and pretty print
    for ln in iter_lines(sys.stdin):
        try:
            obj = json.loads(ln)
        except Exception:
            # Not JSON; show as faint raw
            sys.stdout.write(f"{DIM}{ln}{RESET}\n")
            sys.stdout.flush()
            continue
        try:
            out = render(obj)
        except Exception as e:
            out = f"{RED}[pretty] render error:{RESET} {e}"
        sys.stdout.write(out + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

