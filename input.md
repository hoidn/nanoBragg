Summary: Capture TC-D1/TC-D3 weighted-source parity evidence (metrics + diagnostics) so SOURCE-WEIGHT-001 Phase E can unblock vectorization.
Mode: Parity
Focus: SOURCE-WEIGHT-001 / Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_at_src_003.py; KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_003.py; NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeightsDivergence
Artifacts: reports/2025-11-source-weights/phase_e/<STAMP>/{commands.txt,collect.log,pytest_at_src_003.log,pytest_tc_d_collect.log,py_tc_d1.bin,c_tc_d1.bin,py_tc_d3.bin,c_tc_d3.bin,py_stdout_tc_d1.log,c_stdout_tc_d1.log,py_stdout_tc_d3.log,c_stdout_tc_d3.log,metrics.json,diagnostics.json,simulator_diagnostics.txt,correlation.txt,sum_ratio.txt,env.json}
Do Now: [SOURCE-WEIGHT-001] export KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md; STAMP=$(date -u +%Y%m%dT%H%M%SZ); OUT=reports/2025-11-source-weights/phase_e/$STAMP; FIXTURE=reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt; mkdir -p "$OUT" && pytest --collect-only -q tests/test_at_src_003.py | tee "$OUT/collect.log" && KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_003.py | tee "$OUT/pytest_at_src_003.log" && NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee "$OUT/pytest_tc_d_collect.log" && {
  {
    echo "# $(date -u) SOURCE-WEIGHT-001 parity run";
    echo "export KMP_DUPLICATE_LIB_OK=TRUE";
    echo "export NB_RUN_PARALLEL=1";
    echo "export NB_C_BIN=$NB_C_BIN";
  } > "$OUT/commands.txt";
  cmd_py_d1=("python" "-m" "nanobrag_torch" -mat A.mat -sourcefile "$FIXTURE" -default_F 100 -hdivsteps 0 -vdivsteps 0 -dispsteps 1 -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -floatfile "$OUT/py_tc_d1.bin");
  printf '%s\n' "${cmd_py_d1[@]}" >> "$OUT/commands.txt";
  "${cmd_py_d1[@]}" | tee "$OUT/py_stdout_tc_d1.log";
  cmd_c_d1=("$NB_C_BIN" -mat A.mat -sourcefile "$FIXTURE" -default_F 100 -hdivsteps 0 -vdivsteps 0 -dispsteps 1 -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -floatfile "$OUT/c_tc_d1.bin");
  printf '%s\n' "${cmd_c_d1[@]}" >> "$OUT/commands.txt";
  NB_RUN_PARALLEL=1 "${cmd_c_d1[@]}" | tee "$OUT/c_stdout_tc_d1.log";
  cmd_py_d3=("python" "-m" "nanobrag_torch" -mat A.mat -default_F 100 -hdivrange 0.5 -hdivsteps 3 -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -floatfile "$OUT/py_tc_d3.bin");
  printf '%s\n' "${cmd_py_d3[@]}" >> "$OUT/commands.txt";
  "${cmd_py_d3[@]}" | tee "$OUT/py_stdout_tc_d3.log";
  cmd_c_d3=("$NB_C_BIN" -mat A.mat -default_F 100 -hdivrange 0.5 -hdivsteps 3 -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -floatfile "$OUT/c_tc_d3.bin");
  printf '%s\n' "${cmd_c_d3[@]}" >> "$OUT/commands.txt";
  NB_RUN_PARALLEL=1 "${cmd_c_d3[@]}" | tee "$OUT/c_stdout_tc_d3.log";
} && python - <<'PY'
import json, math, pathlib, numpy as np, torch
from nanobrag_torch.__main__ import create_parser, parse_and_validate_args
from nanobrag_torch.utils.units import angstroms_to_meters
from nanobrag_torch.io.source import read_sourcefile
from nanobrag_torch.utils.auto_selection import auto_select_divergence, auto_select_dispersion, generate_sources_from_divergence_dispersion
from nanobrag_torch.config import BeamConfig

out = pathlib.Path("$OUT")
cases = {
    "TC-D1": {
        "py_bin": out / "py_tc_d1.bin",
        "c_bin": out / "c_tc_d1.bin",
        "argv": ['-mat','A.mat','-sourcefile',str(pathlib.Path("$FIXTURE").resolve()),'-default_F','100','-hdivsteps','0','-vdivsteps','0','-dispsteps','1','-distance','231.274660','-lambda','0.9768','-pixel','0.172','-detpixels_x','256','-detpixels_y','256','-oversample','1','-nonoise','-nointerpolate'],
    },
    "TC-D3": {
        "py_bin": out / "py_tc_d3.bin",
        "c_bin": out / "c_tc_d3.bin",
        "argv": ['-mat','A.mat','-default_F','100','-hdivrange','0.5','-hdivsteps','3','-distance','231.274660','-lambda','0.9768','-pixel','0.172','-detpixels_x','256','-detpixels_y','256','-oversample','1','-nonoise','-nointerpolate'],
    },
}

