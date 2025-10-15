# Gradient Flow Test Fixture Remediation Design

**Initiative:** [GRADIENT-FLOW-001]
**Phase:** C — Test Fixture Design
**Date:** 2025-10-15
**STAMP:** 20251015T054646Z
**Owner:** ralph

## Executive Summary

Phase B zero-intensity probe (20251015T053254Z) conclusively proved that gradient flow is **intact**—all six cell parameters produce non-zero gradients when the simulation generates non-zero intensity. The failing test `test_gradient_flow_simulation` exhibits zero gradients because it produces a zero-intensity image (missing structure factors in the test fixture).

**Recommended Fix:** Add `default_F=100.0` to the `CrystalConfig` instantiation in the failing test. This minimal change restores gradient flow validation while preserving all differentiability coverage.

## Root Cause Summary (Phase B Findings)

From `reports/2026-01-gradient-flow/phase_b/20251015T053254Z/`:

- **Failing case** (test as written): `default_F` not specified → defaults to 0 → zero intensity → zero loss → zero gradients (mathematical consequence)
- **Control case** (probe): `default_F=100.0` → non-zero intensity → non-zero loss → **non-zero gradients for all 6 cell parameters**
  - cell_a gradient: +7782.17
  - cell_b/c gradients: -2947.32
  - cell_alpha gradient: +1.66
  - cell_beta/gamma gradients: ±5278

**Critical insight:** This is NOT a gradient graph break (no `.item()`, no detachment). Zero gradients are the correct mathematical result when differentiating a constant zero output with respect to any parameter.

## Option Comparison: Structure Factor Sources

### Option A: `default_F=100.0` (RECOMMENDED)

**Pros:**
- Minimal change (single keyword argument)
- Matches Phase B control experiment (known-good gradient values)
- No external file dependencies
- Fast test execution (<5s per Phase B timings)
- Aligns with other gradcheck tests in same file (lines 50-83)

**Cons:**
- Slightly less realistic than HKL file (uniform structure factor)

**Implementation:**
```python
config = CrystalConfig(
    cell_a=cell_a,
    cell_b=cell_b,
    cell_c=cell_c,
    cell_alpha=cell_alpha,
    cell_beta=cell_beta,
    cell_gamma=cell_gamma,
    mosaic_spread_deg=0.0,
    mosaic_domains=1,
    N_cells=(5, 5, 5),
    default_F=100.0,  # NEW: Ensure non-zero intensity for gradient validation
)
```

### Option B: HKL File Input

**Pros:**
- More realistic structure factors (varied F values)
- Tests HKL loading path

**Cons:**
- Requires external file (`tests/golden_data/P1.hkl` or similar)
- Slower test execution (file I/O overhead)
- File dependency risk (test fails if file missing/moved)
- Adds complexity to a focused gradient test
- HKL loading is already tested elsewhere (`test_at_src_001.py`, etc.)

**Verdict:** Reject Option B. Gradient flow validation should remain focused and self-contained.

## Verification Metrics & Commands

### Targeted Test Command

Per `testing_strategy.md` §4.1 and `input.md` line 7:

```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -vv tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation \
  --maxfail=1 --durations=25
```

**Expected outcome:** Test PASSES with:
- Loss > 0 (non-zero intensity image)
- All gradient assertions pass:
  - All 6 cell parameter gradients non-None
  - At least one gradient magnitude > 1e-10

**Gradient magnitude floor:** Based on Phase B control experiment, expect:
- Cell length gradients (a/b/c): ≥1e3 magnitude
- Cell angle gradients (α/β/γ): ≥1.0 magnitude

### Gradient Capture Script

To document post-fix gradient values for the ledger, run:

```bash
python - <<'PY' > reports/2026-01-gradient-flow/phase_d/20251015T054646Z/gradients.json
import json, torch, os
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['NANOBRAGG_DISABLE_COMPILE'] = '1'

from nanobrag_torch.config import CrystalConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator

dtype = torch.float64
device = torch.device("cpu")

# Create differentiable parameters
params = {
    'cell_a': torch.tensor(100., dtype=dtype, requires_grad=True),
    'cell_b': torch.tensor(100., dtype=dtype, requires_grad=True),
    'cell_c': torch.tensor(100., dtype=dtype, requires_grad=True),
    'cell_alpha': torch.tensor(90., dtype=dtype, requires_grad=True),
    'cell_beta': torch.tensor(90., dtype=dtype, requires_grad=True),
    'cell_gamma': torch.tensor(90., dtype=dtype, requires_grad=True),
}

config = CrystalConfig(**{k: v for k, v in params.items()},
                       mosaic_spread_deg=0., mosaic_domains=1,
                       N_cells=(5,5,5), default_F=100.)

crystal = Crystal(config=config, device=device, dtype=dtype)
detector = Detector(device=device, dtype=dtype)
sim = Simulator(crystal, detector, crystal_config=config, device=device, dtype=dtype)

loss = sim.run().sum()
loss.backward()

result = {
    'loss': float(loss.item()),
    'gradients': {k: float(v.grad.item()) for k, v in params.items()},
    'gradient_magnitudes': {k: float(abs(v.grad.item())) for k, v in params.items()},
}

json.dump(result, open('/dev/stdout', 'w'), indent=2)
PY
```

