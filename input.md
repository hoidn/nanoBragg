Summary: Capture fresh evidence for the gradient-flow failure so we can diagnose the C19 cluster.
Mode: Parity
Focus: [GRADIENT-FLOW-001] Gradient flow regression
Branch: feature/spec-based-2
Mapped tests: tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation
Artifacts: reports/2026-01-gradient-flow/phase_a/$STAMP/{pytest.log,pytest.xml,gradients.json,summary.md}
Do Now: [GRADIENT-FLOW-001] Phase A1 — env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation --maxfail=1 --durations=25 --tb=short --junitxml reports/2026-01-gradient-flow/phase_a/$STAMP/pytest.xml
If Blocked: Capture the failing stdout/stderr, note the obstacle in summary.md, and stop—do not alter production code.
Priorities & Rationale:
- Plan P1 complete; next step is plan Phase A evidence (plans/active/gradient-flow-regression.md).
- Chunk 03 summary (reports/2026-01-test-suite-triage/phase_o/20251015T043128Z/chunks/chunk_03/summary.md) shows C19 is the sole remaining functional failure.
- arch.md §15 and testing_strategy.md §4.1 mandate CPU + float64 runs with compile disabled for graident checks.
- docs/fix_plan.md Next Action 11 requires fresh artifacts before instrumentation.
How-To Map:
- Export STAMP once: `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and `mkdir -p reports/2026-01-gradient-flow/phase_a/$STAMP/`.
- Run the Do Now command with `| tee reports/2026-01-gradient-flow/phase_a/$STAMP/pytest.log`; capture exit code into `exit_code.txt` (`echo $? > .../exit_code.txt`).
- After pytest, dump gradients:
```
python - <<'PY' > reports/2026-01-gradient-flow/phase_a/$STAMP/gradients.json
import json, os, sys, torch
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("NANOBRAGG_DISABLE_COMPILE", "1")
from nanobrag_torch.config import CrystalConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator

dtype = torch.float64
device = torch.device("cpu")
cell_params = {
    "cell_a": torch.tensor(100.0, dtype=dtype, requires_grad=True),
    "cell_b": torch.tensor(100.0, dtype=dtype, requires_grad=True),
    "cell_c": torch.tensor(100.0, dtype=dtype, requires_grad=True),
    "cell_alpha": torch.tensor(90.0, dtype=dtype, requires_grad=True),
    "cell_beta": torch.tensor(90.0, dtype=dtype, requires_grad=True),
    "cell_gamma": torch.tensor(90.0, dtype=dtype, requires_grad=True),
}
config = CrystalConfig(
    cell_a=cell_params["cell_a"],
    cell_b=cell_params["cell_b"],
    cell_c=cell_params["cell_c"],
    cell_alpha=cell_params["cell_alpha"],
    cell_beta=cell_params["cell_beta"],
    cell_gamma=cell_params["cell_gamma"],
    mosaic_spread_deg=0.0,
    mosaic_domains=1,
    N_cells=(5, 5, 5),
)
crystal = Crystal(config=config, device=device, dtype=dtype)
detector = Detector(device=device, dtype=dtype)
simulator = Simulator(crystal, detector, crystal_config=config, device=device, dtype=dtype)
image = simulator.run()
loss = image.sum()
loss.backward()
report = {
    "loss": float(loss.detach()),
    "gradients": {k: (v.grad.detach().cpu().item() if v.grad is not None else None) for k, v in cell_params.items()},
}
json.dump(report, sys.stdout, indent=2)
PY
```
- Write `summary.md` capturing command, runtime, gradient magnitudes, assertion message, and link back to chunk_03 summary.
Pitfalls To Avoid:
- Do not modify src/ modules; all instrumentation lives under reports/ per plan.
- Keep STAMP constant for the whole loop; rerunning Do Now with a new STAMP breaks ledger parity.
- Ensure env vars (KMP_DUPLICATE_LIB_OK, NANOBRAGG_DISABLE_COMPILE) are set before importing torch.
- Stay on CPU/float64; no CUDA runs for this evidence pass.
- Capture junit XML and tee’d log—ledger automation expects both.
Pointers:
- docs/fix_plan.md:11-19 — active focus + Next Action 11 wording.
- plans/active/gradient-flow-regression.md — Phase A checklist (A1–A3).
- reports/2026-01-test-suite-triage/phase_o/20251015T043128Z/chunks/chunk_03/summary.md — prior failure context.
Next Up: 1. Begin Phase B callchain (`prompts/callchain.md`) once baseline artifacts are in place.
