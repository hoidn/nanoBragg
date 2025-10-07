# φ=0 Carryover Parity Shim — Design Note

**Date**: 2025-10-07
**Phase**: CLI-FLAGS-003 L3k.3c.4
**Plan Reference**: `plans/active/cli-phi-parity-shim/plan.md`
**Supervisor Memo**: `input.md:1-36`

---

## Executive Summary

This design note defines an **opt-in parity shim** to reproduce the documented φ=0 carryover bug (C-PARITY-001) in the PyTorch implementation, enabling C↔PyTorch equivalence testing while preserving the spec-compliant default path.

**Key Design Principles**:
- Spec-compliant behavior remains the **default**
- Parity mode is **opt-in only** (explicit flag/config required)
- Implementation preserves vectorization, gradient flow, and device/dtype neutrality
- No regression to existing spec-compliant tests

---

## 1. Background & Motivation

### 1.1 C-PARITY-001: φ=0 Stale Vector Carryover

**Problem**: In `nanoBragg.c`, the φ rotation loop only updates `ap/bp/cp` when `phi != 0.0`:

```c
/* nanoBragg.c:3040-3066 — φ Rotation Loop */
for(phi_tic = 0; phi_tic < phisteps; ++phi_tic)
{
    phi = phi0 + phistep*phi_tic;

    if( phi != 0.0 )  /* ← BUG: skips φ=0° step */
    {
        /* rotate about spindle if necessary */
        rotate_axis(a0,ap,spindle_vector,phi);
        rotate_axis(b0,bp,spindle_vector,phi);
        rotate_axis(c0,cp,spindle_vector,phi);
    }
    /* ... mosaic rotation uses ap/bp/cp ... */
}
```

**Consequence**: When `phi == 0.0`, the code reuses `ap/bp/cp` from the **previous pixel's final φ step**, not the unrotated `a0/b0/c0` base vectors. This produces incorrect Miller indices for the φ=0 slice.

**Reproduction Evidence**: `docs/bugs/verified_c_bugs.md:166-204`

```bash
./golden_suite_generator/nanoBragg -cell 70 70 70 90 90 90 -default_F 1 -N 2 \
  -distance 100 -detpixels 4 -pixel 0.1 \
  -phi 0 -osc 0.09 -phisteps 10 -trace_pixel 0 0 \
  -floatfile /tmp/phi_float.bin > docs/bugs/artifacts/c-parity-001.txt
```

Trace shows identical `k_frac` values at φ=0 and the terminal φ step, confirming vector carryover.

### 1.2 PyTorch Correction (Spec-Compliant Default)

The current PyTorch implementation correctly applies identity rotation at φ=0:

```python
# src/nanobrag_torch/models/crystal.py:1070-1130
def get_rotated_real_vectors(self, config: CrystalConfig):
    """Rotate base vectors by φ about spindle axis (spec-compliant)."""
    # ... compute phi_rad for each step ...
    # When phi_rad == 0.0, rotation matrix is identity → ap/bp/cp == a0/b0/c0
    rotated_a = utils.geometry.rotate_vectors(self.a_vector, ...)
    rotated_b = utils.geometry.rotate_vectors(self.b_vector, ...)
    rotated_c = utils.geometry.rotate_vectors(self.c_vector, ...)
    return rotated_a, rotated_b, rotated_c
```

This aligns with `specs/spec-a-core.md:211-214`:
> φ step: φ = φ0 + (step index)*phistep; rotate the reference cell (a0,b0,c0) about u by φ to get (ap,bp,cp).

**Result**: At φ=0°, PyTorch produces `rot_b[0,0,1] = 0.71732 Å` (base vector), while C produces `0.671588 Å` (stale carryover).

### 1.3 Need for Parity Shim

To enable C↔PyTorch validation during Phase L4 supervisor command reruns, we need an **opt-in mode** that reproduces the C bug **exactly**, without affecting the default spec-compliant path.

