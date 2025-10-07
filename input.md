Summary: Capture φ=0 state carryover evidence and outline a vectorized parity fix for CLI-FLAGS-003 before touching simulator code.
Mode: Parity
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q; tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c (expected red until carryover fix)
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/rot_vector_state_probe.log; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/phi0_state_analysis.md; reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md (L3k.3c update); reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/commands.txt; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/sha256.txt; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/delta_metrics.json
Do Now: CLI-FLAGS-003 (Handle -nonoise and -pix0_vector_mm) — execute Phase L3k.3c.2 by collecting φ=0 carryover evidence, drafting the vectorized fix plan in diagnosis.md, logging all commands + hashes, generating delta metrics, then run env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q to confirm the harness still imports.
If Blocked: If A.mat or scaled.hkl are unavailable, switch to the existing C/Py traces under reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/202510070839/, document the gap in diagnosis.md, capture a stub entry in commands.txt explaining the missing assets, update sha256.txt accordingly, emit a placeholder delta_metrics.json noting the missing data, and log a new Attempt referencing the dependency issue before proceeding.
Priorities & Rationale:
- docs/fix_plan.md:450 — CLI-FLAGS-003 next actions require L3k.3c evidence prior to code edits so the parity gate stays honest.
- plans/active/cli-noise-pix0/plan.md:274 — L3k.3c.2 mandates documenting the φ=0 carryover using trace comparisons and a proposed remediation path.
- golden_suite_generator/nanoBragg.c:3040 — Reveals the `if(phi!=0.0)` guard that leaves ap/bp/cp stale at φ=0, which explains the 0.6716 Å reference value.
- src/nanobrag_torch/models/crystal.py:1057 — Current Python loop is an interim hack; today’s memo must call out the requirement to re-vectorize with tensor masks.
- reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md — VG-1.4 stays red until the carryover story is captured with artifacts; update references accordingly.
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/202510070839/comparison_summary_20251119.md — Earlier findings already describe the φ drift; append the new evidence to close the loop.
- docs/debugging/debugging.md §Parallel Trace Comparison Rule — Governs how the new log and analysis should be structured and stored.
- docs/architecture/pytorch_design.md#vectorization-strategy — Any future fix must honor the batched flows; note this explicitly in the diagnosis write-up.
- specs/spec-a-parallel.md §Lattice rotation profile — Confirms φ sweeps must mimic the C ordering during parity work.
- docs/development/c_to_pytorch_config_map.md — Validates spindle-axis orientation and phi sequencing; cite it to prove the configuration is correct.
- docs/development/testing_strategy.md §1.4 — Device/dtype neutrality reminder; the eventual fix cannot reintroduce CPU-only code or Python loops.
How-To Map:
- mkdir -p reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123
- touch reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/commands.txt reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/sha256.txt
- Record every shell invocation in commands.txt (prepend with timestamps via `date '+%F %T' >> ...` before each command).
- Capture PyTorch behavior:
  KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python - <<'PY' | tee -a reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/rot_vector_state_probe.log
from pathlib import Path
import torch
from nanobrag_torch.models.crystal import Crystal, CrystalConfig
from nanobrag_torch.config import BeamConfig
from nanobrag_torch.io.mosflm import read_mosflm_matrix
mat = Path('A.mat')
if not mat.exists():
    raise SystemExit('A.mat missing')
a_star, b_star, c_star = read_mosflm_matrix(str(mat), 0.9768)
config = CrystalConfig(cell_a=100.0, cell_b=100.0, cell_c=100.0,
    cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
    N_cells=(36,47,29), mosflm_a_star=a_star, mosflm_b_star=b_star, mosflm_c_star=c_star,
    phi_start_deg=0.0, osc_range_deg=0.1, phi_steps=10, mosaic_domains=1,
    misset_deg=[0.0,0.0,0.0], spindle_axis=[-1.0,0.0,0.0])
beam = BeamConfig(wavelength_A=0.9768)
crystal = Crystal(config, beam_config=beam, device=torch.device('cpu'), dtype=torch.float32)
(rot_a, rot_b, rot_c), _ = crystal.get_rotated_real_vectors(config)
print('b_base_y', crystal.b[1].item())
print('rot_b_phi0_y', rot_b[0,0,1].item())
print('rot_b_phi1_y', rot_b[1,0,1].item())
print('k_frac_placeholder', torch.dot(rot_b[0,0], rot_b[0,0]).item())
PY
- Append both the heredoc and resulting log path into commands.txt for provenance (e.g., printf "python ... >> rot_vector_state_probe.log" >> commands.txt).
- Generate SHA256 hashes for the new log: `cd reports/.../20251123 && sha256sum rot_vector_state_probe.log >> sha256.txt`.
- Derive numeric deltas via scripted analysis:
  KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python - <<'PY' > reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/delta_metrics.json
