# Carryover Cache Validation - PyTorch Trace Capture

**Timestamp:** 2025-10-08T17:27:21Z  
**Commit:** 24062dbfb38324abe8068261b6337ed31e493c1a  
**Loop:** Ralph i=167 (evidence-only mode)

## Purpose

Capture PyTorch trace evidence for CLI-FLAGS-003 parity debugging per `plans/active/cli-noise-pix0/plan.md` M2i.1.

## Configuration

- **Pixel:** (684, 1039) from ROI 684-686 x 1039-1040
- **Config:** supervisor (CUSTOM convention, SAMPLE pivot)
- **Phi mode:** c-parity (emulates C carryover behavior)
- **Dtype:** float64
- **Device:** CPU

## Artifacts

- `trace_py.log`: Main trace (124 lines)
- `trace_py_per_phi.log`: Per-phi rotated vectors (10 lines)
- `trace_harness_stdout.txt`: Full execution log
- `commands.txt`: Reproduction command
- `env.json`: Environment metadata
- `cpu_info.txt`: Hardware info
- `observations.txt`: Analysis notes

## Key Metrics

- Final intensity: 4.06016057371301e-07
- Trace lines captured: 124 (main) + 10 (per-phi)
- Execution clean: ✅ (deprecation warnings only, not affecting correctness)

## Next Steps

1. Compare against C trace (if available)
2. Generate diff via `capture_live_trace.py`
3. Extract metrics (F_latt, first_divergence)
4. Update fix_plan.md with findings