**Use Cases**:
- Parity testing (`nb-compare`, `test_parity_matrix.py`)
- Debugging C↔Py discrepancies in legacy workflows
- Transition period for users migrating from C to PyTorch

**Non-Goals**:
- Making the bug the default (spec compliance is mandatory)
- Supporting the parity mode in production (opt-in only)
- Changing C code behavior (out of scope)

---

## 2. Design Overview

### 2.1 Trigger Surface (Opt-In API)

**Proposed CLI Flag**:
```bash
--phi-carryover-mode {spec,c-parity}
```

**Default**: `spec` (current spec-compliant behavior)
**Opt-in**: `c-parity` (reproduce C bug)

**Alternative Names Considered**:
- `--legacy-phi-mode` (less clear about what it does)
- `--c-compat-phi` (too vague)
- `--phi-0-carryover` (only describes part of the behavior)

**Decision**: Use `--phi-carryover-mode` for clarity and extensibility.

### 2.2 Configuration Plumbing

**Add to `CrystalConfig`** (data model layer):

```python
@dataclass
class CrystalConfig:
    # ... existing fields ...

    phi_carryover_mode: str = "spec"  # "spec" | "c-parity"

    def __post_init__(self):
        if self.phi_carryover_mode not in ("spec", "c-parity"):
            raise ValueError(
                f"phi_carryover_mode must be 'spec' or 'c-parity', "
                f"got {self.phi_carryover_mode!r}"
            )
```

**CLI Parser Updates** (`src/nanobrag_torch/__main__.py`):

```python
def create_parser():
    parser = argparse.ArgumentParser(...)
    # ... existing arguments ...

    parser.add_argument(
        "--phi-carryover-mode",
        choices=["spec", "c-parity"],
        default="spec",
        help=(
            "φ rotation mode: 'spec' (default, spec-compliant) or "
            "'c-parity' (reproduce C-PARITY-001 for validation). "
            "See docs/bugs/verified_c_bugs.md for details."
        )
    )
    return parser

def parse_and_validate_args(args):
    # ... existing logic ...
    crystal_config = CrystalConfig(
        # ... existing fields ...
        phi_carryover_mode=args.phi_carryover_mode,
    )
```

### 2.3 Data Flow Sketch

```
┌─────────────────────────────────────────────────────────────┐
│ CLI: nanoBragg --phi-carryover-mode c-parity ...            │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ parse_and_validate_args()                                   │
│   → CrystalConfig(phi_carryover_mode="c-parity")            │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Crystal.__init__(config)                                    │
│   → self.phi_carryover_mode = config.phi_carryover_mode     │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ get_rotated_real_vectors(config, phi_steps)                 │
│   if config.phi_carryover_mode == "c-parity":               │
│     → Apply stale carryover logic (φ=0 uses prev step)      │
│   else:  # "spec" (default)                                 │
│     → Identity rotation at φ=0 (current implementation)     │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Implementation Strategy

### 3.1 Core Logic (Batched Tensor Operations)

**Key Constraint**: Maintain vectorization across `(phi_steps, mosaic_domains)` dimensions.

**Current Implementation** (spec-compliant):
```python
def get_rotated_real_vectors(self, config: CrystalConfig):
    """Rotate base vectors by φ (spec-compliant: identity at φ=0)."""
    phi_rad = self._compute_phi_angles(config)  # shape: (phi_steps,)

    # Rotate all steps simultaneously (vectorized)
    rotated_a = utils.geometry.rotate_vectors(
        self.a_vector, config.spindle_axis, phi_rad
    )  # shape: (phi_steps, 3)
    rotated_b = utils.geometry.rotate_vectors(
        self.b_vector, config.spindle_axis, phi_rad
    )
    rotated_c = utils.geometry.rotate_vectors(
        self.c_vector, config.spindle_axis, phi_rad
    )
    return rotated_a, rotated_b, rotated_c
