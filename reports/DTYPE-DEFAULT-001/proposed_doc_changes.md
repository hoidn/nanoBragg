# DTYPE-DEFAULT-001 Proposed Documentation Changes

**Date:** 2025-09-30
**Phase:** A2 - Spec/Architecture Reconciliation
**Status:** Complete

## Current State Analysis

### arch.md Current Statements

1. **Line 5** (Header):
   ```
   Implementation target: Python (>=3.11) + PyTorch (float64 default).
   ```

2. **Line 313** (Section 14 - Implementation-Defined Defaults):
   ```
   - dtype: float64 tensors for numerical stability, with `.to(dtype=...)` promoted when needed.
   ```

3. **Line 361** (Section 15.3 - Testing Requirements):
   ```
   4. **Use `torch.autograd.gradcheck`:** With `dtype=torch.float64` for numerical precision
   ```

### Current Documentation Conflicts

**Conflict**: The architecture states "float64 default" but:
- Long-term goal (per prompts): float32 default for performance
- PERF-PYTORCH-004 initiative: Memory/speed optimization
- Industry standard: float32 for deep learning production

**Resolution**: Update docs to reflect float32 default with float64 opt-in for precision-critical paths.

## Proposed Changes

### 1. arch.md - Header (Line 5)

**Current:**
```markdown
Implementation target: Python (>=3.11) + PyTorch (float64 default). Type blocks may use TypeScript-style for clarity; implement with Python dataclasses and torch tensors.
```

**Proposed:**
```markdown
Implementation target: Python (>=3.11) + PyTorch (float32 default; float64 available for gradient checks). Type blocks may use TypeScript-style for clarity; implement with Python dataclasses and torch tensors.
```

**Rationale:**
- Clearly states the new default
- Preserves the opt-in path for high-precision work
- Aligns with performance goals

### 2. arch.md - Section 14 (Line 313)

**Current:**
```markdown
- dtype: float64 tensors for numerical stability, with `.to(dtype=...)` promoted when needed.
```

**Proposed:**
```markdown
- dtype: float32 tensors by default for performance (~2× memory reduction, ~1.5× speedup); float64 available via explicit `dtype=torch.float64` override for gradient checks and high-precision validation. Use `.to(dtype=...)` or `.type_as()` for dtype promotion when needed.
```

**Rationale:**
- Quantifies performance benefits
- Makes opt-in path explicit
- Maintains guidance on dtype handling

### 3. arch.md - Section 15.3 (Line 361)

**Current:**
```markdown
4. **Use `torch.autograd.gradcheck`:** With `dtype=torch.float64` for numerical precision
```

**Proposed:**
```markdown
4. **Use `torch.autograd.gradcheck`:** Always with explicit `dtype=torch.float64` for numerical precision (gradcheck requires higher precision than production runs)
```

**Rationale:**
- Emphasizes the requirement for explicit dtype
- Clarifies that gradcheck is an exception to the float32 default
- **No functional change** - this section already correctly specifies float64

### 4. docs/development/pytorch_runtime_checklist.md

**New Section to Add:**

```markdown
## 1.5 Default Dtype Policy

**Default precision:** float32
- Production simulation runs use float32 for optimal performance
- Memory usage: ~50% reduction vs float64
- Speed: ~30-50% faster on modern GPUs

**Float64 opt-in for:**
- Gradient checks (`torch.autograd.gradcheck`)
- High-precision validation tests
- Numerical stability investigations

**CLI override:**
```bash
# Force float64 for debugging
nanoBragg -dtype float64 [other args...]

# Default float32 (fast)
nanoBragg [args...]
```

**Code pattern:**
```python
# Gradient check (requires float64)
phi = torch.tensor(10.0, requires_grad=True, dtype=torch.float64)

# Production run (uses default float32)
config = CrystalConfig(cell_a=100.0)  # Will use float32
```
```

**Rationale:**
- Provides clear guidance for developers
- Documents the two precision modes
- Shows concrete usage examples

### 5. CLAUDE.md

**Current Line 435** (Memory and Performance Considerations):
```markdown
### PyTorch Port
- Memory-intensive vectorization strategy with batching fallback
- GPU acceleration for tensor operations
- Configurable precision (float32/float64) and batching for memory management
```

