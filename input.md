Summary: Finish SOURCE-WEIGHT Phase E by landing the CLI warning guard, reactivating TC-D2, and capturing parity metrics so VECTOR-GAPS-002 can resume.
Mode: Parity
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests:
- pytest --collect-only -q
- pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v
Artifacts:
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/commands.txt
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/summary.md
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/metrics.json
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/pytest.log
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/pytest_collect.log
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/warning.log
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/env.json
Do Now: [SOURCE-WEIGHT-001] Phase E — implement the Option B CLI warning guard, remove the TC-D2 skip, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v`
If Blocked: Capture TC-D1/TC-D3 CLI outputs with the current simulator, stash binaries+stdout under reports/2025-11-source-weights/phase_e/<UTCSTAMP>/attempts/, and log blocker context + metrics in docs/fix_plan.md before pausing.
Priorities & Rationale:
- specs/spec-a-core.md:150-190 — authoritative language that weights are read but ignored; the warning must cite this range to keep CLI behaviour traceable to the spec.
- arch.md:§2,§8 — detector/beam architecture and broadcast expectations; ensuring the guard stays outside tensor code respects these constraints.
- docs/development/c_to_pytorch_config_map.md — beam parameter mapping; helps verify which CLI flags imply divergence so the guard triggers correctly.
- plans/active/source-weight-normalization.md:Phase-E — status snapshot notes TC-D1/D3/D4 scaffolding exists, TC-D2 awaits guard; closing the phase unblocks profiler work.
- docs/fix_plan.md:[SOURCE-WEIGHT-001] — refreshed Next Actions specify guard location, parity metrics, and documentation follow-up; our Attempt must satisfy them.
- reports/2025-11-source-weights/phase_d/20251009T103212Z/design_notes.md — Option B rationale and risk assessment; confirms no simulator changes beyond the warning are required.
- reports/2025-11-source-weights/phase_d/20251009T104310Z/summary.md — acceptance thresholds and command bundle to reuse; maintain parity with the staged harness.
- tests/test_cli_scaling.py:472-620 — TestSourceWeightsDivergence implementation; TC-D2 currently skips and must switch to warning assertion without disturbing TC-D1/D3/D4.
- reports/2025-11-source-weights/phase_a/20251009T071821Z/summary.md — biased baseline metrics; helpful for before/after commentary in summary.md.
- reports/2025-11-source-weights/phase_d/20251009T102319Z/divergence_analysis.md — documents the original C vs PyTorch divergence counts; reuse its observations when describing Phase E resolution.
- docs/architecture/pytorch_design.md §8 — current Sources narrative; must be updated after evidence, so keep notes on wording changes while implementing the guard.
- docs/development/testing_strategy.md §1.4 & §2.5 — mandates device/dtype neutrality and reuse of authoritative command bundles; reference it when logging skipped CUDA runs.
- galph_memory.md (2025-12-24 entries) — previous supervisor expectations that Phase E evidence unblocks VECTOR-GAPS-002; align new Attempt notes with this context.
- CLAUDE.md Protected Assets rule — reminder that loops through docs/index.md referenced assets cannot be moved while editing CLI/test files.
How-To Map:
1. Export env vars: `export KMP_DUPLICATE_LIB_OK=TRUE` and `export NB_C_BIN=./golden_suite_generator/nanoBragg`; record the chosen binary path in env.json.
2. Confirm guard location: edit `src/nanobrag_torch/__main__.py` argument parsing where CLI options are processed; do not touch simulator core loops.
3. Implement warning: when `-sourcefile` is provided with any of `-hdivrange`, `-vdivrange`, or `-dispersion`, emit `UserWarning("Divergence/dispersion parameters ignored when sourcefile is provided. Sources are loaded from file only (see specs/spec-a-core.md:151-162).")` with `stacklevel=2`.
4. Document guard: add a concise code comment referencing Option B design notes and spec lines to aid future maintenance.
5. Update TC-D2: replace `pytest.skip` with `with pytest.warns(UserWarning) as record:` and assert the warning message includes both "ignored" and the spec citation string.
6. Preserve fixtures: keep the flexible path lookup for `two_sources.txt` so tests run without extra setup.
7. Consider device parameterisation: if adding a `device` fixture is feasible, guard CUDA with `torch.cuda.is_available()` and log skips in pytest output.
8. Run `pytest --collect-only -q` from repo root; redirect stdout to phase_e/<stamp>/pytest_collect.log and ensure 686 tests are discovered.
9. Execute `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v`; tee stdout to phase_e/<stamp>/pytest.log for record.
10. Reproduce TC-D1 via C/Py CLI runs; copy commands from `commands.txt`, route outputs to `c_stdout.log` and `py_stdout.log`, and store float images for metric computation.
11. For TC-D2, run the PyTorch CLI command that should emit the warning; capture stderr into warning.log and ensure the message matches expectations.
12. Repeat the harness for TC-D3 (divergence-only) and TC-D4 (explicit `-oversample 1`) so metrics cover all acceptance cases.
13. Compute metrics with a short Python snippet (load float images, compute correlation and sum ratio); populate metrics.json with keyed entries for each test and include `tc_d2_warning_captured` boolean plus step counts.
14. Draft summary.md with a table of test cases, measured metrics, warning confirmation, device/dtype, and any skips; mention adherence to thresholds.
15. Record environment details (Python, PyTorch, git SHA, NB_C_BIN path, CUDA availability) in env.json; include NB_RUN_PARALLEL status.
16. Stage documentation snippets for `specs/spec-a-core.md` and `docs/architecture/pytorch_design.md` describing the precedence rule, but defer committing until parity evidence is confirmed.
17. Update docs/fix_plan.md with a new Attempt entry summarising metrics, warning behaviour, artifacts, and follow-up (e.g., CUDA backlog if skipped).
18. Refresh `plans/active/source-weight-normalization.md` Phase E table, marking E1/E2 as complete once guard and tests are in place; leave E3/E4 pending until evidence/docs land.
19. In summary.md, note that VECTOR-GAPS-002 Phase B1 is unblocked once this evidence is accepted, and flag any remaining risks (e.g., CUDA parity outstanding).
20. Double-check that the guard is covered by unit tests in addition to CLI tests; if no direct unit test exists, justify in summary.md why CLI-level coverage is sufficient.
21. After running parity commands, verify that `metrics.json` includes raw sums and correlation values with at least 6 decimal digits to simplify future comparisons.
22. Capture the exact stderr output for the warning in warning.log even when pytest already validated it; maintain both automated assertion and manual artifact.
23. Before finalising, run `git diff` to ensure only CLI/test/docs files are touched; no simulator files should change this loop.
24. Update `.gitignore` if temporary directories cause noise (only if absolutely necessary); otherwise delete stray files before committing.
25. Prepare a short blurb for the next supervisor handoff (input.md summary.md) noting any lingering TODOs, such as CUDA parity follow-up or spec wording proposals.
26. Run `pytest -k "TestSourceWeights" -v` if time permits to ensure legacy tests remain green after guard changes; capture output in attempts/ if failures occur.
27. Validate that the warning does not fire for TC-D1 (sourcefile-only) or TC-D3 (divergence-only); note these observations in summary.md to prove selective behaviour.
28. After metrics are captured, compute relative deltas versus Phase A numbers and include them in summary.md for historical continuity.
29. Take screenshots or textual diffs only if anomalies appear; otherwise keep evidence lean and textual as per reporting conventions.
Pitfalls To Avoid:
- Do not relocate guard logic into simulator or config classes; CLI-level enforcement keeps tensor paths stable and honours Option B design.
- Avoid relaxing tolerances; corr ≥0.999 and |sum_ratio−1| ≤1e-3 remain non-negotiable.
- Refrain from modifying or deleting fixtures under reports/2025-11-source-weights/; other attempts rely on them.
- Preserve Protected Assets from docs/index.md (loop.sh, supervisor.sh, input.md, etc.).
- Do not introduce `.item()` calls on tensors that might later require gradients; keep weight handling tensor-friendly even if CLI guard uses scalars.
- Ensure warnings are captured from stderr; redirecting only stdout will miss them.
- Clean temporary output paths (`/tmp`) between CLI runs to prevent stale data mixing with new evidence.
- Document CUDA skips explicitly; silent omission conflicts with testing_strategy.md §1.4 device discipline.
- Avoid adding ad-hoc scripts outside `scripts/`; reuse the existing harness and document commands in commands.txt.
- Use ASCII-only filenames and UTC timestamps for new report directories.
- Keep commit history clean; avoid unrelated changes while preparing parity evidence.
- Verify NB_RUN_PARALLEL is set before running CLI comparisons; if missing, log the skip and resolve before retrying.
- Do not downgrade logging verbosity in tests; keep `-v` to ensure warning lines appear in captured logs.
- Avoid mixing absolute and relative paths inconsistently; prefer absolute paths for CLI commands to prevent cwd-related surprises.
- Do not silence warnings globally (e.g., via `pytest.ini`); TC-D2 must rely on targeted `pytest.warns`.
- Ensure summary.md references artifact filenames exactly; mismatched names slow down reviewers.
- Avoid excessive tmp directory reuse; each attempt should get a fresh `phase_e/<stamp>/` folder for traceability.
- Don't forget to update Attempt history numbering sequentially; skipped numbers cause confusion in later audits.
- Prevent accidental git add of large binary outputs by keeping them under reports/ (already gitignored); double-check staging before commit.
- If using notebooks for quick metrics, do not commit them; transcribe results into summary.md and metrics.json only.
- Do not leave the warning guard active during `pytest --collect-only`; ensure it triggers only when divergence args are present.
- Avoid catching warnings via `warnings.simplefilter` globally; rely on local context managers within tests.
- Keep command transcripts in commands.txt chronological with timestamps; unordered entries complicate reproduction.
- Do not assume GPU availability; gate CUDA-specific logic to avoid raising runtime errors on CPU-only hosts.
- When editing docs later, cross-check Protected Assets rule so spec updates don't remove referenced files.
Pointers:
- plans/active/source-weight-normalization.md:Phase-E — current checklist, including note that TC-D2 is pending guard implementation.
- docs/fix_plan.md:[SOURCE-WEIGHT-001] — updated Next Actions enumerating guard location, parity metrics, and documentation follow-up.
- reports/2025-11-source-weights/phase_d/20251009T103212Z/design_notes.md — Option B decision record with warning copy.
- reports/2025-11-source-weights/phase_d/20251009T104310Z/commands.txt — canonical CLI bundle for TC-D1–TC-D4.
- tests/test_cli_scaling.py:472-620 — TestSourceWeightsDivergence implementation to adjust; ensure artifact capture stays intact.
- reports/2025-11-source-weights/phase_a/20251009T071821Z/summary.md — biased baseline metrics for before/after comparison in summary.md.
- docs/development/testing_strategy.md §1.4 — reiterates device/dtype neutrality expectations when running parity evidence.
- docs/architecture/pytorch_design.md §8 — Sources subsection to update once warning behaviour is implemented.
- docs/development/pytorch_runtime_checklist.md — reminder to keep vectorization/device discipline even when editing CLI.
- reports/2025-11-source-weights/phase_d/20251009T102319Z/divergence_analysis.md — source vs divergence auto-selection notes useful for summary.md context.
- galph_memory.md (latest entries) — captures supervisory intent and downstream dependencies for this work.
- CLAUDE.md — Protected Assets section to revisit before touching CLI/test files, ensuring guard work avoids restricted assets.
- docs/index.md — confirm no newly created artifacts conflict with protected items before finalising.
- reports/2025-11-source-weights/phase_d/20251009T104310Z/warning_capture.log — expected warning text and command example for TC-D2.
- docs/architecture/c_parameter_dictionary.md — quick lookup for divergence flags to ensure guard covers all relevant CLI arguments.
- scripts/validation/README.md — reminder of preferred locations if auxiliary validation scripts become necessary.
- docs/development/implementation_plan.md §Phase 3 — broader simulator context; helpful if guard work exposes deeper implementation questions.
- history/ (latest parity investigations) — skim if correlation anomalies persist after guard implementation.
Next Up: VECTOR-GAPS-002 Phase B1 profiler rerun once Phase E evidence hits thresholds; notify PERF-PYTORCH-004 so Phase B6/B7 benchmarking can restart.
