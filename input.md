Summary: Lock the φ=0 parity shim documentation and checklists to the dual-threshold tolerance so we can move on to the scaling fix.
Mode: Docs
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — Phase L1–L3 documentation sync
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py
Artifacts:
- reports/2025-10-cli-flags/phase_l/rot_vector/20251202_tolerance_sync/
- reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md (updated VG-1 section)
- reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md (VG-1 rows updated)
- docs/bugs/verified_c_bugs.md (C-PARITY-001 addendum)
- docs/fix_plan.md (new Attempt logging Phase L1–L3 completion)
Do Now: Phase L1–L3 — document the relaxed c-parity tolerance, sync plans/checklists/bug log, then run KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py (capture stdout under the new report directory)
If Blocked: If prior edits conflict (merge markers or incompatible instructions), stash copies in reports/2025-10-cli-flags/phase_l/rot_vector/20251202_tolerance_sync/blocked.md, note the issue in docs/fix_plan.md, and pause further changes pending supervisor guidance.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:35 — Phase L targets tolerance/documentation sync before scaling work begins; keep the checklist states aligned.
- plans/active/cli-phi-parity-shim/plan.md:66 — Phase D tasks (D1–D3) remain open until diagnosis.md, docs/bugs, and handoff notes are updated.
- docs/fix_plan.md:460 — Next Actions call for Phase L1–L3 completion before the scaling audit resumes.
- reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md:116 — Needs a dated subsection citing the dtype probe and dual thresholds.
- reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md:12 — VG-1 rows still reference the pre-relaxation tolerance; update them to point at the new artifacts.
- docs/bugs/verified_c_bugs.md:166 — Must mention the opt-in parity shim and relaxed |Δk| ≤ 5e-5 while keeping the spec baseline distinct.
How-To Map:
- mkdir -p reports/2025-10-cli-flags/phase_l/rot_vector/20251202_tolerance_sync
- printf 'date -u: ' && date -u >> reports/.../20251202_tolerance_sync/commands.txt
- Record every command in commands.txt (including editors, pytest, sha256sum)
- Update reports/.../diagnosis.md with a “2025-12-02 Dual-Threshold Update” subsection referencing parity_shim/20251201_dtype_probe/{analysis_summary.md,delta_metrics.json}
- Edit reports/.../fix_checklist.md VG-1 rows to cite the new evidence and mark VG-1.4 as satisfied under the relaxed tolerance
- Touch plans/active/cli-noise-pix0/plan.md Phase L (mark L1 [D] when doc sync finishes, keep L2/L3 statuses accurate)
- In plans/active/cli-phi-parity-shim/plan.md, move Phase C5/C4d to [D] and activate Phase D1–D3 guidance with the new artifact directory
- Append a paragraph under docs/bugs/verified_c_bugs.md C-PARITY-001 describing the parity shim flag, dual thresholds, and evidence paths
- Run KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py > reports/.../20251202_tolerance_sync/collect_only.log
- (cd reports/.../20251202_tolerance_sync && sha256sum * > sha256.txt)
- Add a new Attempt entry to docs/fix_plan.md under CLI-FLAGS-003 summarizing edits, collect-only output, and the tolerance decision
Pitfalls To Avoid:
- Do not modify production code; this loop is documentation only.
- Keep historical notes intact—append new sections without deleting prior evidence.
- Respect Protected Assets (docs/index.md, loop.sh, supervisor.sh, input.md).
- Ensure commands.txt faithfully reflects every command; no undocumented steps.
- Maintain ASCII only; no smart quotes or non-breaking spaces.
- Avoid running full pytest suites or nb-compare yet; only the mapped collect-only command is allowed.
- Re-run sha256 after every file addition inside the report directory to keep hashes current.
- Mention relaxed tolerance only for c-parity mode; spec mode remains ≤1e-6 everywhere else.
- Verify git diff before commit to confirm only targeted docs changed.
- Leave plan states consistent (no flipping to [D] without evidence stored in the new directory).
Pointers:
- plans/active/cli-noise-pix0/plan.md:35
- plans/active/cli-phi-parity-shim/plan.md:66
- docs/fix_plan.md:460
- reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md:116
- reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md:12
- docs/bugs/verified_c_bugs.md:166
- reports/2025-10-cli-flags/phase_l/parity_shim/20251201_dtype_probe/analysis_summary.md:1
Next Up: Phase M1–M3 — scaling parity (audit HKL lookup and fix I_before_scaling) once tolerance/doc sync artifacts are captured.
