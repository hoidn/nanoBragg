Summary: Apply MOSFLM +0.5 beam-center offset and clear detector-config regressions ahead of Phase M.
Mode: Parity
Focus: [DETECTOR-CONFIG-001] Detector defaults audit
Branch: feature/spec-based-2
Mapped tests: pytest -v tests/test_detector_config.py --maxfail=0
Artifacts: reports/2026-01-test-suite-triage/phase_m/$STAMP/{detector_config,full_suite}/
Do Now: [DETECTOR-CONFIG-001] Detector defaults audit — KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py --maxfail=0
If Blocked: Capture notes in plans/active/detector-config.md Phase B checklist, add Attempt entry in docs/fix_plan.md, and pause implementation.
Priorities & Rationale:
- plans/active/detector-config.md Phase B: blueprint enumerates mm→pixel conversion sites and offset rules that must be implemented this loop.
- docs/fix_plan.md#detector-config-001: Next Actions now require Phase C1–C3 to land before we can rerun the suite.
- reports/2026-01-test-suite-triage/phase_l/20251011T104618Z/detector_config/analysis.md: documents failing expectations (513.0/1024.5 px) caused by missing MOSFLM +0.5 offset.
- specs/spec-a-core.md:72-75 & arch.md ADR-03: normative references for MOSFLM beam-center offsets you must match exactly.
- docs/development/pytorch_runtime_checklist.md item 1 & 2: maintain vectorization and device/dtype neutrality while editing Detector.
How-To Map:
- Implementation: adjust `src/nanobrag_torch/models/detector.py` mm→pixel conversion (see lines 78-142, 612-690). Apply MOSFLM-only +0.5 offsets; document rationale in code comments only if non-obvious.
- Tests: extend `tests/test_detector_config.py` to assert MOSFLM pixel centres shift by +0.5 while XDS remains unchanged. Add regression for `Detector.get_pixel_coords()` if needed.
- Docs/ledger: update `docs/architecture/detector.md` (§8.2) and `docs/development/c_to_pytorch_config_map.md` beam-center row to mention the MOSFLM +0.5 application site; refresh `docs/fix_plan.md` Attempt log and `reports/.../analysis.md` with results.
- Commands: `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `mkdir -p reports/2026-01-test-suite-triage/phase_m/$STAMP/detector_config`; `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py --maxfail=0 | tee reports/2026-01-test-suite-triage/phase_m/$STAMP/detector_config/pytest.log`.
- Optional (post-pass): if time, run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/2026-01-test-suite-triage/phase_m/$STAMP/full_suite/pytest_full.xml`.
Pitfalls To Avoid:
- Do not offset non-MOSFLM conventions; verify conditional logic before editing.
- Preserve tensor dtype/device neutrality; avoid `.item()` or hard-coded CPU tensors in Detector.
- Keep vectorization intact; no Python loops added around pixel calculations.
- Respect Protected Assets listed in docs/index.md (e.g., input.md, loop.sh); do not rename or remove them.
- Maintain differentiability by using tensor operations; no `.detach()`/`.numpy()` in core paths.
- Update docs together with code; avoid drift between spec references and implementation.
- Capture artifacts under the documented reports/ path with timestamped STAMP directories.
- Record Attempt details in docs/fix_plan.md and plans/active/detector-config.md once execution completes.
- Run targeted pytest before any full-suite invocation; only run the full suite if the targeted tests pass.
- Set `KMP_DUPLICATE_LIB_OK=TRUE` for every pytest/python command involving torch.
Pointers:
- src/nanobrag_torch/models/detector.py:78-142,612-690
- tests/test_detector_config.py:1
- docs/architecture/detector.md#L60
- docs/development/c_to_pytorch_config_map.md:35
- reports/2026-01-test-suite-triage/phase_l/20251011T104618Z/detector_config/analysis.md
- plans/active/detector-config.md:1
Next Up: 1. After targeted pass, execute Phase M full-suite rerun and sync remediation_tracker.md per plans/active/test-suite-triage.md.
