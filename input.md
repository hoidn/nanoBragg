Summary: Capture fresh TC-D1/TC-D3 weighted-source parity evidence after the lambda override to unblock vectorization work.
Mode: Parity
Focus: SOURCE-WEIGHT-001 / Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_at_src_003.py; KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_003.py; NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeightsDivergence
Artifacts: reports/2025-11-source-weights/phase_e/<STAMP>/{commands.txt,collect.log,pytest_at_src_003.log,pytest_tc_d_collect.log,py_tc_d1.bin,c_tc_d1.bin,py_tc_d3.bin,c_tc_d3.bin,py_stdout_tc_d1.log,c_stdout_tc_d1.log,py_stdout_tc_d3.log,c_stdout_tc_d3.log,simulator_diagnostics.txt,metrics.json,correlation.txt,sum_ratio.txt,env.json}
Do Now: [SOURCE-WEIGHT-001] export KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md; STAMP=$(date -u +%Y%m%dT%H%M%SZ); OUT=reports/2025-11-source-weights/phase_e/$STAMP; FIXTURE=reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt; mkdir -p "$OUT" && pytest --collect-only -q tests/test_at_src_003.py | tee "$OUT/collect.log" && KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_003.py | tee "$OUT/pytest_at_src_003.log" && NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee "$OUT/pytest_tc_d_collect.log" && {
  echo "# $(date -u) SOURCE-WEIGHT-001 parity run"; 
  echo "export KMP_DUPLICATE_LIB_OK=TRUE"; 
  echo "export NB_RUN_PARALLEL=1"; 
} > "$OUT/commands.txt" && {
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
import json
import pathlib
import numpy as np
import torch
from nanobrag_torch.__main__ import create_parser, parse_and_validate_args
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.io.source import read_sourcefile
from nanobrag_torch.utils.units import angstroms_to_meters

out = pathlib.Path("$OUT")
fixture = pathlib.Path("$FIXTURE").resolve()

cases = {
    "TC-D1": ['-mat','A.mat','-sourcefile',str(fixture),'-default_F','100','-hdivsteps','0','-vdivsteps','0','-dispsteps','1','-distance','231.274660','-lambda','0.9768','-pixel','0.172','-detpixels_x','256','-detpixels_y','256','-oversample','1','-nonoise','-nointerpolate'],
    "TC-D3": ['-mat','A.mat','-default_F','100','-hdivrange','0.5','-hdivsteps','3','-distance','231.274660','-lambda','0.9768','-pixel','0.172','-detpixels_x','256','-detpixels_y','256','-oversample','1','-nonoise','-nointerpolate'],
}

with open(out / "simulator_diagnostics.txt", "w") as diag:
    for name, argv in cases.items():
        parser = create_parser()
        args = parser.parse_args(argv)
        config = parse_and_validate_args(args)

        crystal_config = CrystalConfig(
            cell_a=config['cell_params'][0],
            cell_b=config['cell_params'][1],
            cell_c=config['cell_params'][2],
            cell_alpha=config['cell_params'][3],
            cell_beta=config['cell_params'][4],
            cell_gamma=config['cell_params'][5],
            N_cells=(config.get('Na',1), config.get('Nb',1), config.get('Nc',1)),
            phi_start_deg=config.get('phi_deg',0.0),
            osc_range_deg=config.get('osc_deg',0.0),
            phi_steps=config.get('phi_steps',1),
            default_F=config.get('default_F',0.0)
        )

        detector_config = DetectorConfig(
            distance_mm=config.get('distance_mm',100.0),
            pixel_size_mm=config.get('pixel_size_mm',0.1),
            spixels=config.get('spixels',1024),
            fpixels=config.get('fpixels',1024),
            detector_convention=DetectorConvention[config.get('convention','MOSFLM')],
            oversample=config.get('oversample',-1)
        )

        beam_config = BeamConfig(wavelength_A=config.get('wavelength_A',1.0))

        if 'sourcefile' in config:
            wavelength_m = angstroms_to_meters(config.get('wavelength_A',1.0))
            beam_direction = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float32) if detector_config.detector_convention == DetectorConvention.MOSFLM else torch.tensor([0.0, 0.0, 1.0], dtype=torch.float32)
            dirs, weights, lambdas = read_sourcefile(
                config['sourcefile'],
                default_wavelength_m=wavelength_m,
                default_source_distance_m=10.0,
                beam_direction=beam_direction
            )
            beam_config.source_directions = dirs
            beam_config.source_weights = weights
            beam_config.source_wavelengths = lambdas

        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        sim = Simulator(
            crystal=crystal,
            detector=detector,
            crystal_config=crystal_config,
            beam_config=beam_config,
            device=torch.device('cpu'),
            dtype=torch.float32
        )

        n_sources = len(sim._source_directions) if sim._source_directions is not None else 1
        phi_steps = sim.crystal.config.phi_steps
        mosaic_domains = sim.crystal.config.mosaic_domains
        oversample = detector_config.oversample
        steps = n_sources * phi_steps * mosaic_domains * oversample * oversample

        diag.write(f"[{name}]\n")
        diag.write(f"n_sources: {n_sources}\n")
        diag.write(f"phi_steps: {phi_steps}\n")
        diag.write(f"mosaic_domains: {mosaic_domains}\n")
        diag.write(f"oversample: {oversample}\n")
        diag.write(f"steps: {steps}\n")
        diag.write(f"fluence: {sim.fluence.item():.6e}\n\n")