metrics = {}
diagnostics = {}

if hasattr(read_sourcefile, '_wavelength_warned'):
    delattr(read_sourcefile, '_wavelength_warned')

def load_image(path: pathlib.Path) -> np.ndarray:
    data = np.fromfile(path, dtype=np.float32)
    if data.size == 0:
        raise RuntimeError(f"Empty image: {path}")
    side = int(round(math.sqrt(data.size)))
    if side * side != data.size:
        raise RuntimeError(f"Unexpected pixel count {data.size} in {path}")
    return data.reshape(side, side)

for name, info in cases.items():
    py_img = load_image(info['py_bin'])
    c_img = load_image(info['c_bin'])
    py_sum = float(np.sum(py_img))
    c_sum = float(np.sum(c_img))
    sum_ratio = py_sum / c_sum if c_sum > 0 else float('inf')
    py_flat = py_img.ravel()
    c_flat = c_img.ravel()
    if np.std(py_flat) > 0 and np.std(c_flat) > 0:
        corr = float(np.corrcoef(py_flat, c_flat)[0, 1])
    else:
        corr = 1.0 if np.allclose(py_flat, c_flat) else 0.0
    metrics[name] = {
        "correlation": corr,
        "sum_ratio": sum_ratio,
        "py_sum": py_sum,
        "c_sum": c_sum,
    }

    parser = create_parser()
    args = parser.parse_args(info['argv'])
    config = parse_and_validate_args(args)
    dtype = torch.float32
    device = torch.device(getattr(args, 'device', 'cpu'))
    wavelength_A = config.get('wavelength_A', 1.0)
    wavelength_m = angstroms_to_meters(wavelength_A)
    convention = config.get('convention', 'MOSFLM')
    if convention in ('MOSFLM', 'DENZO'):
        beam_direction = torch.tensor([1.0, 0.0, 0.0], dtype=dtype, device=device)
        polarization_axis = torch.tensor([0.0, 0.0, 1.0], dtype=dtype, device=device)
    else:
        beam_direction = torch.tensor([0.0, 0.0, 1.0], dtype=dtype, device=device)
        polarization_axis = torch.tensor([0.0, 1.0, 0.0], dtype=dtype, device=device)

    if 'sourcefile' in config:
        directions, weights, wavelengths = read_sourcefile(
            pathlib.Path(config['sourcefile']).resolve(),
            default_wavelength_m=wavelength_m,
            beam_direction=beam_direction,
            dtype=dtype,
            device=device,
        )
        n_sources = int(directions.shape[0])
        hdiv_count = vdiv_count = disp_count = None
    else:
        h_params, v_params = auto_select_divergence(
            hdivsteps=config.get('hdivsteps'),
            hdivrange=config.get('hdivrange'),
            hdivstep=config.get('hdivstep'),
            vdivsteps=config.get('vdivsteps'),
            vdivrange=config.get('vdivrange'),
            vdivstep=config.get('vdivstep'),
        )
        disp_params = auto_select_dispersion(
            dispsteps=config.get('dispsteps'),
            dispersion=config.get('dispersion'),
            dispstep=None,
        )
        sources, weights, wavelengths = generate_sources_from_divergence_dispersion(
            hdiv_params=h_params,
            vdiv_params=v_params,
            disp_params=disp_params,
            central_wavelength_m=wavelength_m,
            source_distance_m=10.0,
            beam_direction=beam_direction,
            polarization_axis=polarization_axis,
            round_div=config.get('round_div', True),
            dtype=dtype,
        )
        n_sources = int(sources.shape[0])
        hdiv_count = h_params.count
        vdiv_count = v_params.count
        disp_count = disp_params.count

    phi_steps = int(config.get('phi_steps', 1))
    mosaic_domains = int(config.get('mosaic_domains', 1))
    oversample = int(config.get('oversample', -1))
    if oversample == -1:
        cell_a, cell_b, cell_c, *_ = config['cell_params']
        Na = config.get('Na', 1)
        Nb = config.get('Nb', 1)
        Nc = config.get('Nc', 1)
        xtalsize_max = max(cell_a * Na, cell_b * Nb, cell_c * Nc) * 1e-10
        distance_m = config.get('distance_mm', 100.0) / 1000.0
        pixel_size_m = config.get('pixel_size_mm', 0.1) / 1000.0
        reciprocal_pixel = wavelength_m * distance_m / pixel_size_m
        oversample = max(1, math.ceil(3.0 * xtalsize_max / reciprocal_pixel))
    steps = int(n_sources * phi_steps * mosaic_domains * oversample * oversample)
    fluence = float(config.get('fluence', BeamConfig().fluence))

    diagnostics[name] = {
        "n_sources": n_sources,
        "phi_steps": phi_steps,
        "mosaic_domains": mosaic_domains,
        "oversample": oversample,
        "steps": steps,
        "fluence": fluence,
    }
    if hdiv_count is not None:
        diagnostics[name]["hdiv_count"] = hdiv_count
        diagnostics[name]["vdiv_count"] = vdiv_count
        diagnostics[name]["disp_count"] = disp_count

    print(f"{name}: corr={corr:.9f}, sum_ratio={sum_ratio:.9f}, steps={steps}, n_sources={n_sources}")

