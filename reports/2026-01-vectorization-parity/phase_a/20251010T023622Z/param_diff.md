# Parameter Diff

## failing 20251009T095913Z

```
# Phase B1 Profiler Rerun for VECTOR-GAPS-002
# Date: 2025-12-22
# Commit: ac94e90c83cb13cb11377c1b1b022b35a54c9fa2
# Branch: feature/spec-based-2
# Status: BLOCKED - correlation 0.721175 < 0.99 threshold

# Step 1: Verify test collection
pytest --collect-only -q > pytest_collect.log 2>&1
# Exit code: 0 (success - 694 tests collected)

# Step 2: Run profiler with 4096² detector
export KMP_DUPLICATE_LIB_OK=TRUE
python scripts/benchmarks/benchmark_detailed.py \
  --sizes 4096 \
  --device cpu \
  --dtype float32 \
  --profile \
  --keep-artifacts \
  --iterations 1
# Exit code: 0 (benchmark completed)
# Output directory: reports/benchmarks/20251009-025958/
# CRITICAL: Correlation = 0.721175 (BLOCKED - below 0.99 threshold)

# Step 3: Copy artifacts to Phase B directory
cp -r reports/benchmarks/20251009-025958/* reports/2026-01-vectorization-gap/phase_b/20251009T095913Z/profile/

# Step 4: Create blocking documentation
# - correlation.txt (status=BLOCKED)
# - summary.md (root cause analysis)
# - env.json (environment metadata)
# - torch_env.txt (detailed PyTorch info)

# BLOCKING STATUS: Phase B1 incomplete due to parity regression
# Next: Update docs/fix_plan.md with attempt, hand off to galph for triage
```

```json
{
  "python_version": "3.11+",
  "pytorch_version": "2.7.1+cu126",
  "cuda_available": true,
  "device_count": 1,
  "git_commit": "ac94e90c83cb13cb11377c1b1b022b35a54c9fa2"
}
```

## failing 20251010T022314Z

```
# VECTOR-GAPS-002 Phase B1 Profiler Capture (FAILED - parity threshold)
# Timestamp: 20251010T022314Z
# Git SHA: 22ea5c188f6a7c9f38f18228dd1b0e27c14e5290

# Profiler command (executed):
export STAMP='20251010T022314Z'
NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts

# Test collection (executed per blocked protocol):
NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q > reports/2026-01-vectorization-gap/phase_b/$STAMP/collect.log

# Status: BLOCKED (correlation_warm=0.721175 << 0.999 threshold)
# Artifacts moved to: reports/2026-01-vectorization-gap/phase_b/20251010T022314Z/failed/
```

```json
{
  "python": "3.13.5",
  "torch": "2.7.1+cu126",
  "git_sha": "22ea5c188f6a7c9f38f18228dd1b0e27c14e5290"
}
```

## good 20251009-161714

_commands.txt missing_

_env.json missing_
