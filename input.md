Summary: Capture φ=0 rotation vectors and frame hypotheses for the residual k_frac drift before touching simulator code.
Mode: Parity
Focus: CLI-FLAGS-003 – Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: [tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics]
Artifacts:
- reports/2025-10-cli-flags/phase_l/rot_vector/trace_py_rot_vector.log
- reports/2025-10-cli-flags/phase_l/rot_vector/rot_vector_comparison.md
- reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md
Do Now: CLI-FLAGS-003 — mkdir -p reports/2025-10-cli-flags/phase_l/rot_vector && PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --config supervisor --device cpu --dtype float32 --out reports/2025-10-cli-flags/phase_l/rot_vector/trace_py_rot_vector.log && KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics
If Blocked: Capture harness stdout/stderr to reports/2025-10-cli-flags/phase_l/rot_vector/trace_py_rot_vector_raw.txt, note missing TRACE_PY rot lines plus commands in docs/fix_plan.md Attempt history, and halt for supervisor review.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:264-267 elevates Phase L3f/L3g as the current blockers before touching normalization code.
- docs/fix_plan.md:450-463 lists the rotation-vector audit and hypothesis framing as the top next actions for CLI-FLAGS-003.
- reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log anchors the C-side rot vectors that must be matched.
- reports/2025-10-cli-flags/phase_l/per_phi/trace_py_scaling_20251119_per_phi.json shows φ sweep data confirming convergence after the initial step—use it as context when analysing the φ=0 drift.
- specs/spec-a-cli.md §3 and docs/development/c_to_pytorch_config_map.md outline the normative rotation/pivot rules the audit must respect.
How-To Map:
- Ensure env vars: `export PYTHONPATH=src` and `export KMP_DUPLICATE_LIB_OK=TRUE` before running tooling.
- Harness capture: `PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --config supervisor --device cpu --dtype float32 --out reports/2025-10-cli-flags/phase_l/rot_vector/trace_py_rot_vector.log` (creates new main + per-φ traces alongside env metadata).
- Build comparison table: `python - <<'PY'
from pathlib import Path
import re
root = Path('reports/2025-10-cli-flags/phase_l')
py_lines = Path(root, 'rot_vector/trace_py_rot_vector.log').read_text().splitlines()
c_lines = Path(root, 'scaling_audit/c_trace_scaling.log').read_text().splitlines()
pattern = re.compile(r'TRACE_(?P<src>C|PY): (?P<key>rot_[abc](?:_star)?_angstroms|rot_[abc]_star_A_inv) (?P<x>-?\S+) (?P<y>-?\S+) (?P<z>-?\S+)')
def extract(lines, prefix):
    out = {}
    for line in lines:
        m = pattern.match(line)
        if m and m.group('src') == prefix:
            out[m.group('key')] = [float(m.group('x')), float(m.group('y')), float(m.group('z'))]
    return out
py = extract(py_lines, 'PY')
c = extract(c_lines, 'C')
rows = [
    ('rot_a_angstroms', 'Angstrom'),
    ('rot_b_angstroms', 'Angstrom'),
    ('rot_c_angstroms', 'Angstrom'),
    ('rot_a_star_A_inv', 'Angstrom^-1'),
    ('rot_b_star_A_inv', 'Angstrom^-1'),
    ('rot_c_star_A_inv', 'Angstrom^-1')
]
lines = ['| Vector | Units | C | PyTorch | Δ (Py-C) |', '| --- | --- | --- | --- | --- |']
for key, units in rows:
    cx, cy, cz = c.get(key, (float('nan'),)*3)
    px, pyv, pz = py.get(key, (float('nan'),)*3)
    dx, dy, dz = (px-cx, pyv-cy, pz-cz)
    lines.append(f"| {key} | {units} | ({cx:.9f}, {cy:.9f}, {cz:.9f}) | ({px:.9f}, {pyv:.9f}, {pz:.9f}) | ({dx:.3e}, {dy:.3e}, {dz:.3e}) |")
Path(root, 'rot_vector/rot_vector_comparison.md').write_text('\n'.join(lines) + '\n')
PY`
- Hypothesis log: Summarize takeaways (δrot components, suspected causes, follow-up probes) in `reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md`.
- Record findings + commands in docs/fix_plan.md Attempts once artifacts exist.
Pitfalls To Avoid:
- Do not edit production simulator code during this evidence pass.
- Keep harness commands on CPU/float32 unless explicitly testing GPU; avoid accidental dtype/device drift.
- Preserve existing trace artifacts—write new outputs under `rot_vector/` rather than overwriting `scaling_audit/` logs.
- Respect Protected Assets rule: never move/delete files listed in docs/index.md.
- Maintain vectorization guardrails—no new Python loops or `.item()` usage in production paths if later edits are required.
- Capture commands verbatim in Attempts history; no paraphrasing.
- Ensure all temporary scripts/snippets are stored under `reports/…/` (not at repo root) and kept ASCII.
- Run `pytest --collect-only` before leaving the loop to confirm the selector remains valid.
- Avoid committing artifacts until supervisor review; keep git status clean apart from expected report/doc updates.
- Follow trace schema from docs/debugging/debugging.md when adding new trace lines.
Pointers:
- plans/active/cli-noise-pix0/plan.md:264-267 — Phase L3f/L3g task definitions and success criteria.
- docs/fix_plan.md:450-463 — CLI-FLAGS-003 next actions and evidence expectations.
- reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log — C reference rot vectors & lattice factors.
- reports/2025-10-cli-flags/phase_l/per_phi/trace_py_scaling_20251119_per_phi.json — PyTorch per-φ reference for context.
Next Up: 1) If rotation vectors align, draft `rot_vector/analysis.md` conclusions and update docs/fix_plan.md; 2) Prepare code-edit plan for the identified rotation discrepancy (Phase L3g follow-up).