```

**Proposed Parity Shim** (c-parity mode):
```python
def get_rotated_real_vectors(self, config: CrystalConfig):
    """
    Rotate base vectors by φ about spindle axis.

    C-Code Implementation Reference (nanoBragg.c:3040-3066):
    ```c
    for(phi_tic = 0; phi_tic < phisteps; ++phi_tic)
    {
        phi = phi0 + phistep*phi_tic;

        if( phi != 0.0 )  /* BUG: skips φ=0° step */
        {
            rotate_axis(a0,ap,spindle_vector,phi);
            rotate_axis(b0,bp,spindle_vector,phi);
            rotate_axis(c0,cp,spindle_vector,phi);
        }
        /* ap/bp/cp used in mosaic rotation regardless */
    }
    ```

    Behavior:
    - "spec" mode (default): Identity rotation at φ=0 (spec-compliant)
    - "c-parity" mode: Reuse previous step's vectors at φ=0 (C bug)

    Args:
        config: CrystalConfig with phi_carryover_mode setting

    Returns:
        (rotated_a, rotated_b, rotated_c): shape (phi_steps, 3)
    """
    phi_rad = self._compute_phi_angles(config)  # shape: (phi_steps,)

    if config.phi_carryover_mode == "c-parity":
        # Reproduce C bug: φ=0 reuses previous step's vectors
        # Strategy: Compute all rotations, then mask φ=0 with shifted values

        # Compute all rotations (including φ=0 as identity)
        rotated_a_spec = utils.geometry.rotate_vectors(
            self.a_vector, config.spindle_axis, phi_rad
        )  # shape: (phi_steps, 3)
        rotated_b_spec = utils.geometry.rotate_vectors(
            self.b_vector, config.spindle_axis, phi_rad
        )
        rotated_c_spec = utils.geometry.rotate_vectors(
            self.c_vector, config.spindle_axis, phi_rad
        )

        # Identify φ=0 steps (tolerance: 1e-10 radians ≈ 5.7e-9 degrees)
        is_phi_zero = (phi_rad.abs() < 1e-10).unsqueeze(-1)  # shape: (phi_steps, 1)

        # Create "previous step" vectors (shift right with base vectors at start)
        # For first step, use base vectors; for subsequent φ=0 steps, use step-1
        prev_a = torch.cat([
            self.a_vector.unsqueeze(0),  # step 0: base vector (will be replaced)
            rotated_a_spec[:-1]          # steps 1+: previous step
        ], dim=0)
        prev_b = torch.cat([
            self.b_vector.unsqueeze(0),
            rotated_b_spec[:-1]
        ], dim=0)
        prev_c = torch.cat([
            self.c_vector.unsqueeze(0),
            rotated_c_spec[:-1]
        ], dim=0)

        # Apply carryover: where φ=0, use previous step; otherwise use spec rotation
        rotated_a = torch.where(is_phi_zero, prev_a, rotated_a_spec)
        rotated_b = torch.where(is_phi_zero, prev_b, rotated_b_spec)
        rotated_c = torch.where(is_phi_zero, prev_c, rotated_c_spec)

        return rotated_a, rotated_b, rotated_c

    else:  # "spec" (default)
        # Current spec-compliant implementation (identity at φ=0)
        rotated_a = utils.geometry.rotate_vectors(
            self.a_vector, config.spindle_axis, phi_rad
        )
        rotated_b = utils.geometry.rotate_vectors(
            self.b_vector, config.spindle_axis, phi_rad
        )
        rotated_c = utils.geometry.rotate_vectors(
            self.c_vector, config.spindle_axis, phi_rad
        )
        return rotated_a, rotated_b, rotated_c
