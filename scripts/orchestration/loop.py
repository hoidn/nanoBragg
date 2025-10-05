from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from subprocess import Popen, PIPE

from .state import OrchestrationState
from .git_bus import safe_pull, add, commit, push_to, short_head, has_unpushed_commits, assert_on_branch, current_branch


def _log_file(prefix: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("tmp").mkdir(parents=True, exist_ok=True)
    p = Path("tmp") / f"{prefix}{ts}.txt"
    latest = Path("tmp") / f"{prefix}latest.txt"
    try:
        if latest.exists() or latest.is_symlink():
            latest.unlink()
        latest.symlink_to(p.name)
    except Exception:
        pass
    return p


def tee_run(cmd: list[str], stdin_file: Path, log_path: Path) -> int:
    with open(stdin_file, "rb") as fin, open(log_path, "a", encoding="utf-8") as flog:
        flog.write(f"$ {' '.join(cmd)}\n")
        flog.flush()
        proc = Popen(cmd, stdin=fin, stdout=PIPE, stderr=PIPE, text=True, bufsize=1)
        while True:
            line = proc.stdout.readline() if proc.stdout else ""
            if not line:
                break
            sys.stdout.write(line)
            flog.write(line)
        err = proc.stderr.read() if proc.stderr else ""
        if err:
            sys.stderr.write(err)
            flog.write(err)
        return proc.wait()


def main() -> int:
    ap = argparse.ArgumentParser(description="Engineer (ralph) orchestrator")
    ap.add_argument("--sync-via-git", action="store_true", help="Enable cross-machine synchronous mode via Git state")
    ap.add_argument("--sync-loops", type=int, default=int(os.getenv("SYNC_LOOPS", 20)))
    ap.add_argument("--poll-interval", type=int, default=int(os.getenv("POLL_INTERVAL", 5)))
    ap.add_argument("--max-wait-sec", type=int, default=int(os.getenv("MAX_WAIT_SEC", 0)))
    ap.add_argument("--state-file", type=Path, default=Path(os.getenv("STATE_FILE", "sync/state.json")))
    ap.add_argument("--claude-cmd", type=str, default=os.getenv("CLAUDE_CMD", "/home/ollie/.claude/local/claude"))
    ap.add_argument("--branch", type=str, default=os.getenv("ORCHESTRATION_BRANCH", ""))
    args, unknown = ap.parse_known_args()

    log_path = _log_file("claudelog")

    def logp(msg: str) -> None:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

    # Branch guard / resolution
    if args.branch:
        assert_on_branch(args.branch, lambda m: None)
        branch_target = args.branch
    else:
        branch_target = current_branch()

    # Always keep up to date
    safe_pull(logp)

    for _ in range(args.sync_loops):
        if args.sync_via_git:
            args.state_file.parent.mkdir(parents=True, exist_ok=True)
            logp("[SYNC] Waiting for expected_actor=ralph...")
            start = time.time()
            while True:
                safe_pull(logp)
                st = OrchestrationState.read(str(args.state_file))
                if st.expected_actor == "ralph":
                    break
                if args.max_wait_sec and (time.time() - start) > args.max_wait_sec:
                    logp("[SYNC] Timeout waiting for turn; exiting")
                    return 1
                time.sleep(args.poll_interval)

            # Mark running
            st.status = "running-ralph"
            st.write(str(args.state_file))
            add([str(args.state_file)])
            commit(f"[SYNC i={st.iteration}] actor=ralph status=running")
            push_to(branch_target, logp)

        # Execute one engineer loop
        rc = tee_run([args.claude_cmd, "-p", "--dangerously-skip-permissions", "--verbose", "--output-format", "stream-json"], Path("prompts/main.md"), log_path)

        # Complete handoff
        safe_pull(logp)
        sha = short_head()
        st = OrchestrationState.read(str(args.state_file))

        if args.sync_via_git:
            if rc == 0:
                st.stamp(expected_actor="galph", status="complete", increment=True, ralph_commit=sha)
                st.write(str(args.state_file))
                add([str(args.state_file)])
                commit(f"[SYNC i={st.iteration}] actor=ralph → next=galph status=ok ralph_commit={sha}")
                push_to(branch_target, logp)
            else:
                st.stamp(expected_actor="ralph", status="failed", increment=False, ralph_commit=sha)
                st.write(str(args.state_file))
                add([str(args.state_file)])
                commit(f"[SYNC i={st.iteration}] actor=ralph status=fail ralph_commit={sha}")
                push_to(branch_target, logp)
                logp(f"Loop failed rc={rc}; halting")
                return rc

        # Optional: push local commits from the loop (async hygiene)
        if rc == 0 and has_unpushed_commits():
            try:
                push_to(branch_target, logp)
            except Exception as e:
                logp(f"WARNING: git push failed: {e}")
                return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
