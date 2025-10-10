# Phase B3 Validation Path Decision — Summary

**Date**: 2025-10-10T03:29:37Z
**Task**: Draft validation-path memo per `input.md` Do Now
**Mode**: Docs
**Status**: Complete

## Artifacts Generated

- `validation_path.md` — Detailed analysis of Options A/B/C with recommendation
- `commands.txt` — Documentation of context gathering and artifact creation
- `summary.md` — This file

## Recommendation Summary

**Selected Path: Option A (Un-skip test_high_resolution_variant with Golden Data)**

### Key Rationale

1. **Spec-compliant**: spec-a-parallel.md §AT-012 explicitly defines high-res variant as normative acceptance test
2. **Fast unblocking**: 1-2 hour implementation vs 4-6 hours for parity harness bootstrap (Option B)
3. **Tractable scope**: ROI-based comparison (512×512) manageable memory/time
4. **Existing pattern**: Follows same structure as other AT-012 variants (load golden, run PyTorch, compare)
5. **Single truth**: Eliminates benchmark (0.721) vs nb-compare (0.06) tool discrepancy

### Implementation Checklist (Phase B3.1-B3.3)

1. Generate 4096² golden data via C binary:
   ```bash
   ./golden_suite_generator/nanoBragg \
     -lambda 0.5 \
     -cell 100 100 100 90 90 90 \
     -N 5 \
     -default_F 100 \
     -distance 500 \
     -detpixels 4096 \
     -pixel 0.05 \
     -floatfile tests/golden_data/high_resolution_4096/image.bin
   ```
2. Commit golden data + document generation command in `tests/golden_data/README.md`
3. Implement test body in `tests/test_at_parallel_012.py::test_high_resolution_variant`
4. Remove `@pytest.mark.skip` decorator
5. Run test to capture baseline FAIL metrics (expect correlation << 0.95)

### Acceptance Thresholds (from spec)

- No NaNs/Infs
- Correlation ≥ 0.95 on 512×512 ROI
- Top N=50 peaks in ROI within ≤ 1.0 px

### Estimated Effort

- Golden data generation: ~5 minutes (4096² C binary run)
- Test implementation: ~30-60 minutes (ROI extraction, peak matching)
- Documentation: ~15 minutes (README.md update)
- **Total**: 1-2 hours

## Open Questions for Ratification

1. **Golden data storage**: Commit 64MB .bin to repo or generate on-demand per CI run?
   - Recommendation: Commit to repo (acceptable for git-lfs or raw)
2. **Tolerance during debugging**: Use spec threshold (0.95) even though current correlation ~0.06-0.72?
   - Recommendation: Yes, use spec threshold; XFAIL until regression fixed
3. **ROI centering**: How to compute "512×512 ROI centered on beam"?
   - Recommendation: beam_center_mm → pixels, extract [center-256:center+256, center-256:center+256]

## Blockers Lifted (once implemented)

- Phase B4 (ROI scope checks) can proceed with authoritative pytest baseline
- Phase C (trace localization) has single correlation measurement (no tool discrepancy)
- [VECTOR-GAPS-002] and [PERF-PYTORCH-004] unblock once correlation ≥0.999 restored

## Next Loop Actions (supervisor handoff)

1. **Ratify path choice** in `input.md` (confirm Option A or request alternative)
2. **Phase B3.1** (next ralph loop): Generate golden data, commit artifacts
3. **Phase B3.2** (next ralph loop): Implement test, remove skip
4. **Phase B4** (after B3): ROI scope checks via nb-compare --roi

## Context Summary

- Prior evidence: Phase B2 (`20251010T031841Z`) confirmed 0 active 4096² pytest coverage
- Regression metrics: Phase B1 attempts #2-#4 show correlation 0.06-0.72, sum_ratio 225-236x
- Spec reference: `specs/spec-a-parallel.md:90-99` (AT-PARALLEL-012 high-res variant)
- Test stub: `tests/test_at_parallel_012.py:364-377` (skip + requirements docstring)