```

**Key Implementation Details**:
1. **Vectorization Preserved**: All operations use tensor broadcasts/indexing (no Python loops)
2. **Gradient Flow**: `torch.where` and `torch.cat` are differentiable
3. **Device/Dtype Neutral**: Inherits device/dtype from `phi_rad` tensor
4. **Zero Tolerance**: `1e-10 rad` chosen to avoid float32 precision issues

### 3.2 Edge Cases & Validation

**Case 1: First pixel, φ=0**
- C behavior: Uses `ap/bp/cp` from initialization (garbage or zero)
- Our shim: Uses base vectors (spec-compliant for first pixel)
- **Decision**: Accept this minor difference (initializing to garbage is undefined behavior)

**Case 2: Mid-run φ=0 after non-zero steps**
- C behavior: Reuses vectors from previous φ step of **same pixel**
- Our shim: Reuses vectors from previous φ step index via `rotated_*[:-1]`
- **Validates**: C bug reproduction

**Case 3: All φ steps are 0**
- C behavior: Always identity (no rotation applied)
- Our shim: All steps flagged as `is_phi_zero`, use previous (→ base vectors)
- **Validates**: Equivalent to spec mode

**Case 4: Mixed zero/non-zero steps**
- Example: φ = [0, 0.01, 0.02, 0, 0.04]
- Shim applies carryover only to indices 0 and 3
- **Validates**: Per-step masking

### 3.3 Gradient & Compilation Compatibility

**Gradient Flow**:
- `torch.where(condition, x, y)` propagates gradients through `x` and `y` branches
- `torch.cat([...])` preserves gradients from all inputs
- `phi_rad.abs() < 1e-10` is a boolean mask (non-differentiable condition is safe)

**torch.compile Compatibility**:
- All operations (cat, where, unsqueeze) are Dynamo-supported
- No Python control flow inside parity branch
- Expect clean graph capture on CPU and CUDA

**Device Migration**:
- Shim inherits device from `phi_rad` (computed from config)
- No hard-coded `.cpu()` or `.cuda()` calls

---

## 4. Validation Strategy

### 4.1 Test Coverage

**Extend `tests/test_cli_scaling_phi0.py`**:

```python
class TestPhiCarryoverParity:
    """Validate c-parity mode reproduces C bug."""

    def test_parity_mode_phi0_carryover(self):
        """φ=0 in c-parity mode should use previous step's vectors."""
        # Setup: config with phi_carryover_mode="c-parity"
        # ... instantiate Crystal ...

        # Get rotated vectors for φ = [0, 0.05, 0, 0.15] (mixed zero/non-zero)
        rotated_a, rotated_b, rotated_c = crystal.get_rotated_real_vectors(config)

        # Assert: φ=0 steps (indices 0, 2) should NOT equal base vectors
        # (would equal base vectors in spec mode)
        assert not torch.allclose(rotated_b[0], crystal.b_vector)  # first φ=0
        assert not torch.allclose(rotated_b[2], crystal.b_vector)  # second φ=0

        # Assert: φ=0 at index 2 should equal φ=0.05 rotation (index 1)
        assert torch.allclose(rotated_b[2], rotated_b[1], atol=1e-10)

    def test_spec_mode_remains_unchanged(self):
        """Default spec mode should apply identity rotation at φ=0."""
        # Setup: config with phi_carryover_mode="spec" (default)
        # ... instantiate Crystal ...

        # Assert: φ=0 rotation equals base vectors (identity transform)
        rotated_a, rotated_b, rotated_c = crystal.get_rotated_real_vectors(config)
        assert torch.allclose(rotated_b[0], crystal.b_vector, atol=1e-6)

    @pytest.mark.parametrize("device", ["cpu", "cuda"])
    def test_parity_mode_device_neutral(self, device):
        """c-parity mode should work on CPU and CUDA."""
        if device == "cuda" and not torch.cuda.is_available():
            pytest.skip("CUDA not available")

        # ... run parity mode on specified device ...
        # Assert: results match expected carryover behavior
