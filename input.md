Summary: Fix MOSFLM beam-center pixel conversion so detector defaults match spec and unblock C8.
Mode: Parity
Focus: [DETECTOR-CONFIG-001] Detector defaults audit
Branch: feature/spec-based-2
Mapped tests: tests/test_detector_config.py
Artifacts: reports/2026-01-test-suite-triage/phase_l/<STAMP>/detector_config_fix/
Do Now: [DETECTOR-CONFIG-001] Phase B1–B3 & C1–C2 — implement the MOSFLM +0.5 pixel offset fix and rerun KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py
If Blocked: Capture the failing pytest output to reports/2026-01-test-suite-triage/phase_l/<STAMP>/detector_config_fix/blocked.log, note the stack/context in analysis.md, and stop (leave code edits staged but uncommitted).
Priorities & Rationale:
- plans/active/detector-config.md Phase B — spell out the code touch-points (Detector.__init__, pix0/header flows) that must change; follow it before editing.
- docs/fix_plan.md:212 — `[DETECTOR-CONFIG-001]` Next Actions now depend on the Phase B blueprint and Phase C implementation.
- reports/2026-01-test-suite-triage/phase_l/20251011T104618Z/detector_config/analysis.md — authoritative failure analysis citing spec §72 and ADR-03; we must eliminate that gap.
- specs/spec-a-core.md:72 — MOSFLM mandates `Fbeam = Ybeam + 0.5·pixel`; current code violates this contract.
- arch.md:ADR-03 — confirms CUSTOM must not gain the offset; treat non-MOSFLM conventions carefully.
How-To Map:
- Set `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and create `reports/2026-01-test-suite-triage/phase_l/$STAMP/detector_config_fix/{logs,env}`.
- Edit `src/nanobrag_torch/models/detector.py` so the mm→pixel conversion adds +0.5 only when `config.detector_convention` is MOSFLM; audit `_calculate_pix0_vector` and the header back-propagation block (~520–590) to prevent double offsets (document any adjustments in analysis.md).
- Ensure config defaults stay in mm (51.25) — do not pre-offset in `DetectorConfig.__post_init__`; update code comments if behavior changes.
- Extend `tests/test_detector_config.py` with convention-aware assertions if needed (e.g., parametrised cases for MOSFLM vs DENZO vs XDS) and adjust existing expectations to reflect the corrected pixel values.
- Run `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py | tee reports/2026-01-test-suite-triage/phase_l/$STAMP/detector_config_fix/logs/pytest.log`; move `pytest.xml` to the same directory and capture `env/torch_env.txt`, `env/pip_freeze.txt`, `commands.txt` with the exact invocation.
- Summarise code changes, verification steps, and spec references in `reports/2026-01-test-suite-triage/phase_l/$STAMP/detector_config_fix/analysis.md`; call out any follow-up needed for full-suite rerun (Phase C4).
Pitfalls To Avoid:
- Do not add `.cpu()`/`.cuda()` or `.item()` on tensors inside the detector core; maintain dtype/device neutrality.
- Avoid double-applying the +0.5 when later converting back to mm (check header/pix0 recalculations).
- Preserve non-MOSFLM conventions (DENZO, XDS, CUSTOM) — add explicit tests if you change branching logic.
- Keep Protected Assets (loop.sh, input.md, docs/index.md references) untouched.
- Update comments/docstrings only if they remain accurate after the fix; cite spec sections when clarifying.
- Store artifacts under the new `$STAMP` directory; do not overwrite the earlier Phase L bundle.
- Run the targeted pytest command before attempting the full suite; abort if targeted still fails.
- If you touch docs, ensure they stay consistent with spec wording (no ad-hoc semantics changes without supervisor sign-off).
- Avoid reformatting unrelated sections of detector.py to keep diffs tight.
Pointers:
- plans/active/detector-config.md — Phase breakdown and checklist for this workstream.
- docs/development/c_to_pytorch_config_map.md:54-82 — beam-center mapping table.
- specs/spec-a-core.md:68-86 — convention defaults and +0.5 offset rule.
- arch.md:ADR-03 — detector beam-center ADR.
- reports/2026-01-test-suite-triage/phase_l/20251011T104618Z/detector_config/analysis.md — failure reproduction details.
Next Up: After targeted tests pass, rerun the full `pytest tests/` Phase L sweep (plans/active/detector-config.md Phase C4) and refresh remediation_tracker.md.