metrics = {}
for case in ("tc_d1", "tc_d3"):
    py = np.fromfile(out / f"py_{case}.bin", dtype=np.float32)
    c = np.fromfile(out / f"c_{case}.bin", dtype=np.float32)
    corr = float(np.corrcoef(py, c)[0, 1])
    ratio = float(py.sum() / c.sum())
    metrics[case] = {"correlation": corr, "sum_ratio": ratio}

(out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
(out / "correlation.txt").write_text("\n".join(f"{k}:{v['correlation']:.6f}" for k, v in metrics.items()) + "\n")
(out / "sum_ratio.txt").write_text("\n".join(f"{k}:{v['sum_ratio']:.6f}" for k, v in metrics.items()) + "\n")
PY
If Blocked: Capture whatever bins/logs exist under $OUT/attempts/ with a README describing the failure, then log the blocker (metrics, stderr excerpts) in docs/fix_plan.md Attempts before ending the loop.
Priorities & Rationale:
- docs/fix_plan.md:4046 keeps SOURCE-WEIGHT-001 Phase E focused on parity metrics before dependent plans unblock.
- plans/active/source-weight-normalization.md:6 confirms Phase A-D complete; Phase E now hinges on this parity rerun.
- plans/active/vectorization.md:24 lists Phase A1 as waiting on these metrics before profiling restarts.
- reports/2025-11-source-weights/phase_d/20251009T104310Z/commands.txt documents the authoritative reproduction commands used here.
- docs/development/testing_strategy.md:24 requires targeted pytest selectors and timestamped evidence folders.
How-To Map:
- Ensure `$NB_C_BIN` resolves to `./golden_suite_generator/nanoBragg`; rebuild there if missing instead of switching to the frozen binary silently.
- Append every executed command to `$OUT/commands.txt` and capture stdout/stderr via `tee` exactly once per command.
- After the metrics script, capture environment details via:
```
python - <<'PY'
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
```
- Verify thresholds: success requires both TC-D1 and TC-D3 to satisfy corr ≥ 0.999 and |sum_ratio−1| ≤ 1e-3. If either fails, document metrics in fix_plan attempts and stop.
- Once metrics pass, update docs/fix_plan.md `[SOURCE-WEIGHT-001]` Attempts with numbers + artifact paths, flip Phase E rows in the plan to [D], and log an unblock note in galph_memory (reference VECTOR-GAPS-002 Phase B1).
Pitfalls To Avoid:
- Do not alter fixture geometry or CLI parameters; parity thresholds assume the recorded TC-D1/TC-D3 setup.
- Keep outputs confined to `$OUT`; preserve earlier evidence folders untouched.
- Never run without `NB_RUN_PARALLEL=1`; parity tests skip otherwise.
- Capture stderr fully—avoid grepping that drops warning content.
- Remain on CPU; CUDA runs are out-of-scope for this parity gate.
- Use a fresh STAMP for each attempt; no overwriting of prior runs.
- If metrics miss thresholds, document and halt rather than adjusting tolerances.
Pointers: docs/fix_plan.md:4046; plans/active/source-weight-normalization.md:1; plans/active/vectorization.md:24; docs/development/testing_strategy.md:24; reports/2025-11-source-weights/phase_d/20251009T104310Z/commands.txt
Next Up: 1. Update docs/architecture/pytorch_design.md sources section once parity bundle succeeds; 2. Trigger VECTOR-GAPS-002 Phase B profiler capture with the new evidence.