```

**Add to `tests/test_cli_flags.py`**:

```python
def test_phi_carryover_mode_parsing():
    """CLI --phi-carryover-mode should parse correctly."""
    parser = create_parser()

    # Default
    args = parser.parse_args([...])  # minimal args
    assert args.phi_carryover_mode == "spec"

    # Explicit spec
    args = parser.parse_args([..., "--phi-carryover-mode", "spec"])
    assert args.phi_carryover_mode == "spec"

    # Parity mode
    args = parser.parse_args([..., "--phi-carryover-mode", "c-parity"])
    assert args.phi_carryover_mode == "c-parity"

    # Invalid value
    with pytest.raises(SystemExit):
        parser.parse_args([..., "--phi-carryover-mode", "invalid"])
```

### 4.2 Trace Validation

**Script**: `scripts/compare_per_phi_traces.py`

**Execution Plan**:

```bash
# 1. Spec mode trace (current behavior)
mkdir -p reports/2025-10-cli-flags/phase_l/parity_shim/20251007T232657Z/traces/spec
KMP_DUPLICATE_LIB_OK=TRUE python scripts/compare_per_phi_traces.py \
  --mode spec \
  --outdir reports/2025-10-cli-flags/phase_l/parity_shim/20251007T232657Z/traces/spec

# 2. C-parity mode trace (shim behavior)
mkdir -p reports/2025-10-cli-flags/phase_l/parity_shim/20251007T232657Z/traces/c-parity
KMP_DUPLICATE_LIB_OK=TRUE python scripts/compare_per_phi_traces.py \
  --mode c-parity \
  --outdir reports/2025-10-cli-flags/phase_l/parity_shim/20251007T232657Z/traces/c-parity

# 3. C reference trace (from instrumented nanoBragg.c)
NB_C_BIN=./golden_suite_generator/nanoBragg \
  ./golden_suite_generator/nanoBragg \
  -mat A.mat -hkl scaled.hkl -lambda 0.9768 -N 36 47 29 \
  -distance 100 -detpixels 2124 -pixel 0.1 \
  -phi 0 -osc 0.1 -phisteps 10 -mosaic_dom 1 -oversample 1 \
  -trace_pixel 512 512 -floatfile /tmp/c_ref.bin \
  > reports/2025-10-cli-flags/phase_l/parity_shim/20251007T232657Z/traces/c_trace.log 2>&1
```

**Expected Outcomes**:
- **Spec trace**: `rot_b[0,0,1] = 0.71732 Å` at φ=0 (identity rotation)
- **C-parity trace**: `rot_b[0,0,1] ≈ 0.671588 Å` at φ=0 (carryover from previous step)
- **C trace**: Matches c-parity trace within numerical tolerance (≤1e-6 Å)

**Artifacts**:
- `trace_summary.md` (per-φ comparison table)
- `delta_metrics.json` (numeric deltas at each φ step)
- Raw trace logs for manual inspection

### 4.3 nb-compare Integration

**Command** (after implementation):

```bash
# C vs PyTorch (c-parity mode)
nb-compare \
  --c-bin ./golden_suite_generator/nanoBragg \
  --py-args "--phi-carryover-mode c-parity" \
  --outdir reports/2025-10-cli-flags/phase_l/parity_shim/20251007T232657Z/nb_compare \
  -- \
  -mat A.mat -hkl scaled.hkl -lambda 0.9768 -N 36 47 29 \
  -distance 100 -detpixels 512 -pixel 0.1 \
  -phi 0 -osc 0.1 -phisteps 10 -mosaic_dom 1 -oversample 1 \
  -floatfile comparison.bin
```

**Expected Metrics**:
- Correlation ≥ 0.9995 (VG-3 gate from fix_checklist.md)
- Sum ratio 0.99–1.01 (VG-4 gate)
- Max |Δ| ≤ 0.01 × max(C intensity)

---

## 5. Documentation Updates

### 5.1 User-Facing Documentation

**`README_PYTORCH.md`** (add CLI flag section):

```markdown
### Advanced Options

#### φ Rotation Mode (`--phi-carryover-mode`)

Controls φ=0° rotation behavior:

