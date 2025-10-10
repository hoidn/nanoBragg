Summary: Capture simulator-side F_latt taps so we can explain the 32× intensity gap before repeating ROI parity.
Mode: Parity
Focus: docs/fix_plan.md [VECTOR-PARITY-001] Phase D4 – Diagnose simulator F_latt regression
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-parity/phase_d/$STAMP/trace_ref/, reports/2026-01-vectorization-parity/phase_d/$STAMP/simulator_f_latt.log, reports/2026-01-vectorization-parity/phase_d/$STAMP/simulator_f_latt.md
Do Now: docs/fix_plan.md [VECTOR-PARITY-001] Phase D4 — run NB_TRACE_SIM_F_LATT=reports/2026-01-vectorization-parity/phase_d/$STAMP/simulator_f_latt.log KMP_DUPLICATE_LIB_OK=TRUE python - <<'PY' (script below) to regenerate the simulator pixel probe once instrumentation is in place (set STAMP first); include summary notes in simulator_f_latt.md
If Blocked: If instrumentation cannot be added safely, capture the existing simulator output and log the limitation in docs/fix_plan.md Attempts History with proposed follow-up commands.
Priorities & Rationale:
- Resolve the D3 partial noted in docs/fix_plan.md:37-55 so parity progress resumes.
- Follow plans/active/vectorization-parity-regression.md:60-64 guidance for Phase D4 instrumentation.
- Align taps with specs/spec-a-core.md:221-242 to ensure recorded F_latt uses Na×Nb×Nc scaling.
- Preserve existing trace helper flow from scripts/debug_pixel_trace.py (reports/2026-01-vectorization-parity/phase_d/20251010T071935Z/PHASE_D3_SUMMARY.md) while adding simulator probes.
How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ)
- KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --pixel 1792 2048 --tag trace_ref --out-dir reports/2026-01-vectorization-parity/phase_d/$STAMP/trace_ref
- NB_TRACE_SIM_F_LATT=reports/2026-01-vectorization-parity/phase_d/$STAMP/simulator_f_latt.log KMP_DUPLICATE_LIB_OK=TRUE python - <<'PY'
import torch, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'src'))
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention, DetectorPivot
crystal_config = CrystalConfig(cell_a=100.0, cell_b=100.0, cell_c=100.0,
    cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
    N_cells=(5, 5, 5), default_F=100.0,
    phi_start_deg=0.0, osc_range_deg=0.0, phi_steps=1,
    mosaic_spread_deg=0.0, mosaic_domains=1)
detector_config = DetectorConfig(spixels=4096, fpixels=4096,
    pixel_size_mm=0.05, distance_mm=500.0,
    detector_convention=DetectorConvention.MOSFLM,
    detector_pivot=DetectorPivot.BEAM,
    detector_rotx_deg=0.0, detector_roty_deg=0.0,
    detector_rotz_deg=0.0, detector_twotheta_deg=0.0)
beam_config = BeamConfig(wavelength_A=0.5, polarization_factor=0.0,
    flux=0.0, exposure=1.0, beamsize_mm=0.1)
dtype = torch.float64
device = torch.device('cpu')
crystal = Crystal(crystal_config, dtype=dtype, device=device)
detector = Detector(detector_config, dtype=dtype, device=device)
simulator = Simulator(crystal, detector, crystal_config, beam_config, dtype=dtype, device=device)
image = simulator.run()
val = image[1792, 2048].item()
print(f"Simulator pixel (1792,2048): {val:.15e}")
PY
- Summarise key taps (F_latt_a/b/c, F_latt, F_cell, accumulator, final intensity) into reports/2026-01-vectorization-parity/phase_d/$STAMP/simulator_f_latt.md with notes comparing against the trace helper output.
Pitfalls To Avoid:
- Do not modify production physics without env-guarded logging; no permanent print statements.
- Keep device/dtype neutrality when adding taps (use existing tensor device/dtype).
- Preserve Protected Assets listed in docs/index.md; no file moves/renames.
- Avoid rerunning full pytest; evidence loop only (no broad suites).
- Ensure env var NB_TRACE_SIM_F_LATT is unset after run to prevent noisy traces in later tests.
- Reuse scripts/debug_pixel_trace.py flows; do not fork a new untracked script unless documented.
- Maintain vectorization—no per-source Python loops in instrumentation.
- Capture commands.txt alongside artifacts per testing_strategy.md §1.5.
Pointers:
- docs/fix_plan.md:19-55
- plans/active/vectorization-parity-regression.md:12-65
- reports/2026-01-vectorization-parity/phase_d/20251010T071935Z/PHASE_D3_SUMMARY.md
- specs/spec-a-core.md:221-242
- scripts/debug_pixel_trace.py:1-200
Next Up: Prep simulator parity summary + plan D5 smoke rerun once taps align.
