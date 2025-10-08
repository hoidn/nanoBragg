## Context
- Initiative: CLI-FLAGS-003 (`-nonoise` / `-pix0_vector_mm`) — φ=0 parity shim design (Phase L3k.3c.4–L3k.3c.5 in `plans/active/cli-noise-pix0/plan.md`).
- Phase Goal: Design and supervise implementation of an **opt-in** φ=0 carryover shim that reproduces the documented C bug (C-PARITY-001) without regressing the new spec-compliant default path. Deliver validated traces, tests, and documentation so the supervisor command can run PyTorch vs C parity with matching φ behavior.
- Dependencies:
  - `specs/spec-a-core.md:204-240` — Normative φ rotation pipeline.
  - `docs/bugs/verified_c_bugs.md:166-204` — C-PARITY-001 description and reproduction command.
  - `reports/2025-10-cli-flags/phase_l/rot_vector/` — Existing φ trace artifacts (VG-1 baseline evidence).
  - `tests/test_cli_scaling_phi0.py` — Spec compliance tests that must remain green.
  - `src/nanobrag_torch/models/crystal.py:1070-1130` — Current spec-compliant rotation implementation.
  - `scripts/compare_per_phi_traces.py` and `reports/2025-10-cli-flags/phase_l/` harness notes — Required for parity validation.
