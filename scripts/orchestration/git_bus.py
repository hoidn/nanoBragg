from __future__ import annotations

import subprocess
import os
from typing import Iterable, Optional


def _run(cmd: Iterable[str], timeout: Optional[int] = None, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(list(cmd), timeout=timeout, check=check, capture_output=True, text=True)


def _rebase_in_progress() -> bool:
    return os.path.isdir(os.path.join('.git', 'rebase-merge')) or os.path.isdir(os.path.join('.git', 'rebase-apply'))


def _abort_rebase(log_print) -> None:
    try:
        _run(["git", "rebase", "--abort"])
        log_print("Aborted in-progress rebase.")
    except Exception:
        pass


def safe_pull(log_print) -> None:
    if _rebase_in_progress():
        _abort_rebase(log_print)
    try:
        cp = _run(["git", "pull", "--rebase"], timeout=30)
        if cp.stdout:
            log_print(cp.stdout.rstrip())
        if cp.stderr:
            log_print(cp.stderr.rstrip())
        return
    except Exception as e:
        log_print(f"git pull --rebase failed or timed out: {e}")

    # Recovery path
    _abort_rebase(log_print)
    cp2 = _run(["git", "pull", "--no-rebase"])
    if cp2.stdout:
        log_print(cp2.stdout.rstrip())
    if cp2.stderr:
        log_print(cp2.stderr.rstrip())


def add(paths: Iterable[str]) -> None:
    _run(["git", "add", *paths])


def commit(message: str) -> bool:
    cp = _run(["git", "commit", "-m", message])
    return cp.returncode == 0


def push(log_print) -> None:
    cp = _run(["git", "push"])
    if cp.stdout:
        log_print(cp.stdout.rstrip())
    if cp.stderr:
        log_print(cp.stderr.rstrip())


def push_to(branch: str, log_print, remote: str = "origin") -> None:
    cp = _run(["git", "push", remote, f"HEAD:{branch}"])
    if cp.stdout:
        log_print(cp.stdout.rstrip())
    if cp.stderr:
        log_print(cp.stderr.rstrip())


def short_head() -> str:
    cp = _run(["git", "rev-parse", "--short", "HEAD"]) 
    return (cp.stdout or "").strip() or "unknown"


def current_branch() -> str:
    cp = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"]) 
    return (cp.stdout or "").strip()


def assert_on_branch(expected: str, log_print) -> None:
    cur = current_branch()
    if cur != expected:
        log_print(f"ERROR: Expected to run on branch '{expected}', but on '{cur}'. Aborting.")
        raise SystemExit(2)


def has_unpushed_commits() -> bool:
    branch = current_branch()
    if not branch:
        return False
    cp = _run(["git", "diff", "--quiet", f"origin/{branch}..HEAD"])  # exit code 1 if diff present
    return cp.returncode == 1
