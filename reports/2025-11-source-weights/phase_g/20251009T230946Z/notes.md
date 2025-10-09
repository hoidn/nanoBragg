# Phase G0: Fixture Harmonization

Sanitized fixture: /home/ollie/Documents/tmp/nanoBragg/reports/2025-11-source-weights/fixtures/two_sources_nocomments.txt
SHA256: f23e1b1e60412c5378ee197542e0aca1ffc658198edd4e9584a3dffb57330c44

## Rationale

The original fixture from Phase A (20251009T071821Z) includes comment lines that trigger a known C parsing bug ([C-SOURCEFILE-001]). The C code treats comment lines as valid sources with (0,0,0) position and zero weight, which distorts the normalization divisor.

This sanitized variant removes comment lines to allow parity testing before the C bug is fixed. The test geometry (two sources, Z=10.0, weights [1.0, 0.2]) is preserved exactly.

## Hand-off

Related bug: [C-SOURCEFILE-001] - C sourcefile comment parsing bug
Plan: plans/active/c-sourcefile-comment-parsing.md

## Diff Summary

The sanitized fixture removes 2 comment lines (lines 1-2 of the original):
- Line 1: `# Weighted two-source fixture`
- Line 2: `# X Y Z weight wavelength(m)`

Data lines are preserved identically. See `fixture_diff.patch` for full details.

## Test Geometry Verification

Both fixtures define:
- Source 1: position (0.0, 0.0, 10.0), weight 1.0, λ=6.2e-10 m
- Source 2: position (0.0, 0.0, 10.0), weight 0.2, λ=6.2e-10 m

Per `specs/spec-a-core.md:151`, weights and wavelength columns are **ignored** by both C and PyTorch implementations. The CLI `-lambda` parameter overrides per-source wavelengths, and equal weighting results (division by source count).

## Next Steps (Phase G1)

With the sanitized fixture in place, Phase G1 can proceed:
1. Canonicalize PyTorch + C commands using `two_sources_nocomments.txt`
2. Force `-interpolate 0` (or supply minimal HKL) to avoid C segfault
3. Run both binaries and verify they execute without crashing
4. Proceed to Phase G2 for full parity bundle capture