- Current Status (2025-10-08 refresh): Spec baseline locked and the opt-in parity shim landed (Attempts #120/#121). Enhanced traces from `reports/2025-10-cli-flags/phase_l/parity_shim/20251008T023140Z/` show a c-parity Δk plateau ≈2.845e-05 attributed to floating-point roundoff; we still need a dtype-sensitivity probe and an explicit tolerance/remediation decision before Phase C5.
- Artifact Directory: Use `reports/2025-10-cli-flags/phase_l/parity_shim/<YYYYMMDDTHHMMSSZ>/` for new evidence (traces, logs, design notes, checksums).
- Guardrails: Preserve vectorization (no per-step Python loops), maintain device/dtype neutrality, obey Protected Assets (do not move files listed in `docs/index.md`).

### Phase A — Spec Baseline Confirmation (Prerequisite)
Goal: Freeze references confirming spec-compliant behavior so parity shim development cannot regress the default path.
Prereqs: None (evidence already captured; this phase records provenance and identifies gaps).
Exit Criteria: Artifact pointers recorded here and in fix_plan; VG-1 tolerances documented for quick re-validation.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Catalogue existing spec evidence | [D] | ✅ `reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251007T231515Z/` contains `pytest_phi0.log`, `comparison_summary.md`, and `sha256.txt`. Reference these in future memos/tests. |
| A2 | Note authoritative tests & selectors | [D] | ✅ `tests/test_cli_scaling_phi0.py::{TestPhiZeroParity::test_rot_b_matches_c,test_k_frac_matches_spec}` locked to spec constants (tolerance ≤1e-6). Collect-only selector: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py --collect-only -q`. |
| A3 | Record VG-1 tolerances | [D] | ✅ VG-1 gate: |Δrot_b_phi0_y| ≤ 1e-6 Å and |Δk_frac_phi0| ≤ 1e-6. Log lives in `reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md` §VG-1. |

### Phase B — Parity Shim Design & API
Goal: Define how the optional carryover mode is requested, how it flows through configs/models, and how it coexists with the spec path.
Prereqs: Phase A complete; review `golden_suite_generator/nanoBragg.c:3040-3095` for reference logic.
Exit Criteria: Design note approved, interface decisions captured in plan + fix_plan, and implementation ready to start.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Draft design note (`design.md`) | [D] | ✅ Created `reports/2025-10-cli-flags/phase_l/parity_shim/20251007T232657Z/design.md` (10 sections, 496 lines): opt-in trigger (`--phi-carryover-mode {spec,c-parity}`), data flow, batched implementation strategy, validation plan, C-code excerpts per CLAUDE Rule #11. |
| B2 | Choose API & config plumbing | [D] | ✅ Documented in `design.md` §2-3: CLI flag `--phi-carryover-mode`, `CrystalConfig.phi_carryover_mode` field (default="spec"), parser updates in `__main__.py`. Unambiguous naming; no flag collision. |
| B3 | Define validation strategy | [D] | ✅ Documented in `design.md` §4: (a) Extended test classes `TestPhiCarryoverParity`, (b) CPU+CUDA parametrized tests, (c) Per-φ trace commands (`scripts/compare_per_phi_traces.py`), (d) nb-compare integration with `--py-args` flag. Artifact targets enumerated. |

### Phase C — Implementation & Verification Tasks
Goal: Implement the parity shim and prove both modes behave as intended without regressing vectorization, gradients, or devices.
Prereqs: Phase B approvals published and referenced from fix_plan/input.md.
Exit Criteria: Production code contains opt-in shim, tests/logs stored, fix_plan Attempt logged with metrics.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Implement opt-in carryover | [D] | ✅ `src/nanobrag_torch/models/crystal.py:1084-1128` implements the batched φ=0 replacement via `torch.index_select`, preserving gradients and citing `nanoBragg.c:3044-3058` per CLAUDE Rule #11 (Attempt #120). |
| C2 | Update CLI / configs | [D] | ✅ CLI flag `--phi-carryover-mode {spec,c-parity}` and `CrystalConfig.phi_carryover_mode` field landed (`src/nanobrag_torch/__main__.py:377-386`, `config.py:154-171`); validation rejects invalid modes (Attempt #120). |
| C3 | Add regression & parity tests | [D] | ✅ `tests/test_phi_carryover_mode.py` exercises parsing, config wiring, and device/dtype behavior for both modes; `tests/test_cli_scaling_phi0.py` still enforces spec baselines (documented in docs/fix_plan.md Attempt #120). |
| C4 | Capture per-φ traces & resolve tolerance | [P] | Enhanced traces from `reports/2025-10-cli-flags/phase_l/parity_shim/20251008T023140Z/` show a c-parity Δk plateau ≈2.845e-05 attributed to floating-point roundoff. Keep this task open until float64 sensitivity checks run and we document whether to relax VG-1 or pursue remediation. |
| C5 | Summarise metrics & log attempt | [ ] | Write `summary.md` describing test outcomes, trace comparisons, and any tolerances. Update `docs/fix_plan.md` Attempt history (CLI-FLAGS-003) with metrics, references, and git commit SHA. |

#### C4 Diagnostic Checklist — Quantify Precision Plateau

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C4a | Archive enhanced trace evidence | [D] | ✅ Attempt #127 stored spec + c-parity traces in `reports/2025-10-cli-flags/phase_l/parity_shim/20251008T023140Z/`; includes scattering vector taps, reciprocal vectors, V_actual, and delta summaries. Treat this directory as the baseline for subsequent comparisons. |
| C4b | Quantify dtype sensitivity | [ ] | Re-run `scripts/trace_per_phi.py` for both modes with explicit float32 and float64 tensors (e.g., wrap runs with `torch.set_default_dtype(torch.float32)` / `torch.set_default_dtype(torch.float64)` in a temporary harness branch). Save outputs under a new timestamped folder and capture refreshed `delta_metrics.json` to confirm whether the Δk plateau changes or drops below 1e-6. |
| C4c | Decide tolerance vs remediation | [ ] | Based on C4b, update `reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md` with either (i) an acceptance note (relax VG-1 to Δk ≤5e-5) or (ii) a remediation plan (higher-precision reciprocals). Log the decision and supporting metrics in `docs/fix_plan.md` (CLI-FLAGS-003). |
| C4d | Sync plan + checklist | [ ] | Reflect the outcome in `plans/active/cli-noise-pix0/plan.md` L3k.3 rows and `reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md`. Only after this alignment promote C4 to [D] and advance to C5. |

### Phase D — Documentation & Handoff
Goal: Align specs/docs with dual-mode behavior and prepare for Phase L4 supervisor command parity rerun.
Prereqs: Phase C complete, evidence uploaded.
Exit Criteria: Docs refreshed, plan cross-references updated, Next Actions ready for nb-compare rerun.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Update documentation | [ ] | Refresh `reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md` (add parity shim section), `docs/bugs/verified_c_bugs.md` (note shim availability), and `README_PYTORCH.md` or CLI docs if new flag added. Ensure spec documents remain unchanged (bug stays quarantined). |
| D2 | Sync plans/fix_plan | [ ] | Mark relevant rows in `plans/active/cli-noise-pix0/plan.md` as [D] or [P] with links to this plan’s artifacts. Update `docs/fix_plan.md` Next Actions to advance to Phase L4. |
| D3 | Prepare handoff to supervisor command rerun | [ ] | Document in `summary.md` which commands/tests must run next (e.g., nb-compare, supervisor command). Provide clear Do Now guidance for transitioning into Phase L4 in `input.md`. |