**Proposed:**
```markdown
### PyTorch Port
- Memory-intensive vectorization strategy with batching fallback
- GPU acceleration for tensor operations
- **Default precision: float32** (configurable via `-dtype` flag; use float64 for gradient checks)
- Batching support for memory management
```

**Rationale:**
- Makes default explicit in user-facing docs
- Preserves configurability message
- Links to gradient check use case

### 6. README_PYTORCH.md (if exists)

**Section to Add/Update:** CLI Usage

```markdown
### Precision Control

By default, nanoBragg runs in **float32** precision for optimal performance:

```bash
# Default (float32) - fastest
nanoBragg -cell 100 100 100 90 90 90 -lambda 1.0 -distance 100 -detpixels 256

# Explicit float64 - for high-precision work
nanoBragg -dtype float64 -cell 100 100 100 90 90 90 -lambda 1.0 -distance 100 -detpixels 256
```

**Performance comparison:**
- float32: ~2× less memory, ~30-50% faster
- float64: Higher numerical precision, required for gradient checks

**When to use float64:**
- Debugging numerical stability issues
- Running gradient-based optimization (`torch.autograd.gradcheck`)
- Validating against C reference with high correlation thresholds
```

**Rationale:**
- User-facing documentation
- Clear performance trade-offs
- Actionable guidance

## Spec Alignment

### specs/spec-a-core.md

**Current:** No explicit dtype requirement found in normative spec.

**Action:** No change needed. The spec is implementation-agnostic on floating-point precision. The choice of float32 vs float64 is an implementation detail covered by arch.md.

### specs/spec-a-parallel.md

**Current:** Correlation thresholds (e.g., ≥0.9999) are dtype-agnostic.

**Action:** No change needed. Float32 should meet or exceed these thresholds based on AT-PARALLEL-012 results (correlation=1.0 even with float32 peak detection).

## Testing Strategy Implications

### Test Files Needing Explicit dtype=torch.float64

1. **tests/test_crystal_geometry.py**
   - `TestMetricDuality.test_metric_duality_grad`
   - Other gradcheck tests

2. **tests/test_gradients.py** (if exists)
   - All gradient checks

3. **tests/test_detector_geometry.py**
   - Gradient flow tests

**Pattern:**
```python
# Before (relied on default)
phi = torch.tensor(10.0, requires_grad=True)

# After (explicit dtype)
phi = torch.tensor(10.0, requires_grad=True, dtype=torch.float64)
```

### Tests That Should Use Default (float32)

1. **tests/test_at_parallel_*.py** - All acceptance tests
2. **tests/test_parity_matrix.py** - Parallel validation
3. **Integration tests** - Production scenarios

**No code changes needed** - these tests will automatically use the new float32 default.

## Rollout Communication

### Developer Notification

**Message for CLAUDE.md update:**

```markdown
### Recent Changes (2025-09-30)

**DTYPE-DEFAULT-001:** Default precision changed to float32
- **Impact:** All new simulation runs use float32 by default
- **Benefits:** ~2× memory reduction, ~30-50% faster execution
- **Migration:** Gradient tests must explicitly request `dtype=torch.float64`
- **Opt-out:** Use `-dtype float64` CLI flag for high-precision work
- **Reference:** See `docs/development/pytorch_runtime_checklist.md` §1.5
```

### Prompt Updates

**prompts/debug.md** - Add reminder:
```markdown
## Debugging Dtype-Sensitive Issues

If you suspect a numerical precision issue:
1. Rerun with `-dtype float64` to check if issue persists
2. Compare float32 vs float64 correlation
3. Check if issue appears in gradient checks (these always use float64)
```

## Phase A2 Exit Criteria Checklist

- [x] Current arch.md dtype statements catalogued (3 locations)
- [x] Conflicts identified (states float64, goal is float32)
- [x] Proposed changes drafted for all affected docs
- [x] Spec alignment verified (no conflicts)
- [x] Testing strategy impacts documented
- [x] Rollout communication plan defined

**Ready for supervisor sign-off and Phase B implementation.**
