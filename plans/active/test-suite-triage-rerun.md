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
| B1 | Prepare phase folder | [D] | `mkdir -p reports/2026-01-test-suite-refresh/phase_b/$STAMP` (reuse STAMP from Phase A for continuity or create new if run delayed). Copy Phase A `env.txt` for reference. |
| B2 | Execute guarded full suite | [D] | `timeout 3600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=200 --timeout=905" pytest -vv tests/ | tee pytest.log`; store exit code in `run_exit_code.txt`. Capture wall-clock via `/usr/bin/time -v` if available (`/usr/bin/time -v pytest ...`). |
| B3 | Persist junit/timing artifacts | [D] | If pytest `--junitxml` is feasible, append `--junitxml=pytest.junit.xml`. Save `pytest.junit.xml`, `time.txt`, and `commands.txt` in phase folder. |
| B4 | Draft execution summary | [D] | `summary.md` capturing pass/fail/skip counts, runtime, notable slow tests. Note any infra failures (timeouts, flakiness). |

### Phase C — Failure Clustering & Ledger Update
Goal: Classify failing tests into clusters, cross-reference prior IDs, and log attempts in fix_plan.
Prereqs: Phase B completed with failure data; access to prior cluster taxonomy from `reports/2026-01-test-suite-triage/`.
Exit Criteria: Updated failure cluster doc under phase folder; docs/fix_plan.md attempt logged with counts and next steps.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Extract failure list | [D] | Use `python scripts/validation/pytest_failure_parser.py pytest.log > failures.json` (author script if missing) or manual grep. Record nodeids, error summaries. |
| C2 | Map to clusters | [D] | Compare with archived `remediation_tracker.md`; reuse existing cluster IDs when behavior matches. Record new clusters with `CLUSTER-NEW-XX` placeholder until triaged. |
| C3 | Produce triage summary | [D] | `summary.md` detailing clusters, counts, suspected root cause categories (implementation bug vs deprecated test). Include table `Cluster | Tests | Classification | Notes`. |
| C4 | Update fix_plan + attempts | [D] | Append Attempt entry to `[TEST-SUITE-TRIAGE-002]` with counts, artifact path, env info. Ensure Active Focus/Next Actions reflect remediation queue. |

### Phase D — Remediation Scheduling & Delegation Prep
Goal: Translate cluster insights into actionable next steps for implementation loops (Ralph) with explicit test selectors and target components.
Prereqs: Phase C classification complete; contact with downstream plan owners (vectorization, gradient flow, etc.).
Exit Criteria: Next Actions list in fix_plan updated; optional per-cluster mini-briefs stored under `reports/.../phase_d/`.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Draft remediation briefs | [D] | For each active cluster, create `reports/2026-01-test-suite-refresh/phase_d/$STAMP/cluster_<id>.md` summarizing reproduction command, suspected cause, linked findings, and suggested owner plan. Reference `phase_c/$STAMP/triage_summary.md` for baseline context and cite authoritative commands from `docs/development/testing_strategy.md`. |
| D2 | Update docs/fix_plan Next Actions | [D] | Add bullet list mapping clusters → follow-up tasks (e.g., assign to `[VECTOR-TRICUBIC-002]`, `[STATIC-PYREFLY-001]`). |
| D3 | Refresh input.md guidance | [D] | Provide supervisor handoff instructions focusing on highest-priority cluster fix, referencing plan + pytest selectors. |
| D4 | Completion gate | [ ] | Phase D exit when all clusters have documented next steps, fix_plan synced, and artifacts committed. Log state in galph_memory with `<Action State>: [ready_for_implementation]` once delegation instructions prepared. |

#### Phase D Cluster Brief Checklist
Goal: Capture per-cluster remediation briefs sized for direct delegation.
Prereqs: `triage_summary.md` complete; reproduction commands verified against authoritative docs/tests references.
Exit Criteria: Each row below links to a committed brief under `reports/2026-01-test-suite-refresh/phase_d/$STAMP/` with reproduction command, suspected cause, downstream plan owner, and immediate next steps.

| Cluster ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| CLUSTER-CREF-001 | Document C reference harness failure and NB_C_BIN requirements | [D] | Brief recorded in `phase_d/20251015T113531Z/cluster_CLUSTER-CREF-001.md`; captures resolved env-var precedence fix (Attempt #4) and references `[TEST-GOLDEN-001]` for ongoing binary upkeep. |
| CLUSTER-PERF-001 | Record perf regression evidence + profiling plan | [ ] | Include bandwidth numbers from `phase_b/$STAMP/pytest.log`, mark dependency on `[PERF-PYTORCH-004]`, and define profiler command (`pytest -k ATPERF003` with `/usr/bin/time -v`). |
| CLUSTER-TOOLS-001 | Capture nb-compare path resolution failure | [ ] | Reproduce CLI invocation, tie to `[TOOLING-DUAL-RUNNER-001]`, and list expected script path contract from `scripts/validation/README.md`. |
| CLUSTER-CLI-001 | Outline missing CLI golden assets + pix0 findings | [ ] | Note absent `pix0_expected.json`/`scaled.hkl`, cross-reference findings `API-001/002`, and specify regeneration commands from `docs/development/testing_strategy.md §2.3`. |
| CLUSTER-GRAD-001 | Summarize gradient timeout + data capture plan | [ ] | Quote 905 s timeout from Phase B run, highlight `[PERF-PYTORCH-004]` linkage, and propose targeted `pytest -vv tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability` rerun with extended timeout + profiler. |
| CLUSTER-VEC-001 | Detail tricubic vectorization regression | [ ] | Record dtype mismatch symptoms, connect to `[VECTOR-TRICUBIC-002]` + findings `CONVENTION-004..006`, and provide reproduction command covering both failing nodeids. |

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
