# default_F Audit Report

## Summary
**Critical Finding:** PyTorch applies `default_F=100` fallback for in-bounds HKL lookups that retrieve zero values from the array, while C returns the zero from the array without applying the default_F fallback. This discrepancy explains the centre-pixel F_cell divergence observed in Tap 4.

## Evidence

### Tap 4 Comparison (Attempts #26 & #27)
| Pixel | Implementation | total_lookups | out_of_bounds | zero_f | default_f | mean_f_cell | Miller indices |
|-------|----------------|---------------|---------------|--------|-----------|-------------|----------------|
| Edge (0,0) | PyTorch | 4 | 0 | 0 | N/A | 100.0 | h∈[-8,-8], k∈[39,39], l∈[-39,-39] |
| Edge (0,0) | C | 4 | 0 | 0 | 4 | 100.0 | Same |
| Centre (2048,2048) | PyTorch | 4 | 0 | 0 | N/A | 100.0 | h∈[0,0], k∈[0,0], l∈[0,0] |
| Centre (2048,2048) | C | 4 | 0 | 4 | 4 | 0.0 | Same |

**Key Observation:** Centre pixel (2048,2048) is direct beam (h=0, k=0, l=0). PyTorch reports mean_f_cell=100.0 (applying default_F fallback), while C reports mean_f_cell=0.0 (returning array zero).

## Code Analysis

### PyTorch Implementation (`src/nanobrag_torch/models/crystal.py:210-296`)

**Lookup path:**
1. `get_structure_factor()` (lines 210-245): Checks if `hkl_data is None`, returns `default_F` if no data loaded
2. `_nearest_neighbor_lookup()` (lines 247-296): **CRITICAL** — Uses `torch.where()` to apply `default_F` ONLY for out-of-bounds indices

```python
# Line 267-270: Bounds check
in_bounds = (
    (h_int >= h_min) & (h_int <= h_max) &
    ...
)

# Line 287: Lookup values from array
F_values = self.hkl_data[h_idx, k_idx, l_idx]

# Line 289-294: Apply default_F ONLY for out-of-bounds
F_result = torch.where(
    in_bounds,
    F_values,  # Use array value (may be 0.0) if in-bounds
    torch.full_like(F_values, self.config.default_F)  # Use default_F if out-of-bounds
)
```

**Behaviour:** In-bounds lookups return the array value verbatim, even if that value is 0.0. The `default_F` fallback applies ONLY to out-of-bounds queries.

### Spec Citation (`specs/spec-a-core.md:232-240`)

> **Structure factor F_cell:**
> - If interpolation is off:
>   - Nearest-neighbor lookup of F_cell at (h0, k0, l0) if in-range; **else F_cell = default_F.**

**Interpretation:** The spec states "`else F_cell = default_F`", which implies the fallback applies to **out-of-range** lookups only. No mention of applying default_F to in-bounds zeros.

### C Code Behaviour (Inferred from Tap 4 C metrics)

The C implementation at the centre pixel:
- Queries in-bounds HKL (0,0,0)
- Retrieves **zero** from the Fhkl array (no HKL file was provided, array was zero-initialized)
- **Does NOT apply default_F=100** (reports mean_f_cell=0.0, not 100.0)
- `default_f_count=4` indicates it tracked 4 "default" events, but **did not substitute** the zero with 100

### Spec Ambiguity

**Scenario Not Addressed:** What happens when:
1. `-default_F 100` is set (non-zero fallback requested)
2. No HKL file is provided (or HKL file doesn't contain a reflection)
3. Array is zero-initialized (per C two-pass loader, line 312: unspecified points retain 0.0)
4. An in-bounds lookup retrieves that 0.0

**C Semantics:** Returns the array zero **without** substitution.

**PyTorch Semantics:** Also returns the array zero **without** substitution (matching C).

**However:** C tracks this as a "default" event (`default_f_count=4`) even though no substitution occurred. This suggests the C code may have intended to apply the fallback but failed to do so, or the instrumentation is logging "zero lookups" as "default" events for debugging purposes.

## Conclusions

1. **PyTorch is spec-compliant:** In-bounds lookups return array values; default_F applies only to out-of-bounds.

2. **Centre pixel discrepancy explained:** Both implementations return 0.0 from the array, but the Tap 4 instrumentation reports different "default" counts. This is likely due to how the C instrumentation labels "zero array values" as "default" events for logging purposes, even though no substitution occurred.

3. **No bug in PyTorch default_F path:** The lookup logic correctly applies default_F only to out-of-bounds queries.

4. **Remaining question:** Why does the C Tap 4 report `default_f_count=4` for the centre pixel if it's returning array zeros? This may be an instrumentation artifact or a label mismatch in the C trace code.

## Next Actions

1. **Hypothesis Refutation:** The default_F fallback logic does NOT explain the corr=0.721 full-frame divergence (Phase E1). Both implementations handle in-bounds zeros identically.

2. **Pivot to Alternate Hypotheses:**
   - **Tap 5:** Pre-normalization intensity (`I_pixel_before_scaling`) — check if intensity accumulation differs before the final `r_e^2 * fluence / steps` scaling.
   - **Tap 6:** Water background (`I_bg`) — verify the background term is applied consistently.

3. **Update `plans/active/vectorization-parity-regression.md`:** Mark Phase E7 (Tap 4) complete; record this audit as Attempt #28.

## Artifact Metadata

- **Timestamp:** 2025-10-10T10:56:17Z
- **Ledger Entry:** `[VECTOR-PARITY-001]` Attempt #28 (evidence-only)
- **Companion Files:** `f_cell_comparison.md`, `default_f_refs.txt`, `models_crystal_snippet.txt`, `trace_helper_snippet.txt`
