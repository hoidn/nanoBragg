# Metrics Refresh: CLI-FLAGS-003 M2i.2

**Timestamp:** 20251008T174022Z
**Phase:** CLI-FLAGS-003 M2i.2 (Carryover Probe)
**Purpose:** Quantify cache-enabled trace against C baseline before touching simulator code

## Execution Context

**Git SHA:** 313f29d01d397a8f3e8aa6a701aa939abcfd31a4
**Branch:** feature/spec-based-2
**Environment:**
- Python: 3.13.7
- PyTorch: 2.8.0+cu128
- CPU: AMD Ryzen 9 5950X 16-Core Processor

## Command Executed

```bash
KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python scripts/validation/compare_scaling_traces.py \
  --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log \
  --py reports/2025-10-cli-flags/phase_l/carryover_probe/20251008T172721Z/trace_py.log \
  --out reports/2025-10-cli-flags/phase_l/carryover_probe/20251008T174022Z/metrics_refresh/summary.md
```

## Key Findings

### First Divergence
**Factor:** `I_before_scaling` (Raw accumulated intensity before normalization)
- C value: 943654.809
- PyTorch value: 0.511304203
- Relative delta: -9.999995e-01 (CRITICAL)

### Divergent Factors Count
5 factors exceeded tolerance threshold (≤1.00e-06 relative)

### Critical Issues
1. **I_before_scaling**: ~1 million× mismatch (CRITICAL)
2. **I_pixel_final**: 40.9% relative error (CRITICAL)

### Minor Divergences
- **polar** (polarization factor): -2.37e-04 relative
- **omega_pixel** (solid angle): -7.72e-04 relative
- **cos_2theta**: -2.61e-04 relative

## Artifacts

- `summary.md` - Detailed factor-by-factor comparison
- `metrics.json` - Machine-readable metrics
- `run_metadata.json` - Trace metadata
- `commands.txt` - Exact reproduction command
- `env.json` - Python/PyTorch versions
- `cpu_info.txt` - CPU specifications
- `git_sha.txt` - Git commit hash
- `sha256.txt` - File checksums

## Next Actions

Per `plans/active/cli-noise-pix0/plan.md:29` (M2i.2):
1. ✅ Metrics refresh complete - critical divergence quantified
2. ⏭️ Investigate root cause of `I_before_scaling` mismatch
3. ⏭️ Review cache tap implementation for normalization bugs
4. ⏭️ Generate trace diff manual patch for first divergence analysis
5. ⏭️ Update lattice_hypotheses.md with findings

## Related Documents

- Plan: `plans/active/cli-noise-pix0/plan.md`
- Fix Plan Entry: `docs/fix_plan.md` [CLI-FLAGS-003]
- C Trace: `reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log`
- PyTorch Trace: `reports/2025-10-cli-flags/phase_l/carryover_probe/20251008T172721Z/trace_py.log`
