## Context
- Initiative: CLI-FLAGS-003 — restore full CLI parity between PyTorch and nanoBragg.c for `-nonoise` and `-pix0_vector_mm` so the supervisor command is green without opt-in shims.
- Current Objective: With the φ carryover shim fully retired (see Phase D bundle `reports/2025-10-cli-flags/phase_phi_removal/phase_d/20251008T203504Z/`), re-establish spec-mode scaling parity for the supervisor ROI and finish the parity/normalization checks before running the end-to-end nb-compare closure.
  - Authoritative command (PyTorch + C parity harness):
    ```bash
    nanoBragg  -mat A.mat -floatfile img.bin -hkl scaled.hkl  -nonoise  -nointerpolate -oversample 1  -exposure 1  -flux 1e18 -beamsize 1.0  -spindle_axis -1 0 0 \
      -Xbeam 217.742295 -Ybeam 213.907080  -distance 231.274660 -lambda 0.976800 \
      -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 \
      -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 \
      -fdet_vector 0.999982 -0.005998 -0.000118 \
      -pix0_vector_mm -216.336293 215.205512 -230.200866  -beam_vector 0.00051387949 0.0 -0.99999986 \
      -Na 36  -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0
    ```
- Dependencies & References:
  - `specs/spec-a-cli.md` — canonical CLI semantics (noise suppression, detector vectors, precedence rules).
  - `specs/spec-a-core.md:204-240` — normative φ rotation pipeline and lattice factor definitions.
  - `docs/architecture/detector.md §5` — pix0 geometry workflows and pivot handling.
  - `docs/development/c_to_pytorch_config_map.md` — authoritative flag→config parity map.
  - `docs/development/testing_strategy.md §§1.4–2` — device/dtype smoke cadence, trace-driven validation contract.
  - `docs/bugs/verified_c_bugs.md:166-204` — C-PARITY-001 defect dossier (now historical reference only).
  - `plans/archive/cli-phi-parity-shim/plan.md` — archived shim plan documenting prior dual-mode behavior.
  - `reports/2025-10-cli-flags/phase_l/` — canonical evidence directories (rot_vector, scaling_audit, scaling_validation, nb_compare, supervisor_command).
