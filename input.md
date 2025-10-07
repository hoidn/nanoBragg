Summary: Quantify the φ=0 rotation invariants so we can nail the real-space drift before touching simulator code.
Mode: Parity
Focus: CLI-FLAGS-003 – Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: [tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics]
Artifacts:
- reports/2025-10-cli-flags/phase_l/rot_vector/trace_py_rot_vector.log
- reports/2025-10-cli-flags/phase_l/rot_vector/rot_vector_comparison.md
- reports/2025-10-cli-flags/phase_l/rot_vector/invariant_probe.md
- reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md
Do Now: CLI-FLAGS-003 — mkdir -p reports/2025-10-cli-flags/phase_l/rot_vector && PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --config supervisor --device cpu --dtype float32 --out reports/2025-10-cli-flags/phase_l/rot_vector/trace_py_rot_vector.log && python - <<'PY'
from pathlib import Path
import numpy as np
root = Path('reports/2025-10-cli-flags/phase_l')
log_c = root / 'scaling_audit/c_trace_scaling.log'
log_py = root / 'rot_vector/trace_py_rot_vector.log'

def grab(path, prefix):
    real, recip = {}, {}
    for parts in (line.split() for line in path.read_text().splitlines()):
        if len(parts) < 5 or parts[0] != f'TRACE_{prefix}:' or not parts[1].startswith('rot_'):
            continue
        vec = np.array(list(map(float, parts[2:5])))
        (recip if '_star_' in parts[1] else real)[parts[1]] = vec
    return real, recip
real_c, recip_c = grab(log_c, 'C')
real_py, recip_py = grab(log_py, 'PY')

def volume(real):
    return float(np.dot(real['rot_a_angstroms'], np.cross(real['rot_b_angstroms'], real['rot_c_angstroms'])))
vol_c = volume(real_c)
vol_py = volume(real_py)

def dot_map(real, recip):
    out = {}
    for axis in 'abc':
        out[axis] = float(np.dot(real[f'rot_{axis}_angstroms'], recip[f'rot_{axis}_star_A_inv']))
    return out
dots_c = dot_map(real_c, recip_c)
dots_py = dot_map(real_py, recip_py)
rows = ['# Rotation Invariants Probe', '', f'| Metric | C | PyTorch | Δ (Py-C) |', '| --- | --- | --- | --- |', f"| Unit-cell volume (Å^3) | {vol_c:.6f} | {vol_py:.6f} | {vol_py - vol_c:+.6e} |"]
for axis in 'abc':
    rows.append(f"| {axis} · {axis}* | {dots_c[axis]:.9f} | {dots_py[axis]:.9f} | {dots_py[axis] - dots_c[axis]:+.3e} |")
rows.extend(['', 'Source logs:', f'- C trace: {log_c}', f'- PyTorch trace: {log_py}'])
Path(root / 'rot_vector' / 'invariant_probe.md').write_text('\n'.join(rows) + '\n', encoding='utf-8')
PY
 && KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics
If Blocked: If the harness fails or missing TRACE lines, dump stdout/stderr to reports/2025-10-cli-flags/phase_l/rot_vector/trace_py_rot_vector_raw.txt, note which key is absent, update docs/fix_plan.md Attempt history, and pause for supervisor review.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:265 states Phase L3f must supply aligned rot vectors ahead of normalization changes.
- plans/active/cli-noise-pix0/plan.md:266 requires hypotheses plus confirming probes before simulator edits.
- docs/fix_plan.md:450-463 pins the φ=0 k_frac drift as the blocker for getting -nonoise/-pix0_vector_mm parity.
- specs/spec-a-cli.md:1-120 anchor the CUSTOM convention precedence we are auditing.
- docs/development/c_to_pytorch_config_map.md:36-78 remind us beam/pivot mapping and volume rules must stay in lockstep with C.
How-To Map:
- Refresh `reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md` with the invariant results (volume deltas, dot products) and call out which Phase L3g hypothesis looks most likely.
- Append docs/fix_plan.md Attempt #88 with the command, key metrics (Δvolume ≈ +3.3e-03 Å^3, dot deltas), and the follow-up probes you select.
- Cross-check the invariant numbers against `reports/2025-10-cli-flags/phase_l/rot_vector/rot_vector_comparison.md` so the tables tell a consistent story.
- Keep all new helper snippets under `reports/…/rot_vector/`; do not introduce ad-hoc scripts elsewhere.
Pitfalls To Avoid:
- Do not alter production simulator code during this evidence pass.
- Leave C trace artifacts untouched; only regenerate the PyTorch side.
- Maintain device/dtype neutrality—no `.cpu()` or `.item()` on tensors in harness updates.
- Respect Protected Assets: never move/delete files referenced by docs/index.md.
- Don’t skip the pytest collect check; it’s our guardrail that the selector stays valid.
- Avoid mixing new logs with existing scaling_audit artifacts; keep outputs in rot_vector/.
- Document every command verbatim in docs/fix_plan.md to preserve reproducibility.
- Keep temporary calculations ASCII and inside the reports tree; no root-level clutter.
- If you touch trace_harness.py, follow docs/debugging/debugging.md trace schema exactly.
Pointers:
- reports/2025-10-cli-flags/phase_l/rot_vector/rot_vector_comparison.md — current C vs Py rotation deltas.
- reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md — hypotheses for Phase L3g.
- docs/debugging/debugging.md:34-88 — required TRACE naming/precision rules.
- plans/active/cli-noise-pix0/plan.md:253-274 — Phase L3 context and exit criteria.
- docs/architecture/pytorch_design.md:120-188 — rotation/misset data flow that must stay intact.
Next Up: If invariants confirm the issue lies in real-space reconstruction, prepare a trace patch plan for Crystal.get_real_from_reciprocal before any simulator edits.
