Summary: Capture dtype evidence for the tricubic vectorization regression so we can unblock CLUSTER-VEC-001 remediation.
Mode: Parity
Focus: TEST-SUITE-TRIAGE-002 (Next Action 9 – CLUSTER-VEC-001 diagnostics)
Branch: feature/spec-based-2
Mapped tests: tests/test_tricubic_vectorized.py::TestTricubicGather::test_vectorized_matches_scalar; tests/test_tricubic_vectorized.py::TestTricubicGather::test_oob_warning_single_fire
Artifacts: reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-VEC-001/$STAMP/
Do Now: TEST-SUITE-TRIAGE-002#9 — env KMP_DUPLICATE_LIB_OK=TRUE CUDA_VISIBLE_DEVICES=-1 pytest -vv --maxfail=1 tests/test_tricubic_vectorized.py::TestTricubicGather::test_vectorized_matches_scalar tests/test_tricubic_vectorized.py::TestTricubicGather::test_oob_warning_single_fire
If Blocked: Run the dtype snapshot script (see How-To Map step 3) and log the console output to the cluster folder; note in summary.md why pytest could not be executed.
Priorities & Rationale:
- docs/fix_plan.md:60-66 keeps Next Action 9 focused on CLUSTER-VEC-001 diagnostics before any remediation.
- reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-VEC-001.md:1-30 outlines required evidence (CPU run, dtype dump, plan linkage).
- plans/active/vectorization.md:14-19 flags tricubic work as blocked pending updated evidence, so today’s capture unblocks the backlog refresh.
- docs/development/testing_strategy.md:18-28 mandates device/dtype neutrality checks whenever tensor math regresses.
How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ); export CLUSTER_DIR=reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-VEC-001/$STAMP; mkdir -p "$CLUSTER_DIR"; printf '%s\n' "$STAMP" > "$CLUSTER_DIR/commands.txt".
- env KMP_DUPLICATE_LIB_OK=TRUE CUDA_VISIBLE_DEVICES=-1 pytest -vv --maxfail=1 tests/test_tricubic_vectorized.py::TestTricubicGather::test_vectorized_matches_scalar tests/test_tricubic_vectorized.py::TestTricubicGather::test_oob_warning_single_fire | tee "$CLUSTER_DIR/pytest_cpu.log"; expect the run to fail with "Float did not match Double".
- python - <<'PY' > "$CLUSTER_DIR/dtype_snapshot.json"
import json, sys, torch
from nanobrag_torch.config import CrystalConfig
from nanobrag_torch.models.crystal import Crystal

def make_crystal():
    cfg = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=[5, 5, 5], default_F=100.0,
        misset_deg=[0.0, 0.0, 0.0], phi_start_deg=0.0,
        osc_range_deg=0.0, phi_steps=1,
        spindle_axis=[0.0, 1.0, 0.0],
        mosaic_spread_deg=0.0, mosaic_domains=1,
        mosaic_seed=None
    )
    crystal = Crystal(cfg)
    h_range = k_range = l_range = 11
    hkl_data = torch.zeros((h_range, k_range, l_range), dtype=torch.float32)
    for i in range(h_range):
        for j in range(k_range):
            for k in range(l_range):
                h_idx = i - 5
                k_idx = j - 5
                l_idx = k - 5
                hkl_data[i, j, k] = 100.0 + 10.0 * h_idx + 1.0 * k_idx + 0.1 * l_idx
    crystal.hkl_data = hkl_data
    crystal.hkl_metadata = {
        'h_min': -5, 'h_max': 5,
        'k_min': -5, 'k_max': 5,
        'l_min': -5, 'l_max': 5,
        'h_range': 10, 'k_range': 10, 'l_range': 10
    }
    return crystal

