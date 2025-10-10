Summary: Capture PyTorch traces for the 4096² parity regression pixels so we can diff against the new C logs.
Mode: Parity
Focus: VECTOR-PARITY-001 / Phase C2 PyTorch trace capture
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2026-01-vectorization-parity/phase_c/<STAMP>/py_traces/, reports/2026-01-vectorization-parity/phase_c/<STAMP>/summary.md, reports/2026-01-vectorization-parity/phase_c/<STAMP>/env/trace_env.json, reports/2026-01-vectorization-parity/phase_c/<STAMP>/commands.txt
Do Now: [VECTOR-PARITY-001] Phase C2 — PyTorch trace capture; command: KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q
If Blocked: Log root cause in Attempt history and park the partially captured traces under reports/2026-01-vectorization-parity/phase_c/blocked/<brief_reason>/ with commands.txt before stopping.
Priorities & Rationale:
- Match the new C traces before diffing (docs/fix_plan.md:19-45) so parity diagnosis can proceed.
- Follow the Phase C checklist (plans/active/vectorization-parity-regression.md:1-60) to keep artifacts consistent across pixels.
- Stay within the parallel trace SOP expectations (docs/development/testing_strategy.md:60-200) for reproducibility and comparability.
How-To Map:
- Source env vars each run: `export KMP_DUPLICATE_LIB_OK=TRUE` and `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`.
- Update `scripts/debug_pixel_trace.py` to accept `--pixel S F`, `--tag NAME`, and `--out-dir PATH`, emitting `TRACE_PY:` lines that mirror the C schema (pix0_vector, pixel_pos, scattering_vec, hkl, F_cell, omega_pixel, steps, scaling terms).
- After edits, run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q` and save the log to `reports/2026-01-vectorization-parity/phase_c/$STAMP/pytest_collect.log`.
- Generate trace (float64 CPU) for ROI center: `python scripts/debug_pixel_trace.py --pixel 2048 2048 --tag ROI_center --out-dir reports/2026-01-vectorization-parity/phase_c/$STAMP/py_traces`
- Generate trace for ROI boundary: `python scripts/debug_pixel_trace.py --pixel 1792 2048 --tag ROI_boundary --out-dir reports/2026-01-vectorization-parity/phase_c/$STAMP/py_traces`
- Generate trace for far edge: `python scripts/debug_pixel_trace.py --pixel 4095 2048 --tag far_edge --out-dir reports/2026-01-vectorization-parity/phase_c/$STAMP/py_traces`
- For each run, tee stdout to `TRACE_PY` logs, capture command lines in `commands.txt`, and record environment metadata (git SHA, python version, device/dtype, ROI bounds) in `env/trace_env.json`.
- Write `summary.md` noting whether intensities are zero; if all remain background, identify an on-peak candidate from ROI metrics for the next loop.
- Keep raw tensors uncommitted; only reference report paths in fix_plan attempts.
Pitfalls To Avoid:
- Do not commit the generated trace files; they must stay under reports/.
- Avoid leaving `STAMP` unset—no more `phase_c/unknown/` bundles.
- Ensure `TRACE_PY:` labels exactly match the C trace tokens for diff tooling.
- Stay on CPU float64 for trace capture; no opportunistic CUDA runs here.
- Preserve deterministic ordering—process pixels sequentially, not parallel background jobs.
- Retain ROI bounds (1792-2303) in the script so future runs stay comparable.
- Keep `pytest --collect-only` clean; fix import errors before logging success.
- Document every command in commands.txt; do not rely on shell history.
- Leave `reports/` artifacts untracked; verify `git status` is clean before finishing.
Pointers:
- docs/fix_plan.md:19-45 — active parity ledger + Next Actions
- plans/active/vectorization-parity-regression.md:1-60 — Phase C expectations and checklist
- docs/development/testing_strategy.md:60-200 — parallel trace SOP and canonical commands
- reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/summary.md — reference C-trace findings
Next Up: Phase C3 diff + first_divergence.md once Py traces land.