with open(out / "metrics.json", "w") as fh:
    json.dump(metrics, fh, indent=2)

with open(out / "diagnostics.json", "w") as fh:
    json.dump(diagnostics, fh, indent=2)

with open(out / "correlation.txt", "w") as fh:
    for name, vals in metrics.items():
        fh.write(f"{name}: {vals['correlation']:.9f}\n")

with open(out / "sum_ratio.txt", "w") as fh:
    for name, vals in metrics.items():
        fh.write(f"{name}: {vals['sum_ratio']:.9f}\n")

with open(out / "simulator_diagnostics.txt", "w") as fh:
    for name, diag in diagnostics.items():
        fh.write(f"{name}\n")
        for key in ("n_sources","phi_steps","mosaic_domains","oversample","steps","fluence","hdiv_count","vdiv_count","disp_count"):
            if key in diag and diag[key] is not None:
                fh.write(f"  {key}: {diag[key]}\n")
        fh.write("\n")
PY
&& python - <<'PY'
import json, os, pathlib, torch
out = pathlib.Path("$OUT")
summary = {
    'NB_C_BIN': os.environ.get('NB_C_BIN'),
    'torch_version': torch.__version__,
    'cuda_available': torch.cuda.is_available(),
    'KMP_DUPLICATE_LIB_OK': os.environ.get('KMP_DUPLICATE_LIB_OK'),
    'NB_RUN_PARALLEL': os.environ.get('NB_RUN_PARALLEL'),
    'AUTHORITATIVE_CMDS_DOC': os.environ.get('AUTHORITATIVE_CMDS_DOC'),
}
with open(out / 'env.json', 'w') as fh:
    json.dump(summary, fh, indent=2)
PY
If Blocked: If NB_C_BIN is missing or commands fail, capture stderr in $OUT/attempt.log, record the failure in docs/fix_plan.md Attempts, and run pytest --collect-only -q to keep discovery proof before stopping.
Priorities & Rationale:
- specs/spec-a-core.md:150-190 — Spec mandates ignoring source weights/wavelengths; parity proof is required to close SOURCE-WEIGHT-001.
- docs/fix_plan.md:4046 — Next Actions demand fresh TC-D1/TC-D3 metrics ≥0.999 corr with |sum_ratio-1| ≤1e-3 before downstream plans unblock.
- plans/active/source-weight-normalization.md — Phase E hinges entirely on this evidence bundle; without it VECTOR-GAPS-002 stays blocked.
- plans/active/vectorization.md:24 — Phase A1 cannot progress until Phase E parity metrics are archived.
- docs/development/testing_strategy.md §1.5 — Requires targeted pytest selectors and timestamped artifact directories (followed via $OUT path).
How-To Map:
- Ensure `NB_C_BIN` points to `./golden_suite_generator/nanoBragg`; rebuild there if the binary is stale rather than switching to the frozen root binary.
- Append every executed command to `$OUT/commands.txt` before running it; use `tee` so stdout/stderr land in both console and logs.
- Verify CLI runs complete with exit code 0; if warnings appear, retain them in the tee’d stdout logs.
- After the Python metrics script runs, inspect its printed summary; thresholds are corr ≥0.999 and |sum_ratio−1| ≤1e-3 for BOTH cases.
- Update docs/fix_plan.md `[SOURCE-WEIGHT-001]` Attempts with metrics + artifact path and flip plan Phase E rows once thresholds are met.
Pitfalls To Avoid:
- Don’t modify fixture inputs or CLI parameters; parity thresholds rely on the canonical TC-D1/TC-D3 setup.
- Do not run without `NB_RUN_PARALLEL=1`; the parity pytest selector enforces this guard.
- Keep all new artifacts under the fresh `$OUT` directory; never overwrite earlier evidence.
- Avoid grepping stdout (which drops warnings); rely on full tee’d logs.
- Do not skip the targeted pytest runs; we need both collection proof and execution logs before CLI calls.
- Resist “quick fixes” if metrics miss thresholds—document the failure and stop for supervisor review.
- Stay on CPU for these runs; CUDA parity is out-of-scope for this gate.
- Leave `reports/` outputs uncommitted; only reference the paths in fix_plan attempts.
- Ensure the Python metrics script finishes (no truncated heredoc); watch for syntax errors before proceeding.
Pointers: docs/fix_plan.md:4046; plans/active/source-weight-normalization.md:1; plans/active/vectorization.md:24; specs/spec-a-core.md:150; docs/development/testing_strategy.md:24
Next Up: 1. Update docs/architecture/pytorch_design.md sources section with the recorded metrics; 2. Trigger VECTOR-GAPS-002 Phase B profiler capture once parity evidence is logged.
