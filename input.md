Summary: Regenerate the C per-φ trace and recompute VG-1 deltas so CLI-FLAGS-003 Phase L3k.3b is unblocked.
Mode: Parity
Focus: CLI-FLAGS-003 Phase L3k.3b TRACE_C_PHI rerun
Branch: feature/spec-based-2
Mapped tests: env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/c_trace_phi_20251123.log; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/trace_py_rot_vector_20251123_per_phi.json; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/comparison_stdout_20251123.txt; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/delta_metrics.json; reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md (L3k.3c.2 update); reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/commands.txt; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/sha256.txt
Do Now: CLI-FLAGS-003 (Handle -nonoise and -pix0_vector_mm) — execute Phase L3k.3b by rebuilding the instrumented C binary, rerunning the supervisor command with -trace_pixel 685 1039 to capture `c_trace_phi_20251123.log`, regenerating the PyTorch per-φ trace via `trace_harness.py`, and re-running `scripts/compare_per_phi_traces.py` so VG-1 deltas populate under the 20251123 timestamp before recording the updated metrics in diagnosis.md. Finish with env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q.
If Blocked: If the instrumented C binary is missing TRACE_C_PHI output, re-apply the instrumentation patch (see golden_suite_generator/nanoBragg.c:3156-3160), rerun `make -C golden_suite_generator`, and retry the command. If C still cannot be rebuilt on this machine, copy `c_trace_phi_202510070839.log` into the 20251123 directory, document the reuse decision in diagnosis.md, flag the delta computation as provisional inside delta_metrics.json, and stop after updating commands.txt + sha256.txt.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:288 — L3k.3 requires a fresh TRACE_C_PHI run paired with the 20251123 PyTorch probe before VG-1 can progress.
- plans/active/cli-noise-pix0/plan.md:300 — L3k.3c.2 stays [P] until Δb_y/Δk_frac are measured and logged.
- docs/fix_plan.md:458 — Next actions explicitly call for regenerating the C per-φ trace and updating diagnosis.md before moving on to nb-compare.
- docs/development/c_to_pytorch_config_map.md — Confirms the supervisor spindle axis / detector parameters that must match when regenerating parity traces.
- docs/debugging/debugging.md §Parallel Trace Comparison Rule — Governs the trace capture workflow and artifact naming.
How-To Map:
- mkdir -p reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123
- date '+%F %T TRACE START' | tee -a reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/commands.txt
- make -C golden_suite_generator -j | tee -a reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/commands.txt
- NB_C_BIN=./golden_suite_generator/nanoBragg ./golden_suite_generator/nanoBragg \
  -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 \
  -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 \
  -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 \
  -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 \
  -odet_vector -0.000088 0.004914 -0.999988 \
  -sdet_vector -0.005998 -0.999970 -0.004913 \
  -fdet_vector 0.999982 -0.005998 -0.000118 \
  -pix0_vector_mm -216.336293 215.205512 -230.200866 \
  -beam_vector 0.00051387949 0.0 -0.99999986 \
  -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 \
  -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 \
  -trace_pixel 685 1039 \
  2>&1 | tee reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/c_trace_phi_20251123.log
- PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python \
  reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py \
  --config supervisor --pixel 685 1039 \
  --out reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/trace_py_rot_vector_20251123.log \
  --device cpu --dtype float64 \
  | tee -a reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/commands.txt
- PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/compare_per_phi_traces.py \
  reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/trace_py_rot_vector_20251123_per_phi.json \
  reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/c_trace_phi_20251123.log \
  | tee reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/comparison_stdout_20251123.txt
- PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python - <<'PY'
import json, pathlib
base = pathlib.Path('reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123')
py = json.load((base/'trace_py_rot_vector_20251123_per_phi.json').open())['per_phi_entries']
with (base/'c_trace_phi_20251123.log').open() as fh:
    cvals = [float(line.split()[3].split('=')[1]) for line in fh if line.startswith('TRACE_C_PHI')]
metrics = {
    'status': 'ok',
    'phi0': {
        'py_k_frac': py[0]['k_frac'],
        'c_k_frac': cvals[0],
        'delta_k': py[0]['k_frac'] - cvals[0]
    },
    'phi9': {
        'py_k_frac': py[9]['k_frac'],
        'c_k_frac': cvals[9],
        'delta_k': py[9]['k_frac'] - cvals[9]
    }
}
(base/'delta_metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
PY
- sha256sum reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/* > reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/sha256.txt
- Update reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md with an L3k.3c.2 entry summarising the new Δk values, the command hashes, and the remediation path (φ==0 mask or equivalent vectorized carryover) before touching simulator code.
- env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q | tee -a reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/commands.txt
Pitfalls To Avoid:
- Do not edit simulator/crystal code this loop; evidence only.
- Keep all command transcripts in commands.txt with timestamps so the rerun is auditable.
- Ensure NB_C_BIN points at golden_suite_generator/nanoBragg; the root binary lacks TRACE_C_PHI instrumentation.
- Maintain device/dtype neutrality when running harness scripts (stay on cpu/float64 as specified).
- Do not overwrite older base_vector_debug directories; add the new timestamp alongside 202510070839/20251122.
- Preserve failing pytest expectations in tests/test_cli_scaling_phi0.py; no edits to mask the red baseline.
- Run compare_per_phi_traces.py after both traces exist; it will raise if paths are wrong.
- Append to diagnosis.md rather than replacing earlier sections so chronology is intact.
- Regenerate sha256.txt after all files are in place to avoid stale hashes.
- Keep delta_metrics.json formatted as JSON (no trailing comments) for future automation.
Pointers:
- plans/active/cli-noise-pix0/plan.md:288-307 — Current L3k.3 checklist and subtasks.
- docs/fix_plan.md:458-466 — Next actions aligned with this loop.
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/202510070839/diagnosis.md — Reference commands from the prior successful TRACE_C_PHI run.
- golden_suite_generator/nanoBragg.c:3156-3160 — TRACE_C_PHI instrumentation hook.
- reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md#L19 — VG-1.4 acceptance thresholds to update after deltas recorded.
Next Up: Once VG-1 deltas are in place, move to Phase L3k.3d to repair the nb-compare ROI totals.