import json
from pathlib import Path
from decimal import Decimal
log = Path('reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/rot_vector_state_probe.log').read_text().splitlines()
py_values = {line.split()[0]: Decimal(line.split()[-1]) for line in log if line.startswith(('b_base_y','rot_b_phi0_y','rot_b_phi1_y'))}
with Path('reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/202510070839/c_trace_phi_202510070839.log').open() as fh:
    c_phi0 = None
    for line in fh:
        if 'TRACE_C_PHI phi_tic=0' in line:
            parts = line.strip().split()
            c_phi0 = Decimal(parts[-3])
            break
if c_phi0 is None:
    raise SystemExit('C phi0 value not found')
delta = py_values['rot_b_phi0_y'] - c_phi0
json.dump({'rot_b_phi0_y_delta_A': float(delta)}, open('reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/delta_metrics.json','w'), indent=2)
PY
- Hash delta_metrics.json and append to sha256.txt.
- Compare against C trace lines: use `grep -n "TRACE_C_PHI phi_tic=0" ...` and `grep -n "TRACE_C_PHI phi_tic=9" ...` to extract the reference values; capture snippets in phi0_state_analysis.md with computed deltas (Δb_y ≈ +4.57e-2 Å, Δk_frac ≈ +2.28).
- In phi0_state_analysis.md, include sections for “Observed PyTorch Values”, “C Reference”, “Delta Summary”, “Vectorization Risk”, and “Next Diagnostic Step”.
- Update reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md with:
  • Dated heading (2025-11-22)
  • Summary of new probe results (cite log + hash + delta_metrics.json)
  • Explanation referencing golden_suite_generator/nanoBragg.c:3040-3095 and src/nanobrag_torch/models/crystal.py:1057-1084
  • A proposed vectorized remediation: compute all rotated vectors, retain a lagged copy via `torch.roll`, and use a φ==0 mask to swap in the prior step so performance stays batched
  • Risks/next steps (need to ensure gradients intact, confirm with gradcheck after implementation)
- Cross-link the diagnosis entry to reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/202510070839/comparison_summary_20251119.md for historical continuity.
- Run env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q | tee -a reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/commands.txt to confirm imports.
- If collect-only output is redirected to a log, hash it and append to sha256.txt.
- Note the commands and hashes in docs/fix_plan.md Attempt notes after supervisor review.
Pitfalls To Avoid:
- Do not edit src/nanobrag_torch/models/crystal.py this loop; gather evidence only.
- Avoid reasserting that PyTorch is “correct” relative to physics; parity with the C binary remains the acceptance criterion until the supervisor command passes.
- Do not relocate or overwrite the 202510070839 trace assets; link to them.
- Keep the new logs under the 20251123 directory to preserve chronology for Protected Assets review.
- Do not add new pytest expectations or change tolerances while the test is intentionally red.
- Avoid introducing additional Python loops in downstream proposals; emphasize tensorized masks in the diagnosis section.
- Ensure every shell command is captured in commands.txt for reproducibility.
- Keep environment variables (`KMP_DUPLICATE_LIB_OK`, optional `NB_C_BIN`) explicit in commands to avoid hidden state.
- Do not invoke nb-compare or heavy GPU runs during this evidence loop; stay focused on φ=0 analysis.
- Maintain clean git staging; only docs/reports/input updates should appear when the loop ends.
- Double-check sha256.txt entries; each line should be `hash  filename` for reproducibility audits.
- Do not forget to append the pytest collect-only invocation to commands.txt even if it passes instantly.
- Avoid editing tests/test_cli_scaling_phi0.py; the assertions must remain red until the fix lands.
- Do not delete prior diagnosis sections; add a new dated entry instead.
Pointers:
- docs/fix_plan.md:450 (CLI-FLAGS-003 next actions)
- plans/active/cli-noise-pix0/plan.md:274 (L3k.3c checklist)
- golden_suite_generator/nanoBragg.c:3040
- src/nanobrag_torch/models/crystal.py:1057
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/202510070839/c_trace_phi_202510070839.log
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/202510070839/trace_py_rot_vector_202510070839.log
- reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/202510070839/comparison_summary_20251119.md
- reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md
- tests/test_cli_scaling_phi0.py:25
- docs/debugging/debugging.md
- docs/architecture/pytorch_design.md#vectorization-strategy
- specs/spec-a-parallel.md §Lattice rotation profile
- docs/development/c_to_pytorch_config_map.md
- docs/development/testing_strategy.md §1.4
Next Up: 1) Implement the vectorized φ carryover fix and rerun the targeted pytest selector; 2) Regenerate per-φ traces plus nb-compare metrics once VG-1 tolerances pass; 3) Revisit vectorization plan Phase C3 to ensure no long-term regressions remain.
