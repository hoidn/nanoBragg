# Lambda Sweep Experiment Summary
## SOURCE-WEIGHT-001 Phase E Task E2

**Date:** 2025-12-09T13:04:33Z
**Commit:** d4206cd6af67599fa7d3e214720a6c9566d90f9d
**Branch:** feature/spec-based-2

## Hypothesis

PyTorch honors the sourcefile wavelength column (6.2 Å) while the C reference uses CLI `-lambda` (0.9768 Å), causing ~300× intensity inflation in weighted source tests.

## Experimental Design

Two PyTorch CLI runs with identical parameters except sourcefile wavelength:

1. **lambda62**: Sourcefile with wavelength 6.2e-10 m (6.2 Å)
2. **lambda09768**: Sourcefile with wavelength 9.768e-11 m (0.9768 Å)

Both runs use CLI `-lambda 0.9768` to test which wavelength source PyTorch actually uses.

## Results

| Fixture | Sourcefile λ (Å) | CLI λ (Å) | Total Sum | Max Intensity | Non-zero Pixels |
|---------|------------------|-----------|-----------|---------------|-----------------|
| lambda62 | 6.2 | 0.9768 | 2.53e5 | 168.4 | 65159 |
| lambda09768 | 0.9768 | 0.9768 | 0.0 | 0.0 | 0 |

## Findings

### Critical Discovery

**PyTorch DOES honor the sourcefile wavelength column, producing vastly different results:**

- **lambda62 (6.2 Å)**: Strong diffraction signal with 253k total intensity
- **lambda09768 (0.9768 Å)**: Complete absence of signal (ZERO intensity)

This confirms the hypothesis: PyTorch reads and uses the sourcefile wavelength values, while the C reference implementation ignores them in favor of the CLI `-lambda` parameter.

### Intensity Ratio Analysis

The wavelength ratio is:
- λ₁ / λ₂ = 6.2 / 0.9768 ≈ 6.35

The expected Bragg condition shift would move diffraction peaks completely out of the detector frame when wavelength changes by this factor, explaining the zero signal in the lambda09768 case.

### Spec Violation

Per `specs/spec-a-core.md:151`:
> "The weight column is read but ignored."

The spec does not explicitly state that the **wavelength column** should be ignored, but the C reference implementation treats it as metadata only, using CLI `-lambda` for all physics calculations.

## Implications

1. **Parity Failure Root Cause**: The 140-300× divergence in TC-D1/TC-D3 tests is caused by PyTorch using sourcefile wavelengths (6.2 Å) instead of CLI wavelength (0.9768 Å).

2. **Implementation Gap**: PyTorch's `source_wavelengths` field is populated from the sourcefile and used directly in physics calculations, diverging from C behavior.

3. **Required Fix**: PyTorch must ignore sourcefile wavelengths and use only the CLI `-lambda` parameter, matching C semantics.

## Recommended Actions

1. **Update PyTorch Implementation**: Modify sourcefile parsing to ignore wavelength column values and populate `source_wavelengths` from CLI `-lambda` only.

2. **Add Validation**: Emit a warning when sourcefile contains wavelength values that differ from CLI `-lambda`.

3. **Rerun Parity Tests**: After fix, regenerate TC-D1/TC-D3 metrics to confirm correlation ≥0.999 and sum_ratio ≈1.0.

4. **Update Spec**: Clarify in `specs/spec-a-core.md` that both weight AND wavelength columns in sourcefiles are read but ignored.

## Artifacts

- Commands: `lambda62/commands.txt`, `lambda09768/commands.txt`
- Metrics: `lambda62/metrics.json`, `lambda09768/metrics.json`
- Environment: `lambda62/env.json`
- Output logs: `lambda62/py_stdout.log`, `lambda09768/py_stdout.log`
- Float images: `/tmp/py_lambda62.bin`, `/tmp/py_lambda09768.bin`

## Next Steps (Phase E Task E3)

**BLOCKED** until wavelength-handling fix is implemented. Once PyTorch ignores sourcefile wavelengths:

1. Execute synchronized PyTorch+C reruns with corrected fixture
2. Compute correlation/sum_ratio for TC-D1/TC-D3
3. Verify parity thresholds (corr ≥0.999, |sum_ratio-1| ≤1e-3)
4. Capture trace inputs for any remaining deviations
