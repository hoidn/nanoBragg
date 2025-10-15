Summary: Capture a design note then patch `test_gradient_flow_simulation` to use non-zero structure factors and prove gradients return.
Mode: none
Focus: [GRADIENT-FLOW-001] Gradient flow regression
Branch: feature/spec-based-2
Mapped tests: tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation
Artifacts: reports/2026-01-gradient-flow/phase_c/$STAMP/{design.md}, reports/2026-01-gradient-flow/phase_d/$STAMP/{gradients.json,summary.md,pytest.log}
Do Now: [GRADIENT-FLOW-001] Phase C — write design.md for the default_F patch, apply it in tests/test_gradients.py, then run `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation --maxfail=1 --durations=25`
If Blocked: Record open questions + current evidence in design.md and summary.md, note the blocker in docs/fix_plan.md attempts, and stop before editing src/tests further.
Priorities & Rationale:
- plans/active/gradient-flow-regression.md: updated Phase C/D tables now require a design packet before touching code.
- docs/fix_plan.md:715-731 — Next Actions 3-6 gate on documenting the fixture decision and verifying gradients post-fix.
- tests/test_gradients.py:397-448 — The failing acceptance test that needs the structure-factor injection.
- docs/development/testing_strategy.md:140-210 — Gradient runs must use CPU, float64, and `NANOBRAGG_DISABLE_COMPILE=1`.
- arch.md:330-352 — Differentiability guardrails stay in force while modifying the test.
How-To Map:
- Export a STAMP once: `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`.
- Scaffold directories: `mkdir -p reports/2026-01-gradient-flow/phase_c/$STAMP` and `mkdir -p reports/2026-01-gradient-flow/phase_d/$STAMP`.
- Phase C design note: capture option comparison and verification plan in `reports/2026-01-gradient-flow/phase_c/$STAMP/design.md` (recommend default_F injection, note thresholds ≥1e-6 for gradient magnitudes, list the pytest command and any follow-on chunk reruns).
- Apply the fixture change: edit `tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation` to pass `default_F=100.0` (or documented alternative) into `CrystalConfig` and add a brief comment referencing the Phase B zero-intensity finding.
- Execute the targeted test: `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation --maxfail=1 --durations=25 | tee reports/2026-01-gradient-flow/phase_d/$STAMP/pytest.log`.
- Capture gradient magnitudes: run
  `python - <<'PY2' > reports/2026-01-gradient-flow/phase_d/$STAMP/gradients.json`
import json, torch
from nanobrag_torch.config import CrystalConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator

dtype = torch.float64
device = torch.device("cpu")
params = dict(cell_a=100., cell_b=100., cell_c=100., cell_alpha=90., cell_beta=90., cell_gamma=90.)
tensors = {k: torch.tensor(v, dtype=dtype, requires_grad=True) for k, v in params.items()}
config = CrystalConfig(**tensors, mosaic_spread_deg=0., mosaic_domains=1, N_cells=(5,5,5), default_F=100.)
crystal = Crystal(config=config, device=device, dtype=dtype)
detector = Detector(device=device, dtype=dtype)
sim = Simulator(crystal, detector, crystal_config=config, device=device, dtype=dtype)
loss = sim.run().sum()
loss.backward()
json.dump({k: float(tensors[k].grad) for k in tensors}, open(0, 'w'), indent=2)
PY2
- Summarise results in `reports/2026-01-gradient-flow/phase_d/$STAMP/summary.md` (record loss value, gradient magnitudes, pytest outcome). Update docs/fix_plan.md Attempt log and remediation tracker references once work lands.
Pitfalls To Avoid:
- Do not skip the design.md rationale; Phase C exit criteria demand it.
- Keep execution on CPU with float64 and compile disabled; no CUDA smoke on this loop.
- Avoid touching production src/ beyond the test fixture change.
- Keep gradients attached — do not detach tensors when computing magnitudes.
- Respect Protected Assets listed in docs/index.md (only edit the targeted test file).
- Preserve existing test assertions; only extend with the new config parameter and comment.
- Use a single STAMP across all new artifacts; do not overwrite Phase B bundles.
- Ensure pytest command exits cleanly; if it fails, capture the log and stop for triage.
- Update docs/fix_plan.md Attempts with STAMP + artifact pointers after completion.
Pointers:
- plans/active/gradient-flow-regression.md:52-94
- docs/fix_plan.md:703-731
- tests/test_gradients.py:397-448
- docs/development/testing_strategy.md:140-210
- reports/2026-01-gradient-flow/phase_b/20251015T053254Z/summary.md
Next Up: 1. Once gradients are restored, rerun chunk 03 timing for C18 per plans/active/test-suite-triage.md Phase P guidance.