### Follow-On Chunk Rerun

If targeted test passes, optionally rerun chunk 03 to validate no broader regressions:

```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -vv tests/test_gradients.py --maxfail=5 --durations=25 \
  2>&1 | tee reports/2026-01-gradient-flow/phase_d/20251015T054646Z/chunk_rerun.log
```

**Expected:** No new failures; C19 cluster resolved (1 failure → 0 failures).

## Documentation Touchpoints

1. **Test Docstring Comment** (`tests/test_gradients.py:385-388`):
   Add brief comment explaining structure-factor requirement:

   ```python
   def test_gradient_flow_simulation(self):
       """Verify end-to-end gradient flow through full simulation pipeline.

       Note: Requires non-zero structure factors (default_F) to generate
       non-zero intensity, ensuring gradients can be validated. Zero intensity
       produces zero gradients mathematically (∂(0)/∂θ = 0).
       """
   ```

2. **fix_plan.md Attempts History** (`docs/fix_plan.md:703-725`):
   Append Phase C+D summary with artifacts and STAMP references.

3. **testing_strategy.md (Optional)** (`docs/development/testing_strategy.md` §4.1):
   Consider adding a note about structure-factor requirements for gradient flow tests. Defer to Phase D decision based on whether this is a one-off or recurring concern.

4. **Remediation Tracker** (`reports/2026-01-test-suite-triage/remediation_tracker.md`):
   Mark C19 cluster as RESOLVED once targeted test passes.

## Implementation Sequence (Phase D Tasks)

| Task | Description | Estimated Time |
|------|-------------|----------------|
| D1 | Apply test fixture change (edit test_gradients.py line ~409) | 2 min |
| D2a | Run targeted pytest command | 5 min |
| D2b | Run gradient capture script | 2 min |
| D3 | Update docs (docstring, fix_plan, tracker) | 5 min |
| **Total** | | **~15 min** |

## Acceptance Criteria (Phase D Exit)

- [ ] Targeted test passes (exit code 0)
- [ ] Loss value > 0 documented in summary.md
- [ ] All 6 gradient magnitudes > threshold documented in gradients.json
- [ ] Test docstring updated with structure-factor note
- [ ] fix_plan.md Attempts History updated with Phase C+D STAMPs
- [ ] remediation_tracker.md C19 cluster marked RESOLVED
- [ ] Artifacts archived under `reports/2026-01-gradient-flow/phase_d/20251015T054646Z/`

## Risk Assessment

**Risk:** Changing test expectations weakens gradient coverage.
**Mitigation:** Phase B control experiment validates gradient graph integrity. Test still verifies end-to-end gradient flow; only the input configuration changes (zero-F → non-zero-F).

**Risk:** Other tests may have same issue.
**Mitigation:** Phase O baseline (20251015T043128Z) shows only 1 gradient flow failure (this test). All gradcheck tests pass with guard. No evidence of broader issue.

**Risk:** default_F masks future gradient breaks.
**Mitigation:** Gradcheck tests (lines 90-257) provide comprehensive per-parameter validation. This test's role is end-to-end integration; gradcheck suite catches breaks at unit level.

## References

- **Phase B Findings:** `reports/2026-01-gradient-flow/phase_b/20251015T053254Z/summary.md`
- **Zero-Intensity Probe:** `reports/2026-01-gradient-flow/phase_b/20251015T053254Z/zero_intensity_probe.json`
- **Plan:** `plans/active/gradient-flow-regression.md` Phase C tasks
- **Spec:** `arch.md` §15 (Differentiability Guidelines), `testing_strategy.md` §4.1
- **Test File:** `tests/test_gradients.py:385-449`
- **Phase O Baseline:** `reports/2026-01-test-suite-triage/phase_o/20251015T043128Z/summary.md` (C19 cluster)

## Approval Checklist

- [x] Spec alignment: `arch.md` §15 differentiability preserved
- [x] Option comparison documented (A vs B, A recommended)
- [x] Verification metrics defined (gradient floor ≥1e-6, loss > 0)
- [x] Canonical commands provided (targeted test, capture script, chunk rerun)
- [x] Documentation touchpoints enumerated (4 items)
- [x] Risk assessment complete (3 risks, mitigations documented)
- [x] Effort estimate reasonable (~15 min Phase D)
- [x] Exit criteria comprehensive (6 checkpoints)

**Recommendation:** Proceed to Phase D implementation using Option A (`default_F=100.0` injection).
