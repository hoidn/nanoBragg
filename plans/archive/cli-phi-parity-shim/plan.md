---
**CLOSURE NOTE (2025-10-08):**

This plan has been **ARCHIVED** following the completion of φ carryover shim removal (Phase D1, Attempt #183).

**Why Archived:** The φ=0 carryover bug (C-PARITY-001) was implemented as an opt-in parity shim to enable C↔PyTorch validation during CLI-FLAGS-003 development. After rigorous validation, the shim and all related infrastructure (CLI flags, config plumbing, tests) were removed in Phase B-C of `plans/active/phi-carryover-removal/plan.md` to align the implementation with the normative spec (`specs/spec-a-core.md:204-240`), which mandates fresh φ rotations each step.

**Evidence:** Phase D1 proof-of-removal bundle stored at `reports/2025-10-cli-flags/phase_phi_removal/phase_d/20251008T203504Z/` contains C/Py traces showing spec-mode behavior, pytest proof (2 passed, VG-1 tolerance ≤1e-6), and ripgrep sweep confirming zero `phi_carryover_mode` references in production code.

**Historical Context:** The work described in this plan (Phases A-D) was successfully completed during Attempts #120-#136. The shim served its purpose for parity debugging but is no longer present in the codebase as of commit 340683f (Phase B1) and subsequent cleanup.

**Current Status:** PyTorch implementation now follows the spec exclusively. For scaling/parity work going forward, refer to `plans/active/cli-noise-pix0/plan.md` Phase L tasks and the canonical Phase D bundle evidence.

**Cross-References:**
- `plans/active/phi-carryover-removal/plan.md` — Shim retirement initiative
- `docs/fix_plan.md` CLI-FLAGS-003 — Ledger with full attempt history
- `docs/bugs/verified_c_bugs.md` C-PARITY-001 — C-only bug classification

---

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
- Current Status (2025-12-08 refresh): Spec baseline locked, opt-in parity shim landed (Attempts #120/#121), and the dtype sensitivity probe in `reports/2025-10-cli-flags/phase_l/parity_shim/20251201_dtype_probe/` confirmed the Δk≈2.845e-05 plateau is inherent to the C carryover bug. Decision logged to relax the VG-1 tolerance for c-parity mode to |Δk| ≤ 5e-5; documentation/test updates (Phase C5/D) remain outstanding.
- 2025-12-08 (galph review): `specs/spec-a-core.md:205-233` still mandates fresh φ rotations each step; no spec text incorporates the carryover bug. C5 `summary.md` must cite this section to show PyTorch default remains spec-compliant while the shim is C-only.
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
| C4 | Capture per-φ traces & resolve tolerance | [D] | ✅ Attempts #127/#130 captured enhanced traces plus float32/float64 sweeps; `analysis_summary.md` (20251201) recommends relaxing VG-1 to |Δk| ≤ 5e-5 for c-parity while keeping spec at ≤1e-6. Decision recorded in docs/fix_plan.md Attempt #130; next work shifts to documentation (C5/D). |
| C5 | Summarise metrics & log attempt | [ ] | Draft `summary.md` capturing spec-vs-parity behavior, cite `specs/spec-a-core.md:205-233` to confirm φ resets each step, and document tolerances for both modes. Update `docs/fix_plan.md` Attempt history (CLI-FLAGS-003) with metrics, spec references, and git commit SHA. |
#### C5 Evidence Checklist

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C5a | Confirm spec isolation | [ ] | In `summary.md`, cite `specs/spec-a-core.md:205-233` showing φ rotations recompute from the reference lattice each step; note that carryover exists only in c-parity shim and capture diffs if the spec ever changes. (Galph 2025-12-08 review confirmed these lines remain unchanged.) |
| C5b | Sync bug ledger | [ ] | Ensure `docs/bugs/verified_c_bugs.md` retains C-only classification for C-PARITY-001 and links to the new `summary.md`; note parity shim availability for PyTorch. |
| C5c | Update fix plan entry | [ ] | Append metrics, spec citations, shim mode notes, and the new artifact path to `docs/fix_plan.md` (CLI-FLAGS-003 Attempt); include git SHA and timestamp. |


#### C4 Diagnostic Checklist — Quantify Precision Plateau

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C4a | Archive enhanced trace evidence | [D] | ✅ Attempt #127 stored spec + c-parity traces in `reports/2025-10-cli-flags/phase_l/parity_shim/20251008T023140Z/`; includes scattering vector taps, reciprocal vectors, V_actual, and delta summaries. Treat this directory as the baseline for subsequent comparisons. |
| C4b | Quantify dtype sensitivity | [D] | ✅ Attempt #130 stored float32/float64 traces and `delta_metrics.json` under `reports/2025-10-cli-flags/phase_l/parity_shim/20251201_dtype_probe/`, showing Δk(fp32 vs fp64)=1.42e-06. |
| C4c | Decide tolerance vs remediation | [D] | ✅ Same attempt documented the decision to relax VG-1 for c-parity (|Δk| ≤ 5e-5) in `analysis_summary.md` and docs/fix_plan.md Attempt #130; remediation deferred. |
| C4d | Sync plan + checklist | [D] | ✅ Updated `reports/.../rot_vector/diagnosis.md` §Dual-Threshold Decision, `fix_checklist.md` VG-1.4, `docs/bugs/verified_c_bugs.md` C-PARITY-001. Artifacts: `20251201_dual_threshold/{commands.txt,collect_only.log,sha256.txt}`. Phase C4 complete; ready for Phase C5/D documentation hand-off. |

### Phase D — Documentation & Handoff
Goal: Align specs/docs with dual-mode behavior and prepare for Phase L4 supervisor command parity rerun.
Prereqs: Phase C complete, evidence uploaded.
Exit Criteria: Docs refreshed, plan cross-references updated, Next Actions ready for nb-compare rerun.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Update documentation | [D] | ✅ Refreshed `reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md` with Phase L sync note (2025-10-07), updated `docs/bugs/verified_c_bugs.md` C-PARITY-001 to note parity shim availability. Spec documents unchanged (bug quarantined). CLI flag `--phi-carryover-mode` already documented in code. |
| D2 | Sync plans/fix_plan | [D] | ✅ Marked Phase D/L tasks complete in both plans. Logged Attempt #136 in `docs/fix_plan.md` CLI-FLAGS-003 with tolerance sync, artifacts linked to `reports/.../20251007T212159Z/`. |
| D3 | Prepare handoff to supervisor command rerun | [ ] | Extend `summary.md` with explicit next-step callouts (Phase M scaling parity, Phase N nb-compare, Phase O supervisor rerun), ensure `plans/active/cli-noise-pix0/plan.md` cross-references the new summary, and note in the next `input.md` draft which artifacts/tests Ralph must pick up. |
