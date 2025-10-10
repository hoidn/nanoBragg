## Context
- Initiative: CLI-DEFAULTS-001 — restore minimal `-default_F` CLI render so Acceptance Test AT-CLI-002 passes and `[TEST-SUITE-TRIAGE-001]` Phase D remediation can advance.
- Phase Goal: Build a phased investigation + remediation playbook covering evidence capture, callchain tracing, and fix validation for the CLI default_F regression.
- Dependencies:
  - `specs/spec-a-cli.md` §AT-CLI-002 — normative behaviour for default_F-only renders and header outputs.
  - `specs/spec-a-core.md` §§3–4 — structure-factor fallback, fluence defaults, and sampling pipeline.
  - `docs/development/c_to_pytorch_config_map.md` — authoritative CLI↔config parity.
  - `docs/development/testing_strategy.md` §1.5 — test command sourcing and artifact policy.
  - `docs/debugging/debugging.md` — parallel trace SOP for simulator instrumentation.
  - `reports/2026-01-test-suite-triage/phase_d/20251010T153138Z/` and `20251010T154759Z/` — prior reproduction + investigation notes for this failure.
  - `debug_default_f.py` — control-path reproduction that currently succeeds.
- Artifact Policy: New work MUST live under `reports/2026-01-test-suite-triage/phase_d/<STAMP>/cli-defaults/` with subfolders per phase (`phase_a`, `phase_b`, …). Each attempt captures `commands.txt`, `env.json`, raw logs, `summary.md`, and any diff artefacts.

### Status Snapshot (2025-10-10)
- Phase A: complete (Attempt #3 — artifacts in `reports/2026-01-test-suite-triage/phase_d/20251010T155808Z/cli-defaults/phase_a/`)
- Phase B: complete (Attempt #4 — artifacts in `reports/2026-01-test-suite-triage/phase_d/20251010T160902Z/cli-defaults/phase_b/`)
- Phase C: complete (Attempt #5 — artifacts in `reports/2026-01-test-suite-triage/phase_d/20251010T161925Z/cli-defaults/phase_c/`)

### Phase A — Baseline Reconciliation (CLI vs direct API)
Goal: Prove the divergence between the CLI runner and direct API invocation using identical configs, locking reproducibility before deeper tracing.
Prereqs: Editable install (`pip install -e .`), `debug_default_f.py` confirmed working, clean workspace for artifact capture.
Exit Criteria: Artifact bundle showing CLI zero-output vs direct API non-zero output with matched configs + environment snapshot.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Capture CLI reproduction baseline | [D] | Attempt #3 → logs under `reports/2026-01-test-suite-triage/phase_d/20251010T155808Z/cli-defaults/phase_a/cli_pytest/` (`pytest.log`, `commands.txt`). |
| A2 | Record CLI configuration dump | [D] | Attempt #3 → `reports/2026-01-test-suite-triage/phase_d/20251010T155808Z/cli-defaults/phase_a/cli_pytest/config_dump.txt` and `float_stats.txt` capture config parity. |
| A3 | Capture direct API control output | [D] | Attempt #3 → `reports/2026-01-test-suite-triage/phase_d/20251010T155808Z/cli-defaults/phase_a/api_control/run.log` records non-zero output with matching device/dtype. |
| A4 | Produce reconciliation summary | [D] | Attempt #3 → `reports/2026-01-test-suite-triage/phase_d/20251010T155808Z/cli-defaults/phase_a/summary.md` documents CLI vs API parity and hypothesis ranking. |

### Phase B — Callchain & State Capture
Goal: Identify the first point where CLI execution diverges from the working direct invocation by tracing simulator internals per SOP.
Prereqs: Phase A complete; confirm both runs done on same commit and device/dtype.
Exit Criteria: Callchain artefacts for both CLI and API runs pinpointing the divergent variable (e.g., reflection counts, Ewald filter output, intensity accumulator).

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Define analysis question & scope | [D] | Attempt #4 → `reports/2026-01-test-suite-triage/phase_d/20251010T160902Z/cli-defaults/phase_b/analysis.md` defines question: "Why does CLI default_F emit zeros while API yields intensities?" Initiative: cli-defaults-b1, scope: CLI orchestration, HKL assignment, structure factor fallback. |
| B2 | Execute callchain tracing for CLI path | [D] | Attempt #4 → Static analysis via subagent produced `callchain/static.md` documenting CLI entry→config→simulator→sink with file:line anchors. Root cause identified at `__main__.py:1090`. |
| B3 | Mirror callchain for direct API path | [D] | Attempt #4 → `api_callchain/static.md` documents API control path showing clean default_F flow with no HKL assignment interference. |
| B4 | Summarise divergence | [D] | Attempt #4 → `summary.md` identifies first divergent tap (Tap 4: HKL assignment check), proposes fix for `__main__.py:1090` conditional, recommends Phase C implementation. |

### Phase C — Remediation Blueprint & Regression Guard
Goal: Using Phase B findings, outline the fix strategy (without coding) and specify regression coverage to close AT-CLI-002 reliably.
Prereqs: Divergence located (Phase B summary complete), relevant codepaths understood (`Simulator.run`, CLI config plumbing).
Exit Criteria: Documented remediation plan with acceptance tests + validation steps queued for implementation.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Draft fix hypothesis & owner tasks | [D] | Attempt #5 → `reports/2026-01-test-suite-triage/phase_d/20251010T161925Z/cli-defaults/phase_c/remediation_plan.md` enumerates root cause, code touchpoints, and sequencing with device/dtype guardrails. |
| C2 | Map regression coverage | [D] | Attempt #5 → `reports/2026-01-test-suite-triage/phase_d/20251010T161925Z/cli-defaults/phase_c/tests.md` lists selectors, auxiliary tools, and artifact expectations. |
| C3 | Update fix_plan & input hooks | [D] | Attempt #5 → `docs/fix_plan.md` header/Next Actions refreshed and `input.md` rewritten (2025-10-10T16:19:25Z) to launch implementation Attempt #6. |

### Phase D — Validation Gate (post-fix, pending implementation)
Goal: Define validation protocols to run once the fix is coded (kept in plan for continuity, executed later).
Prereqs: Fix implemented by Ralph/subagent per Phase C instructions.
Exit Criteria: Documented checklist describing final validation commands, parity comparisons, and documentation updates.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Validation command suite | [ ] | Pre-author `phase_d/checklist.md` enumerating `pytest -v tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F`, floatfile value assertions, and optional nb-compare ROI command to confirm non-zero image. |
| D2 | Documentation touchpoints | [ ] | Note spec/arch/doc updates required after fix (e.g., README_PYTORCH minimal example). Keep placeholders until implementation completes. |

### Exit Criteria (Overall Plan)
- Phases A–C completed with `[D]` status, artifacts stored under timestamped subdirectories, and findings synced to `docs/fix_plan.md` and `galph_memory.md`.
- Phase D retains templated validation steps ready for activation post-implementation.
- `[CLI-DEFAULTS-001]` Next Actions in `docs/fix_plan.md` reference this plan file and the latest completed phase.

### References
- `tests/test_at_cli_002.py`
- `src/nanobrag_torch/__main__.py` (CLI orchestration)
- `src/nanobrag_torch/simulator.py` (core physics loop)
- `debug_default_f.py`
- `prompts/callchain.md`
