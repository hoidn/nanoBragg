# CLI-FLAGS-003 Phase H6g Post-Fix Evidence Capture

## Attempt #41 — 2025-10-06

### Result Summary
**PASS** — All pix0 deltas below 5e-5 m threshold.

### Metrics

#### pix0 Component Deltas (C vs PyTorch)

| Component | C Value (m) | PyTorch Value (m) | |Δ| (m) | |Δ| (µm) |
|-----------|-------------|-------------------|----------|-----------|
| Fast | -2.164758362048360e-01 | -2.164757131429300e-01 | 1.231e-07 | 0.123 |
| Slow | 2.163430504922150e-01 | 2.163431647522500e-01 | 1.143e-07 | 0.114 |
| Close | -2.301924143005370e-01 | -2.301952656292300e-01 | 2.851e-06 | **2.851** |

**Maximum Delta:** 2.851 µm (well below 50 µm threshold)

### Key Observations

1. **Detector Convention Confirmed:** Both traces show `detector_convention=CUSTOM`, confirming pivot forcing logic is active.

2. **Close Distance Alignment:**
   - C: 0.231271826111781 m
   - Py: 0.231274663460392 m
   - Δ: ~2.84 µm (consistent with pix0 close component delta)

3. **Basis Vectors Match:** fdet, sdet, odet vectors align to floating-point precision between C and PyTorch traces.

4. **No Unit System Confusion:** All values correctly in meters, no millimeter-scale mismatches observed in prior attempts.

### Artifacts Generated

- `trace_py.log` — Full PyTorch trace for pixel (slow=1039, fast=685)
- `trace_py_HHMMSS.log` — Timestamped backup
- `pix0_delta_analysis.txt` — Delta computation summary
- `metadata.json` — Environment snapshot (Python 3.13.7, PyTorch 2.8.0+cu128, CUDA available)
- `env_snapshot.txt` — Timestamp, commit hash, Python/PyTorch versions
- `harness_stdout.log` — Full harness execution log
- `attempt_notes.md` — This document

### Environment Details

- **Commit:** (see metadata.json)
- **Python:** 3.13.7 (Anaconda)
- **PyTorch:** 2.8.0+cu128
- **CUDA:** Available (NVIDIA GeForce RTX 3090)
- **Default dtype:** torch.float32
- **NB_C_BIN:** Not set for this run (C trace from prior capture)

### Hypotheses Validated

1. ✅ Pivot fix (Attempt #40) successfully resolved pix0 computation when custom detector basis vectors are present.
2. ✅ CUSTOM convention correctly detected and forced SAMPLE pivot mode.
3. ✅ No residual unit system bugs in detector pix0 calculation path.

### Next Actions

Per `plans/active/cli-noise-pix0/plan.md` Phase H6g completion criteria:

1. **Evidence Captured:** ✅ This attempt provides required trace and delta artifacts.

2. **Threshold Met:** ✅ Max |Δpix0| = 2.85 µm << 50 µm threshold.

3. **Phase K2 Ready:** Scaling-chain refresh can proceed once this evidence is logged in `docs/fix_plan.md`.

4. **Regression Test (Phase K3):** After K2, run full pytest suite to confirm no regressions.

5. **Long-term Goal #1:** Supervisor parity command can execute after K3 passes.

### Command Reference

Trace harness command executed:
```bash
env PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py --out reports/2025-10-cli-flags/phase_h6/post_fix/trace_py.log
```

Delta analysis command:
```bash
python reports/2025-10-cli-flags/phase_h6/post_fix/pix0_delta_analysis.py
```

### Deviation from Prior Attempts

- **Attempt #39:** |Δpix0| values not recorded (plan phase incomplete).
- **Attempt #40:** Documented pivot forcing fix, but no post-fix trace captured.
- **Attempt #41 (this):** First complete evidence capture after pivot fix landed.

### Compliance Check

- ✅ No source files modified (evidence-only loop)
- ✅ Reports directory structure preserved
- ✅ Artifacts reference commit hash for reproducibility
- ✅ All deltas expressed in meters (primary) with µm equivalents
- ✅ C trace treated as read-only reference
- ✅ No manual edits to trace files
- ✅ Environment snapshot includes CUDA device name
- ✅ Harness patch intact (tracing enabled)

### Blocker Resolution Status

**Previous Blockers (from input.md context recap):**

1. ✅ SAMPLE pivot forcing when custom detector basis vectors present — **Resolved** (Attempt #40)
2. ✅ Unit logging mismatches — **No longer observed** (all values in meters as expected)
3. ✅ Phase H6g |Δpix0| < 5e-5 m threshold — **Met** (2.85 µm << 50 µm)

**No active blockers for Phase K2/K3 progression.**

### ROI nb-compare Note

Per input.md checklist step 15, ROI nb-compare validation is deferred until full-frame parity work (Phase L). This evidence loop focuses solely on pix0 trace verification per Phase H6g requirements.

### Documentation Updates Required

1. **docs/fix_plan.md:** Add Attempt #41 to CLI-FLAGS-003 Attempts History with metrics, artifacts, and observations from this document.

2. **plans/active/cli-noise-pix0/plan.md:** Mark Phase H6g complete with artifact references.

3. **reports/2025-10-cli-flags/phase_h5/parity_summary.md:** Append new section citing post-fix deltas (optional, per input.md reporting reminder).

### Future Audit Trail

This attempt provides the required evidence gate for:
- Phase K2: Scaling-chain artifact regeneration
- Phase K3: Full pytest regression validation
- Long-term Goal #1: Supervisor parity command execution

All artifacts archived under `reports/2025-10-cli-flags/phase_h6/post_fix/` with timestamp and commit references for reproducibility.
