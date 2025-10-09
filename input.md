Summary: Clear pyrefly BLOCKER violations (beam center & ROI None guards) and log Phase D Round 1 kickoff
Mode: none
Focus: [STATIC-PYREFLY-001] Run pyrefly analysis and triage — Phase D delegation (Round 1 blockers)
Branch: feature/spec-based-2
Mapped tests:
- pytest -v tests/test_models.py::TestDetector -k "beam_center"
- pytest -v tests/test_simulator.py -k "roi"
- pytest -v tests/test_at_parallel_001.py
- pytest -v tests/test_at_parallel_012.py
Artifacts:
- reports/pyrefly/20251222T<timestamp>/commands.txt
- reports/pyrefly/20251222T<timestamp>/pyrefly.log
- reports/pyrefly/20251222T<timestamp>/summary.md
- reports/pyrefly/20251222T<timestamp>/env.json
- reports/pyrefly/20251222T<timestamp>/beam_center.log
- reports/pyrefly/20251222T<timestamp>/roi.log
- reports/pyrefly/20251009T044937Z/summary.md (append progress note)
- docs/fix_plan.md (new Attempt logging Round 1 progress)
- plans/active/static-pyrefly.md (Phase D1–D3 state flip)
Do Now: [STATIC-PYREFLY-001] Phase D Round 1 — implement BL-1/BL-2 None guards, rerun targeted pytest selectors, then capture a fresh `pyrefly check src` bundle under reports/pyrefly/20251222T<timestamp>/
If Blocked: If fixes cannot land, stop editing code; instead run `pyrefly check src`, store the new log in reports/pyrefly/20251222T<timestamp>/, and document blockers (file:line, stack trace, suspected contract issue) in summary.md plus docs/fix_plan.md Attempts
Priorities & Rationale:
- plans/active/static-pyrefly.md:47 — Phase D tasks are the only open checklist items before moving to fix delegation
- reports/pyrefly/20251009T044937Z/summary.md:19 — BL-1/BL-2 enumerated as immediate crashers with validation selectors
- docs/fix_plan.md:3818 — Next Actions explicitly call for Round 1 blocker fixes and supervisor memo hooks
- specs/spec-a-core.md:204 — Beam center defaults must resolve to convention-defined values when CLI omits overrides
- docs/architecture/detector.md:118 — Detector pix0/beam center initialization contract for None inputs
- docs/development/testing_strategy.md:75 — Targeted pytest selectors required before any integration sweep
- prompts/pyrefly.md:1 — Static-analysis SOP mandates timestamped artifacts and environment capture every run
How-To Map:
- Step 01: `git status -sb` to confirm branch feature/spec-based-2 and list staged files (record in commands.txt)
- Step 02: Re-read reports/pyrefly/20251009T044937Z/summary.md §§“BL-1” and “BL-2” to refresh affected line numbers and validation commands
- Step 03: `timestamp=$(date -u +"%Y%m%dT%H%M%SZ")`; `export PYREFLY_RUN=reports/pyrefly/${timestamp}`; `mkdir -p "$PYREFLY_RUN"`
- Step 04: Initialize `$PYREFLY_RUN/commands.txt` with timestamp, git rev-parse HEAD, and environment (python --version, pyrefly --version)
- Step 05: Annotate `$PYREFLY_RUN/summary.md` with a heading “Round 1 — BL-1/BL-2” and note baseline violation counts (22 blockers)
- Step 06: In `src/nanobrag_torch/models/detector.py`, add explicit defaults so `beam_center_{s,f}` never propagate None past constructor; rely on convention helpers in docs/architecture/detector.md
- Step 07: Ensure new defaults preserve differentiability by building tensors on `config_device` without `.item()`; cite spec lines in inline comments only where necessary
- Step 08: Update pix0 cached properties so they recompute after default injection; confirm `invalidate_cache()` still fires before reuse
- Step 09: In `src/nanobrag_torch/simulator.py`, wrap ROI arithmetic (`roi_ymax+1`, `roi_xmax+1`) with guard clauses; fall back to detector dimensions when ROI is None
- Step 10: Add unit helper if needed (e.g., `_normalize_roi_bounds` returning inclusive slice indices) keeping vectorization intact
- Step 11: Review ROI caching logic to ensure guard branch still constructs proper tensor slices for CPU and CUDA devices
- Step 12: Update or add regression tests if existing suites do not cover ROI=None and beam center defaults; keep tests device-parametrised where possible
- Step 13: Run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_models.py::TestDetector -k "beam_center" | tee "$PYREFLY_RUN/beam_center.log"` and capture exit code in commands.txt
- Step 14: Run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_simulator.py -k "roi" | tee "$PYREFLY_RUN/roi.log"`
- Step 15: Execute beam-center parity checks: `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_001.py`; log command + status
- Step 16: Execute ROI none/full-frame regression: `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_012.py`
- Step 17: If any selector fails, note failure output in summary.md and stop for triage before moving forward
- Step 18: After tests pass, run full static analysis: `pyrefly check src | tee "$PYREFLY_RUN/pyrefly.log"`; record return code and compare counts vs baseline (target: 12 blocker errors remaining from BL-3..BL-6)
- Step 19: Create `$PYREFLY_RUN/env.json` capturing `{ 'python': <version>, 'pyrefly': <version>, 'torch': <torch.__version__>, 'cuda_available': torch.cuda.is_available(), 'uname': platform.uname() }`
- Step 20: Compute SHA256 checksums for pyrefly.log and summary.md (`sha256sum > $PYREFLY_RUN/sha256.txt`) for reproducibility
- Step 21: Append a “Diff vs baseline” table to summary.md showing blocker/high/medium counts before/after (e.g., Blocker 22→12)
- Step 22: Update reports/pyrefly/20251009T044937Z/summary.md quick-notes section with “BL-1/BL-2 resolved → see $PYREFLY_RUN”
- Step 23: Add `PYREFLY_RUN` path and highlights to commands.txt for cross-turn navigation
- Step 24: Edit `docs/fix_plan.md` `[STATIC-PYREFLY-001]` Attempts with a new entry (Attempt #5) summarizing BL-1/BL-2 fix, tests run, new counts, and pointers to `$PYREFLY_RUN`
- Step 25: Within the same entry, adjust Next Actions to emphasise BL-3/BL-4 for the next loop and restate rerun cadence (`pyrefly check src` after each blocker batch)
- Step 26: Modify `plans/active/static-pyrefly.md` — mark Phase D1–D3 `[D]`, quote `$PYREFLY_RUN`, and note that Phase E awaits BL-3/BL-6 completion plus rerun diff
- Step 27: Review docs/index.md to ensure no Protected Asset touched; log the check in commands.txt
- Step 28: Inspect `git diff` for detector.py/simulator.py to verify guards handled both CPU/CUDA flows without new loops or `.cpu()` calls
- Step 29: Run `python -m compileall src/nanobrag_torch` quickly to ensure syntax is clean after guard additions (log in commands.txt)
- Step 30: Stage intentional files (`git add src/nanobrag_torch/models/detector.py src/nanobrag_torch/simulator.py docs/fix_plan.md plans/active/static-pyrefly.md reports/pyrefly/${timestamp}`) but do not commit; leave staged state noted in summary.md
- Step 31: Capture final `git status -sb` into commands.txt so auditors know tree state at handoff
- Step 32: In summary.md, clearly list remaining blockers (BL-3..BL-6) with counts, plus any unexpected residuals uncovered by pyrefly rerun
- Step 33: Diff `$PYREFLY_RUN/pyrefly.log` against the baseline log to quantify which errors disappeared; record highlights in summary.md and commands.txt
- Step 34: Add a short "Verification" paragraph to summary.md confirming each mapped pytest selector succeeded (include durations where notable)
- Step 35: Capture `git diff --stat --staged` output into commands.txt so reviewers see change scope before commit
- Step 36: Note in summary.md whether any HIGH/MEDIUM findings regressed (should remain unchanged) and flag unexpected increases immediately
Pitfalls To Avoid:
- Avoid `.item()` or `.detach()` when bridging scalar config values; keep tensors differentiable
- Do not mutate Protected Assets (docs/index.md, loop.sh, supervisor.sh, input.md) outside mandated updates
- Ensure new guards do not change public CLI defaults; cross-check spec values when beam_center inputs missing
- Keep ROI guard logic vectorized; no pixel-by-pixel loops permitted
- Capture every command in commands.txt; missing provenance breaks pyrefly SOP
- Treat pyrefly findings conservatively—if uncertain, document as residual rather than silently ignoring
- Confirm tests are run with `KMP_DUPLICATE_LIB_OK=TRUE` to avoid MKL clashes
- Do not rerun full pytest suite; stick to mapped selectors unless failure investigation requires more
- Ensure pix0/beam center caches invalidate properly (no stale tensors crossing device boundaries)
- Leave clear TODOs only in summary.md; production files must remain TODO-free
- Keep ROI guard logic compatible with GPU execution by avoiding implicit CPU tensor creation
- When editing detector defaults, respect MOSFLM +0.5 pixel shifts documented in docs/development/c_to_pytorch_config_map.md
Pointers:
- reports/pyrefly/20251009T044937Z/summary.md:19
- src/nanobrag_torch/models/detector.py:70
- src/nanobrag_torch/models/detector.py:250
- src/nanobrag_torch/simulator.py:560
- src/nanobrag_torch/simulator.py:1120
- docs/architecture/detector.md:118
- docs/fix_plan.md:3776
- plans/active/static-pyrefly.md:47
- docs/development/testing_strategy.md:74
- prompts/pyrefly.md:1
- specs/spec-a-core.md:204
- docs/architecture/pytorch_design.md:80
- reports/pyrefly/20251008T053652Z/pyrefly.log:1
- docs/architecture/undocumented_conventions.md:94
- docs/development/c_to_pytorch_config_map.md:120
- src/nanobrag_torch/config.py:140
- src/nanobrag_torch/simulator.py:900
- src/nanobrag_torch/utils/auto_selection.py:25
- tests/test_models.py:220
Next Up: After BL-1/BL-2 are green, tackle BL-3/BL-4 (source direction and pix0 None handling) or begin drafting the H-1 tensor/scalar boundary refactor proposal for CLI I/O paths
