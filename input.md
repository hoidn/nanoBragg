Summary: Capture fresh TC-D1 PyTorch evidence (stdout + simulator diagnostics) to unblock SOURCE-WEIGHT-001 normalization analysis.
Mode: Parity
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: main
Mapped tests: none — evidence-only
Artifacts: reports/2025-11-source-weights/phase_e/<STAMP>/
Do Now: [SOURCE-WEIGHT-001] Phase E2 evidence refresh — `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `mkdir -p reports/2025-11-source-weights/phase_e/$STAMP`; run `KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -mat A.mat -sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt -default_F 100 -hdivsteps 0 -vdivsteps 0 -dispsteps 1 -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -floatfile reports/2025-11-source-weights/phase_e/$STAMP/py_tc_d1.bin | tee reports/2025-11-source-weights/phase_e/$STAMP/py_stdout.log`; then append simulator diagnostics with `python - <<'PY' > reports/2025-11-source-weights/phase_e/$STAMP/simulator_diagnostics.txt
import torch
from nanobrag_torch.__main__ import create_parser, parse_and_validate_args
from nanobrag_torch.config import DetectorConfig, CrystalConfig, BeamConfig, DetectorConvention
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.io.source import read_sourcefile
from nanobrag_torch.utils.units import angstroms_to_meters
parser = create_parser()
args = parser.parse_args(['-mat','A.mat','-sourcefile','reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt','-default_F','100','-hdivsteps','0','-vdivsteps','0','-dispsteps','1','-distance','231.274660','-lambda','0.9768','-pixel','0.172','-detpixels_x','256','-detpixels_y','256','-oversample','1','-nonoise','-nointerpolate'])
config = parse_and_validate_args(args)
crystal_config = CrystalConfig(cell_a=config['cell_params'][0], cell_b=config['cell_params'][1], cell_c=config['cell_params'][2], cell_alpha=config['cell_params'][3], cell_beta=config['cell_params'][4], cell_gamma=config['cell_params'][5], N_cells=(config.get('Na',1), config.get('Nb',1), config.get('Nc',1)), phi_start_deg=config.get('phi_deg',0.0), osc_range_deg=config.get('osc_deg',0.0), phi_steps=config.get('phi_steps',1), default_F=config.get('default_F',0.0))
detector_config = DetectorConfig(distance_mm=config.get('distance_mm',100.0), pixel_size_mm=config.get('pixel_size_mm',0.1), spixels=config.get('spixels',1024), fpixels=config.get('fpixels',1024), detector_convention=DetectorConvention[config.get('convention','MOSFLM')], oversample=config.get('oversample',-1))
beam_config = BeamConfig(wavelength_A=config.get('wavelength_A',1.0))
if 'sourcefile' in config:
    wavelength_m = angstroms_to_meters(config.get('wavelength_A',1.0))
    beam_direction = torch.tensor([1.0,0.0,0.0], dtype=torch.float32) if detector_config.detector_convention == DetectorConvention.MOSFLM else torch.tensor([0.0,0.0,1.0], dtype=torch.float32)
    dirs, weights, lambdas = read_sourcefile(config['sourcefile'], default_wavelength_m=wavelength_m, default_source_distance_m=10.0, beam_direction=beam_direction)
    beam_config.source_directions = dirs
    beam_config.source_weights = weights
    beam_config.source_wavelengths = lambdas
crystal = Crystal(crystal_config)
detector = Detector(detector_config)
sim = Simulator(crystal=crystal, detector=detector, crystal_config=crystal_config, beam_config=beam_config, device=torch.device('cpu'), dtype=torch.float32)
n_sources = len(sim._source_directions) if sim._source_directions is not None else 1
phi_steps = sim.crystal.config.phi_steps
mosaic_domains = sim.crystal.config.mosaic_domains
oversample = detector_config.oversample
steps = n_sources * phi_steps * mosaic_domains * oversample * oversample
print(f"n_sources: {n_sources}")
print(f"phi_steps: {phi_steps}")
print(f"mosaic_domains: {mosaic_domains}")
print(f"oversample: {oversample}")
print(f"steps: {steps}")
print(f"fluence: {sim.fluence.item():.6e}")
PY`
If Blocked: If CLI or diagnostics fail, log the full command output to `reports/2025-11-source-weights/phase_e/$STAMP/attempt.log`, note the failure in docs/fix_plan.md Attempts for SOURCE-WEIGHT-001, and stop without editing simulator code.
Priorities & Rationale:
- docs/fix_plan.md:4026 — refreshed Next Actions demand new PyTorch-only evidence before parity reruns.
- plans/active/source-weight-normalization.md:11 — status snapshot shows normalization gap after guard success.
- specs/spec-a-core.md:147 — spec mandates weights are read but ignored; diagnostics confirm inputs follow this rule.
- reports/2025-11-source-weights/phase_e/20251009T115838Z/summary.md — prior failure metrics (140–300×) to contextualize new run.
- docs/development/testing_strategy.md:56 — requires authoritative commands and artifact capture for evidence loops.
How-To Map:
- Export timestamp: `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`.
- Create folder: `mkdir -p reports/2025-11-source-weights/phase_e/$STAMP`.
- Run PyTorch CLI command above; tee stdout to `py_stdout.log` and leave `.bin` under same folder.
- Capture simulator diagnostics via provided Python snippet; verify output lists `n_sources`, `steps`, `fluence`.
- After commands, write `commands.txt` in the same folder documenting exact commands and environment vars.
Pitfalls To Avoid:
- Do not edit production code or tests this loop — evidence only.
- Keep `KMP_DUPLICATE_LIB_OK=TRUE`; missing env var will crash torch on some platforms.
- Maintain device/dtype neutrality; no `.cpu()`/.cuda()` shims in diagnostics scripts.
- Preserve Protected Assets (docs/index.md listings: loop.sh, supervisor.sh, input.md, etc.).
- Do not delete prior reports; add new timestamped folder alongside existing ones.
- No full pytest runs; this loop captures CLI output only.
- Avoid writing artifacts outside `reports/2025-11-source-weights/phase_e/`.
- Ensure `STAMP` is UTC to keep chronological ordering.
- Verify fixture path (`reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt`) exists before running.
- If C binary is absent, do not attempt parity rerun yet; that belongs to Phase E3.
Pointers:
- docs/fix_plan.md:4026
- plans/active/source-weight-normalization.md:11
- specs/spec-a-core.md:147
- reports/2025-11-source-weights/phase_e/20251009T115838Z/summary.md
- docs/development/testing_strategy.md:56
Next Up: Rebuild `golden_suite_generator/nanoBragg` and execute TC-D1/TC-D3 parity captures once fresh PyTorch diagnostics are archived.
