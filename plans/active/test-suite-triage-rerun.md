## Context
- Initiative: TEST-SUITE-TRIAGE-002 — Relaunch full `pytest tests/` execution, capture current failures, and unblock remediation sequencing per supervisor directive.
- Phase Goal: Produce a fresh, comprehensive health snapshot for the PyTorch test suite (collection → execution → cluster triage) with artifacts suitable for rapid handoff to implementation loops.
- Dependencies:
  - `docs/development/testing_strategy.md` §§1–2 for authoritative commands, environment guards, and chunking expectations.
  - `arch.md` §§2, 15 for device/dtype and differentiability guardrails that must be preserved during runs.
  - `docs/development/pytorch_runtime_checklist.md` for preflight sanity requirements (KMP env, compile guards).
  - `plans/archive/test-suite-triage.md` (Phase R summary) for prior baselines and tolerance decisions.
  - `docs/fix_plan.md` (Attempt history + cluster IDs) to ensure triage labels remain consistent.

### Artifact Root & Naming
- Use `reports/2026-01-test-suite-refresh/` as the new root to avoid clobbering archived Phase R bundles.
- Stamp format: `YYYYMMDDTHHMMSSZ` (UTC) created via `date -u +%Y%m%dT%H%M%SZ`.
- Each phase stores commands, logs, env dumps, and summaries inside `phase_<letter>/<STAMP>/`.

### Phase A — Preflight & Environment Guard
Goal: Validate environment, record guardrails, and capture a collection-only dry run before executing the suite.
Prereqs: Editable install (`pip install -e .`), NB_C_BIN exported when required, CUDA availability noted.
Exit Criteria: Collection succeeds (no ImportErrors); guard env recorded; artifact bundle persisted.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Create STAMP + artifact skeleton | [D] | `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `mkdir -p reports/2026-01-test-suite-refresh/phase_a/$STAMP`. Record `STAMP` in attempts log. |
| A2 | Capture environment guard | [D] | Write `env.txt` documenting `CUDA_VISIBLE_DEVICES`, `NANOBRAGG_DISABLE_COMPILE`, `KMP_DUPLICATE_LIB_OK`. Use `printenv` redirected to `env.txt`; include Python/torch versions via `python -m torch.utils.collect_env`. |
| A3 | Run collection-only smoke | [D] | `KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest --collect-only -q tests > pytest-collect.log 2>&1`; store log + `commands.txt`. Success threshold: exit 0, 692 tests collected (note any drift). |
| A4 | Summarize preflight outcome | [D] | Draft `summary.md` with collection counts, notable skips, and environment guard confirmation. |

Phase A status: Completed via Attempt #1 (STAMP 20251015T113531Z; 700 tests collected, env guard captured).

### Phase B — Full Suite Execution & Capture
Goal: Execute `pytest tests/` once under guarded environment, recording timing and failure set.
Prereqs: Phase A artifacts complete; verify disk space; ensure timeout guard ready (default 905 s for slow gradient case per Phase R tolerance).
Exit Criteria: Full suite run captured with `pytest.log`, junit XML (if available), and timing metrics.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Prepare phase folder | [ ] | `mkdir -p reports/2026-01-test-suite-refresh/phase_b/$STAMP` (reuse STAMP from Phase A for continuity or create new if run delayed). Copy Phase A `env.txt` for reference. |
| B2 | Execute guarded full suite | [ ] | `timeout 3600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=200 --timeout=905" pytest -vv tests/ | tee pytest.log`; store exit code in `run_exit_code.txt`. Capture wall-clock via `/usr/bin/time -v` if available (`/usr/bin/time -v pytest ...`). |
| B3 | Persist junit/timing artifacts | [ ] | If pytest `--junitxml` is feasible, append `--junitxml=pytest.junit.xml`. Save `pytest.junit.xml`, `time.txt`, and `commands.txt` in phase folder. |
| B4 | Draft execution summary | [ ] | `summary.md` capturing pass/fail/skip counts, runtime, notable slow tests. Note any infra failures (timeouts, flakiness). |

### Phase C — Failure Clustering & Ledger Update
Goal: Classify failing tests into clusters, cross-reference prior IDs, and log attempts in fix_plan.
Prereqs: Phase B completed with failure data; access to prior cluster taxonomy from `reports/2026-01-test-suite-triage/`.
Exit Criteria: Updated failure cluster doc under phase folder; docs/fix_plan.md attempt logged with counts and next steps.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Extract failure list | [ ] | Use `python scripts/validation/pytest_failure_parser.py pytest.log > failures.json` (author script if missing) or manual grep. Record nodeids, error summaries. |
| C2 | Map to clusters | [ ] | Compare with archived `remediation_tracker.md`; reuse existing cluster IDs when behavior matches. Record new clusters with `CLUSTER-NEW-XX` placeholder until triaged. |
| C3 | Produce triage summary | [ ] | `summary.md` detailing clusters, counts, suspected root cause categories (implementation bug vs deprecated test). Include table `Cluster | Tests | Classification | Notes`. |
| C4 | Update fix_plan + attempts | [ ] | Append Attempt entry to `[TEST-SUITE-TRIAGE-002]` with counts, artifact path, env info. Ensure Active Focus/Next Actions reflect remediation queue. |

### Phase D — Remediation Scheduling & Delegation Prep
Goal: Translate cluster insights into actionable next steps for implementation loops (Ralph) with explicit test selectors and target components.
Prereqs: Phase C classification complete; contact with downstream plan owners (vectorization, gradient flow, etc.).
Exit Criteria: Next Actions list in fix_plan updated; optional per-cluster mini-briefs stored under `reports/.../phase_d/`.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Draft remediation briefs | [ ] | For each active cluster, create `reports/2026-01-test-suite-refresh/phase_d/$STAMP/cluster_<id>.md` summarizing reproduction command, suspected cause, and suggested owner plan. |
| D2 | Update docs/fix_plan Next Actions | [ ] | Add bullet list mapping clusters → follow-up tasks (e.g., assign to `[VECTOR-TRICUBIC-002]`, `[STATIC-PYREFLY-001]`). |
| D3 | Refresh input.md guidance | [ ] | Provide supervisor handoff instructions focusing on highest-priority cluster fix, referencing plan + pytest selectors. |
| D4 | Completion gate | [ ] | Phase D exit when all clusters have documented next steps, fix_plan synced, and artifacts committed. Log state in galph_memory with `<Action State>: [ready_for_implementation]` once delegation instructions prepared. |

### Verification & Guardrails
- Respect Protected Assets list in `docs/index.md`; never delete `loop.sh`, `input.md`, etc.
- Device neutrality: keep CPU (`CUDA_VISIBLE_DEVICES=-1`) by default; flag if GPU reruns required.
- Timeout policy: start with 905 s max per Phase R tolerance; adjust only with supervisor approval.
- Documentation alignment: Any change in test counts or tolerance decisions must be reflected in `docs/development/testing_strategy.md` §2 once implemented (defer updates until after remediation).

### Exit Criteria Summary
- Phase A artifacts (collection, env guard) present under phase_a.
- Phase B full-suite artifacts captured with reproducible commands.
- Phase C triage summary + fix_plan attempt logged with cluster table.
- Phase D remediation briefs + updated Next Actions ready for delegation.
- galph_memory entry records Action State progression with timestamps for supervisory continuity.