- Artifact Policy: Continue storing new work under `reports/2025-10-cli-flags/phase_l/<topic>/<timestamp>/`, capturing `commands.txt`, raw logs, `summary.md`, `env.json`, and `sha256.txt` per CLI-FLAGS-003 conventions.
- Guardrails: Preserve vectorization (no scalar φ loops), maintain device/dtype neutrality, respect Protected Assets (`docs/index.md`), and cite nanoBragg.c snippets via CLAUDE Rule #11 when touching simulator/physics code.
- Status Snapshot (2025-10-22 refresh):
  - ✅ `-nonoise` plumbing merged with regression coverage (`tests/test_cli_nonoise.py`) — files: `src/nanobrag_torch/io/noise.py`, artifacts `reports/2025-10-cli-flags/phase_j/nonoise_plumbing/`.
  - ✅ pix0 precedence and SAMPLE pivot parity fixed (Attempt #129) — see `reports/2025-10-cli-flags/phase_k/pix0_precedence/20251006T231255Z/`.
  - ✅ φ carryover shim removed end-to-end (Attempts #176–#183) — definitive proof in `reports/2025-10-cli-flags/phase_phi_removal/phase_d/20251008T203504Z/`; shim plan archived.
  - ✅ Trace tooling + instrumentation audits (Phase M0) ensure debug caches gated by trace flag and remain device/dtype neutral (`reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T070513Z/`).
  - ⚠️ Scaling parity (VG‑2) still failing: fresh spec-mode bundle `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/metrics.json` confirms `first_divergence = "I_before_scaling"` with PyTorch 14.643% low relative to C (I_before_scaling: 8.05e5 vs 9.44e5). Downstream factors (r_e², fluence, steps, capture_fraction, polar, omega, cos_2theta) remain ≤1e-6.
  - 🧪 Phase M2 divergence analysis complete (Attempt #186) — `analysis_20251008T212459Z.md` and `lattice_hypotheses.md` isolate the F_latt sign flip (PyTorch +1.379 vs C −2.383) and elevate Hypothesis H4 (φ rotation mismatch) to HIGH confidence.
  - 🚩 Downstream nb-compare + supervisor command reruns remain blocked until Phase M closes.

---

### Phase L — Instrumentation & CLI Surface Sync (Complete)
Goal: Keep documentation, trace harness, and CLI plumbing aligned with the post-shim spec while preserving historical references for audit trails.
Prereqs: Archive `plans/active/cli-phi-parity-shim/plan.md`; ensure `docs/bugs/verified_c_bugs.md` reflects C-only status.
Exit Criteria: Docs/checklists updated, instrumentation guarded by trace flag, Attempt logged in fix_plan.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| L1 | Update tolerance + doc references | [D] | `reports/2025-10-cli-flags/phase_phi_removal/phase_c/20251008T200154Z/summary.md` documents updates to `docs/bugs/verified_c_bugs.md` and prompts to declare spec-only behavior. |
| L2 | Trace instrumentation hygiene | [D] | `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T070513Z/` audited `_enable_trace` gating and device/dtype handling; pytest CPU+CUDA logs attached. |
| L3 | Ledger sync | [D] | `docs/fix_plan.md` Attempt #136 and subsequent #184 record Phase L completion and shim archival paths. |

### Phase M — Spec-Mode Structure-Factor & Normalization Parity (VG‑2)
Goal: Regenerate spec-mode scaling evidence post-shim removal, identify the current source of the `I_before_scaling` delta, and implement the physics fix so PyTorch and C agree to ≤1e-6 on `F_cell`, `F_latt`, and `I_before_scaling` for the supervisor ROI.
Prereqs: Phase L ✅, Phase D (shim removal) ✅, trace harness usable without `--phi-mode`.
Exit Criteria: Latest `trace_harness.py` comparison yields `first_divergence = None`, targeted pytest/trace probes pass on CPU and CUDA, and fix_plan/docs reference the new green bundle.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| M1 | Capture fresh spec-mode baseline | [D] | ✅ Attempt #185 (2025-10-08). Bundle: `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/` with trace_harness commands, compare_scaling_traces metrics, env/sha256, and pytest collect log. First divergence remains `I_before_scaling` (Δ_rel = -1.4643e-01). |
| M2 | Partition divergence contributions | [D] | ✅ Attempt #186 (2025-10-22). `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/analysis_20251008T212459Z.md` quantifies the 14.6% deficit, updates `scaling_validation_summary.md`, and appends ranked hypotheses (H4–H8) to `.../20251008T075949Z/lattice_hypotheses.md`. |
| M3a | Add per-φ trace instrumentation | [D] | ✅ Attempt #187 (2025-10-22). Design document produced (`/tmp/m3a_instrumentation_design.md`) with logging points (Crystal.py:1131, Simulator.py:253), trace format (TRACE_PY_PHI), and implementation checklist. Implementation deferred to code-change loop (Phase M4). |
| M3b | Generate sincg sensitivity table | [D] | ✅ Attempt #187 (2025-10-22). Sweep complete (`reports/.../20251008T215755Z/phase_m3_probes/sincg_sweep.{md,csv,png}`). Zero-crossing confirmed at k≈-0.5955; C value (-0.607) yields sincg=+1.051, PyTorch (-0.589) yields sincg=-0.858 (182% swing from 3% k_frac shift). |
| M3c | Single-φ parity experiment | [D] | ✅ Attempt #187 (2025-10-22). Experiment complete (`reports/.../20251008T215634Z/phase_m3_probes/phistep1/`). Critical discovery: PyTorch 126,000× higher than C (max: 6.9e7 vs 548); correlation 0.999999. Root cause: missing `I/steps` normalization (C nanoBragg.c:3358). |
| M3d | Rotation matrix audit | [D] | ✅ Attempt #187 (2025-10-22). Audit complete (`reports/.../20251008T215700Z/phase_m3_probes/rotation_audit.md`). rot_b Y-component +6.8% error (0.717 vs 0.672 Å) traced to C-PARITY-001 φ=0 carryover bug; PyTorch spec-compliant but differs from buggy C. |
| M4 | Implement physics fix | [ ] | Execute the Phase M4a–M4d checklist below to land the normalization fix without regressing vectorization/device parity. |
| M5 | Gradient + CUDA validation | [ ] | Repeat M1 parity comparison on CUDA (`--device cuda --dtype float64` if available) and re-run the 2×2 ROI gradcheck harness from `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T165745Z_carryover_cache_validation/` to ensure gradients survive. Document results in `reports/.../<timestamp>/gpu_smoke/`. |
| M6 | Ledger & documentation sync | [ ] | Update `docs/fix_plan.md` Attempts (VG‑2 closure), refresh this plan’s Status Snapshot, and append a closure note to `reports/2025-10-cli-flags/phase_l/scaling_validation_summary.md` with metrics + git SHA. |

#### Phase M4 Checklist — Normalization Fix & Evidence Bundle

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| M4a | Confirm normalization contract | [ ] | Re-read `specs/spec-a-core.md:446-633` (intensity accumulator + steps division) and `docs/development/c_to_pytorch_config_map.md` scaling notes, then capture a short design memo (`reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/design_memo.md`) summarising the expected `intensity /= steps` behaviour with citations to `nanoBragg.c:3336-3365`. |
| M4b | Patch simulator normalization | [ ] | Implement the fix in `src/nanobrag_torch/simulator.py` (maintain batched tensor ops; no `.item()`, `.cpu()`, or scalar loops). Docstring MUST include the `nanoBragg.c` snippet per CLAUDE Rule #11. Update/extend per-φ logging hooks from M3a design notes so traces expose the corrected accumulator before/after the division. |
| M4c | Targeted regression & parity tests | [ ] | Run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py` plus any new unit tests covering the normalization branch (CPU first, then CUDA if available). Rerun `scripts/validation/compare_scaling_traces.py` against the supervisor bundle and store outputs under `reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/`. |
| M4d | Capture closure artifacts | [ ] | Archive Py vs C traces (`trace_py_fix.log`, `trace_c_baseline.log`), pytest logs, commands, env snapshot, and `sha256.txt` in the same `fix_<timestamp>` directory. Summarise results in `summary.md` (note first_divergence=None, include delta tables) and update `lattice_hypotheses.md` with final disposition of Hypothesis H4. |

### Phase N — ROI nb-compare Parity (VG‑3 & VG‑4)
Goal: After Phase M turns green, prove image-level parity on the supervisor ROI via nb-compare.
Prereqs: Phase M rows M1–M6 marked [D]; new green bundle path recorded.
Exit Criteria: `nb-compare` correlation ≥0.9995, sum_ratio 0.99–1.01, peak alignment within spec, artifacts archived.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| N1 | Regenerate C & PyTorch ROI outputs | [ ] | Run the authoritative command for both implementations, storing float images + metadata under `reports/2025-10-cli-flags/phase_l/nb_compare/<timestamp>/inputs/`. |
| N2 | Execute nb-compare | [ ] | `nb-compare --roi 100 156 100 156 --resample --threshold 0.98 --outdir reports/2025-10-cli-flags/phase_l/nb_compare/<timestamp>/results/ -- [command args]`. Capture `summary.json`, PNG previews, CLI stdout. |
| N3 | Log results | [ ] | Summarise metrics in `reports/.../nb_compare/<timestamp>/analysis.md` and update `docs/fix_plan.md` Attempts (VG-3/VG-4). |

### Phase O — Supervisor Command Closure (VG‑5)
Goal: Final verification that the full CLI command (spec-mode) runs cleanly and meets acceptance thresholds.
Prereqs: Phases M and N complete with green metrics.
Exit Criteria: Supervisor command rerun recorded with expected correlation/intensity metrics; fix_plan and plan archived/closed out.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| O1 | Final supervisor rerun | [ ] | Execute the authoritative command via the harness (CPU mandatory, CUDA optional). Store outputs + logs in `reports/2025-10-cli-flags/phase_l/supervisor_command/<timestamp>/`. |
| O2 | Ledger update | [ ] | Record Attempt with metrics (correlation, sum_ratio, mean_peak_distance) in `docs/fix_plan.md`, refresh this plan’s Status Snapshot, and note closure in `galph_memory.md`. |
| O3 | Archive & handoff | [ ] | Move stabilized artifacts to `reports/archive/cli-flags-003/`, mark plan ready for archive, and provide supervisor notes for future maintenance. |

### Phase P — Post-Fix Watch (Optional)
Goal: Establish lightweight guardrails so scaling regressions are caught early.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| P1 | Add hygiene checklist item | [ ] | Extend `docs/fix_plan.md` cleanup guidance to require rerunning `trace_harness.py` (spec-mode) on a quarterly cadence; cite the latest green bundle. |
| P2 | Schedule nb-compare smoke | [ ] | Document a biannual nb-compare smoke test command + expected metrics in `reports/archive/cli-flags-003/watch.md`. |
