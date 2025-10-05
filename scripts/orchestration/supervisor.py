from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from subprocess import Popen, PIPE

from .state import OrchestrationState
from .git_bus import safe_pull, add, commit, push, short_head


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
        # Best effort on platforms without symlink support
        pass
    return p


def tee_run(cmd: list[str], stdin_file: Path, log_path: Path) -> int:
    with open(stdin_file, "rb") as fin, open(log_path, "a", encoding="utf-8") as flog:
        flog.write(f"$ {' '.join(cmd)}\n")
        flog.flush()
        proc = Popen(cmd, stdin=fin, stdout=PIPE, stderr=PIPE, text=True, bufsize=1)
        # Stream stdout
        while True:
            line = proc.stdout.readline() if proc.stdout else ""
            if not line:
                break
            sys.stdout.write(line)
            flog.write(line)
        # Stream remaining stderr
        err = proc.stderr.read() if proc.stderr else ""
        if err:
            sys.stderr.write(err)
            flog.write(err)
        return proc.wait()


def main() -> int:
    ap = argparse.ArgumentParser(description="Supervisor (galph) orchestrator")
    ap.add_argument("--sync-via-git", action="store_true", help="Enable cross-machine synchronous mode via Git state")
    ap.add_argument("--sync-loops", type=int, default=int(os.getenv("SYNC_LOOPS", 20)), help="Number of iterations to run")
    ap.add_argument("--poll-interval", type=int, default=int(os.getenv("POLL_INTERVAL", 5)))
    ap.add_argument("--max-wait-sec", type=int, default=int(os.getenv("MAX_WAIT_SEC", 0)))
    ap.add_argument("--state-file", type=Path, default=Path(os.getenv("STATE_FILE", "sync/state.json")))
    ap.add_argument("--codex-cmd", type=str, default=os.getenv("CODEX_CMD", "codex"))
    args, unknown = ap.parse_known_args()

    log_path = _log_file("supervisorlog")

    def logp(msg: str) -> None:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

    if not args.sync_via_git:
        # Legacy async mode: run N iterations back-to-back
        for _ in range(args.sync_loops):
            rc = tee_run([args.codex_cmd, "exec", "-m", "gpt-5-codex", "-c", "model_reasoning_effort=high", "--dangerously-bypass-approvals-and-sandbox"], Path("prompts/supervisor.md"), log_path)
            if rc != 0:
                return rc
        return 0

    # Sync via Git
    logp(f"Running supervisor in SYNC via git mode for {args.sync_loops} iteration(s)")
    args.state_file.parent.mkdir(parents=True, exist_ok=True)

    for _ in range(args.sync_loops):
        safe_pull(logp)

        # Initialize state if missing
        if not args.state_file.exists():
            st = OrchestrationState()
            st.expected_actor = "galph"
            st.status = "idle"
            st.write(str(args.state_file))
            add([str(args.state_file)])
            commit("[SYNC init] actor=galph status=idle")
            push(logp)

        # Wait for our turn
        logp("Waiting for expected_actor=galph...")
        start = time.time()
        while True:
            safe_pull(logp)
            st = OrchestrationState.read(str(args.state_file))
            if st.expected_actor == "galph":
                break
            if args.max_wait_sec and (time.time() - start) > args.max_wait_sec:
                logp("Timeout waiting for galph turn")
                return 1
            time.sleep(args.poll_interval)

        # Mark running
        st.status = "running-galph"
        st.write(str(args.state_file))
        add([str(args.state_file)])
        commit(f"[SYNC i={st.iteration}] actor=galph status=running")
        push(logp)

        # Execute one supervisor iteration
        rc = tee_run([args.codex_cmd, "exec", "-m", "gpt-5-codex", "-c", "model_reasoning_effort=high", "--dangerously-bypass-approvals-and-sandbox"], Path("prompts/supervisor.md"), log_path)

        safe_pull(logp)
        sha = short_head()

        st = OrchestrationState.read(str(args.state_file))
        if rc == 0:
            st.stamp(expected_actor="ralph", status="waiting-ralph", galph_commit=sha)
            st.write(str(args.state_file))
            add([str(args.state_file)])
            commit(f"[SYNC i={st.iteration}] actor=galph → next=ralph status=ok galph_commit={sha}")
            push(logp)
        else:
            st.stamp(expected_actor="galph", status="failed", galph_commit=sha)
            st.write(str(args.state_file))
            add([str(args.state_file)])
            commit(f"[SYNC i={st.iteration}] actor=galph status=fail galph_commit={sha}")
            push(logp)
            logp(f"Supervisor iteration failed rc={rc}. Halting.")
            return rc

        # Wait for Ralph to finish and increment iteration
        logp(f"Waiting for Ralph to complete i={st.iteration}...")
        current_iter = st.iteration
        while True:
            safe_pull(logp)
            st2 = OrchestrationState.read(str(args.state_file))
            if st2.expected_actor == "galph" and st2.iteration > current_iter:
                logp(f"Ralph completed iteration {current_iter}; proceeding to {st2.iteration}")
                break
            time.sleep(args.poll_interval)

    logp("Supervisor SYNC loop finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

