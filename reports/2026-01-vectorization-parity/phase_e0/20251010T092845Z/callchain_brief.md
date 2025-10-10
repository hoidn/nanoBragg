# Phase E0 Callchain Brief

## Variables for prompts/callchain.md

**analysis_question**: "Why does the 4096x4096 full-frame parity stay at 0.721 when the 512x512 ROI matches? Focus: edge/background factors."

**initiative_id**: vectorization-parity-edge

**scope_hints**:
- "edge pixels"
- "scaling"
- "background"
- "F_cell=0 regions"

**roi_hint**: "single edge pixel (0,0) or (4095,4095)"

**namespace_filter**: "nanobrag_torch"

**time_budget_minutes**: 30

## Context from Attempt #21

- **ROI metrics** (512² center, slow/fast 1792-2303):
  - correlation = 1.000000 (0.9999999985)
  - sum_ratio = 0.999987
  - RMSE = 3.28e-05
  - All exit criteria MET ✅

- **Full-frame metrics** (4096² complete):
  - correlation = 0.721177 ❌ (required ≥0.999, delta −0.277823)
  - speedup_warm = 0.81×
  - C_time = 0.532s, Py_time_warm = 0.654s

- **Implication**: Phase D lattice fix resolved central physics but residual bugs exist at edges/background

- **Phase C1 observation**: Selected pixels (2048,2048), (1792,2048), (4095,2048) are all background-only (F_cell=0)

## Linked Artifacts

- Attempt #21 blockers: `reports/2026-01-vectorization-parity/phase_e/20251010T091603Z/blockers.md`
- Attempt #20 ROI validation: `reports/2026-01-golden-refresh/phase_c/20251010T090248Z/phase_c_summary.md`
- Attempt #10 first divergence analysis: `reports/2026-01-vectorization-parity/phase_c/20251010T061605Z/first_divergence.md`

## Trace Strategy

Focus on edge pixels where background/scaling factors dominate:
1. Identify entry point (Simulator.run or __main__)
2. Map config flow into edge pixel computation
3. Trace normalization/scaling chain for F_cell=0 cases
4. Identify sinks and final writes
5. Propose taps for edge-specific diagnostics

## Expected Outputs

All deliverables under `reports/2026-01-vectorization-parity/phase_e0/20251010T092845Z/`:
- `callchain/static.md` - static code flow analysis
- `callgraph/dynamic.txt` - optional dynamic trace
- `trace/tap_points.md` - proposed numeric taps
- `summary.md` - one-page findings
- `env/trace_env.json` - environment metadata