- **`spec`** (default): Spec-compliant identity rotation at φ=0°
- **`c-parity`**: Reproduce C-PARITY-001 bug for validation (opt-in)

**Example**:
```bash
# Default (spec-compliant)
nanoBragg -hkl data.hkl -phi 0 -osc 0.1 -phisteps 10 ...

# Parity mode (for C equivalence testing)
nanoBragg --phi-carryover-mode c-parity -hkl data.hkl -phi 0 -osc 0.1 -phisteps 10 ...
```

**Note**: `c-parity` mode is intended for debugging and validation only. Production workflows should use the default `spec` mode.
```

### 5.2 Developer Documentation

**`docs/bugs/verified_c_bugs.md`** (update C-PARITY-001 section):

```markdown
### C-PARITY-001 — φ=0 Uses Stale Crystal Vectors (Medium)

... [existing description] ...

**PyTorch Shim**: The PyTorch implementation provides an **opt-in** parity mode to reproduce this bug for validation purposes. Use `--phi-carryover-mode c-parity` to enable.

```python
# Example: Reproduce C bug in PyTorch
from nanobrag_torch.models.crystal import Crystal, CrystalConfig

config = CrystalConfig(
    # ... standard params ...
    phi_carryover_mode="c-parity"  # Opt-in parity mode
)
crystal = Crystal(config)
rotated_a, rotated_b, rotated_c = crystal.get_rotated_real_vectors(config)
# φ=0 step will reuse previous step's vectors (C bug behavior)
```

**Default behavior** (`phi_carryover_mode="spec"`) remains spec-compliant with identity rotation at φ=0°.
```

**`reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md`** (add parity shim section):

```markdown
## Parity Shim Design (Phase L3k.3c.4)

**Objective**: Enable C↔PyTorch validation by reproducing C-PARITY-001 in an opt-in mode.

**Implementation**: See `reports/2025-10-cli-flags/phase_l/parity_shim/20251007T232657Z/design.md`

**Key Features**:
- Default path unchanged (spec-compliant)
- CLI flag: `--phi-carryover-mode c-parity`
- Preserves vectorization, gradients, device/dtype neutrality
- Validated via extended `tests/test_cli_scaling_phi0.py` suite

