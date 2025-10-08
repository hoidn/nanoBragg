Summary: Diagnose the φ₀ lattice-factor mismatch by refreshing the scaling trace and reproducing sincg contributions.
Mode: Parity
Focus: CLI-FLAGS-003 Phase M2 lattice investigation
Branch: feature/spec-based-2
Mapped tests:
- pytest --collect-only tests/test_cli_scaling_phi0.py::TestScalingParity::test_I_before_scaling_matches_c
- pytest --collect-only tests/test_phi_carryover_mode.py
Artifacts:
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/commands.txt
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/trace_py_scaling.log
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/trace_harness.log
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/compare_scaling_traces.stdout
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/scaling_validation_summary.md
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/metrics.json
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/manual_sincg.md
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/lattice_hypotheses.md
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/run_metadata.json
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/sha256.txt
- plans/active/cli-noise-pix0/plan.md (M2 checklist updates)
- docs/fix_plan.md (Attempt log)
Do Now: CLI-FLAGS-003 Phase M2a — `ts=$(date -u +%Y%m%dT%H%M%SZ); RUN_DIR=reports/2025-10-cli-flags/phase_l/scaling_validation/$ts; mkdir -p "$RUN_DIR"; {
  git rev-parse HEAD > "$RUN_DIR/git_sha.txt";
  git status -sb > "$RUN_DIR/git_status.txt";
  printf '# Commands\\n' > "$RUN_DIR/commands.txt";
  printf 'git rev-parse HEAD\\n' >> "$RUN_DIR/commands.txt";
  git rev-parse HEAD >> "$RUN_DIR/commands.txt";
  printf '\\nPYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --phi-mode c-parity --pixel 685 1039 --device cpu --dtype float64 --out %s/trace_py_scaling.log\\n' "$RUN_DIR" >> "$RUN_DIR/commands.txt";
  RUN_DIR="$RUN_DIR" PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --phi-mode c-parity --pixel 685 1039 --device cpu --dtype float64 --out "$RUN_DIR/trace_py_scaling.log" |& tee "$RUN_DIR/trace_harness.log";
  printf '\\nPYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py %s/trace_py_scaling.log --out %s/scaling_validation_summary.md\\n' "$RUN_DIR" "$RUN_DIR" >> "$RUN_DIR/commands.txt";
  RUN_DIR="$RUN_DIR" PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py "$RUN_DIR/trace_py_scaling.log" --out "$RUN_DIR/scaling_validation_summary.md" |& tee "$RUN_DIR/compare_scaling_traces.stdout";
  printf '\\nRUN_DIR=%s python - <<\'PY\' > %s/manual_sincg.md\\n' "$RUN_DIR" "$RUN_DIR" >> "$RUN_DIR/commands.txt";
  RUN_DIR="$RUN_DIR" python - <<'PY' > "$RUN_DIR/manual_sincg.md"
import math
import os
from pathlib import Path

def parse_trace(path: Path, prefix: str):
    data = {}
    if not path.exists():
        return data
    with path.open() as fh:
        for line in fh:
            if not line.startswith(prefix):
                continue
            parts = line.strip().split()
            if len(parts) < 3:
                continue
            key = parts[1]
            if key == 'hkl_frac' and len(parts) >= 5:
                data['h_frac'] = float(parts[2])
                data['k_frac'] = float(parts[3])
                data['l_frac'] = float(parts[4])
            elif key == 'hkl_rounded' and len(parts) >= 5:
                data['h_round'] = int(parts[2])
                data['k_round'] = int(parts[3])
                data['l_round'] = int(parts[4])
            elif key in {'F_latt', 'F_latt_a', 'F_latt_b', 'F_latt_c'}:
                data[key] = float(parts[2])
    return data

def sincg(x: float, N: int) -> float:
    if abs(x) < 1e-12:
        return float(N)
    return math.sin(N * x) / math.sin(x)

def fmt(val: float) -> str:
    if val is None:
        return 'nan'
    return f"{val:.9f}"

run_dir = Path(os.environ['RUN_DIR'])
py_trace = run_dir / 'trace_py_scaling.log'
c_trace = Path('reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log')
py_vals = parse_trace(py_trace, 'TRACE_PY:')
c_vals = parse_trace(c_trace, 'TRACE_C:')

Na, Nb, Nc = 36, 47, 29
rows = []
product_full = 1.0
product_local = 1.0
axes = (
    ('a', py_vals.get('h_frac'), py_vals.get('h_round'), Na),
    ('b', py_vals.get('k_frac'), py_vals.get('k_round'), Nb),
    ('c', py_vals.get('l_frac'), py_vals.get('l_round'), Nc),
)
for axis, frac, rounded, N in axes:
    if frac is None or rounded is None:
        continue
    full = sincg(math.pi * frac, N)
    local = sincg(math.pi * (frac - rounded), N)
    product_full *= full
    product_local *= local
    rows.append({
        'axis': axis,
        'frac': frac,
        'rounded': rounded,
        'N': N,
        'sincg_pi_frac': full,
        'sincg_pi_delta': local,
        'c_value': c_vals.get(f'F_latt_{axis}'),
        'py_value': py_vals.get(f'F_latt_{axis}')
    })

F_latt_c = c_vals.get('F_latt')
F_latt_py = py_vals.get('F_latt')
summary_lines = [
    '# Manual sincg reproduction',
    '',
    f'- Run directory: {run_dir}',
    f'- Py trace: {py_trace}',
    f'- C trace: {c_trace.resolve()}',
    f'- Na, Nb, Nc = ({Na}, {Nb}, {Nc})',
    ''
]
summary_lines.append('| Axis | frac | rounded | sincg(π·frac) | sincg(π·(frac-h0)) | C trace | Py trace |')
summary_lines.append('| --- | --- | --- | --- | --- | --- | --- |')
for row in rows:
    summary_lines.append(
        f"| {row['axis']} | {row['frac']:.9f} | {row['rounded']} | {row['sincg_pi_frac']:.9f} | "
        f"{row['sincg_pi_delta']:.9f} | {fmt(row['c_value'])} | {fmt(row['py_value'])} |")
summary_lines.extend([
    '',
    f'- Product using sincg(π·frac): {product_full:.9f}',
    f'- Product using sincg(π·(frac-h0)): {product_local:.9f}',
    f'- C trace F_latt: {fmt(F_latt_c)}',
    f'- Py trace F_latt: {fmt(F_latt_py)}',
    '',
    'Interpretation:',
    '- Compare the C trace columns to identify which sincg flavour matches.',
    '- Use these values when drafting `lattice_hypotheses.md`.'
])
print('\n'.join(summary_lines))
PY
  printf '\\nPYTHONPATH=src pytest --collect-only tests/test_cli_scaling_phi0.py::TestScalingParity::test_I_before_scaling_matches_c >> %s/pytest_collect.log\\n' "$RUN_DIR" >> "$RUN_DIR/commands.txt";
  PYTHONPATH=src pytest --collect-only tests/test_cli_scaling_phi0.py::TestScalingParity::test_I_before_scaling_matches_c |& tee -a "$RUN_DIR/pytest_collect.log";
  printf '\\nPYTHONPATH=src pytest --collect-only tests/test_phi_carryover_mode.py >> %s/pytest_collect.log\\n' "$RUN_DIR" >> "$RUN_DIR/commands.txt";
  PYTHONPATH=src pytest --collect-only tests/test_phi_carryover_mode.py |& tee -a "$RUN_DIR/pytest_collect.log";
  printf '\\nls -1 %s | tee %s/dir_listing.txt\\n' "$RUN_DIR" "$RUN_DIR" >> "$RUN_DIR/commands.txt";
  ls -1 "$RUN_DIR" | tee "$RUN_DIR/dir_listing.txt" >/dev/null;
  printf '\\n(cd %s && shasum -a 256 * > sha256.txt)\\n' "$RUN_DIR" >> "$RUN_DIR/commands.txt";
  (cd "$RUN_DIR" && shasum -a 256 * > sha256.txt)
}``
If Blocked: If `compare_scaling_traces.py` or the manual sincg script fails, capture stdout/err plus exit codes in `$RUN_DIR/blocked.md`, leave plan checklist untouched, and halt for review.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:21 — Status snapshot now points at 20251008T072513Z baseline; next step is lattice analysis.
- plans/active/cli-noise-pix0/plan.md:96 — M2 checklist (M2a–M2c) demands refreshed traces and sincg reproduction before code changes.
- docs/fix_plan.md:455 — Next Actions emphasise Phase M2 lattice investigation using existing instrumentation.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T072513Z/validation_report.md — Confirms script stability yet highlights the 0.13% `F_latt` residual to analyse.
- docs/bugs/verified_c_bugs.md:166 — Context for φ carryover bug; ensures spec-compliant path stays intact while investigating parity mode.
How-To Map:
1. Allocate a new UTC timestamped `RUN_DIR`; log git SHA/status and every executed command into `commands.txt` for reproducibility.
2. Run `trace_harness.py` (CPU, float64, `--phi-mode c-parity`) to capture fresh PyTorch trace data; tee output to `trace_harness.log`.
3. Invoke `compare_scaling_traces.py` immediately afterward; retain stdout, exit status, and generated `metrics.json`/`run_metadata.json` alongside the markdown summary.
4. Use the embedded Python script to compute both sincg flavours (π·frac vs π·(frac−h0)) and write the comparison table to `manual_sincg.md`.
5. After reviewing `manual_sincg.md`, draft `lattice_hypotheses.md` with bullet-point hypotheses, references to `nanoBragg.c` lines 2604–3278, and next diagnostic steps (this is M2c).
6. Run the collect-only pytest selectors to document test availability; append outputs to `pytest_collect.log` in the run directory.
7. Update plan checklist states (M2a–M2c), append a docs/fix_plan Attempt (include timestamp, key deltas, hypotheses summary), and refresh SHA256 hashes.
Pitfalls To Avoid:
- Do not reuse the 20251008 artifacts; every loop needs a fresh timestamp.
- Keep `KMP_DUPLICATE_LIB_OK=TRUE` and `PYTHONPATH=src` on every Python invocation.
- Remain in evidence mode—no simulator/crystal edits until hypotheses are logged.
- Ensure the manual sincg table contains numeric values (no TODO placeholders) and explicitly compares against C trace numbers.
- Preserve Protected Assets (`input.md`, `docs/index.md`, `loop.sh`, `supervisor.sh`).
- Avoid running full pytest suites; only the two collect-only commands listed above.
- Record SHA256 hashes after all artifacts exist; rerun if new files are added later.
- If sincg computation yields NaN/inf, stop and log rather than patching the script ad hoc.
- Maintain device/dtype neutrality in any temporary analysis code (no hard-coded `.cpu()` conversions).
Pointers:
- plans/active/cli-noise-pix0/plan.md:17
- plans/active/cli-noise-pix0/plan.md:96
- docs/fix_plan.md:455
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T072513Z/validation_report.md
- scripts/validation/compare_scaling_traces.py:1
Next Up: After M2a–M2c artifacts exist, prepare targeted pytest scaffolding (`test_I_before_scaling_matches_c`) before implementing the lattice fix.
