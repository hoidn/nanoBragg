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
- Current Status (2025-11-27): Spec baseline locked (VG-1 met with ≤1e-6 deltas); parity shim not yet designed. Default path removes `_phi_last_cache`. Need explicit toggle plus regression coverage before L4 supervisor command rerun.
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
| B1 | Draft design note (`design.md`) | [ ] | Create `parity_shim/<timestamp>/design.md` summarising: (1) Opt-in trigger surface (CLI flag vs environment vs config field); (2) Data flow sketch showing when stale vectors should replace spec vectors; (3) Gradient/torch.compile considerations; (4) Interaction with batching (phi × mosaic). Include direct C-code excerpts per CLAUDE Rule #11. |
| B2 | Choose API & config plumbing | [ ] | Decide naming/location (e.g., `CrystalConfig.phi_carryover_mode` or `SimulatorConfig.c_parity`). Document default (`spec`) vs legacy (`c`) modes; ensure CLI mapping is unambiguous and does not repurpose existing flags. Update `design.md` and note required changes to `src/nanobrag_torch/__main__.py` and config dataclasses. |
| B3 | Define validation strategy | [ ] | Enumerate required tests & scripts: (a) extend `tests/test_cli_scaling_phi0.py` with parity-toggle cases; (b) targeted pytest selectors (CPU and CUDA); (c) per-φ trace capture using `scripts/compare_per_phi_traces.py`; (d) nb-compare/ROI expectations if needed. Add these to `design.md` with commands and artifact targets. |

### Phase C — Implementation & Verification Tasks
Goal: Implement the parity shim and prove both modes behave as intended without regressing vectorization, gradients, or devices.
Prereqs: Phase B approvals published and referenced from fix_plan/input.md.
Exit Criteria: Production code contains opt-in shim, tests/logs stored, fix_plan Attempt logged with metrics.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Implement opt-in carryover | [ ] | Modify `Crystal.get_rotated_real_vectors` (and supporting helpers) to optionally reuse φ_{last} vectors when parity mode enabled. Must remain batched: use tensor masking/index operations rather than Python loops. Include C reference snippet (`nanoBragg.c:3044-3058`) in docstring as mandated. Ensure default path unchanged. |
| C2 | Update CLI / configs | [ ] | Wire the chosen API through `CrystalConfig`, `SimulatorConfig`, and CLI parser. Provide unit coverage in `tests/test_cli_flags.py` (e.g., new `TestPhiParityShim`) verifying flag parsing, default mode, and interaction with existing options. |
| C3 | Add regression & parity tests | [ ] | Extend `tests/test_cli_scaling_phi0.py` with parity-enabled assertions (expect C bug values). Parameterise over devices (CPU + CUDA when available). Capture logs under `parity_shim/<timestamp>/pytest_{cpu,cuda}.log`. Ensure spec tests still pass. |
| C4 | Capture per-φ traces | [ ] | Run `scripts/compare_per_phi_traces.py` twice (spec vs C parity, parity-shim vs C). Store outputs (`trace_summary.md`, `delta_metrics.json`, raw traces) under the new report directory. Confirm parity mode reproduces Δk/Δb from C within 1e-6 while spec mode remains at spec baselines. |
| C5 | Summarise metrics & log attempt | [ ] | Write `summary.md` describing test outcomes, trace comparisons, and any tolerances. Update `docs/fix_plan.md` Attempt history (CLI-FLAGS-003) with metrics, references, and git commit SHA. |

### Phase D — Documentation & Handoff
Goal: Align specs/docs with dual-mode behavior and prepare for Phase L4 supervisor command parity rerun.
Prereqs: Phase C complete, evidence uploaded.
Exit Criteria: Docs refreshed, plan cross-references updated, Next Actions ready for nb-compare rerun.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Update documentation | [ ] | Refresh `reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md` (add parity shim section), `docs/bugs/verified_c_bugs.md` (note shim availability), and `README_PYTORCH.md` or CLI docs if new flag added. Ensure spec documents remain unchanged (bug stays quarantined). |
| D2 | Sync plans/fix_plan | [ ] | Mark relevant rows in `plans/active/cli-noise-pix0/plan.md` as [D] or [P] with links to this plan’s artifacts. Update `docs/fix_plan.md` Next Actions to advance to Phase L4. |
| D3 | Prepare handoff to supervisor command rerun | [ ] | Document in `summary.md` which commands/tests must run next (e.g., nb-compare, supervisor command). Provide clear Do Now guidance for transitioning into Phase L4 in `input.md`. |