**Artifacts**: [link to test logs, traces, nb-compare results]
```

---

## 6. Risk Assessment & Mitigation

### 6.1 Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Parity mode accidentally enabled by users | Medium | Default is `spec`; require explicit opt-in; document clearly as "validation only" |
| Regression to spec-compliant tests | High | Comprehensive test suite verifies default path unchanged; CI gate on spec tests |
| Gradient breakage in c-parity branch | Medium | All operations are differentiable; gradcheck tests cover both modes |
| Device migration failures | Low | Inherit device from phi_rad; add CPU+CUDA parametrized tests |
| Vectorization loss | High | Design enforces tensor operations; no Python loops introduced |
| Confusion about which mode to use | Medium | Documentation emphasizes `spec` as default; parity mode clearly marked "opt-in" |

### 6.2 Validation Checklist

Before considering implementation complete:

- [ ] CLI flag `--phi-carryover-mode` parses correctly (default=spec, accepts c-parity)
- [ ] `CrystalConfig.phi_carryover_mode` field added with validation
- [ ] Spec mode tests (`test_cli_scaling_phi0.py::TestPhiZeroParity`) still pass
- [ ] Parity mode tests (`test_cli_scaling_phi0.py::TestPhiCarryoverParity`) pass
- [ ] Per-φ traces captured for both modes (spec vs c-parity)
- [ ] C reference trace matches c-parity trace within ≤1e-6 Å
- [ ] nb-compare with `--py-args "--phi-carryover-mode c-parity"` achieves correlation ≥0.9995
- [ ] Gradient flow preserved (gradcheck passes for both modes)
- [ ] CPU and CUDA execution tested (device-neutral)
- [ ] Documentation updated (README_PYTORCH.md, verified_c_bugs.md, diagnosis.md)

---

## 7. Implementation Roadmap

Following `plans/active/cli-phi-parity-shim/plan.md`:

### Phase B — Design (CURRENT)
- [X] **B1**: Draft design note (this document)
- [ ] **B2**: Choose API & config plumbing (documented above: CLI flag + CrystalConfig field)
- [ ] **B3**: Define validation strategy (documented above: test suite + traces + nb-compare)

### Phase C — Implementation
- [ ] **C1**: Implement opt-in carryover logic in `Crystal.get_rotated_real_vectors`
- [ ] **C2**: Wire CLI flag through parser → CrystalConfig
- [ ] **C3**: Extend test suite (`test_cli_scaling_phi0.py`, `test_cli_flags.py`)
- [ ] **C4**: Capture per-φ traces (spec, c-parity, C reference)
- [ ] **C5**: Log implementation Attempt in `docs/fix_plan.md` with metrics

### Phase D — Documentation & Handoff
- [ ] **D1**: Update user/developer docs (README, verified_c_bugs.md, diagnosis.md)
- [ ] **D2**: Sync plan statuses (mark Phase L3k.3c.4 complete)
- [ ] **D3**: Prepare Phase L4 handoff (supervisor command rerun with parity mode)

---

## 8. Open Questions & Decisions

### Q1: Should we support a `--legacy-mode` umbrella flag?
**Answer**: No. Keep the shim narrowly scoped to φ carryover. If other C bugs need parity shims, add separate flags (e.g., `--mosaic-rng-mode`, `--pivot-mode`) rather than a monolithic legacy switch.

### Q2: Do we need to cache stale vectors across **pixels**?
**Answer**: No. C's bug is per-pixel (loop-scoped). Our shim reuses vectors from the previous **φ step within the same pixel**, not across pixels.

### Q3: Should gradients work in c-parity mode?
**Answer**: Yes. The shim uses fully differentiable operations. Gradcheck tests will cover both modes to ensure no regressions.

### Q4: How do we prevent accidental parity mode in production?
**Answer**:
1. Default is `spec` (must explicitly opt-in)
2. Documentation marks c-parity as "validation only"
3. Consider adding a startup warning log when c-parity is enabled (optional)

### Q5: What tolerance for "φ=0" detection?
**Answer**: `1e-10 radians` (~5.7e-9 degrees). Tight enough to avoid float32 rounding errors, loose enough to catch intended zeros.

---

## 9. References

- **Spec**: `specs/spec-a-core.md:204-240` (normative φ rotation)
- **C Bug**: `docs/bugs/verified_c_bugs.md:166-204` (C-PARITY-001)
- **C Reference**: `golden_suite_generator/nanoBragg.c:3040-3066` (φ loop with `if (phi != 0.0)`)
- **Plan**: `plans/active/cli-phi-parity-shim/plan.md`
- **Fix Plan**: `docs/fix_plan.md` (CLI-FLAGS-003 L3k.3c.4)
- **Evidence**: `reports/2025-10-cli-flags/phase_l/rot_vector/` (VG-1 baseline traces)
- **Tests**: `tests/test_cli_scaling_phi0.py` (spec compliance suite)

---

## 10. Approval & Next Steps

**Design Review Checklist**:
- [X] Opt-in trigger surface defined (CLI flag + config field)
- [X] Data flow documented (CLI → config → model)
- [X] Implementation preserves vectorization (no Python loops)
- [X] Gradient/device/dtype neutrality confirmed
- [X] Validation strategy enumerated (tests + traces + nb-compare)
- [X] C-code reference extracted (CLAUDE Rule #11)
- [X] Risk assessment completed
- [X] Documentation plan outlined

**Approval**: Ready for implementation (Phase C).

**Next Actions** (per `input.md:34-36`):
1. Run collect-only selector and archive log
2. Promote chosen API through Crystal/Simulator configs (Plan C2)
3. Prepare pytest parity cases once mode exists (Plan C3)

---

**End of Design Note**
