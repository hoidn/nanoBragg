Summary: Map the gradient flow pipeline and capture zero-intensity evidence so we can localise the C19 failure.
Mode: Parity
Focus: [GRADIENT-FLOW-001] Gradient flow regression
Branch: feature/spec-based-2
Mapped tests: tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation
Artifacts: reports/2026-01-gradient-flow/phase_b/$STAMP/{zero_intensity.md,zero_intensity_probe.json,callchain/static.md,trace/tap_points.md,summary.md,env/trace_env.json,hook_gradients.txt}
Do Now: [GRADIENT-FLOW-001] Phase B prep/B1 — capture zero-intensity probe and follow prompts/callchain.md (analysis_question="Why do cell parameters have zero gradients in test_gradient_flow_simulation?", initiative_id="grad-flow", scope_hints=["Crystal","Simulator","reciprocal_vectors"]) with outputs under reports/2026-01-gradient-flow/phase_b/$STAMP/
If Blocked: Record whatever partial evidence you gathered (logs, notes) in zero_intensity.md, note the blocker in summary.md, and stop without editing src/.
Priorities & Rationale:
- plans/active/gradient-flow-regression.md:25-34 — Phase B requires callchain + hook evidence before touching implementation.
- docs/fix_plan.md:703-718 — Next Actions 2-4 demand zero-intensity confirmation, callchain deliverables, and autograd hook scrape.
- tests/test_gradients.py:397-448 — The failing acceptance test documents the expected gradient behaviour we need to defend.
- arch.md:310-352 — Differentiability guardrails (no `.item()`, retain tensors) define the invariants to check in the callchain.
- docs/development/testing_strategy.md:140-210 — Gradient evidence must use CPU + float64 with compile disabled; keep that contract for every probe.
How-To Map:
- Export a single STAMP and scaffold directories: `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `mkdir -p reports/2026-01-gradient-flow/phase_b/$STAMP/{callchain,callgraph,trace,env}`.
- Zero-intensity probe (captures Next Action 2):
  - Run the control script and store raw numbers: `python - <<'PY' > reports/2026-01-gradient-flow/phase_b/$STAMP/zero_intensity_probe.json`
import json, torch
from nanobrag_torch.config import CrystalConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator

def run(default_F):
    dtype = torch.float64
    device = torch.device("cpu")
    cell = dict(cell_a=100., cell_b=100., cell_c=100., cell_alpha=90., cell_beta=90., cell_gamma=90.)
    params = {k: torch.tensor(v, dtype=dtype, requires_grad=True) for k, v in cell.items()}
    config = CrystalConfig(**params, mosaic_spread_deg=0., mosaic_domains=1, N_cells=(5,5,5), default_F=default_F)
    crystal = Crystal(config=config, device=device, dtype=dtype)
    detector = Detector(device=device, dtype=dtype)
    sim = Simulator(crystal, detector, crystal_config=config, device=device, dtype=dtype)
    image = sim.run()
    loss = image.sum()
    loss.backward()
    grads = {k: float(v.grad) if v.grad is not None else None for k, v in params.items()}
    return float(loss.detach()), grads
loss0, grads0 = run(0.0)
loss100, grads100 = run(100.0)
json.dump({"default_F": {"0.0": {"loss": loss0, "grads": grads0}, "100.0": {"loss": loss100, "grads": grads100}}}, open(0, 'w'), indent=2)
PY
  - Summarise findings in `reports/2026-01-gradient-flow/phase_b/$STAMP/zero_intensity.md` (cite tests/test_gradients.py:397-448 and explain why default_F=0 causes zero gradients).
- Callchain (Phase B1): review prompts/callchain.md and execute the SOP with
  - `analysis_question="Why do cell parameters have zero gradients in test_gradient_flow_simulation?"`
  - `initiative_id="grad-flow"` (outputs go under the same STAMP path)
  - `scope_hints=["Crystal","Simulator","reciprocal_vectors"]`
  - `namespace_filter="nanobrag_torch"`
  Produce `callchain/static.md`, optional `callgraph/dynamic.txt` (tiny ROI), `trace/tap_points.md`, `summary.md`, and `env/trace_env.json` (JSON should include commit SHA, Python, torch, CUDA availability, env vars like NANOBRAGG_DISABLE_COMPILE).
- Autograd hook scrape (Phase B2): create `reports/2026-01-gradient-flow/phase_b/$STAMP/hooks.py` that rebuilds the failing configuration, registers hooks on reciprocal vectors / rotated real vectors / final intensity tensor, runs backward, and writes hook outputs to `hook_gradients.txt`. Example pattern:
  - inside hooks.py, import configs, create tensors with `requires_grad=True`, call `register_hook(lambda grad: log.append(("tensor", grad.detach().cpu().tolist())))`, and dump JSON.
  - Execute with `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 python reports/2026-01-gradient-flow/phase_b/$STAMP/hooks.py > reports/2026-01-gradient-flow/phase_b/$STAMP/hook_gradients.txt`.
- After hooks, update `reports/2026-01-gradient-flow/phase_b/$STAMP/summary.md` with (1) zero-intensity confirmation, (2) callchain highlights with file:line anchors, (3) first node where gradients vanish per hook outputs, and (4) recommended next instrumentation step.
Pitfalls To Avoid:
- Do not touch src/ or tests/; all probes live under reports/.
- Keep the same STAMP across every artifact this loop.
- Honor CPU/float64 + `NANOBRAGG_DISABLE_COMPILE=1`; no CUDA runs here.
- Register hooks on existing tensors only; never clone/detach before hooking.
- Follow prompts/callchain.md deliverable structure exactly (no missing files).
- Record command snippets and assumptions in summary.md; future loops depend on them.
- Respect Protected Assets, especially anything listed in docs/index.md.
- Do not rerun the full pytest suite; stay within targeted probes only.
- Capture environment metadata (torch, python, OS) in env/trace_env.json.
- Avoid writing temporary files outside the STAMP directory.
Pointers:
- plans/active/gradient-flow-regression.md:25-34 — Phase B checklist and deliverable expectations.
- docs/fix_plan.md:703-717 — Current ledger direction for `[GRADIENT-FLOW-001]`.
- tests/test_gradients.py:397-448 — Acceptance test contract for gradient flow.
- arch.md:330-352 — Differentiability guardrails relevant to gradient tracing.
- docs/development/testing_strategy.md:150-210 — Gradient evidence environment requirements.
Next Up: 1. Once callchain evidence is captured, stage C18 timing review per plans/active/test-suite-triage.md Phase P.
