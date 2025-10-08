# Option 1 φ-Carryover Cache Design Refresh

**Date:** 2025-12-08
**Loop:** Ralph i=156 (docs mode)
**Phase:** CLI-FLAGS-003 Phase M2g.1
**Purpose:** Design refresh ahead of Option 1 architecture decision (Action 0)

## Executive Summary

This memo refreshes the Option 1 (Pixel-Indexed Cache) design requirements per supervisor directive ([CLI-FLAGS-003](#context) Phase M2g.1), consolidates spec citations (lines 205-233) and prior diagnosis notes (`phi_carryover_diagnosis.md`), and tees up the architecture decision matrix for next loop.

**Key Findings:**
1. **Spec baseline:** `specs/spec-a-core.md:211-213` mandates fresh φ rotations each step from reference lattice (a0,b0,c0) → carryover is C-only bug.
2. **Option 1 feasibility:** Pixel-indexed cache remains architecturally sound (memory ~224 MB supervisor case @ float32, ROI-friendly).
3. **New blocker (Attempt #155):** Rotation tensor shapes lack pixel dimension required for per-pixel φ carryover.
4. **Decision required:** Choose architecture variant (A/B/C) before M2g.3–M2g.6.

---

## 1. Spec Baseline (Normative φ Semantics)

### Relevant Spec Lines (specs/spec-a-core.md:211-213)

```
φ step: φ = φ0 + (step index)*phistep; rotate the reference cell (a0,b0,c0)
about u by φ to get (ap,bp,cp).
Mosaic: for each domain, apply the domain's rotation to (ap,bp,cp) to get (a,b,c).
```

**Interpretation:** Every φ step computes fresh rotations from the canonical reference vectors (a0,b0,c0). No accumulation or carryover semantics exist in the spec — PyTorch default path must ignore the C carryover bug (C-PARITY-001).

**Implication for parity shim:** The opt-in `phi_carryover_mode="c-parity"` reproduces the bug to match golden C data, but `mode="spec"` (default) follows the quoted normative contract.

### Documented C Bug (verified C-PARITY-001)

**Source:** `docs/bugs/verified_c_bugs.md:166-204`
**Symptom:** `nanoBragg.c:3044-3095` skips φ=0 rotation, reusing thread-local vectors from prior pixel's φ=final.
**Reproduction:** Golden supervisor command with `-phi 0 -phisteps 10 -osc 1.0` produces distinct φ=0 F_latt vs spec recomputation.
**Parity shim landed:** Attempts #120/#121 (`--phi-carryover-mode c-parity` CLI flag).

---

## 2. Option 1 Design Summary (from phi_carryover_diagnosis.md)

### 2.1 Core Concept

**Pixel-Indexed Cache with Deferred Substitution** — Store φ=final vectors per (s,f,m) and substitute them into φ=0 slot during physics computation.

### 2.2 Cache Tensor Shape

```python
_phi_cache_a/b/c: (S, F, N_mos, 3)
    S     = detector.spixels  (slow pixels, e.g., 2527)
    F     = detector.fpixels  (fast pixels, e.g., 2463)
    N_mos = mosaic_domains    (e.g., 1 for supervisor, 10 max typical)
    3     = vector components (x, y, z)
```

**Memory cost (float32):**
- Supervisor full-frame: 3 vectors × 2527 × 2463 × 1 × 3 × 4 bytes = **224 MB**
- With N_mos=10: 3 × 2527 × 2463 × 10 × 3 × 4 = **2.24 GB**
- ROI (56×56): 3 × 56 × 56 × 1 × 3 × 4 = **113 KB** (negligible)

**Allocation strategy:**
- Device: same as crystal base vectors (follows caller device/dtype)
- Timing: allocate at first `run()` when detector dimensions known
- Invalidation: clear on detector geometry change or crystal cell parameter change

### 2.3 C-Code Equivalent (OpenMP `firstprivate`)

**Reference:** `nanoBragg.c:2797-2800` and `3044-3095`

```c
#pragma omp parallel for ... firstprivate(ap,bp,cp,...)
for(pixel_i=0; pixel_i < num_pixels; ++pixel_i) {  // Thread-local loop
    for(phi_tic=0; phi_tic<phisteps; ++phi_tic) {
        phi = phi0 + phistep*phi_tic;
        if( phi != 0.0 ) {
            rotate_axis(a0,ap,spindle_vector,phi);  // Update ap/bp/cp
        }
        // When phi==0: ap/bp/cp retain PREVIOUS PIXEL's φ=final values
    }
}
```

**Semantics:** Thread processes pixels sequentially → per-thread state persists across pixel iterations. PyTorch equivalent requires explicit (s,f)-indexed cache to simulate thread-local persistence.

### 2.4 Integration Points (from diagnosis.md §Option 1)

**Original proposal (Option 1A):**
```python
Simulator.run()
  └─ for slow in range(detector.spixels):
      └─ for fast in range(detector.fpixels):
          ├─ rotated_vecs = crystal.get_rotated_real_vectors()  # Fresh compute
          ├─ if phi_carryover_mode == "c-parity":
          │   └─ rotated_vecs = crystal.apply_phi_carryover(slow, fast, rotated_vecs)
          ├─ _compute_physics_for_position(pixel, rotated_vecs)
          └─ crystal.store_phi_final(slow, fast, rotated_vecs[-1])  # Save for next pixel
```

**Problem (Attempt #155):** Current vectorized path computes rotations once for entire run (`(N_phi, N_mos, 3)` shape); pixel coordinates never reach rotation methods.

---

## 3. New Architectural Blocker (Attempt #155 Finding)

### 3.1 Current Vectorization Flow

```python
# Simulator.run() line ~820 (hypothetical)
rotated_real, rotated_recip = crystal.get_rotated_real_vectors(crystal_config)
# Shape: (N_phi, N_mos, 3) - computed ONCE for entire image

# All pixels (s,f) use the SAME rotation tensor:
for s in range(spixels):
    for f in range(fpixels):
        # Same `rotated_real` for all (s,f) → no per-pixel carryover
        physics_result = _compute_physics_for_position(s, f, rotated_real)
```

**Observation:** Rotation tensors lack a pixel dimension — they're global per-run, not per-pixel.

### 3.2 Architecture Mismatch

To achieve per-pixel φ carryover, rotation methods need access to (s,f) coordinates. Three variants:

**Option A — Add Pixel Dims to Rotation Stack:**
```python
rotated_real: (S, F, N_phi, N_mos, 3)  # ❌ Explodes memory (~100 GB for supervisor)
```

**Option B — Batch-Process with Explicit Indexing:**
```python
# Compute rotations per-pixel-batch (e.g., vectorize over s dimension):
for f_batch in batches(fpixels):
    rotated_real_batch = crystal.get_rotated_real_vectors_for_pixels(s_range, f_batch)
    # Apply cached φ=0 substitution per (s,f) within batch
```

**Option C — Alternative Integration Point:**
```python
# Defer rotation computation until physics loop:
for s, f in pixels:
    if phi_carryover_mode == "c-parity" and cache_valid[s,f]:
        rotated_real = cache[s,f]  # Retrieve cached φ=final from prior pixel
    else:
        rotated_real = crystal.get_rotated_real_vectors_fresh(phi_steps)
        cache[s,f] = rotated_real[-1]  # Store φ=final for next pixel
```

### 3.3 Constraints from Prior Design (diagnosis.md §1.4)

1. **Gradient preservation (CLAUDE Rule #8-10):** No `.detach()`, functional indexing, @property pattern.
2. **Vectorization (CLAUDE Rule #16):** No Python loops in hot path; preserve batched tensor flows.
3. **Device/dtype neutrality:** Cache must follow caller device/dtype.
4. **Memory acceptable:** ~224 MB supervisor @ float32 is OK; 100 GB is not.

**Upshot:** Option A violates memory constraints. Options B/C trade vectorization purity for per-pixel semantics.

---

## 4. Architecture Decision Matrix (To Be Filled Next Loop)

### 4.1 Option A: Expand Rotation Stack Shape

| Dimension | Pros | Cons |
|-----------|------|------|
| Implementation | Minimal API changes | ❌ Memory explosion (100 GB supervisor) |
| Gradients | ✅ Preserves graph | ❌ OOM on large detectors |
| Vectorization | ✅ Pure batched ops | ❌ Impractical for >1024² |
| **Verdict** | — | **REJECT** (memory infeasible) |

### 4.2 Option B: Batch-Indexed Rotation Helper

| Dimension | Pros | Cons |
|-----------|------|------|
| Implementation | Medium complexity | ⚠️ Requires refactoring call sites |
| Gradients | ✅ Preserves if done carefully | ⚠️ Advanced indexing needs care |
| Vectorization | ⚠️ Partial (batch level) | ⚠️ More loops than pure broadcast |
| Memory | ✅ ROI-friendly (~10–100 MB) | — |
| **Verdict** | **FEASIBLE** | Needs design iteration for gradient safety |

### 4.3 Option C: Deferred Per-Pixel Rotation

| Dimension | Pros | Cons |
|-----------|------|------|
| Implementation | Simple semantics | ❌ May break mandatory vectorization (CLAUDE Rule #16) |
| Gradients | ✅ Direct caching | ⚠️ Gradient checks still required |
| Vectorization | ❌ Sequential pixel loop | ❌ 10-100× slower (documented in diagnosis.md) |
| Memory | ✅ Cache same as Option B | — |
| **Verdict** | **REJECT** | Violates vectorization mandate |

### 4.4 Recommendation (To Be Finalized)

**Preliminary:** Option B (batch-indexed helper) is the only architecturally compliant path. Requires:
1. Define batch granularity (per-row? per-column? tile?)
2. Design `get_rotated_real_vectors_for_pixels(s_idx, f_idx)` API
3. Wire cache lookup/store into batch loop
4. Validate gradients with small (2×2) ROI test

**Next actions:** Draft detailed Option B design in separate memo, simulate memory/timing, then revisit this matrix.

---

## 5. Spec Citation Record (for C5 summary.md)

Per supervisor guidance (`plans/active/cli-phi-parity-shim/plan.md:54`), the Phase C5 `summary.md` must cite these lines:

**specs/spec-a-core.md:211-213:**
> φ step: φ = φ0 + (step index)*phistep; rotate the reference cell (a0,b0,c0) about u by φ to get (ap,bp,cp).

**Interpretation:** The spec requires fresh rotation from (a0,b0,c0) every step — no mention of carryover. PyTorch default (`phi_carryover_mode="spec"`) implements this contract exactly. The c-parity shim reproduces the C bug for golden data matching only.

**Action for C5:** Include this quote + interpretation in the summary memo; cross-link to `docs/bugs/verified_c_bugs.md` C-PARITY-001 classification.

---

## 6. Cache Design Requirements Summary

### 6.1 Functional Requirements (from diagnosis.md)

1. **Storage:** Per-pixel φ=final vectors keyed by (s, f, mosaic_domain)
2. **Retrieval:** Substitute cached vectors into φ=0 slot for next pixel
3. **Lifecycle:** Allocate on first run, invalidate on geometry/cell change
4. **Scope:** c-parity mode only; spec mode ignores cache entirely

### 6.2 Non-Functional Requirements

1. **Memory:** ≤ 500 MB full-frame @ float32, ROI-scalable
2. **Gradients:** Preserve `requires_grad` through cache ops
3. **Vectorization:** No sequential pixel loops (CLAUDE Rule #16)
4. **Devices:** CPU/CUDA neutral, no hard-coded `.cpu()/.cuda()`

### 6.3 Open Questions (for Architecture Decision)

- [ ] How to batch rotation computation without full (S,F,...) tensor?
- [ ] Where to insert cache lookup (Crystal method vs Simulator loop)?
- [ ] How to handle ROI changes mid-run (cache subset vs full realloc)?
- [ ] Gradient check strategy for batched indexing?

---

## 7. Delta from Prior Diagnosis (phi_carryover_diagnosis.md)

### What's New in This Refresh

1. **Blocker discovery (Attempt #155):** Rotation stack shape mismatch documented
2. **Architecture matrix:** Three options (A/B/C) enumerated with pros/cons
3. **Spec citation:** Explicit quote from lines 211-213 for C5 handoff
4. **Memory estimates:** Refined with supervisor case numbers

### What Remains Unchanged

1. C-code reference (lines 2797, 3044-3095) still accurate
2. Memory footprint math (224 MB @ float32) confirmed
3. Gradient preservation requirements (no .detach()) still apply
4. Test plan (M2h multi-pixel gradcheck) still valid

---

## 8. Next Actions (Architecture Decision Sequence)

### Immediate (Next Loop — Ralph)

1. **Design Option B variant:** Draft `option_b_batch_design.md` with:
   - Batch granularity choice (row-wise? tile?)
   - API signature for `get_rotated_real_vectors_for_pixels(...)`
   - Cache integration pseudocode
   - Memory/gradient tradeoffs

2. **Simulate small case:** Prototype 4×4 ROI with batch approach:
   - Measure memory overhead vs vectorized baseline
   - Run gradcheck on cell parameter
   - Profile runtime (ensure no >2× slowdown)

3. **Document decision:** Once Option B design validates, update this memo with chosen variant and proceed to M2g.3–M2g.6 implementation.

### Phase Handoff (Galph)

- Incorporate findings into `plans/active/cli-noise-pix0/plan.md` Phase M2g decision point
- Update `docs/fix_plan.md` CLI-FLAGS-003 with architecture blocker note
- Link this memo from C5 `summary.md` when documenting carryover shim

---

## 9. References

### Specifications & Design Docs

- `specs/spec-a-core.md:205-233` — Normative φ rotation pipeline
- `docs/bugs/verified_c_bugs.md:166-204` — C-PARITY-001 classification
- `reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md` — Original Option 1 proposal
- `plans/active/cli-phi-parity-shim/plan.md` — Parity shim plan (Phases A–D)
- `plans/active/cli-noise-pix0/plan.md:59-108` — Parent plan Phase M tasks

### C-Code References (CLAUDE Rule #11)

- `nanoBragg.c:2797-2800` — OpenMP `firstprivate(ap,bp,cp,...)` declaration
- `nanoBragg.c:3044-3095` — Conditional rotation skip (`if(phi != 0.0)`)

### Implementation Files

- `src/nanobrag_torch/models/crystal.py:1084-1128` — Current c-parity shim (landed Attempt #120)
- `src/nanobrag_torch/simulator.py:~820` — Rotation call site (hypothetical line number)
- `tests/test_cli_scaling_phi0.py` — Spec baseline tests (VG-1 gate)
- `tests/test_phi_carryover_mode.py` — Dual-mode validation tests

### Evidence Artifacts

- `reports/2025-10-cli-flags/phase_l/rot_vector/20251007T231515Z/` — Spec baseline (Phase A evidence)
- `reports/2025-10-cli-flags/phase_l/parity_shim/20251201_dtype_probe/` — Tolerance decision (Attempt #130)
- `reports/2025-10-cli-flags/phase_l/per_phi/20251008T100653Z/` — Two-pixel carryover probe (M2d evidence)

---

## 10. Appendix: Rotation Stack Shape Analysis

### Current Implementation (Vectorized, No Per-Pixel State)

```python
# Crystal.get_rotated_real_vectors()
phi_angles = phi0 + torch.arange(phi_steps) * phistep  # Shape: (N_phi,)
rotation_matrices = compute_rotation_matrix(spindle_axis, phi_angles)  # (N_phi, 3, 3)
rotated_a = torch.einsum('pij,j->pi', rotation_matrices, base_a)  # (N_phi, 3)
# Mosaic: expand to (N_phi, N_mos, 3) if needed
# Result: rotated_a has NO pixel dimension
```

**Problem for carryover:** All pixels share the same `rotated_a[0]` (φ=0 slice) → no way to substitute per-pixel cached values.

### Required for Option 1 (Per-Pixel Cache Substitution)

```python
# Desired API (hypothetical)
def get_rotated_real_vectors_for_pixels(self, s_indices, f_indices, phi_steps, ...):
    # Return: (len(s_indices), len(f_indices), N_phi, N_mos, 3)
    # Allows: cache lookup at rotated_a[s,f,0] for φ=0 substitution
```

**Memory cost for full-frame:** (2527, 2463, 10, 1, 3) × 4 bytes = **747 MB per vector × 3 = 2.24 GB**

**Option B compromise:** Batch over one dimension (e.g., process row-by-row), reducing peak memory to ~1 MB per row while preserving vectorization within the batch.

---

## Metadata

- **Commit SHA:** (to be recorded post-commit)
- **Test Collection:** ✅ `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q` passed (35 tests collected)
- **Mode:** Docs (no code changes per input.md directive)
- **Artifacts Directory:** `reports/2025-10-cli-flags/phase_l/scaling_validation/20251208_option1_refresh/`