def capture(tag, h, k, l):
    c = make_crystal()
    result = c._tricubic_interpolation(h, k, l)
    return {
        "tag": tag,
        "input_shapes": {
            "h": list(h.shape),
            "k": list(k.shape),
            "l": list(l.shape),
        },
        "input_dtypes": {
            "h": str(h.dtype),
            "k": str(k.dtype),
            "l": str(l.dtype),
        },
        "output_dtype": str(result.dtype),
        "crystal_dtype": str(c.dtype),
        "device": str(result.device),
        "values": result.detach().cpu().tolist(),
        "warning_shown": c._interpolation_warning_shown,
        "interpolate_flag": c.interpolate,
    }

cases = [
    capture(
        "scalar_float32",
        torch.tensor([1.5], dtype=torch.float32),
        torch.tensor([2.3], dtype=torch.float32),
        torch.tensor([0.5], dtype=torch.float32),
    ),
    capture(
        "batch3_float32",
        torch.tensor([1.5, 2.3, -1.2], dtype=torch.float32),
        torch.tensor([2.3, -0.5, 3.1], dtype=torch.float32),
        torch.tensor([0.5, 1.8, -2.0], dtype=torch.float32),
    ),
    capture(
        "grid2x3_float32",
        torch.tensor([[1.5, 2.3, 0.8], [-1.2, 3.1, 1.9]], dtype=torch.float32),
        torch.tensor([[2.3, -0.5, 1.2], [3.1, -2.0, 0.5]], dtype=torch.float32),
        torch.tensor([[0.5, 1.8, -1.0], [-2.0, 0.3, 2.5]], dtype=torch.float32),
    ),
    capture(
        "edge_oob_float32",
        torch.tensor([4.5], dtype=torch.float32),
        torch.tensor([0.0], dtype=torch.float32),
        torch.tensor([0.0], dtype=torch.float32),
    ),
    capture(
        "batch3_float64_inputs",
        torch.tensor([1.5, 2.3, -1.2], dtype=torch.float64),
        torch.tensor([2.3, -0.5, 3.1], dtype=torch.float64),
        torch.tensor([0.5, 1.8, -2.0], dtype=torch.float64),
    ),
]

data = {
    "default_torch_dtype": str(torch.get_default_dtype()),
    "expected_default_tensor_dtype": str(torch.tensor(100.0).dtype),
    "cases": cases,
}
json.dump(data, sys.stdout, indent=2)
PY
- python -m torch.utils.collect_env > "$CLUSTER_DIR/torch_env.txt"; env | LC_ALL=C sort > "$CLUSTER_DIR/env.txt"; tee a short summary with failure message, observed dtypes, and next-step recommendation into "$CLUSTER_DIR/summary.md".
- if python - <<'PY' 2>/dev/null <<<"import torch; import sys; sys.exit(0 if torch.cuda.is_available() else 1)"; then env KMP_DUPLICATE_LIB_OK=TRUE CUDA_VISIBLE_DEVICES=0 pytest -vv --maxfail=1 tests/test_tricubic_vectorized.py::TestTricubicGather::test_vectorized_matches_scalar tests/test_tricubic_vectorized.py::TestTricubicGather::test_oob_warning_single_fire | tee "$CLUSTER_DIR/pytest_gpu.log"; fi
Pitfalls To Avoid:
- Do not touch production code or tests; this is an evidence-only loop.
- Keep all artifacts under the cluster directory and include the STAMP in filenames.
- Avoid full-suite pytest runs; only execute the two targeted nodeids with --maxfail=1.
- Preserve the captured failure output—do not rerun pytest with --maxfail=0, which would prolong runtime unnecessarily.
- If CUDA is unavailable or unstable, skip the optional GPU step rather than forcing the run.
Pointers:
- docs/fix_plan.md:60-66
- reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-VEC-001.md:1-30
- plans/active/vectorization.md:1-40
- tests/test_tricubic_vectorized.py:20-200
- docs/development/testing_strategy.md:18-34
- docs/development/pytorch_runtime_checklist.md:1-24
Next Up: Once dtype evidence is captured, update plans/active/vectorization.md Phase D with the findings before drafting remediation steps.
