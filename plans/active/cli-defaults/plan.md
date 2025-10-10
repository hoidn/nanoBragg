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

### Phase A — Baseline Reconciliation (CLI vs direct API)
Goal: Prove the divergence between the CLI runner and direct API invocation using identical configs, locking reproducibility before deeper tracing.
Prereqs: Editable install (`pip install -e .`), `debug_default_f.py` confirmed working, clean workspace for artifact capture.
Exit Criteria: Artifact bundle showing CLI zero-output vs direct API non-zero output with matched configs + environment snapshot.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Capture CLI reproduction baseline | [ ] | Run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F` and store full log + floatfile stats under `phase_a/<STAMP>/cli_pytest/`. Note pytest exit code, runtime, and command copy in `commands.txt`. |
| A2 | Record CLI configuration dump | [ ] | Re-run the CLI command with `-show_config` (same args) and redirect output to `phase_a/<STAMP>/cli_pytest/config_dump.txt`. Confirm `default_F`, fluence, sources, device/dtype. |
| A3 | Capture direct API control output | [ ] | Execute `KMP_DUPLICATE_LIB_OK=TRUE python debug_default_f.py` and archive stdout + intensity tensor statistics under `phase_a/<STAMP>/api_control/`. Ensure script uses identical device/dtype as CLI. |
| A4 | Produce reconciliation summary | [ ] | Write `phase_a/<STAMP>/summary.md` comparing CLI vs API stats (min/max/non-zero counts), highlight any config discrepancies, and embed references to raw artifacts. |

### Phase B — Callchain & State Capture
Goal: Identify the first point where CLI execution diverges from the working direct invocation by tracing simulator internals per SOP.
Prereqs: Phase A complete; confirm both runs done on same commit and device/dtype.
Exit Criteria: Callchain artefacts for both CLI and API runs pinpointing the divergent variable (e.g., reflection counts, Ewald filter output, intensity accumulator).

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Define analysis question & scope | [ ] | Draft `phase_b/<STAMP>/analysis.md` stating why CLI zeroes while direct API produces intensity; set initiative_id `cli-defaults-b1`, scope hints `['Simulator.run', 'Ewald filter', 'HKL occupancy']`. |
| B2 | Execute callchain tracing for CLI path | [ ] | Follow `prompts/callchain.md` using CLI entry (`python -m nanobrag_torch ...`). Generate `reports/2026-01-test-suite-triage/phase_d/<STAMP>/cli-defaults/phase_b/callchain/static.md` etc. Capture ROI/pixel focus (use pixel with expected intensity e.g., centre (16,16)). |
| B3 | Mirror callchain for direct API path | [ ] | Repeat Callchain SOP on `debug_default_f.py` (or equivalent harness). Ensure identical tap names for cross-comparison. Store under `phase_b/<STAMP>/api_callchain/`. |
| B4 | Summarise divergence | [ ] | Synthesize `phase_b/<STAMP>/summary.md` outlining first mismatching variable, cite file:line anchors from traces, and recommend instrumentation focus for Phase C. |

### Phase C — Remediation Blueprint & Regression Guard
Goal: Using Phase B findings, outline the fix strategy (without coding) and specify regression coverage to close AT-CLI-002 reliably.
Prereqs: Divergence located (Phase B summary complete), relevant codepaths understood (`Simulator.run`, CLI config plumbing).
Exit Criteria: Documented remediation plan with acceptance tests + validation steps queued for implementation.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Draft fix hypothesis & owner tasks | [ ] | Author `phase_c/<STAMP>/remediation_plan.md` enumerating suspected root cause, required code touchpoints (with file:line refs), and implementation sequencing for Ralph/subagents. Include device/dtype + vectorization guardrails. |
| C2 | Map regression coverage | [ ] | Update `phase_c/<STAMP>/tests.md` listing targeted pytest selectors (AT-CLI-002 plus any new regression tests) and additional sanity checks (e.g., nb-compare vs debug script). |
| C3 | Update fix_plan & input hooks | [ ] | Record Phase C outputs in `docs/fix_plan.md` ([CLI-DEFAULTS-001] section Attempts/Next Actions) and prepare supervisor `input.md` guidance for implementation attempt. |

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
