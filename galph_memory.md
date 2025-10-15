### 2025-10-11 (galph loop - focus selection note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase M0 baseline rerun
- Action type: Review/housekeeping
- Mode: Parity

### 2025-10-11 (galph loop - Phase M0 chunk playbook)
- Updated `plans/active/test-suite-triage.md` Phase M0 guidance with the 10-command chunk map to respect the 360 s harness cap (lines 168-208).
- Aligned `docs/fix_plan.md` Next Actions with the chunked rerun workflow (lines 48-51) and preserved Attempt #18 context.
- Rewrote `input.md` to direct STAMPed preflight + chunk execution, including per-chunk logging and aggregation steps.
- Action State: [ready_for_implementation]

### 2025-10-11 (galph loop - Phase K timeout remediation prep)
- Recorded focus/action/mode before edits per Step 3.1: focus=`[TEST-SUITE-TRIAGE-001] Phase K rerun`, action=Review/housekeeping, mode=Parity.
- Updated `docs/fix_plan.md` (lines 1-90) to log Attempt #14 timeout analysis, require `timeout 3600` + STAMP pre-creation, and shift the next logging step to Attempt #15.
- Refreshed `plans/active/test-suite-triage.md` Phase K status + checklist with the timeout guidance and adjusted tracker instructions; status snapshot now reflects the blocked run.
- Reissued `input.md` with the 60-minute `timeout` command, STAMP workflow, and explicit tracker/analysis refresh tasks for Ralph.
- Action State: [ready_for_implementation]

### 2025-10-10 (galph loop - Test Suite Phase E relaunch)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase E refresh (Action: Planning, Mode: Parity).
- Added Phase E–G sections plus updated status snapshot in `plans/active/test-suite-triage.md` to mandate the new full-suite rerun and downstream triage refresh.
- Rewrote `docs/fix_plan.md` Next Actions/Reproduction paths to point at `phase_e` artifacts and logged the new task ladder.
- Issued `input.md` instructing Ralph to perform the collect-only preflight, full `pytest tests/` run, and artifact/ledger updates under a fresh `phase_e/$STAMP` directory.
- Action State: [ready_for_implementation]

### 2025-10-10 (galph loop - Tap 5.3 instrumentation brief prep)
- Focus issue: [VECTOR-PARITY-001] Next Actions refresh (Action: Review/housekeeping, Mode: Docs).
- Updated docs/fix_plan.md Active Focus + Next Actions to pivot completely to Tap 5.3 instrumentation, PyTorch/C captures, and synthesis.
- Issued input.md guiding Ralph to author tap5_accum_plan.md and log collect-only; artefact cadence uses phase_e0/<STAMP>.
- No code changes; awaiting instrumentation plan before enabling new traces.

### 2026-01-11 (galph loop - PyTorch Tap 5.1 audit prep)
- Confirmed `[VECTOR-PARITY-001]` Next Actions stay focused on Tap 5.1/5.2; plan rows (vectorization-parity-regression.md E12–E14) already capture the schema.
- No plan edits needed; evidence backlog (Tap 5 comparison + hypotheses) remains authoritative.
- Replaced input.md with Parity-mode instructions to add the `hkl_subpixel` tap, archive centre-pixel JSON under a fresh stamp, and summarise findings in tap5_hkl_audit.md.
- Expect Attempt log with PyTorch Tap 5.1 before we authorise the C mirror instrumentation (E13).

### 2026-01-10 (galph loop - Tap 5 comparison planning)
- Heads audit: Reviewed Ralph commits 25c88957 (PyTorch Tap 5 tooling) and e8dafd99 (C Tap 5 instrumentation); evidence looks solid, no regressions spotted.
- Updated `docs/fix_plan.md` Next Actions (lines 67-69) to swap in Tap 5 comparison + hypothesis ranking; removed the now-complete instrumentation directive.
- Refreshed `plans/active/vectorization-parity-regression.md` Phase E rows: E9 marked [D] with Attempt #30 notes, new E10/E11 tasks capture comparison + follow-up decision gating; Phase F wording now defers to whatever Tap 5 remediation emerges.
- Synced `plans/active/vectorization.md` status snapshot to note the 4× C vs PyTorch `I_before_scaling` gap uncovered by Attempt #30.
- Authored input.md (Mode: Parity) steering Ralph to produce `intensity_pre_norm.md` and `tap5_hypotheses.md` under a fresh Phase E0 bundle before we pick Tap 6 vs deeper Tap 5 instrumentation.
- Follow-up: Expect Attempt logging with the new comparison pack; supervisor to review ratios, bless next tap (likely water background) or scope per-subpixel audit.

### 2026-01-07 (galph loop - TEST-GOLDEN-001 kickoff)
- Added `[TEST-GOLDEN-001]` ledger entry and authored `plans/active/test-golden-refresh.md` to manage golden-data regeneration blocking Phase E.
- Updated `[VECTOR-PARITY-001]` Next Actions to depend on the new plan; noted gating in vectorization/vectorization-parity active plans.
- Replaced input.md with Phase A audit instructions (Mode: Parity) directing Ralph to capture the high-res ROI nb-compare and draft scope_summary.md under `reports/2026-01-golden-refresh/phase_a/$STAMP/`.
- Expect Attempt #18 delivering scope_summary.md + metrics before launching regeneration (Phase B).

### 2026-01-06 (galph loop - Phase D1 kickoff)
- Confirmed Phase C traces + first_divergence complete; updated plans/active/vectorization-parity-regression.md to mark C2/C3 done and replaced commit-bisect Phase D with physics remediation tasks (H1–H3).
- Refreshed docs/fix_plan.md `[VECTOR-PARITY-001]` Next Actions to call out Phase D1–D4 workflow with m^-1 scattering vector requirement.
- Authored input.md (Mode: Parity) directing Ralph to implement the Phase D1 scattering-vector fix, capture new trace under `reports/2026-01-vectorization-parity/phase_d/$STAMP/`, and diff against the C log with 1e-6 tolerance.
- Next follow-up: expect Attempt update containing diff_scattering_vec artifacts; supervisor to review parity alignment before green-lighting fluence remediation (Phase D2).

### 2026-01-06 (galph loop - Phase C1 trace prep handoff)
- Reviewed Phase C trace plan vs fix_plan; resolved conflict by updating trace_plan.md to reinforce extending `scripts/debug_pixel_trace.py` instead of spawning a new script.
- No new parity evidence collected; focus remains on `[VECTOR-PARITY-001]` Phase C1 C-trace capture.
- Authored input.md (Mode: Parity) directing Ralph to instrument `golden_suite_generator/nanoBragg` with TRACE_C taps for pixels (2048,2048), (1792,2048), (4095,2048), rebuild the binary, record logs under `reports/2026-01-vectorization-parity/phase_c/<STAMP>/c_traces/`, and run `pytest --collect-only -q` after Python trace edits.
- Follow-up: Expect Attempt update with commands.txt, trace_env.json, and three TRACE_C logs; supervisor to review earliest divergence before moving to Phase C2 PyTorch traces.

### 2026-01-06 (galph loop - VECTOR-PARITY Phase C instrumentation handoff)
- Repo already synced; reviewed required spec/arch/testing docs and active plans before selection. Coin flip = heads → audited Ralph commits 0548f356 (ROI parity bundle) and b401d45f (Phase C trace plan). ROI commit added tracked `reports/…/roi_compare` artifacts; reinforced keep-future-artifacts-untracked guidance in plan/input.
- Confirmed trace_plan open questions: approved pixel set (2048,2048), (1791,2048), (4095,2048); aggregate tap scope only; reuse `scripts/debug_pixel_trace.py`.
- Updated plans/active/vectorization-parity-regression.md (lines 12,50-52) and docs/fix_plan.md (line 37) with supervisor decisions; Next Actions now stage Phase C1–C3 instrumentation.
- Replaced input.md (Mode: Parity) directing Ralph to instrument C & Py traces, store logs under `reports/2026-01-vectorization-parity/phase_c/<STAMP>/`, and draft first_divergence.md skeleton.
- Follow-up: Expect Attempt logging with c_traces/py_traces + first_divergence.md; supervisor to review earliest mismatch before authorising ROI sweeps or implementation.

### 2026-01-04 (galph loop - VECTOR-PARITY Phase B4 kickoff)
- Repo already up to date; reviewed required spec/arch/testing docs and active plans before analysis. Coin flip = heads → audited Ralph commit 15a4d338 (Option A enablement) noting `test_high_resolution_variant` now fails with corr≈0.716 as expected.
- Updated `plans/active/vectorization-parity-regression.md` Status Snapshot and Phase B table: B3a–B3e marked [D] with artifact references; Phase B4 ROI sweep remains open.
- Refreshed `docs/fix_plan.md` `[VECTOR-PARITY-001]` Next Actions to focus on Phase B4a nb-compare ROI run + B4b summary and trace staging.
- Replaced `input.md` (Mode: Parity) directing Ralph to execute the 512² ROI `nb-compare` command and archive outputs under `reports/2026-01-vectorization-parity/phase_b/<STAMP>/roi_compare/`.
- Follow-up: Expect Attempt logging for B4a metrics/summary; once ROI evidence lands, plan for trace callchain prep per Phase C guidance.

### 2026-01-03 (galph loop - Option A activation)
- Repo already synced. Reviewed required docs + active plans; coin flip = heads → audited Ralph commits `cab99e1`, `ab9aaee` (evidence-only, no regressions).
- Adopted VECTOR-PARITY Phase B3 Option A (un-skip high-res pytest). Updated `plans/active/vectorization-parity-regression.md` with tasks B3a–B3e/B4a–B4b and refreshed status snapshot.
- Refreshed `docs/fix_plan.md` `[VECTOR-PARITY-001]` Next Actions to align with Option A execution (golden data generation, doc updates, pytest run, ROI nb-compare).
- Replaced `input.md` (Mode: Parity) instructing Ralph to generate the 4096² golden image, update docs, implement the ROI-based pytest, run the targeted selector (expected FAIL), and capture artifacts under `reports/2026-01-vectorization-parity/phase_b/$STAMP/`.
- Follow-up: Expect Attempt logging for B3a–B3d with golden data + pytest failure evidence; then proceed to B4 ROI sweep and Phase C trace prep.

### 2026-01-03 (galph loop - VECTOR-PARITY Phase B2 prep)
- Repo already up to date; reread spec/arch/testing docs and active plans before analysis. Coin flip = heads → reviewed Ralph commit f1a6a9b9 (benchmark evidence only); regression remains but no new regressions introduced.
- Updated plans/active/vectorization-parity-regression.md status snapshot + Phase B1 row to log bundle 20251010T030852Z; fix_plan Next Actions now center on Phase B2 pytest + ROI scope before trace work.
- Replaced input.md (Mode: Parity) directing Ralph to execute Phase B2 `pytest -v tests/test_at_parallel_*.py -k 4096` with fresh STAMP bundle under reports/2026-01-vectorization-parity/phase_b/.
- Follow-up: Expect Attempt #5 in [VECTOR-PARITY-001] capturing pytest log/summary; supervisor should review parity metrics vs benchmark delta, then unblock Phase B3 and trace prep if failure reproduces.

### 2025-12-31 (galph loop - VECTOR-PARITY Phase B kickoff)
- Repo already up to date; re-read spec/arch/testing docs and active plans before analysis. Coin flip = heads → reviewed Ralph commits b69ad67/a7c739d (evidence-only bundles + plan update); no regressions found.
- Updated `plans/active/vectorization-parity-regression.md` status snapshot to mark Phase A1–A3 [D] and expanded Phase B1 guidance (benchmark copy + nb-compare sum_ratio capture under `reports/2026-01-vectorization-parity/phase_b/$STAMP/`).
- Refreshed `docs/fix_plan.md` `[VECTOR-PARITY-001]` Next Actions to point at the Phase B1 evidence bundle (include copy step from `reports/benchmarks/<ts>` and full-resolution nb-compare).
- Replaced `input.md` (Mode: Parity) directing Ralph to execute Phase B1: rerun the 4096² benchmark, copy the output into the phase_b bundle, run nb-compare for correlation/sum_ratio, and stage env/summary/commands artifacts; mapped tests now include `pytest -v tests/test_at_parallel_*.py -k 4096` for the follow-up.
- Next follow-up: Expect Attempt #2 in `[VECTOR-PARITY-001]` with the new evidence bundle; supervisor should review metrics, then hand Vector-Parity plan into Phase B2 parity selectors / Phase C trace prep.

### 2025-12-25 (galph loop - SOURCE-WEIGHT Phase H kickoff)
- Synced repo (already up to date). Reviewed specs/arch/testing docs plus active plans before analysis.
- Coin flip = heads → audited Ralph commits a1a6281 and 58b3da4; parity evidence solid, no regressions detected.
- Updated `plans/active/source-weight-normalization.md` to mark Phase G tasks complete (Attempts #34–#35) and expanded Phase H with new H4 dependency notification step.
- Refreshed `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` status/Next Actions to focus on Phase H memo + test flip; reproduction commands now reference the sanitised fixture.
- Replaced `input.md` (Mode: Docs) directing Ralph to author the Phase H parity memo, remove the xfail, and rerun the targeted pytest selector while depositing artifacts under `reports/2025-11-source-weights/phase_h/<STAMP>/`.
- Follow-up: Ralph to execute Phase H1–H2 per new input, then prep for H3/H4 ledger propagation next loop.

### 2025-12-24 (galph loop - SOURCE-WEIGHT Phase G reset)
- Audited the 20251009T212241Z evidence bundle: PyTorch CLI aborted (`Need -hkl/-default_F`), `test_c_divergence_reference` XPASSed, and no metrics/commands were captured; reopened Phase G2/G3 and documented the anomaly (`unexpected_c_parity/metrics.json`).
- Updated `plans/active/source-weight-normalization.md` Phase G guidance to require rebuilding the C binary, capturing full artifact sets, and halting if C parity persists; fix_plan entry `[SOURCE-WEIGHT-001]` now marks Attempt #27 as FAILED with explicit next steps.
- Rewrote `input.md` (Mode: Docs+Parity) directing Ralph to rebuild the C binary, rerun the Phase F command set, archive a fresh `<STAMP>` bundle (logs, metrics, stdout/stderr), and log a new Attempt before proceeding.
- Follow-up for Ralph: execute the refreshed Phase G2 instructions, ensure the CLI commands succeed with `-default_F`, collect Py/C metrics plus correlation, then update docs/fix_plan.md and leave Phase G blocked if divergence remains unresolved.

### 2025-12-24 (galph loop - SOURCE-WEIGHT parity bundle refresh)
- Re-read plans/active/source-weight-normalization.md and docs/fix_plan.md:4046; focus stays on TC-D1/TC-D3 parity metrics before VECTOR work can unblock.
- Replaced input.md (Mode: Parity) with explicit TC-D1/TC-D3 commands (PyTorch + C) including default_F, divergence parameters, and artifact expectations; pointed Ralph at prior diagnostic snippet (reports/2025-11-source-weights/phase_e/20251009T123427Z/commands.txt) for simulator_diagnostics capture and scripted the metrics computation.
- No plan edits this loop; awaiting fresh parity evidence before flipping Phase E3 / VECTOR-TRICUBIC-002 Phase A2.

### 2025-12-24 (galph loop - vectorization relaunch plan)
- Authored `plans/active/vectorization.md` to relaunch the vectorization initiative (Phase A dependency gate through Phase E closure) and logged it in `docs/fix_plan.md` as `[VECTOR-TRICUBIC-002]` with explicit Next Actions (SOURCE-WEIGHT-001 parity → regression refresh → profiler relaunch).
- Updated `input.md` (Mode: Perf) to direct Ralph to capture SOURCE-WEIGHT-001 Phase E parity artifacts (corr ≥0.999, |sum_ratio−1| ≤1e-3) per the new plan’s Phase A1 and stored guidance in How-To Map.
- Fix_plan index now includes `[VECTOR-TRICUBIC-002]` (in_planning) pointing to the new plan; dependency links to VECTOR-GAPS-002 and PERF-PYTORCH-004 clarified.
- Follow-up for Ralph: execute the parity evidence run (pytest selector + CLI bundle), archive outputs under `reports/2025-11-source-weights/phase_e/<STAMP>/`, then update `docs/fix_plan.md` attempts so Phase A can flip to ready.

### 2025-12-24 (galph loop - SOURCE-WEIGHT Phase E parity prep)
- Confirmed guard already landed in commit 3140629; marked Phase E1 done in `plans/active/source-weight-normalization.md` and refreshed E2 guidance to require an in-process `pytest.warns(UserWarning)` assertion plus fresh parity metrics.
- Updated `docs/fix_plan.md` Next Actions to focus on TC-D2 pytest.warns, rebuilding the C binary if needed, and capturing TC-D1/D3 correlation ≥0.999 with |sum_ratio−1| ≤1e-3 before notifying vectorization/perf initiatives.
- Replaced `input.md` with instructions to convert TC-D2 to pytest.warns, run the targeted parity pytest selector, reproduce the CLI bundle, and archive metrics/warning logs under a new `phase_e/<STAMP>/` directory.
- Follow-up for Ralph: adjust the test as directed, rebuild the instrumented nanoBragg binary if absent, run the mapped pytest + CLI commands, capture metrics in the new reports folder, and update docs/fix_plan.md attempts once evidence meets the thresholds.

### 2025-12-24 (galph loop - SOURCE-WEIGHT guard alignment)
- Updated `plans/active/vectorization-gap-audit.md` status snapshot and B1 row to mark the profiler trace as BLOCKED until SOURCE-WEIGHT-001 Phase E parity evidence lands (corr ≥0.999, |sum_ratio−1| ≤1e-3), keeping fix_plan + plan in sync.
- Replaced input.md with Parity-mode instructions emphasizing conversion of the CLI warning from stderr print to `warnings.warn(... stacklevel=2)`, reactivating TC-D2 via `pytest.warns`, and capturing the Phase D3 command bundle metrics under `reports/2025-11-source-weights/phase_e/<STAMP>/`.
- Follow-up for Ralph: implement the guard change in `src/nanobrag_torch/__main__.py`, update TC-D2, run the mapped pytest + CLI commands with NB_RUN_PARALLEL=1, archive artifacts, then update docs/fix_plan attempts and plan Phase E rows.

### 2025-12-24 (galph loop - SOURCE-WEIGHT Phase E execution prep)
- Reviewed plans/active/source-weight-normalization.md Phase E tasks and docs/fix_plan.md:4027-4029; no plan edits needed, but parity evidence still outstanding.
- Reissued input.md focusing on CLI warning guard implementation, TC-D2 activation, and parity artifact capture (commands/metrics/warning logs) so VECTOR-GAPS-002 Phase B can unblock once evidence lands.
- Highlighted requirement to rerun Phase D3 command bundle, compute correlation/sum-ratio manually, and update docs/fix_plan + plan with new timestamp after execution.
- Follow-up for Ralph: implement the guard in __main__.py, switch TC-D2 to pytest.warns, rerun targeted pytest + CLI commands, capture artifacts under reports/2025-11-source-weights/phase_e/<STAMP>/, then record a new Attempt in fix_plan.md and advance plan Phase E rows.

# Galph Memory

### 2025-12-24 (galph loop - Source-weight Phase D design prep)
- Marked Phase D1 complete in `plans/active/source-weight-normalization.md` (evidence at `reports/2025-11-source-weights/phase_d/20251009T102319Z/`) and rewrote D2/D3 guidance to require a design_notes.md decision doc plus harness prep before implementation.
- Updated `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` Next Actions to focus on drafting the design decision and acceptance harness prior to Phase E parity runs.
- Issued new `input.md` (Mode: Docs) directing Ralph to create the Phase D2 design bundle: fresh timestamped folder, design_notes.md synthesising divergence options, collect-only pytest proof, and summary scaffolding.
- Follow-up for Ralph: deliver the design_notes.md recommendation with command log + pytest collect output, then update fix_plan attempts; next loop we can green-light Phase D3 harness work.

### 2025-12-24 (galph loop - SOURCE-WEIGHT Phase D evidence gate)
- Discovered that no Phase D artifacts exist for SOURCE-WEIGHT-001; warm-run profiler captures still show correlation 0.721. Updated docs/fix_plan.md ([SOURCE-WEIGHT-001] status, Next Actions, Attempt #7) and plans/active/source-weight-normalization.md to mark Phase C done and Phase D pending. Repointed [VECTOR-GAPS-002] Phase B1 as BLOCKED until Phase D logs correlation ≥0.99.
- Replaced input.md with Parity-mode instructions directing Ralph to rerun the weighted-source parity test (NB_RUN_PARALLEL=1, -oversample 1), collect CLI metrics under reports/2025-11-source-weights/phase_d/<STAMP>/, and update the ledger once evidence lands.
- Follow-up for Ralph: execute the new Do Now commands, archive metrics/summary/env files, then append Attempt #7 completion details to docs/fix_plan.md so the 4096² profiler rerun can resume next loop.

### 2025-12-24 (galph loop - Vectorization gap Phase B1 rerun prep)
- Confirmed no fresh profiler evidence exists after SOURCE-WEIGHT-001; the latest Phase B1 bundles (20251009T070458Z/094735Z) still report 0.72 correlation, so Phase B2 remains blocked.
- Updated `docs/fix_plan.md` `[VECTOR-GAPS-002]` Next Actions to require the Phase B1 rerun to capture ≥0.99 correlation in both `correlation.txt` and `summary.md` for downstream backlog work.
- Reissued `input.md` (Perf mode) instructing Ralph to create a new UTC-stamped reports folder, rerun the 4096² CPU profiler, generate correlation/top-k kernel summaries via inline Python snippets, and log a new Attempt once parity is verified.
- Follow-up for Ralph: execute the refreshed Do Now commands, archive artifacts under `reports/2026-01-vectorization-gap/phase_b/<STAMP>/`, and update docs/fix_plan.md Attempt #3 with timings, correlation, and any anomalies from top_kernels.txt before proceeding to Phase B2.

### 2025-12-23 (galph loop - Vectorization plan archival & gap handoff)
- Archived `plans/active/vectorization.md` to `plans/archive/vectorization.md` with Phase H status lines updated; marked `[VECTOR-TRICUBIC-001]` as done in `docs/fix_plan.md` (Attempt #18 closure recorded).
- Refreshed `plans/active/vectorization-gap-audit.md` Status Snapshot and Phase B1 guidance to note SOURCE-WEIGHT-001 + VECTOR-TRICUBIC-001 dependencies cleared; profiler capture now unblocked.
- Issued new `input.md` (Mode: Perf) directing Ralph to execute Phase B1 profiler run with fresh UTC-stamped artifacts, correlation ≥0.99, env snapshot, and ledger Attempt update under `reports/2026-01-vectorization-gap/phase_b/<STAMP>/`.
- Follow-up for Ralph: run the Phase B1 command bundle, document results (commands/env/summary/correlation), append Attempt #3 in fix_plan, and flag any correlation regressions before moving to B2 hotspot mapping.

### 2025-12-23 (galph loop - Vectorization Phase H kickoff)
- Synced clean; reviewed vectorization docs/fix_plan + recent PERF-PYTORCH-004 Attempt #36 device-placement commit. Determined Phase H blocker cleared.
- Updated `plans/active/vectorization.md` Phase H section: marked H1 [D] with commit reference, refreshed status snapshot, expanded H2 guidance with explicit CUDA pytest/benchmark commands, clarified prereqs met.
- Refreshed `docs/fix_plan.md` `[VECTOR-TRICUBIC-001]` header: status now reflects Phase H execution, Next Actions trimmed to H2/H3 deliverables, reproduction list includes CUDA selectors + benchmark commands.
- Issued new `input.md` (Mode: Perf) directing Ralph to capture CUDA parity logs and benchmarks under `reports/2025-10-vectorization/phase_h/<STAMP>/`, gather env metadata, and log Attempt #18.
- Follow-up for Ralph: execute Phase H2 commands per input.md, store artifacts/summary, then update fix_plan + plan before archival; notify galph if CUDA parity slips below thresholds.

### 2025-12-23 (galph loop - Vectorization Phase H prep)
- Rebuilt `plans/active/vectorization.md` with phased tables (A–H) and Phase H checklist for CUDA follow-up; captured outstanding tasks H1–H3.
- Updated `docs/fix_plan.md` `[VECTOR-TRICUBIC-001]` status/Next Actions to mirror the new plan and keep CUDA evidence pending Attempt #18.
- Issued `input.md` (Parity mode) directing Ralph to fix simulator device placement (incident_beam_direction caching) and rerun CUDA vectorization tests/benchmarks.
- Follow-up: Expect CUDA logs under `reports/2025-10-vectorization/phase_h/<STAMP>/` with Attempt #18 before archiving the plan.

> Entries prior to 2025-11 have been moved to `archive/galph_memory/2025-09_to_2025-10.md` (summarized on 2025-12-04).

### 2025-12-22 (galph loop - Source weight Phase C staging)
- Updated `plans/active/source-weight-normalization.md` status snapshot: Phases A/B marked complete; Phase C implementation flagged as the active gate for PERF-PYTORCH-004 and VECTOR-GAPS-002.
- Refreshed `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` Next Actions to call for Phase C1–C3 implementation plus Phase D validation; recorded Attempt metadata alignment (updated owner/date, revised divergence text).
- Rewrote `input.md` (Parity mode) to steer Ralph toward implementing the normalization fix, adding regression tests, running compare_scaling_traces, and staging artifacts under `reports/2025-11-source-weights/phase_c/` + `/phase_d/`.
- Follow-up: Await Ralph’s Attempt #3 with implementation + validation logs before resuming vectorization-gap profiler work.

### 2025-12-22 (galph loop - Vectorization gap planning)
- Authored `plans/active/vectorization-gap-audit.md` to drive VECTOR-GAPS-002 (Phase A loop inventory through Phase D closure).
- Added `[VECTOR-GAPS-002]` section + index row to `docs/fix_plan.md` with Phase A/B/C next actions and Attempt #0 placeholder.
- Replaced input.md (Perf mode) directing Ralph to build the AST-based loop inventory script, run the new command, and log artifacts under `reports/2026-01-vectorization-gap/phase_a/<STAMP>/`.
- Follow-up: Once script outputs land, ensure Phase A3 summary + fix_plan Attempt capture counts; prepare profiler run for Phase B1.

### 2025-12-22 (galph loop - Source weighting Phase B kickoff)
- Updated `plans/active/source-weight-normalization.md` Status Snapshot to highlight Phase B dependency on vectorization-gap profiling and expanded B1–B3 guidance with explicit artifact paths under `phase_b/<STAMP>/`.
- Refreshed `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` Next Actions so Phase B1–B3 documentation is the immediate deliverable (Attempt #2) before implementation, noting the link to PERF-PYTORCH-004 P3.0b/P3.0c fixes.
- Overwrote `input.md` (Parity mode) directing Ralph to execute Phase B1–B3 documentation work: collect-only proof, normalization_flow.md, strategy.md, tests.md, summary, commands, env, and update plan/fix_plan after completion.
- Follow-up: After Ralph lands the Phase B bundle, verify plan rows B1–B3 flip to [D], log fix_plan Attempt #2 with artifacts, and prepare supervisor guidance for Phase C implementation.

### 2025-12-22 (galph loop - Vectorization gap Phase B kickoff)
- Verified Phase A3 artifacts (20251009T065238Z) already satisfy classification requirements; no new plan needed.
- Updated `docs/fix_plan.md` `[VECTOR-GAPS-002]` entry to `in_progress`, refreshed Next Actions for Phase B1–B3, and logged Attempt #2 referencing the classification bundle.
- Replaced `input.md` (Perf mode) instructing Ralph to execute Phase B1 profiler capture, store artifacts under `reports/2026-01-vectorization-gap/phase_b/<STAMP>/`, run collect-only proof, and update ledger/plan status.
- No code changes; awaiting profiler results before adjusting plan Phase B table.
- Follow-up: After Ralph lands B1 metrics, mark plan row B1 to [P]/[D], append Attempt #3 in fix_plan with inclusive-time data, then supervise Phase B2 loop correlation.

### 2025-12-22 (galph loop - Source grid vectorization evidence)
- Focused on [PERF-PYTORCH-004] Goal 2 gap: logged `generate_sources_from_divergence_dispersion` triple-loop cost (~0.126 s per call for 3,969 sources).
- Created reports/2025-10-vectorization/gaps/20251009T061928Z/{analysis.md,generate_sources_timing.txt,commands.txt,env.json}.
- Input.md now directs Ralph to batch this function, capture new timings, run `pytest tests/test_divergence_culling.py -v`, and log Attempt update under fix_plan.
- Open follow-up: update perf plan section with new sub-phase after Ralph lands implementation; ensure CUDA benchmarking queued post device-placement fix.

## Archived Summary (2025-09 → 2025-10)
- Established supervisor workflow, enforced prompts/debug.md routing, and opened initial parity/performance plans (AT-021 trace parity, AT-012 rotation, PERF-PYTORCH-004, REPO-HYGIENE-002).
- Diagnosed key issues: φ=0 carryover, metric duality regression (V_actual vs formula volume), pix0 override drift, torch.compile warm-up overhead, and float32 plateau fragmentation hurting peak matching.
- Captured repeated reminders on Protected Assets/dirty worktree hygiene and documented long-term goals (CLI parity restoration before vectorization, Dynamo cache validation, detector pivot rules).
- Logged recommended follow-ups: restore Core Rule #13 duality, regenerate parity traces, tighten test tolerances after fixes, and prioritize evidence artifacts under `reports/` for Ralph’s loops.

## 2025-12-21 (galph loop - Phase N2 planning)
- Git up to date; refreshed docs/index.md, specs/spec-a.md shards, arch.md, docs/development/c_to_pytorch_config_map.md, docs/debugging/debugging.md, docs/development/testing_strategy.md, docs/fix_plan.md, and plans/active/cli-noise-pix0/plan.md before choosing focus.
- Coin flip=heads; reviewed Ralph commit e7ad6b6 (Attempt #199) — documentation/artifact updates only, ROI float images captured, no regressions.
- Detected plan drift (Phase N1 still open); selected Planning action on CLI-FLAGS-003 Phase N to realign plan/status with fix_plan.
- Updated plans/active/cli-noise-pix0/plan.md Status Snapshot date and marked Phase N1 row [D] with Attempt #199 path.
- Authored new input.md (Parity mode) directing Ralph to run targeted pytest, execute nb-compare for Phase N2, create analysis.md, and log metrics in docs/fix_plan + plan row N2.
- Long-term Goals review: Goal 1 (phi carryover removal) confirmed complete; Goal 2 (spec audit) unchanged—docs/bugs keeps C bug quarantined; Goal 3 (vectorization) plan already current, no edits today.
- Follow-up for Ralph: run the nb-compare command exactly as documented, capture summary/PNG/diff outputs under results/, update todo_nb_compare checklist, record Attempt with metrics, and flip plan row N2 to [D].

## 2025-12-21 (galph loop - Phase N1 ROI prep)
- Git up to date; re-read docs/index.md, specs/spec-a-core.md, arch.md, docs/development/c_to_pytorch_config_map.md, docs/debugging/debugging.md, docs/development/testing_strategy.md, plans/active/cli-noise-pix0/plan.md before analysis.
- Coin flip=heads; reviewed Ralph commits c0b4b8b and 0ed4037 — documentation-only work (Phase M6 skip record + Option 1 bundle) with no regressions.
- Focus set to CLI-FLAGS-003 Phase N1; no new plan needed (existing plan already structured).
- Confirmed docs/fix_plan.md Next Actions point at Phase N1 ROI regeneration; plan row N1 still open and metadata-only bundle 20251009T014553Z lacks float images.
- Authored new input.md (Parity mode, 101 lines) directing Ralph to run pytest, regenerate C/PyTorch ROI floatfiles under <STAMP>, capture commands/env/sha, and log Attempt updates for docs/fix_plan + plan row N1.
- Long-term goals status: φ carryover removal remains complete; documentation audit (Goal 2) shows spec shards free of carryover bug; vectorization/backlog unchanged pending CLI closure.
- Follow-up for Ralph: execute Phase N1 per input.md, produce ROI floatfiles + metadata, update fix_plan Attempt, and mark plan row N1 to [P] once artifacts exist; hold nb-compare for next loop.

## 2025-11-06 (galph loop - K3d dtype evidence prep)
- Coin flip=heads → reviewed Ralph commits d150858, b73f0e2; work productive (Phase H1 evidence, Phase G3 orientation fix).
- Updated plans/active/cli-noise-pix0/plan.md Phase H goal + tasks (H1 marked done; new H2 beam propagation, H3 lattice, H4 parity).
- docs/fix_plan.md Next Actions now call out H2–H4 sequence; reinforced beam-vector fix as first deliverable.
- Authored new input.md (Do Now: Phase H2 beam propagation + targeted pytest) and committed with message "SUPERVISOR: CLI H2 plan refresh - tests: not run".
- Working tree clean post-push (feature/spec-based-2 @ 35cd319).
 - Follow-up: Ralph to wire detector.beam_vector into Simulator, rerun beam trace, and land targeted pytest per input.md.
## 2025-10-06 (galph loop - Phase H3 evidence prep)
- git sync clean (ba649f0). Reviewed required specs/arch/testing docs plus plans/active entries before analysis per SOP.
- Long-term Goal 1 status: beam vector fix merged (commit 8c1583d) but Phase H3 evidence missing—PyTorch trace still shows pre-fix divergence. Key gaps: rerun `trace_harness.py` without manual overrides, diff against `trace_c.log`, log first divergence; likely causes for residual lattice mismatch are either incorrect `sincg` argument (`π*(h-h0)` vs `π*h`) or Na/Nb/Nc scaling once incident vector confirmed. Goal 2 (vectorization) remains blocked until CLI parity evidence complete; Phase A baseline still outstanding.
- Coin flip → heads; reviewed last ~10 Ralph iterations. Latest commit 8c1583d correctly delegates `detector.beam_vector` into Simulator, adds regression test (`TestCLIBeamVector::test_custom_beam_vector_propagates`), no regressions observed. Work productive; advised to capture post-fix trace before touching lattice math.
- Plan upkeep: marked `plans/active/cli-noise-pix0/plan.md` Phase H2 as [D] with Attempt #20 context and refreshed H3 guidance to require new trace evidence + hypothesis logging. Input memo rewritten (108 lines) directing Ralph to produce `trace_py_after_H2` artifacts, diff vs C, update reports/implementation notes, and run targeted pytest.
- Follow-ups for Ralph next loop: run trace harness with env vars, store `trace_py_after_H2` + diff + comparison markdown, update docs/fix_plan Attempt log with findings, keep loop evidence-only (no code edits) before advancing to lattice fixes.

## 2025-10-06 (galph loop - H3 sincg diagnosis setup)
- Git already up to date (15fdec5); mandatory spec/arch/testing docs and active plans refreshed before analysis.
- Long-term Goal 1: New Phase H3 evidence (commit ce28187) shows `F_latt` mismatch; confirmed top hypothesis is PyTorch feeding `(h-h0)` into `sincg`. Updated `plans/active/cli-noise-pix0/plan.md` H3 guidance to require manual `sincg(M_PI*h, Na)` reproduction and hypothesis logging before any simulator edits.
- docs/fix_plan.md `[CLI-FLAGS-003]` Next Actions now point at rerunning `trace_harness.py`, capturing manual `sincg` calculations, then executing Phase H4 once the lattice fix is staged.
- Coin flip=heads → reviewed Ralph’s latest code commit (ce28187). Evidence-only trace capture landed as expected, no regressions observed; productive iteration highlighting sincg vs lattice scaling suspects.
- Long-term Goal 2: `plans/active/vectorization.md` Phase A updated to author reusable tricubic/absorption benchmark harnesses under `scripts/benchmarks/` so baseline timings can be captured once CLI parity stabilises; fix_plan Next Actions adjusted accordingly.
- Authored new input.md (Do Now: rerun trace harness, compute manual sincg table, pytest collect) and staged reporting guardrails for today’s evidence-only loop.
- Follow-ups for Ralph: regenerate PyTorch trace under `trace_py_after_H3.log`, create `manual_sincg.md` comparing `(h-h0)` vs absolute arguments, append findings to `implementation_notes.md`, and keep Attempt log current before proposing the simulator fix.
## 2025-10-06 (galph loop - Phase H3 pix0 evidence refresh)
- Re-read core docs + active plans; long-term Goal 1 still blocked by Phase H3 lattice parity, Goal 2 (vectorization) queued until CLI parity stabilises.
- Evidence review: trace diff shows 1.14 mm gap between PyTorch `pix0_override_m` and C’s BEAM-pivot transform, cascading to pixel_pos, scattering_vec, and h/k/l deltas. Sincg confirmed equivalent; root cause is detector pix0 override handling.
- Plan upkeep: updated `plans/active/cli-noise-pix0/plan.md` Phase H exit criteria and H3 task to require reproducing C’s pix0 math + restoring attempt log. docs/fix_plan.md Next Actions now point at capturing `pix0_reproduction.md`, propagating deltas, and logging Attempt #21 properly before code edits.
- Coin flip = heads → reviewed Ralph commits `ce28187`, `4e0e36e` (evidence-only, productive; no regressions). Feedback captured in input.md.
- Authored new input.md directing Ralph to rerun trace harness, build pix0 reproduction notebook, clean up `attempt_log.txt`, append implementation notes, and run `pytest --collect-only -q` (evidence loop).
- Follow-ups for Ralph next loop: produce the refreshed trace + pix0 reproduction artifacts, restore the attempt log with human-readable Attempt #21, log findings in implementation_notes.md, keep work evidence-only pending detector fix design.

## 2025-10-06 (galph loop - Phase H3b kick-off)
- `git pull --rebase` clean. Reviewed core docs + active plans + testing strategy per SOP.
- Goal 1: Phase H3 evidence (Attempt #21) now complete; updated `plans/active/cli-noise-pix0/plan.md` to split H3 into H3a (done) and new H3b implementation task, and refreshed `[CLI-FLAGS-003]` Next Actions to focus on applying the BEAM-pivot transform plus regression test.
- Goal 1 follow-up: Authored new input.md directing Ralph to implement the pix0 transform, add a targeted CLI regression test, capture artifacts under `reports/2025-10-cli-flags/phase_h/implementation/`, and document Attempt #22 before moving to parity (Phase H4).
- Goal 2: Vectorization plan unchanged—Phase A evidence still outstanding; keep queued until CLI parity unblocks bandwidth.
- Coin flip = heads: reviewed Ralph’s latest evidence commits (`4e0e36e`, `0f18548`); both were productive (manual sincg rejection, pix0 reproduction) with no regressions.
- Follow-ups for Ralph: execute Phase H3b implementation per new memo, then proceed to H4 parity once regression test passes.

## 2025-10-06 (galph loop - Phase H3b implementation prep)
- `git pull --rebase` clean; no upstream changes to reconcile. Coin flip → tails, so skipped retrospective commit audit per instructions.
- Refined `plans/active/cli-noise-pix0/plan.md` H3b guidance to spell out the projection workflow (`pix0_override - distance·beam` → F/S beam offsets, beam-centre tensor updates) and mandated artifact targets (`pix0_expected.json`, regression log, implementation notes).
- Updated `docs/fix_plan.md` `[CLI-FLAGS-003]` Next Actions to mirror the new projection math, regression expectations, and artifact checklist ahead of Attempt #22.
- Rewrote `input.md` (114 lines) directing Ralph to implement the BEAM-pivot transform, add the targeted pytest node, capture traces/logs under `reports/2025-10-cli-flags/phase_h/implementation/`, and log Attempt #22 once complete.
- No code edits performed; awaiting Ralph’s implementation pass before moving to Phase H4 parity.
## 2025-10-06 (galph loop - Phase H3b retargeted)
- Coin flip → tails; skipped retrospective review per SOP.
- Re-read required docs plus `plans/active/vectorization.md` and `plans/active/cli-noise-pix0/plan.md`; long-term Goal 1 still blocked on pix0 override parity, Goal 2 remains queued until CLI parity settles.
- Evidence review: targeted pytest node now aborts during CLI parsing (missing `-default_F`), and manual Detector instantiation reproduces large X-component error (pix0 ≈1.19e-04 m vs C’s −0.2165 m). `Detector._calculate_pix0_vector` projection math yields F/S beams ≈0.2177/0.2139 m, driving unrealistic beam-centre tensors (~1.25e3 px) and failing to match C.
- Updated `plans/active/cli-noise-pix0/plan.md` Phase H3b to split into H3b1 (capture C/Py traces with/without override), H3b2 (mirror actual CUSTOM/BEAM mapping without projection), and H3b3 (fix CLI regression test). Annotated the phase with Attempt #22 failure context.
- Synced `docs/fix_plan.md` Next Actions to align with the new H3b1–H3b3 scope (trace collection → implementation → regression test repair).
- Authored new input.md directing Ralph to gather paired C/Py traces, stash logs under `reports/2025-10-cli-flags/phase_h/implementation/`, and summarise deltas in `pix0_mapping_analysis.md` before touching detector code.
- Follow-up for Ralph next loop: execute H3b1 evidence capture (both NB_C_BIN and Py harness runs, override on/off), document findings, then proceed to H3b2 using measured relationships.

## 2025-10-06 (galph loop - H3b2 readiness)
- Reviewed CLI-FLAGS-003 status; confirmed Attempt #23 evidence proves C ignores `-pix0_vector_mm` when custom vectors present, leaving 1.14 mm pix0 Y delta from PyTorch.
- Updated plans/active/cli-noise-pix0/plan.md Phase H3b: marked H3b1 complete, rewrote H3b2/H3b3 guidance to enforce precedence (custom vectors > override) and to adjust regression test expectations.
- Regenerated input.md (100 lines) directing Ralph to implement the precedence fix, update tests/test_cli_flags.py, capture artifacts under reports/2025-10-cli-flags/phase_h/implementation/, and log Attempt #24.
- No code changes performed; repo remains clean aside from plan/input updates.
- Follow-ups for Ralph: execute H3b2 implementation + H3b3 regression rewrite, rerun targeted pytest node, update docs/fix_plan.md Attempt log with metrics, and stash validation artifacts before moving to Phase H4.
## 2025-10-06 (galph loop - Phase H4 prep)
- `git pull --rebase` clean; reviewed required docs and active plans.
- Phase analysis: CLI parity still blocked by +3.9 mm pix0 Y delta despite H3b2 precedence fix; vectorization plan untouched (Phase A evidence pending).
- Coin flip = heads → reviewed Ralph’s last iterations (commits 5a9a9ea, d6f158c, 60852bb). Precedence implementation productive but regression test currently tolerates 5 mm delta — flagged for tightening post-fix.
- Updated `plans/active/cli-noise-pix0/plan.md` context + Phase H3b2/H3b3 entries to reflect completion and refocused H4 guidance on C beam-centre recomputation. Synced docs/fix_plan.md Next Actions and refreshed pix0_mapping_analysis.md checklist.
- Authored new input.md (100 lines) directing Ralph to port C’s post-rotation Fbeam/Sbeam recomputation, rerun traces, tighten pytest tolerances, and archive artifacts under `reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/`.
- Reminder for next loop: verify H4 implementation lands, tighten test tolerance to ≤5e-5 m, capture Attempt #25 evidence. Vectorization plan remains frozen until CLI parity cleared.
## 2025-10-17 (galph loop - H4 decomposition)
- Coin flip → tails; skipped retrospective commit audit per instructions.
- Deep-dive vs long-term goals: Goal 1 still blocked by pix0 parity; traced 1.14 mm Y delta to missing post-rotation `newvector` projection and stale `distance_corrected` updates in `src/nanobrag_torch/models/detector.py:326`. Goal 2 (vectorization) unchanged—Phase A evidence pending once CLI parity unblocks bandwidth.
- Debugging hypotheses documented for Ralph: (1) Absence of C’s `newvector` recomputation keeps Fbeam/Sbeam stale (highest confidence; next step is to port nanoBragg.c:1822-1859). (2) `distance_corrected` not refreshed after recompute may subtly skew downstream geometry—verify once H4a lands. (3) Beam-centre tensors may retain MOSFLM offsets under CUSTOM; confirm during implementation. Highest-confidence path is hypothesis #1 with direct code port as confirming step.
- Updated `plans/active/cli-noise-pix0/plan.md` Phase H to split H4 into H4a/H4b/H4c with explicit artifacts, tolerance targets, and pytest expectations for the pix0 recomputation work.
- Synced `docs/fix_plan.md` Next Actions with the new H4a–H4c breakdown so the ledger points Ralph to the updated plan.
- Regenerated `input.md` (100 lines) instructing Ralph to execute CLI-FLAGS-003 Phase H4a implementation, gather parity traces, tighten regression tolerances, and log Attempt #25 once complete.
- Follow-ups for Ralph: implement H4a per plan, capture parity evidence under `reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/`, tighten tests/test_cli_flags tolerance, and update docs/fix_plan.md with Attempt #25 metrics before moving to H4b.

## 2025-10-18 (galph loop - Phase H4 staging)
- `git pull --rebase` clean; reviewed CLI-FLAGS-003 plan/fix_plan, confirmed H4a–H4c remain the critical blocker for Goal 1.
- Pix0 mismatch analysis: PyTorch never mirrors nanoBragg.c’s post-rotation `newvector` projection, leaving Fbeam/Sbeam stale (≈3.9 mm Y delta). High confidence that porting lines 1822–1859 plus refreshing `distance_corrected` will close parity.
- Secondary watch-outs: ensure recompute updates cached beam centres/geometry and maintains MOSFLM +0.5 offsets; tighten regression tolerance to 5e-5 m once traces align.
- Vectorization plan (`plans/active/vectorization.md`) reviewed—structure is sound, but Phase A evidence capture still outstanding before Ralph touches tricubic refactor.
- docs/fix_plan.md now 1080 lines; flagged the need for a future archival pass once CLI parity lands.
- Regenerated `input.md` (Implementation phase) directing Ralph to execute CLI-FLAGS-003 Phase H4a–H4c, capture parity_after_lattice_fix traces, and rerun the targeted pytest node; added fallback trace harness guidance.
- Follow-ups for Ralph: implement the `newvector` recompute exactly as in C, refresh traces + summary, tighten test tolerance, log Attempt #25, then proceed to polarization (Phase I) after supervisor review.
## 2025-10-18 (galph loop - Phase I staging)
- Marked CLI-FLAGS-003 Phase H4 complete in plans/active/cli-noise-pix0/plan.md and updated the snapshot to focus on Phase I polarization; H4a–H4c rows now reference Attempt #25 artifacts under reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/.
- Synced docs/fix_plan.md: CLI-FLAGS-003 status now calls out Phase A-H done with Phase I pending; Next Actions rewritten for polarization Attempt #26 and exit-criteria item (xi) flipped to ✅.
- Noted root cause for remaining parity gap: PyTorch BeamConfig defaults polarization_factor=0.0 while nanoBragg.c uses 1.0 (golden_suite_generator/nanoBragg.c:308); Ralph must realign defaults and capture new traces/tests.
- Regenerated input.md (Phase: Implementation) directing Ralph to execute Phase I (I1–I3), add a CLI polarization regression test, rerun targeted pytest nodes, and stash evidence under reports/2025-10-cli-flags/phase_i/.
- Vectorization plan untouched; Phase A baseline capture still pending once CLI parity clears.
- Follow-ups for Ralph: implement polarization parity per plan, update docs/fix_plan.md Attempt #26 with metrics, and only then advance to nb-compare / vectorization work.

## 2025-10-19 (galph loop - Phase I3 parity directive)
- `git pull --rebase` clean; workspace already on feature/spec-based-2. Reviewed prior memory plus required docs (spec-a shards, arch.md, config map, debugging guide, testing strategy, fix_plan, docs/index).
- Long-term goal sweep: CLI parity stalled only on Phase I3; vectorization plan Phases A–F untouched pending parity evidence. `_tricubic_interpolation` still falls back to nearest-neighbour for batched tensors, reinforcing urgency once CLI closes.
- Hypotheses for Phase I3 parity gap (triage): (1) Polarization factor may still diverge if CLI path misses Kahn defaults despite BeamConfig fix—confirm by running nb-compare; (2) -nonoise might still emit noiseimage if simulator flag regressed; (3) pix0 override suppression with custom vectors must match C—verify stdout pix0 to ensure parity. Highest-confidence risk is #1; next step is the nb-compare command recorded in input.md (correlation + polarization metrics).
- No new plan drafted—`plans/active/cli-noise-pix0/plan.md` remains authoritative. Updated docs/fix_plan.md next actions to focus on Attempt #27 parity run and deepened I3 guidance.
- Regenerated input.md (143 lines, Validation phase) instructing Ralph to run nb-compare with the supervisor command, archive artifacts under `reports/2025-10-cli-flags/phase_i/supervisor_command/`, execute targeted pytest, and document Attempt #27 metrics.
- Follow-ups for Ralph: execute Do Now nb-compare command, capture stdout/stderr + summary.json, run targeted pytest + collect-only, update README + docs/fix_plan Attempt #27, leave code untouched.
## 2025-10-19 (galph loop - Phase J directive)
- `git pull --rebase` was clean; reviewed CLAUDE guardrails, spec shards, arch.md, config map, debugging + testing strategy, fix_plan, and active plans before action.
- Deep-dive confirmed Goal #1 is now blocked solely by a 1.24538e5× intensity gap even after polarization parity; Goal #2 (vectorization) remains paused until CLI parity lands (Phase A evidence still outstanding).
- Reviewed Ralph’s recent commits (`e8146c2`, `beadffc`): polarization default fix + new tests look solid; nb-compare tooling patch captured parity failure evidence without regressions. No course correction needed, but scaling issue persists.
- Updated `plans/active/cli-noise-pix0/plan.md` with new Phases J–L covering scaling evidence → normalization implementation → final parity; marked I3 as blocked and refreshed context to emphasise the scaling gap.
- Synced `docs/fix_plan.md` Next Actions with the Phase J checklist and noted that Attempt #27 directives are superseded; Phase K work now gated on Attempt #28 evidence.
- Regenerated `input.md` (Evidence phase) instructing Ralph to capture C/Py scaling traces, build `scaling_chain.md`, and log Attempt #28 before any simulator edits.
- Follow-ups for Ralph: deliver plan tasks J1–J3 (logs + analysis + fix_plan update) under `reports/2025-10-cli-flags/phase_j/`, then pause for supervisor review before touching normalization code.

## 2025-10-21 (galph loop - Phase H5 reopen)
- Phase J scaling traces revealed C honours `-pix0_vector_mm` even with custom detector vectors; PyTorch still skips override in that path → 1.14 mm pix0 delta, h/k/l drift, F_latt collapse.
- Updated `plans/active/cli-noise-pix0/plan.md` with Phase H5 (C evidence, override reinstatement, trace verification, fix_plan logging) and corrected the prior note that C ignored overrides.
- Synced `docs/fix_plan.md` Next Actions to require H5a–H5c before Phase K; Attempt #28 observations now document the confirmed driver (missing override in custom-vector path).
- Regenerated `input.md` (Implementation phase) directing Ralph to execute Phase H5b with fresh C/PyTorch traces and targeted pytest.
- Follow-up: Expect Attempt #29 after override fix; pause Phase K normalization work until H5 parity evidence lands.

## 2025-10-06 (galph loop - Phase H5 evidence setup)
- Reviewed required guardrails (docs/index.md, specs/spec-a*, arch.md, config map, debugging guide, testing strategy, docs/fix_plan.md). Focus remains CLI-FLAGS-003 Phase H5; vectorization plan untouched until parity lands.
- Confirmed plans/active/cli-noise-pix0/plan.md already tracks Phase H5a–H5d; no new plan needed. docs/fix_plan.md Next Actions (line 448) aligned with H5 checklist.
- Identified outstanding gap: need fresh C traces with and without -pix0_vector_mm to validate override precedence (Phase J evidence shows F_latt divergence from pix0 mismatch). Hypotheses logged in supervisor summary; implementation deferred until traces captured.
- input.md rewritten (Evidence phase) directing Ralph to run long-form C command twice and archive logs under reports/2025-10-cli-flags/phase_h5/c_traces/, plus document derivation in c_precedence.md before touching PyTorch.
- No code/doc changes yet; awaiting H5a artifacts. Next follow-up: after Ralph captures traces, greenlight H5b override reapplication and revisit docs/fix_plan Attempt log.

## 2025-10-22 (galph loop - Phase H5 evidence refresh)
- Updated plans/active/cli-noise-pix0/plan.md: marked H5b [D], set H5a to [P] with new requirement to refresh C traces dated 2025-10-21, clarified H5c/H5d deliverables.
- docs/fix_plan.md now points Next Actions to C trace reruns + PyTorch parity capture; logged new Attempt #29 (2025-10-21) noting override reinstatement pending evidence.
- input.md reissued (Evidence phase) directing Ralph to run NB_C_BIN command with/without override, update c_precedence.md, extend Phase H harness for H5c, and archive outputs under reports/2025-10-cli-flags/phase_h5/.
- Next follow-up: Expect refreshed C logs in reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-21/ plus PyTorch parity log; after evidence lands, revisit Phase K normalization tasks.

## 2025-10-23 (galph loop - H5a evidence push)
- Confirmed Phase J traces still show pix0 Y delta ~1.14 mm and `F_latt` 7.69e1 vs C 3.56e4 (`reports/2025-10-cli-flags/phase_j/trace_py_scaling.log:1-27`, `trace_c_scaling.log:164-190`); geometry remains the blocker before normalization.
- Expanded `plans/active/cli-noise-pix0/plan.md` context with a 2025-10-22 correction note and tightened H5c guidance to demand `F_latt` ≈3.5636e4 and pix0 <5e-5 m deltas before Phase K.
- Clarified `docs/fix_plan.md` Attempt #29 to mark the 2025-10-06 "override ignored" conclusion as instrumentation error so future loops do not rely on it.
- Reissued `input.md` (Evidence phase, 100 lines) instructing Ralph to rerun the C command with/without `-pix0_vector_mm`, store logs under `reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/`, diff them, and update `c_precedence.md` with dot-product derivations.
- Follow-ups for Ralph: deliver H5a (both C traces + precedence memo), keep prior logs untouched, then pause for supervisor review before starting H5c PyTorch traces.

## 2025-10-24 (galph loop - Phase H5 revert directive)
- `git pull --rebase` clean; re-read docs/index.md, spec shards, arch.md, config map, debugging + testing strategy, fix_plan, and active plans before proceeding.
- Deep analysis vs long-term goals: parity still blocked by pix0 mismatch (PyTorch applies override while C ignores with custom vectors); vectorization plan untouched until CLI parity closes.
- Reviewed Ralph’s latest loops (5878f16, 052307f): evidence solidly shows nanoBragg ignores `-pix0_vector_mm` when custom detector vectors supplied, but repo still carries Attempt #29 override change → root cause of 3.6e-7 `F_latt` ratio. Direction needed to undo that change.
- Updated `plans/active/cli-noise-pix0/plan.md` Phase H5: marked H5a [D], replaced H5b with "revert override when custom vectors supplied", refreshed H5c/H5d guidance, and revised context to cite 2025-10-22 C evidence.
- Synced `docs/fix_plan.md` Next Actions with new H5b/H5c tasks, emphasized Attempt #29 now needs a revert, and kept Attempt #30 observations as canonical precedence proof.
- Reissued `input.md` (131 lines, Implementation phase) directing Ralph to remove the override for custom vectors, rerun targeted pytest + trace harness, update parity_summary.md, and log Attempt #31 before touching Phase K.
- Hypotheses for remaining intensity gap now hinge on normalization once geometry parity returns; no new plan beyond existing Phase K tasks.
- Follow-ups for Ralph: execute Do Now revert + tests, capture PyTorch traces under `reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/`, update parity_summary.md and docs/fix_plan Attempt history, then pause for supervisor review before Phase K work.

## 2025-10-24 (galph loop - H5c evidence prep)
- Refreshed CLI-FLAGS-003 plan: marked H5b/H5d done, inserted doc anchor list, and rewrote Phase K tasks to target the sincg(h) bug (`plans/active/cli-noise-pix0/plan.md`).
- Updated fix_plan next actions to focus on H5c traces then Phase K1 lattice-factor fix (`docs/fix_plan.md:448-510`).
- Replaced `reports/2025-10-cli-flags/phase_h5/parity_summary.md` with post-revert guidance pointing Ralph to regenerate TRACE_PY logs (2025-10-22 baseline).
- Issued new input.md (Evidence phase) directing Ralph to run the trace harness and archive metrics before code changes.
- Key finding: PyTorch SQUARE lattice factor still feeds sincg with `(h-h0)` (src/nanobrag_torch/simulator.py) vs C’s `sincg(M_PI*h, Na)` (`golden_suite_generator/nanoBragg.c:3063-3080`); Phase K1 must correct this.
- Follow-up expectations: Ralph generates H5c PyTorch traces under `reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/`, updates parity_summary metrics, and drafts Attempt #32.

## 2025-10-24 (galph loop - Phase H5 unit fix directive)
- Reconfirmed pix0 fast-axis delta (≈1.1 mm) persists post-H5b revert; traced root cause to Detector BEAM pivot still treating beam_center_f/s as pixel counts (mm×m bug).
- Added Phase H5e row to `plans/active/cli-noise-pix0/plan.md` directing mm→m conversion with new trace artifacts; refreshed docs/fix_plan.md Next Actions to prioritise H5a/H5c/H5e sequence before Phase K.
- Issued `input.md` (Implementation phase) instructing Ralph to implement unit fix, capture trace evidence under `reports/2025-10-cli-flags/phase_h5/unit_fix/`, run `tests/test_cli_flags.py::TestCLIPix0Override`, and log Attempt #33.
- No code changes made this loop; planning/docs only. Next follow-up: verify H5e Attempt captures <5e-5 m pix0 deltas, then greenlight Phase K1 (sincg update).

## 2025-10-24 (galph loop - Phase K1 directive)
- Re-ran parity backlog review after clean `git pull`; active focus remains CLI-FLAGS-003. H5c traces still missing post-unit-fix, so emphasized capturing them as part of upcoming Phase K work.
- Deep dive confirmed SQUARE lattice factor still uses `(h-h0)` in `src/nanobrag_torch/simulator.py:200-280`, violating `specs/spec-a-core.md:218` and C reference `golden_suite_generator/nanoBragg.c:3069-3079`. Phase J evidence (`reports/2025-10-cli-flags/phase_j/scaling_chain.md`) still shows 3.6e-7 intensity ratio.
- Ralph’s recent loop (315a54c) successfully closed H5e; no regressions spotted in commit diffs. Pending action is Phase K1 sincg parity plus Phase K2 scaling refresh.
- Issued new `input.md` (Implementation phase, 107 lines) detailing Phase K1 tasks: swap to `sincg(torch.pi * h, Na)`, rerun scaling traces, author `tests/test_cli_scaling.py::test_f_latt_square_matches_c`, and update plan/attempt logs with artifacts under `reports/2025-10-cli-flags/phase_k/`.
- Follow-up for next supervisor loop: verify Ralph delivers Phase K1 artifacts (trace_py_after.log, scaling_chain_after.md, pytest log) and updates docs/fix_plan.md Attempt #34 before greenlighting Phase K2.

## 2025-10-24 (galph loop - H5c trace refresh directive)
- Re-ran `git pull --rebase` (clean) then reviewed plans/fix_plan/context.
- Noted K1 lattice fix landed in commit 0fef8f7 but plan still marked [ ]; updated `plans/active/cli-noise-pix0/plan.md:125-133` to mark K1 done, tighten H5c guidance (new 2025-10-24 trace path), and clarify K2/K3 follow-ups.
- Updated `docs/fix_plan.md:470-480` Next Actions to focus on H5c trace rerun, refreshed scaling chain (K2), and targeted pytest/docs work (K3) before Phase L.
- Flagged that parity summary still referenced pre-unit-fix data; injected TODO banner in `reports/2025-10-cli-flags/phase_h5/parity_summary.md` reminding Ralph to regenerate traces after Attempt #33.
- Issued new supervisor memo (`input.md`) directing Ralph to execute H5c trace harness, capture artifacts under `reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-24/`, and log Attempt #35; memo length trimmed to Evidence-only tasks with expanded timeline.
- No code changes made; repo remains clean pending Ralph’s evidence.
- Follow-up for Ralph: run Do Now command, update parity_summary + fix_plan attempt, then pause for supervisor review before touching Phase K2.

## 2025-10-24 (galph loop - Phase H6 spin-up)
- Coin flip = tails → skipped retrospective review; focused on active CLI parity gap per long-term Goal #1.
- Deep analysis confirms pix0 parity still fails after Attempt #35 (ΔF ≈ -1.136 mm, ΔS ≈ +0.139 mm) even with beam-center mm→m fix; `plans/active/cli-noise-pix0/plan.md` lacked follow-up guidance.
- Added Phase H6 section (H6a–H6d) to `plans/active/cli-noise-pix0/plan.md` and updated H5c state to [P]; plan now requires matched C/Py instrumentation to isolate `_calculate_pix0_vector` divergence.
- Refreshed CLI-FLAGS-003 Next Actions in `docs/fix_plan.md` to mandate H6 evidence before resuming normalization (K2/K3).
- Issued new `input.md` (Evidence phase) directing Ralph to instrument nanoBragg.c and the PyTorch trace harness, capture logs under `reports/2025-10-cli-flags/phase_h6/`, and log Attempt #36.
- Follow-up for Ralph: execute Phase H6a/H6b/H6c tasks, update parity_summary + docs/fix_plan (Attempt #36), then coordinate a targeted fix to collapse pix0 deltas <5e-5 m before returning to Phase K.

## 2025-10-25 (galph loop - H6 harness alignment)
- Ran `git pull --rebase` (clean) and reviewed Phase H6 context. Noted PyTorch harness still forces `detector_pivot=BEAM` and likely executes the stale site-package build when `PYTHONPATH` is missing.
- Updated `plans/active/cli-noise-pix0/plan.md` to mark H6a/H6d complete and to call out two guardrails for H6b: import via `PYTHONPATH=src` and fix the BEAM hardcode.
- Added matching guidance to `docs/fix_plan.md` Next Actions so CLI-FLAGS-003 explicitly requires the editable install + SAMPLE pivot trace.
- Rewrote `input.md` (Evidence phase) directing Ralph to patch `trace_harness.py`, capture the new TRACE_PY log under `reports/2025-10-cli-flags/phase_h6/py_trace/`, and stash env/git context before diffing.
- Follow-up for Ralph: deliver Phase H6b artifacts (trace, stderr, env snapshot, git context) and update parity_summary.md; Phase H6c diff comes next.

## 2025-10-25 (galph loop - H6b harness prep refresh)
- Confirmed repo already synced; quick editable-import script reproduces C pix0 within 3e-6 m, so the outstanding 1.14 mm delta is a harness problem.
- Refined Phase H6b guidance in `plans/active/cli-noise-pix0/plan.md` and the CLI-FLAGS-003 Next Actions to demand editable import plus ≤5e-6 m acceptance.
- Issued new implementation memo (`input.md`) directing Ralph to monkey-patch `_calculate_pix0_vector` via the harness, drop the BEAM hardcode, log TRACE_PY with C-style precision, and archive stdout/stderr + env/git metadata under `reports/2025-10-cli-flags/phase_h6/py_trace/`.
- Reviewed Ralph commits 9ee2ada / bf9925b — C instrumentation captured clean, no regressions; remind future loop to unwind trace hooks once parity closes.
- Next follow-up: ensure Phase H6b artifacts land, then proceed to H6c diff analysis before reopening normalization work.
## 2025-10-06 (galph loop - Phase H6c prep)
- `git pull --rebase` clean; no incoming changes.
- Reviewed CLI parity status vs long-term goal #1. Diffed `phase_h6` traces and confirmed first divergence occurs at `beam_center_m` (PyTorch logging millimetres vs C metres).
- Updated `plans/active/cli-noise-pix0/plan.md` to mark H6b complete (Attempt #37) and refocused H6c task description on trace analysis.
- Refreshed `docs/fix_plan.md` Next Actions so bullet #1 now targets H6c diff/analysis rather than instrumentation.
- Authored new `input.md` (Evidence phase) directing Ralph to produce the trace diff, document findings, and log Attempt #38.
- Follow-up for Ralph: execute H6c diff per memo, update `reports/2025-10-cli-flags/phase_h6/analysis.md` + `reports/2025-10-cli-flags/phase_h5/parity_summary.md`, then record Attempt #38 in fix_plan before moving to H6d/H5c.

## 2025-10-26 (galph loop - H6e pivot evidence setup)
- `git pull --rebase` clean; reviewed Phase H6 artifacts plus docs/index/spec/arch/config map per SOP.
- Deep dive on pix0 traces shows C runs supervisor command in SAMPLE pivot while PyTorch config still defaults to BEAM when custom detector vectors are provided; this aligns with Attempt #38 residual deltas.
- Updated `plans/active/cli-noise-pix0/plan.md` Phase H6 to mark H6c done and add new rows H6e–H6g covering pivot evidence, config fix, and post-fix trace reruns.
- Refreshed `docs/fix_plan.md` Next Actions to require H6e pivot proof, H6f pivot logic change + regression test, then H6g trace rerun before resuming Phase K work.
- Issued new Evidence-phase memo (`input.md`) directing Ralph to capture pivot parity evidence and log it under `reports/2025-10-cli-flags/phase_h6/pivot_parity.md` (no code edits yet).
- Next follow-up for Ralph: execute H6e (document pivot mismatch), update parity_summary + fix_plan Attempt log, then proceed to H6f implementation in a subsequent loop.

## 2025-10-06 (galph loop - H6f pivot enforcement prep)
- `git pull --rebase` clean; reviewed CLI parity backlog vs long-term goal #1 and vectorization plan status (no edits required yet).
- Deep dive on pix0 gap: Phase H6 evidence confirms C forces SAMPLE pivot when custom vectors are supplied; PyTorch still defaults to BEAM. Normalization remains blocked until pivot + lattice parity close.
- Coin flip → heads: inspected Ralph’s last two commits (`5d0a34d`, `0b7eaf7`). Evidence quality is solid, but parity visuals landed in repo root (`img*_*.png`, `intimage*.jpeg`, `noiseimage_preview.jpeg`) — flagged for relocation into reports before further work.
- Updated `docs/fix_plan.md` Next Actions for CLI-FLAGS-003 to mark H6e done, add H6f-prep cleanup, and call H6f/H6g/H6 progressions (Attempt #40 reserved for post-fix evidence).
- Issued new implementation memo (`input.md`) directing Ralph to move the stray images under `reports/2025-10-cli-flags/phase_h6/visuals/`, enforce SAMPLE pivot selection in `DetectorConfig`, add a targeted regression test, rerun focused pytest, and capture post-fix trace output for H6g.
- Follow-up for Ralph: execute H6f per memo, log Attempt update + regression artifacts, then pause for supervisor review before H6g.

## 2025-10-06 (galph loop - H6g evidence kickoff)
- `timeout 30 git pull --rebase` returned "Already up to date"; no conflicts encountered.
- Reviewed CLI-FLAGS-003 entry (`docs/fix_plan.md:448-462`) and Phase H6 table (`plans/active/cli-noise-pix0/plan.md:131-145`); confirmed Attempt #40 landed pivot forcing but H6g artifacts remain outstanding.
- Updated `plans/active/cli-noise-pix0/plan.md` context with Attempt #40 recap and marked H6f as `[D]`; rewrote H6g guidance to require post-fix trace + nb-compare artifacts under `reports/…/phase_h6/post_fix/` and to log Attempt #41.
- Refreshed `docs/fix_plan.md` Next Actions so list now centers on H6g verification → K2 scaling-chain rerun → K3 regression test → Phase L gating.
- Coin flip → tails, so skipped historical commit audit; focused on evidence planning.
- Authored new `input.md` (Evidence phase) instructing Ralph to rerun the trace harness with pivot fix, capture diff vs C trace, compute deltas, run ROI nb-compare, and prepare Attempt #41 notes; memo also emphasises no pytest this loop.
- Key gap notes: normalization tasks K2/K3 still blocked pending H6g; vectorization plan untouched (Phase A baseline scripts outstanding).
- Follow-up for Ralph: execute H6g evidence capture, archive artifacts under `reports/2025-10-cli-flags/phase_h6/post_fix/`, then log Attempt #41 in `docs/fix_plan.md` with measured |Δpix0| before touching normalization.

## 2025-10-27 (galph loop - K2 evidence staging)
- `git pull --rebase` clean; synced with origin before review.
- Read docs/index.md, specs/spec-a.*, arch.md, config map, debugging SOP, testing_strategy.md to refresh guardrails for CLI parity + scaling work.
- Verified CLI-FLAGS-003 Attempt #41 already landed: pix0 deltas ≤2.85 µm with SAMPLE pivot. Updated `plans/active/cli-noise-pix0/plan.md` context (new 2025-10-27 snapshot) and marked H6g `[D]`; expanded Phase K2 guidance to demand quantitative ratios explaining `test_metrics_failure.json`.
- Refreshed `docs/fix_plan.md` Next Actions so K2 (scaling harness rerun + ratio analysis) and K3 (targeted pytest + docs) are the only blockers before Phase L. Issued replacement Evidence memo in `input.md` targeting K2 harness rerun and scaling markdown refresh.
- Coin flip → heads: reviewed Ralph’s last commits. `ea8092f` (H6f) adds solid pivot forcing + regression test ✅. `921780a` only updates fix_plan. `0b7eaf7` still leaves parity PNG/JPEG artifacts in repo root (img*_*.png, intimage*.jpeg, noiseimage_preview.jpeg) — remind Ralph to relocate/delete once evidence obligations satisfied.
- Noted that `reports/2025-10-cli-flags/phase_k/f_latt_fix/test_metrics_failure.json` still reflects pre-pivot ratios (corr≈0.173); next loop must regenerate after SAMPLE pivot to see if F_cell/F_latt remain off.
- Vectorization plan remains untouched; Phase A baselines for tricubic/absorption still pending once CLI parity unblocks bandwidth.
- Follow-up for Ralph: execute Phase K2 per new memo, write updated scaling metrics (including F_cell vs C), keep Attempt #41 notes intact, and stage plan for K3 if ratios finally align.

## 2025-10-31 (galph loop - K2 rescope)
- Evidence review shows PyTorch still rescales MOSFLM cross products; C only does so when `user_cell` is set. Root cause for F_latt_b ≈ +21.6% identified. K2b added to plan with required `mosflm_rescale.py` artifact.
- Noted BeamConfig Kahn factor should default to 0.0 (C `polarization`). Reopened Phase I2 and updated fix_plan next steps to include default realignment during K3.
- Issued new Evidence memo (input.md) directing Ralph to rerun trace harness, refresh scaling markdown, and capture orientation deltas before touching normalization code.

## 2025-11-05 (galph loop - Phase K3 prep)
- Reviewed CLI parity backlog vs long-term goal #1; confirmed `Crystal.compute_cell_tensors` still rescales MOSFLM cross-products and `BeamConfig.polarization_factor` remains 1.0, explaining the lingering F_latt and polar deltas.
- Refreshed `plans/active/cli-noise-pix0/plan.md` context with a new 2025-11-05 recap and rewrote Phase K into a checklist (K3a–K3c) covering rescale gating, polarization defaults, and regression/docs closure.
- Updated `docs/fix_plan.md` CLI-FLAGS-003 Next Actions to point at the new Phase K3 tasks and the exact scripts/tests Ralph must run after code changes.
- Issued `input.md` (Implementation phase) instructing Ralph to land K3a–K3c, capture mosflm_rescale + scaling_chain artifacts under `reports/2025-10-cli-flags/phase_k/f_latt_fix/`, and rerun the targeted scaling pytest.
- Follow-up for Ralph: implement the rescale guard + polarization default fix, regenerate scaling evidence, run `pytest tests/test_cli_scaling.py::test_f_latt_square_matches_c`, then log Attempt #43 before moving to Phase L.

## 2025-11-06 (galph loop - K3d dtype evidence prep)
- Reviewed CLI-FLAGS-003 parity status: traces still show F_latt drift (Py F_latt_b≈46.98 vs C 38.63) despite SAMPLE pivot parity. Fractional h shifts (2.0012→1.9993) line up with ~2.8 µm close-distance delta.
- Hypothesis: float32 rounding in detector geometry/scattering vector pipeline drives the sincg amplification; added Phase K3d dtype sweep to plan and fix_plan (dtype_sensitivity.md artifacts under reports/2025-10-cli-flags/phase_k/f_latt_fix/dtype_sweep/).
- Updated supervisor memo targeting evidence-only float64 rerun; no pytest this loop.
- Follow-up: Ralph to execute K3d command, archive dtype comparison, then resume K3a/K3c implementation once rounding impact is quantified.

## 2025-11-07 (galph loop - K3e per-phi parity setup)
- `git pull --rebase` clean at start; reviewed plan/fix_plan, dtype sweep confirmed precision not root cause.
- Deep dive: PyTorch trace logs `k≈1.9997` (phi=0°) while C logs `k≈1.9928` (phi=0.09°); rotating PyTorch `b` by 0.09° reproduces C values ⇒ phi-grid mismatch now primary blocker.
- Updated `plans/active/cli-noise-pix0/plan.md` Phase K3a/K3b/K3d to `[D]`, added K3e (per-phi evidence) & K3f (phi sampling fix) plus new gap snapshot noting phi issue.
- Synced `docs/fix_plan.md` Next Actions with new tasks (per-phi trace capture & sampling fix); status line now reflects K3a/K3b/K3d completion.
- Authored `input.md` (Implementation phase) directing Ralph to extend `analyze_scaling.py` with `--per-phi`, instrument nanoBragg.c, and dump matched C/PyTorch phi traces under `reports/…/per_phi/`.
- Follow-up for Ralph: execute K3e per memo, produce per-phi JSON/MD logs, then we can plan the phi sampling fix (K3f) next loop.

## 2025-11-07 (galph loop - K3f baseline instrumentation)
- `git pull --rebase` clean; reviewed latest Attempt logs and vectorization backlog.
- Deep dive confirmed long-term Goal #1 still blocked by Δk≈6 gap (CLI-FLAGS-003); F_latt parity depends on capturing base lattice & scattering traces before phi rotation.
- Refreshed `plans/active/cli-noise-pix0/plan.md` Phase K3f with checklist K3f1–K3f4 (instrument C/Py, diff traces, document root cause) and synced `docs/fix_plan.md` Next Actions to match.
- Issued new Evidence-phase input.md directing Ralph to execute K3f1 (C trace run) and stage matching PyTorch harness output under `reports/2025-10-cli-flags/phase_k/base_lattice/`.
- Next Ralph steps: add TRACE_C_BASE instrumentation, run the supervisor command into `base_lattice/c_trace.log`, extend the Py harness for `TRACE_PY_BASE`, and prep for K3f3 diff once both logs exist.

## 2025-11-08 (galph loop - K3f harness correction)
- `git pull --rebase` clean; read docs/index.md, spec shards, arch.md, config map, debugging SOP, testing strategy, fix_plan, vectorization plan.
- Reviewed Ralph’s recent evidence commits (271e2b6, 2467064): instrumentation valuable but per-phi script subtracts `pix0_vector` from `detector.get_pixel_coords()`, yielding plane-relative vectors and explaining the 6-unit Δk seen in Attempt #45.
- Updated `plans/active/cli-noise-pix0/plan.md` (K3f context + K3f2 guidance) and `docs/fix_plan.md` next actions to require sample-to-pixel vectors with no double subtraction before new traces are captured.
- Chosen focus: CLI-FLAGS-003 Phase K3f base-lattice parity. Hypotheses recorded (primary: trace harness bug; secondary: confirm real/reciprocal vectors + scattering after harness fix). Next confirming step: capture corrected C/Py base traces per plan.
- Authored Evidence-phase `input.md` directing Ralph to instrument `golden_suite_generator/nanoBragg.c`, rebuild, run the supervisor CLI command, and add a corrected PyTorch harness under `reports/2025-10-cli-flags/phase_k/base_lattice/` with comparison tooling.
- No additional plan work required for vectorization yet; Phase A still pending once CLI parity unblocks bandwidth.

## 2025-11-08 (galph loop - MOSFLM rescale implementation prep)
- Verified base-lattice traces: PyTorch keeps placeholder `V≈1 Å^3` when MOSFLM A* is present, giving |a|≈5.8×10^3 Å and Δh≈6; C rescales with `V_cell≈2.4682×10^4 Å^3` before metric duality.
- Updated `plans/active/cli-noise-pix0/plan.md` Phase K3f (rows marked `[D]`) and added Phase K3g tasks for implementing the MOSFLM rescale pipeline + regression coverage; docs/fix_plan Next Actions now call out K3g1–K3g3.
- Issued Implementation-phase `input.md` (Do Now = K3g1) instructing Ralph to document root cause, mirror C’s MOSFLM real-vector rebuild, add scaling tests, refresh parity traces, and rerun `tests/test_cli_scaling.py::test_f_latt_square_matches_c` with the proper env vars.
- Long-term goal #2 (vectorization) left untouched this loop; revisit after CLI parity is recovered.

## 2025-11-08 (galph loop - K3g3 evidence staging)
- Verified commit 46ba36b’s MOSFLM rescale branch by running Crystal.compute_cell_tensors() (float64 CPU). Added `reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/cell_tensors_py.txt` and appended base_lattice summary with 2025-11-08 update.
- Updated `plans/active/cli-noise-pix0/plan.md` (K3f4 → [D], K3g1/K3g2 → [D]) and refreshed fix_plan Attempt #47 with evidence + next steps focused on Phase K3g3 parity rerun.
- Authored `input.md` directing Ralph to execute K3g3: rerun `tests/test_cli_scaling.py::test_f_latt_square_matches_c`, regenerate nb-compare metrics, refresh traces, and document results under phase_k/f_latt_fix/.
- Follow-up for Ralph: Complete K3g3 tasks per memo, update scaling_chain.md + summary.md with new metrics, and capture nb-compare/trace diffs before we attempt Phase L.

## 2025-11-08 (galph loop - K3g3 evidence prep)
- `git pull --rebase` clean; reviewed CLI-FLAGS-003 status and vectorization plan (no updates needed yet).
- Identified open gap: Phase K3g3 still needs post-fix scaling evidence; MOSFLM rescale landed in 46ba36b but traces/nb-compare not refreshed.
- Hypotheses: (1) Parity should succeed once traces regenerated; (2) residual discrepancies most likely from polarization factor default if it still logs 1.0. Await evidence.
- Authored Evidence-phase input.md (lines 1-100) directing Ralph to rerun `tests/test_cli_scaling.py::test_f_latt_square_matches_c`, capture nb-compare artifacts, refresh `scaling_chain.md` & `base_lattice/summary.md`, and log Attempt update.
- Follow-up: Ralph to complete K3g3 tasks, archive artifacts under `reports/2025-10-cli-flags/phase_k/f_latt_fix/`, and update docs/fix_plan.md before we schedule Phase L parity runs.

## 2025-11-08 (galph loop - K3g3 parity rerun directive)
- Coin flip → tails; skipped retrospective review per SOP.
- Re-read CLI parity artifacts: scaling_chain.md still frozen at Oct-06 failure; trace_diff compares old C log vs Py trace (no post-fix diff yet).
- Selected focus issue: CLI-FLAGS-003 Phase K3g3. Emphasised rerunning tests/test_cli_scaling.py::test_f_latt_square_matches_c and nb-compare with timestamped outputs under reports/2025-10-cli-flags/phase_k/f_latt_fix/post_fix/.
- Input memo instructs Ralph to regenerate C & Py base traces (run_c_trace.sh + trace_harness.py) using shared stamp, update scaling_chain.md + summary.md, and record Attempt update in docs/fix_plan.md.
- Validated pytest selector via collect-only (env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1).

## 2025-11-09 (galph loop - K3g3 evidence prep + vectorization reminder)
- `git pull --rebase` clean; reviewed docs/index.md, specs/spec-a shards, arch.md, config map, debugging SOP, testing strategy, fix_plan.
- Long-term goal check:
  * CLI parity: MOSFLM rescale/polarization fixes landed but scaling evidence still missing; base_lattice summary shows post-fix addendum yet main diff logs remain pre-fix.
  * Vectorization: Phase A artifacts never created; no reports under `reports/2025-10-vectorization/phase_a/`.
- Hypotheses logged: (1) K3g3 pytest/nb-compare likely pass now that MOSFLM rescale is fixed (confidence medium); (2) If mismatch persists, trace regeneration will expose lingering normalization gaps; (3) Remaining variance could stem from pix0/beam vector interplay, so trace-first debugging stays mandatory.
- Updated `plans/active/vectorization.md` with a 2025-11-09 gap snapshot and refreshed `docs/fix_plan.md` VECTOR-TRICUBIC-001 next actions to highlight Phase A A1–A3 as blocking.
- Authored new supervisor `input.md` directing Ralph to execute K3g3 (targeted pytest + nb-compare + trace refresh) with stamped artifacts and to update scaling_chain/summary plus fix_plan Attempt log.
- Follow-up for Ralph: run the specified pytest node under parity env, regenerate nb-compare + base-lattice traces, refresh reports/summary, and record Attempt update; if blocked, capture trace logs under `base_lattice/blocked/` and document stall.

## 2025-11-09 (galph loop - Phase L1 HKL parity prep)
- `timeout 30 git pull --rebase` clean; coin toss = tails so no retrospective audit.
- CLI-FLAGS-003 still blocked by supervisor command parity (corr≈0.9965, sum_ratio≈1.26e5). Updated `plans/active/cli-noise-pix0/plan.md` Phase L with explicit L1–L4 tasks (HKL parity → scaling trace → diagnosis → rerun) and synced docs/fix_plan Next Actions to those steps.
- Authored new `input.md` (Mode=Parity) directing Ralph to execute Phase L1 by building `scripts/validation/compare_structure_factors.py`, regenerating a stamped `Fdump_scaled` cache, and logging HKL parity metrics under `reports/2025-10-cli-flags/phase_l/hkl_parity/`.
- Hypotheses for 1.26e5× intensity gap: (H1) HKL ingestion mismatch (PyTorch grid defaults vs C’s Fdump) — high confidence; next confirming step is L1 comparison script. (H2) Residual scaling-chain divergence post-MOSFLM fix (fluence/polar chain) — medium confidence; confirmation via Phase L2 traces after HKL parity passes.
- Vectorization goal remains untouched; plan `plans/active/vectorization.md` still at Phase A baseline because `_tricubic_interpolation` falls back to nearest-neighbor for batched tensors (see src/nanobrag_torch/models/crystal.py:272+). Keep on radar once CLI parity clears.

## 2025-11-09 (galph loop - L1b prep)
- Reproduced Phase L1 parity run with a fresh cache (`Fdump_scaled_20251006175946.bin`); mismatch persists (max |ΔF| 5.22e2, 99,209 voxels). File encodes 182,700 doubles (≈9.5k extra) and shifts reflections (Δk≈+10–12, Δl≈−2…−8), pointing to a layout/ordering discrepancy rather than corruption.
- Updated `plans/active/cli-noise-pix0/plan.md` Phase L table (L1a–L1d) to capture completed evidence and new layout-analysis + IO alignment tasks. Logged the addendum referencing the new cache.
- Synced `docs/fix_plan.md` with Phase L1b–L1d focus and recorded Attempt #51 (evidence update). Added layout-analysis to next actions block.
- Authored `input.md` directing Ralph to implement Phase L1b via a new `scripts/validation/analyze_fdump_layout.py` helper and to stash findings in `reports/2025-10-cli-flags/phase_l/hkl_parity/` before moving to L1c.
- Follow-up: Ralph to build the layout-analysis script, document axis/order findings in `layout_analysis.md`, update fix_plan attempt log, then proceed to L1c once structure-factor parity holds.

## 2025-11-09 (galph loop - L1c alignment prep)
- Re-ran repo sync (already clean); reviewed docs/index.md, specs/spec-a shards, arch.md, config map, debugging + testing strategies, fix_plan, and plans/active/.*
- Deep-dive findings vs goals:
  * CLI parity: HKL mismatch traced to nanoBragg padding `(range+2)` along each axis; PyTorch `read_fdump`/`write_fdump` still assume compact grids, so structure-factor parity blocks supervisor command. Need to drop padded planes on read and write the padded layout.
  * Normalization gap: Once HKL parity lands, revisit scaling chain — current blockers remain Phase L2+, but no new divergences found today.
  * Vectorization backlog: `plans/active/vectorization.md` still stuck in Phase A; zero artefacts under `reports/2025-10-vectorization/phase_a/`.
- Hypotheses + triage (CLI parity):
  1. H1 (high confidence): PyTorch Fdump loader ignores the padded plane nanoBragg emits, causing index shifts (Δk≈+10, Δl≈−2…−8). Next confirming step: update read/write to handle padding, then rerun structure-factor parity script. Evidence: analyze_fdump_layout.py, compare_structure_factors metrics (max |ΔF|=5.22e2).
  2. H2 (medium): Even after HKL alignment, residual F_latt differences could stem from remaining MOSFLM real-vector rescale logic—confirm once L1d passes by replaying Phase K base trace. Next step: rerun base_lattice traces post-L1d if mismatch persists.
  3. H3 (medium-low): Cache metadata might desync when multiple caches exist; ensure new regression test guards header vs tensor consistency. Quick check: include metadata assertions in L1c test.
- Coin flip: heads → Reviewed Ralph’s last loops (`85f7606`, `4e73062`). Work is on track: evidence-only commits built `compare_structure_factors.py` and `analyze_fdump_layout.py`, no regressions spotted, attempt logs thorough.
- Plan updates: Marked Phase L1b as complete in `plans/active/cli-noise-pix0/plan.md`, refreshed docs/fix_plan.md next-actions to call out padded layout fix, and emitted new input.md (Do Now = Phase L1c parity implementation + regression test).
- Follow-up for Ralph: Implement Phase L1c per new input.md — add roundtrip pytest, adjust HKL IO to mirror padded layout, regenerate parity artefacts, and update fix_plan/plan tables. Proceed to L1d once parity metrics hit ≤1e-6.

## 2025-11-09 (galph loop - L1d parity rerun prep)
- `timeout 30 git pull --rebase` clean; re-read docs/index.md, specs/spec-a-cli.md, arch.md, c_to_pytorch_config_map, debugging SOP, testing_strategy, docs/fix_plan.md, and plans/active/cli-noise-pix0.md/vectorization.md for continuity.
- Coin flip = heads: reviewed Ralph’s latest work (`4e73062`, `572217b`) — HKL layout analysis + padding fix landed with good regression coverage; no regressions spotted.
- Updated `plans/active/cli-noise-pix0/plan.md` Phase L snapshot (L1c → [D], new note on Attempt #53) and synced `docs/fix_plan.md` Next Actions to show L1c completion; left L1d as the active blocker.
- Authored new `input.md` (Mode=Parity) directing Ralph to regenerate the C Fdump cache and rerun `scripts/validation/compare_structure_factors.py` for Phase L1d, storing outputs under `reports/2025-10-cli-flags/phase_l/hkl_parity/`.
- Hypotheses refined: (1) With padding fix, expect HKL parity to hit max |ΔF| ≤ 1e-6 once rerun; (2) if Δk≈6 persists afterward, capture fresh per-phi traces (Plan K3f/K3g) to isolate reciprocal-vector drift; (3) remaining intensity gap likely tied to sincg normalization order pending new evidence.
- Follow-up for Ralph: Execute L1d per memo, update docs/fix_plan Attempts with metrics, and prep Phase L2 scaling diagnostics if parity clears.

## 2025-11-09 (galph loop - Phase L2 kickoff)
- Coin flip landed heads; reviewed recent Ralph commits (`572217b`, `3e47b38`) — HKL padding/parity artifacts look solid, no regressions observed.
- Deep-dive into CLI parity status: scaling mismatch (sum_ratio≈1.26e5) still open; plan lacked Phase L coverage beyond L1. Vectorization initiative remains untouched pending CLI closure.
- Updated `plans/active/cli-noise-pix0/plan.md` with Phases L2–L4 (scaling audit → normalization fix → supervisor rerun) including checklist tasks and artifact targets under `reports/2025-10-cli-flags/phase_l/`.
- Refreshed `docs/fix_plan.md` Next Actions to point Ralph at Phase L2a–L2c; authored new `input.md` instructing instrumentation + C trace capture for the scaling audit.
- Hypotheses (scaling divergence):
  1. Missing capture_fraction/omega application during oversample=1 path (Confidence: medium; C LOG shows capture_fraction=1 even when oversample flags off). Next confirming step: inspect TRACE_C vs TRACE_PY ordering once L2 traces exist.
  2. Misapplied steps divisor (possible double divide) leading to ×10 discrepancy that compounds with other factors (Confidence: low-medium). Next step: compare `steps` values logged in L2 traces.
  3. Fluence scaling mismatch (BeamConfig vs C computed area) causing ×~1.27e5 ratio (Confidence: medium-high, matches numeric magnitude). Next step: verify fluence logged from C vs PyTorch traces in L2a/L2b.
- Follow-up for Ralph: execute new input.md focusing on Phase L2a; once traces captured, proceed through L2b/L2c before touching implementation.

## 2025-10-06 (galph loop - Phase L2b trace directive)
- Synced cleanly; reviewed docs/index.md, specs/spec-a.md, arch.md, c_to_pytorch_config_map.md, debugging.md, testing_strategy.md, docs/fix_plan.md, and plans/active/* (CLI + vectorization) per SOP.
- Deep analysis: long-term Goal #1 still blocked in Phase L; C scaling trace captured (Attempt #55) but PyTorch trace missing. Goal #2 vectorization remains at Phase A with no artifacts.
- Hypotheses (CLI scaling mismatch):
  1. Missing capture_fraction logging/logic parity between C and PyTorch (confidence: medium; C trace shows capture=1.0, Py harness must confirm). Next step: complete L2b harness and compare capture terms.
  2. Potential omission of polarization factor in Py normalization (confidence: medium-low; previous phases reset default but need trace evidence). Next step: include polarization in Py trace and inspect delta vs C log.
  3. Residual steps normalization drift for oversample=1 (confidence: low; subpixel path divides by steps but needs confirmation). Next step: ensure steps printed from Py trace match C=10.
- Coin flip (heads): reviewed Ralph’s latest commits (`3e47b38`, `f3f116b`). Progress solid—HKL parity verified, C scaling trace captured with thorough artifacts, no regressions observed.
- Plan maintenance: Marked Phase L2a as complete in `plans/active/cli-noise-pix0/plan.md`; refreshed `docs/fix_plan.md` Next Actions to focus on L2b/L2c. input.md now directs Ralph to deliver the PyTorch scaling trace (Phase L2b).
- Follow-up for Ralph: implement Phase L2b per new memo, archive artifacts under `reports/2025-10-cli-flags/phase_l/scaling_audit/`, then proceed to L2c diff once trace captured.

## 2025-11-10 (galph loop - Phase L2b instrumentation)
- Synced cleanly; re-read docs/index.md, specs/spec-a.md shards pointer, arch.md, c_to_pytorch_config_map.md, debugging/debugging.md, docs/fix_plan.md, testing_strategy.md, and plans/active/* for continuity before analysis.
- Deep dive vs long-term Goal #1 found TRACE_PY still emits placeholder scaling data (`polar=1`, `capture_fraction=1`, `steps=phi_steps`) so Phase L2b cannot progress; identified need to thread real tensors from `_apply_polarization` and `_apply_detector_absorption` through the debug path.
- Coin flip → heads: Reviewed Ralph’s recent commits (`3e47b38`, `f3f116b`, `f466b39`); C trace capture solid, but evidence-only harness attempt stalled because instrumentation can’t expose values—no regressions spotted.
- Updated `plans/active/cli-noise-pix0/plan.md` Phase L2 context and table to require simulator instrumentation fixes, a new TRACE_PY regression test, and harness rerun sequencing; synced `docs/fix_plan.md` next actions accordingly.
- Authored new `input.md` directing Ralph to patch TRACE_PY, add `tests/test_trace_pixel.py`, rerun the scaling harness, and archive comparison artifacts under `reports/2025-10-cli-flags/phase_l/scaling_audit/`.
- Follow-up for Ralph: Execute Phase L2b per updated plan—implement real scaling trace output, add the regression test, regenerate PyTorch trace + comparison JSON, and log Attempt update before moving to L2c.

## 2025-11-10 (galph loop - L2b harness rerun directive)
- Synced clean, reviewed core docs (`docs/index.md`, specs/spec-a.md shards, arch.md, config map, debugging SOP, testing strategy), CLI plan, and fix_plan entries before analysis per SOP.
- Confirmed Ralph’s latest work: commit 6b055dc replaced TRACE_PY placeholders with real tensors and added `tests/test_trace_pixel.py`; fix_plan Attempt #57 documents the change. Harness artifacts still missing (`trace_py_scaling.log` absent) because the prior run failed (`trace_py_fullrun.log` shows ValueError unpacking `read_hkl_file`).
- Evidence review: C scaling trace (`reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log:260-300`) reports `k_frac≈-0.607` and `F_latt≈-2.38`, while the latest PyTorch trace (`reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_after_133134.log:46-65`) still shows `hkl_frac≈(2,2,-13)` and `F_latt≈4.47e4`. Polarization also stays at 1.0 vs C’s 0.9146. Scaling gap therefore persists upstream of normalization.
- Hypotheses logged: (1) fractional Miller index mismatch leading to runaway `F_latt`; (2) polarization factor still diverges despite new instrumentation. Both require a fresh PyTorch scaling trace to quantify.
- Rewrote `input.md` directing Ralph to rerun `trace_harness.py` with the supervisor command (slow=685, fast=1039), capture stdout/stderr, parse key factors into `scaling_audit_summary.md`, and keep `pytest --collect-only` in evidence mode; set “Mapped tests: none — evidence-only”.
- Next steps for Ralph: execute Phase L2b Step 3 (harness rerun), document deltas in notes/summary JSON, then move to Phase L2c comparison once numbers land. No new planning artifacts created; existing plan remains authoritative.
## 2025-11-11 (galph loop - Phase L2b0 harness reminder)
- Added new gap snapshot in plans/active/cli-noise-pix0/plan.md noting prior Py trace omitted -beam_vector/-oversample/-flux/-beamsize, which forced auto oversample=4 and +Z beam.
- Updated Phase L2b guidance to require rerunning trace_harness.py with the authoritative supervisor command before analysing scaling factors; docs/fix_plan.md now lists Phase L2b0 as step 1.
- Issued input.md loop instructions directing Ralph to regenerate trace_py_scaling.log via `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --out reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log --device cpu --dtype float32` and capture fresh notes.
- Expect Ralph to refresh trace_py_env.json/notes.md, then proceed to instrumentation regression test (tests/test_trace_pixel.py) once Phase L2b0 evidence lands.

## 2025-10-06 (galph loop - Phase L2b instrumentation prep)
- Synced clean; coin flip tails so no commit review.
- Confirmed Attempt #66 harness rerun now passes full supervisor flags: `trace_py_scaling.log` reports steps=10, fluence≈1e24, yet `I_before_scaling` remains absent and polar=0, so intensity still zero.
- Updated `plans/active/cli-noise-pix0/plan.md` gap snapshot + L2b row to mark L2b0 complete and emphasize instrumentation work; refreshed `docs/fix_plan.md` next actions (2025-11-12 refresh).
- Authored new `input.md` directing Ralph to thread real scaling tensors through TRACE_PY, add regression test, rerun harness, and diff against C trace.
- Focus next loop: complete Phase L2b instrumentation, record comparison metrics, then proceed to L2c.

## 2025-10-06 (galph loop - Phase L2b harness focus)
- Sync clean (git pull --rebase no-op). Reviewed docs/index.md, specs/spec-a.md shards pointer, arch.md, config map, debugging SOP, testing strategy, docs/fix_plan.md, and plans/active/* per SOP.
- Long-term Goal #1 status: CLI-FLAGS-003 remains blocked at Phase L2b because `reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py` still fabricates TRACE_PY lines (`I_before_scaling NOT_EXTRACTED`, `polar 0`, `I_pixel_final 0`). Simulator instrumentation already emits real values (see `tests/test_trace_pixel.py`), so harness must capture stdout instead of synthesizing constants.
- Hypothesis summary: (1) Harness bypass writes placeholders → confirmed by lines 263-283 in trace_harness.py; (2) Missing stdout capture leaves trace_py_stdout.txt empty, so scaling_audit_summary.md lacks real numbers. Next step is to pipe the actual TRACE_PY output into trace_py_scaling.log before comparing to C.
- Long-term Goal #2 check: `plans/active/vectorization.md` is still valid; Phase A evidence artifacts remain absent, so no plan rewrite yet. Ensure Ralph captures tricubic/absorption baselines before implementation when that goal activates.
- No new plan drafted; existing CLI plan already captures Phase L2b work. Updated input.md directing Ralph to fix the harness (collect live TRACE_PY output) and rerun targeted regression test.
- Follow-up for Ralph: execute revised input.md — update trace_harness.py to record real simulator output, refresh `trace_py_scaling.log`, update scaling_audit_summary.md with live values, then proceed to Phase L2c comparison once numbers land.

## 2025-11-12 (galph loop - L2b harness refresh directive)
- Sync clean; reviewed docs/index.md, specs/spec-a.md shard pointers, arch.md, config map, debugging SOP, testing_strategy.md, docs/fix_plan.md, and plans/active/* before analysis.
- Deep analysis: CLI-FLAGS-003 still blocked because `reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py` fabricates TRACE_PY entries (see lines 252-281). Latest PyTorch trace with live instrumentation (`reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_after_133134.log`) shows `hkl_frac≈(2,2,-12.99)` and `polar=1.0`, diverging sharply from C trace (`c_trace_scaling.log:265-287` reports `hkl_frac≈(-6.88,-0.607,-13.77)` and `polar=0.9146`). Need authentic TRACE_PY output before tackling normalization.
- Hypotheses triage captured in supervisor summary; top issue remains reciprocal lattice mismatch (likely k-component) pending fresh harness data.
- Coin flip → heads; reviewed Ralph’s recent commits (`f130d19`, `1d2e6ac`, `bcd08b8`). Instrumentation patch clean (no regressions); harness fix partial (still placeholders); comparison tooling solid but awaits real data. No regressions spotted.
- Updated `plans/active/cli-noise-pix0/plan.md` L2b/L2c rows to mark simulator instrumentation/regression complete and call out the remaining harness rerun requirement. Refreshed `docs/fix_plan.md` next actions to center on harness refresh → comparison rerun → L3 prep.
- Authored new `input.md` instructing Ralph to stream live TRACE_PY output via `debug_config={'trace_pixel': [685,1039]}`, rerun the harness, and validate with the targeted trace test before proceeding to comparison.
- Follow-up for Ralph: execute L2b Step 3 (harness refresh + rerun), archive updated logs/env snapshots under `reports/2025-10-cli-flags/phase_l/scaling_audit/`, run the trace regression selector, update Attempts History, then rerun `compare_scaling_traces.py` once real data exists.

## 2025-11-13 (galph loop - CLI harness regression triage)
- Synced clean; traced Phase L2b blockage to `trace_harness.py` still unpacking legacy `read_hkl_file` outputs. Logged the regression as Attempt #70 in docs/fix_plan.md:458-484 and updated the plan gap snapshot / L2b guidance (`plans/active/cli-noise-pix0/plan.md:13-18`, `:239-242`).
- Authored new input.md (100 lines) directing Ralph to adapt the harness to the `(F_grid, metadata)` API, rerun the supervisor command capture, and archive refreshed TRACE_PY artifacts before Phase L2c resumes.
- Focus next loop: confirm harness patch lands, collect live trace data, then execute compare_scaling_traces.py to re-enter normalization analysis.

## 2025-11-14 (galph loop - Phase L2b orientation fix)
- Verified repo up to date; reviewed core docs plus CLI plan & latest scaling artifacts.
- Diagnosed F_cell=0 in trace harness: `trace_harness.py` feeds all MOSFLM vectors into `mosflm_a_star` and leaves the other slots `None`, so Crystal falls back to default orientation during Phase L2b.
- Updated `plans/active/cli-noise-pix0/plan.md` L2b guidance and `docs/fix_plan.md` Next Actions / Attempt notes to call out the MOSFLM injection bug as the gating fix.
- Rewrote `input.md` directing Ralph to patch the harness, rerun the supervisor trace command, refresh artifacts, then proceed to L2c comparison.
- Follow-up for Ralph: apply the harness fix (`mosflm_a_star/b_star/c_star` assignments), rerun trace harness with supervisor flags, archive refreshed `trace_py_scaling.log`, execute `compare_scaling_traces.py`, and log the new Attempt entry before tackling normalization.

## 2025-11-14 (galph loop - L2b HKL wiring)
- `git pull --rebase` clean; reviewed core docs plus CLI plan and fix_plan before analysis.
- Evidence run (`reports/.../harness_hkl_state.txt`) shows `trace_harness.py` never assigns `Crystal.hkl_data`/`hkl_metadata`, leaving structure factors at default_F=0 and keeping F_cell=0 in TRACE_PY.
- Updated docs/fix_plan.md (Attempt #73) and plans/active/cli-noise-pix0/plan.md L2b guidance to call out the missing HKL attachment; next action is to set `crystal.hkl_data = F_grid` and `crystal.hkl_metadata = metadata` before simulator construction.
- Authored new input.md instructing Ralph to wire HKL metadata into the harness, rerun the supervisor trace command, refresh scaling_audit_summary.md, and validate via targeted pytest collection + compare_scaling_traces.
- Follow-up for Ralph: patch harness HKL assignment, rerun L2b command, update artifacts (trace_py_scaling.log, notes.md, harness_hkl_state.txt), then rerun the comparison tool to re-enter Phase L2c.
## 2025-10-06 (galph loop - CLI-FLAGS structure-factor probe)
- Marked Phase L2 as complete in plans/active/cli-noise-pix0/plan.md and refreshed Phase L3 task list (L3a/L3b now target supervisor pixel F_cell evidence).
- Updated docs/fix_plan.md Next Actions to focus on structure-factor ingestion; clarified divergence as F_cell=0 vs 190.27 at hkl≈(-7,-1,-14).
- Authored new input.md (L3a instructions) directing Ralph to build a probe under reports/.../structure_factor and log HKL vs Fdump amplitudes.
- Noted Fdump snapshots currently in repo do not cover (-7,-1,-14); follow-up question recorded for L3b to locate/replicate C’s data source.
- Follow-up for Ralph: implement the probe per input.md, store outputs in reports/2025-10-cli-flags/phase_l/structure_factor/, and feed findings into L3b planning.


## 2025-11-15 (galph loop - Phase L3 structure-factor sourcing)
- Confirmed repo-local `scaled.hkl` is a 13-byte stub containing only `(1,12,3)`; golden_suite_generator/Fdump.bin and tmp/Fdump.bin are tiny (≤2×2×2 grids) and cannot supply F_cell for (-7,-1,-14).
- Loaded `reports/2025-10-cli-flags/phase_l/hkl_parity/Fdump_scaled_20251006175946.bin` via `read_fdump`; grid spans h∈[-24,24], k∈[-28,28], l∈[-31,30] and returns `F_cell=190.27` for the supervisor pixel. This confirms sourcing the C-generated Fdump reproduces the trace amplitude.
- Implication: Phase L3 must treat the archived Fdump as the authoritative dataset (or regenerate an equivalent cache) before normalization work; running the CLI with the stub HKL will overwrite the cache with zeros.
- Next supervisor handoff: instruct Ralph to rerun `reports/.../structure_factor/probe.py` including `--fdump reports/2025-10-cli-flags/phase_l/hkl_parity/Fdump_scaled_20251006175946.bin`, capture the refreshed probe.log/analysis.md, and decide whether to stage that Fdump alongside the supervisor command or regenerate it from the original HKL source.

## 2025-11-16 (galph loop - VECTOR-TRICUBIC-001 kickoff)
- Refreshed `plans/active/vectorization.md` Context/Phase A guidance to flag the Phase A evidence push (collect-only log, env snapshot) and reinforced harness locations under `scripts/benchmarks/`.
- Updated `docs/fix_plan.md` next-actions list for VECTOR-TRICUBIC-001 with the env.json + collect-only requirements so the fix-plan matches the plan.
- Authored input.md handing Ralph Phase A1–A3 tasks (capture tricubic/absorption baselines, build benchmark harnesses, persist logs in `reports/2025-10-vectorization/phase_a/`).
- Follow-up for Ralph: execute the outlined commands, write harness stubs, drop Attempt #1 evidence into fix_plan once artifacts exist, then proceed to Phase B design when Phase A closes.

## 2025-11-17 (galph loop - Phase A2/A3 planning refresh)
- `git pull --rebase` clean; reviewed core docs plus vectorization plan/fix_plan entries before analysis.
- Coin flip = heads → reviewed Ralph’s recent commits (142230b, 6e12854). Evidence collection and baseline logs look solid; no regressions spotted. Noted that tests/test_at_str_002.py and absorption logs already captured in reports/2025-10-vectorization/phase_a/.
- Updated plans/active/vectorization.md gap snapshot and Phase A table to mark A1 complete and highlight missing A2/A3 harnesses.
- Refreshed docs/fix_plan.md VECTOR-TRICUBIC-001 status to `in_progress`, tightened next actions to focus on creating tricubic/absorption baseline scripts.
- Authored expanded input.md (Perf mode) directing Ralph to implement Phase A2/A3 benchmark harnesses, capture timing artifacts (JSON/Markdown/run_log/env.json), and log metrics in fix_plan.
- No code changes; focus next loop: ensure harness scripts and reports land, then proceed to Phase B design memo.

## 2025-11-17 (galph loop - CLI-FLAGS L3 readiness)
- Sync clean; revisited docs/index.md, spec shards, arch.md, config map, debugging SOP, testing strategy, fix_plan, and active plans.
- Noted inconsistency: `structure_factor/probe.log` shows scaled.hkl spans [-24,24]×[-28,28]×[-31,30] with F_cell=190.27, but `scaling_audit/config_snapshot.json` still reports h/k/l ranges (1,12,3) and TRACE_PY keeps F_cell=0.
- Updated docs/fix_plan.md: CLI-FLAGS-003 Next Actions now start with a fresh Phase L3a probe rerun plus harness/CLI audits; VECTOR-TRICUBIC-001 Next Actions point to Phase B design tasks (B1–B3).
- No new evidence generated; left instructions for Ralph to recapture HKL coverage on the current machine, reconcile harness metadata, then proceed with Phase L3 scaling fixes once F_cell matches C.
## 2025-11-17 (galph loop - L3 harness alignment)
- `git pull --rebase` clean; reviewed docs/index.md, specs/spec-a.md shards, arch.md, config map, debugging SOP, testing strategy, fix_plan, and active plans before selecting focus.
- Focused on CLI-FLAGS-003 after Attempt #77; updated `plans/active/cli-noise-pix0/plan.md` (added 2025-11-17 gap snapshot, marked L3a [D], clarified evidence expectations) and refreshed `docs/fix_plan.md` next-actions list to center L3c harness/CLI audits and L3e validation script.
- Authored new `input.md` (Parity mode) directing Ralph to rerun the scaling trace harness with scaled.hkl attached, capture HKL metadata in `harness_hkl_state_20251117.txt`, promote new trace/env snapshots, and update `analysis.md` before touching simulator code.
- Key follow-up for Ralph: execute the harness audit command, preserve timestamped artifacts, summarise findings in analysis.md, and log outcomes in fix_plan prior to proceeding to the CLI ingestion audit (L3c) next loop.

## 2025-11-17 (galph loop - CLI-FLAGS L3c update)
- `git pull --rebase` clean; reviewed specs/spec-a-cli.md, docs/architecture/detector.md, config map, testing strategy, plan/fix_plan entries, and latest Phase L artifacts before selecting focus.
- Marked Plan L3b complete and redirected L3c toward auditing `__main__.py` HKL ingestion; added new gap snapshot note about Attempt #78 harness parity.
- Updated docs/fix_plan.md Next Actions + Attempt #78 to reflect harness success and to queue the CLI ingestion audit, regression coverage, validation script, and parity rerun.
- Authored input.md (Parity mode) directing Ralph to run the CLI audit script and capture findings under `reports/2025-10-cli-flags/phase_l/structure_factor/` before touching simulator code.
- Follow-up: expect CLI ingestion audit results + `cli_hkl_audit.md` artifacts next loop, then proceed to regression tests (L3d).
- Logged new fix_plan items ABS-OVERSAMPLE-001 and SOURCE-WEIGHT-001 with dedicated plans (`plans/active/oversample-thick-subpixel.md`, `plans/active/source-weight-normalization.md`) to track oversample_thick bug and source-weight normalization bug.

## 2025-11-17 (galph loop - CLI L3c device probe)
- Re-audited CLI HKL attachment after harness fixes; updated `reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_audit.md` with fc600db findings showing dtype+metadata are wired but tensors never move to `-device cuda`.
- Added note in `docs/fix_plan.md` (CLI-FLAGS-003 Next Actions) flagging the device gap so L3c implementation covers it.
- Authored new `input.md` (Parity mode) instructing Ralph to capture `cli_hkl_device_probe.json`, record env metadata, update the audit doc, and log Attempt #79 before any simulator edits.
- Open questions: confirm whether CUDA probe reproduces the device mismatch on the local machine; plan to queue CLI-side fix once evidence is captured.

## 2025-11-18 (galph loop - VECTOR-TRICUBIC Phase B prep)
- `git pull --rebase` already up to date; no conflicts.
- Updated `plans/active/vectorization.md` gap snapshot + supervisory note to reflect Phase A completion and highlight Phase B design memo as the new blocker.
- Synced `docs/fix_plan.md` status/index for VECTOR-TRICUBIC-001 (Phase A complete, Phase B outstanding) and refreshed Next Actions to call for the Phase B design memo.
- Authored new `input.md` (Docs mode) directing Ralph to draft `reports/2025-10-vectorization/phase_b/design_notes.md` covering tasks B1–B3, including tensor shapes, polin3 tensorization, and gradient/device checklist.
- Follow-up for Ralph: produce the memo, cite baseline artifacts, outline regression/benchmark plan, and log the attempt in fix_plan before attempting any implementation work.
## 2025-11-18 (galph loop - VECTOR-TRICUBIC Phase C kick-off)
- Synced clean; reviewed latest plan/docs plus Ralph’s recent commits (`d30a581`, `30ab2d1`). Design memo now exists and captures B1–B3; CLI device audit revealed HKL tensors stuck on CPU but no regressions observed.
- Updated `plans/active/vectorization.md` context + Phase B table to mark B1–B3 complete, steering focus to Phase C implementation (C1–C3). Refreshed `docs/fix_plan.md` next-actions accordingly.
- Authored new `input.md` (Perf mode) directing Ralph to implement Phase C1 batched tricubic gather with a fresh targeted pytest and to log implementation notes under phase_c/.
- Expect Ralph next loop to land the gather vectorization, add the new test, and document deltas before moving to Phase C2 fallback validation. CLI-FLAGS-003 remains pending after gather work.
## 2025-11-18 (galph loop - CLI-FLAGS L3c audit prep)
- Chose Evidence focus on CLI-FLAGS-003 Phase L3c to unblock the supervisor-command parity goal.
- Reviewed src/nanobrag_torch/__main__.py:438-450 and 1068-1076; confirmed CLI still attaches HKL data after Crystal construction but leaves tensors on CPU and instantiates Crystal without propagating the CLI device/dtype.
- Noted interpolation flag wiring mismatch (cli writes `crystal.interpolation_enabled`) for follow-up once L3c closes.
- Replaced input.md with Parity-mode guidance directing Ralph to refresh the CLI HKL device probe, update cli_hkl_audit.md with current code references, and run pytest --collect-only for tests/test_cli_scaling.py.
- Expect Ralph to capture new probe artifacts under reports/2025-10-cli-flags/phase_l/structure_factor/, update the audit doc with 2025-11-18 findings, and log the attempt in docs/fix_plan.md before proceeding to L3d.

## 2025-11-18 (galph loop - CLI L3d planning refresh)
- Marked Phase L3c complete in `plans/active/cli-noise-pix0/plan.md` and added 2025-11-18 gap snapshot noting Attempt #80’s audit results; fix_plan Next Actions now target L3d implementation, L3e validation, and L3f documentation.
- Authored new `input.md` (Parity mode) instructing Ralph to add the L3d regression test, capture the failing selector, patch `__main__.py:1073` with `.to(device=device, dtype=dtype)`, rerun the probe, and log artifacts under `reports/2025-10-cli-flags/phase_l/structure_factor/`.
- Reminder for next loop: verify vectorization plan still shows C1 as open despite commit 88fd76a; plan update pending once CLI L3d work is underway.

## 2025-11-19 (galph loop - CLI L3e evidence setup)
- Verified L3d landed earlier (TestHKLDevice present, `.to(device=device, dtype=dtype)` already in `__main__.py`), so refreshed plan snapshot to steer toward Phase L3e scaling validation.
- Updated `plans/active/cli-noise-pix0/plan.md` (L3d → [D]) and `docs/fix_plan.md` Next Actions to focus on L3e metrics, L3f documentation, and L4 rerun.
- Authored Parity-mode `input.md` directing Ralph to upgrade `scripts/validation/compare_scaling_traces.py` to emit ≤1e-6 JSON metrics + metadata under `reports/2025-10-cli-flags/phase_l/scaling_validation/` before any simulator edits.
- Follow-up: expect new `metrics.json`, `run_metadata.json`, and summary markdown plus fix_plan attempt update next loop; if metrics fail tolerance, halt for supervisor review.

## 2025-11-19 (galph loop - CLI-FLAGS L3e parity snapshot)
- Ran `compare_scaling_traces.py` against `trace_py_scaling_20251117.log`; generated `scaling_validation_summary_20251119.md`, refreshed metrics/run_metadata, and logged Attempt #83 under CLI-FLAGS-003.
- Key finding: HKL ingestion now matches C (F_cell≈190.27) but lattice factor remains divergent (C `F_latt=-2.3832` vs Py `+1.35136`). Per-phi `TRACE_C_PHI` entries show the sign oscillation missing from PyTorch traces.
- Authored `analysis_20251119.md` recommending per-phi instrumentation; updated input.md to direct Ralph to extend the trace harness, emit `TRACE_PY_PHI`, and compare against archived C per-phi logs before touching simulator code.
- Expect Ralph to capture new per-phi PyTorch trace/JSON under `reports/2025-10-cli-flags/phase_l/per_phi/`, run the targeted pytest selector for scaling traces, and append findings to docs/fix_plan.md Attempt history.

## 2025-11-19 (galph loop - CLI L3e per-phi refresh setup)
- Confirmed `git pull --rebase` succeeded without conflicts.
- Reviewed Phase L3 evidence: `analysis_20251119.md` still shows F_cell parity yet `trace_py_scaling_per_phi.log` lacks any `TRACE_PY_PHI`, indicating the harness output is stale.
- Updated `docs/fix_plan.md` next actions to call for a 2025-11-19 per-phi trace rerun and noted the empty log under Attempt #83 observations.
- Refreshed `plans/active/cli-noise-pix0/plan.md` gap snapshot and revised the L3e task description to emphasise regenerating per-phi artifacts before scaling validation can pass.
- Authored new `input.md` (Parity mode) instructing Ralph to rerun `trace_harness.py` with `--out trace_py_scaling_20251119.log`, regenerate per-phi comparison data, rerun `compare_scaling_traces.py`, and capture the targeted pytest output.
- Follow-up: expect refreshed logs/JSON under `reports/2025-10-cli-flags/phase_l/per_phi/`, updated scaling_validation metrics, and a docs/fix_plan.md attempt summarising whether the Δk≈6 offset persists.
## 2025-11-19 (galph loop - CLI rotation audit setup)
- Updated CLI-FLAGS-003 next actions + plan Phase L3 to reflect Attempt #86 per-phi evidence and new phi=0 rotation mismatch; L3e marked done, new tasks L3f (rot-vector comparison) and L3g (hypothesis framing) added.
- Input.md now directs Ralph to capture rotation vectors via trace_harness, build `rot_vector_comparison.md`, and log hypotheses before touching simulator code.
- Key observation logged: PyTorch rot_b at phi=0 uses k_frac ≈ -0.589 vs C -0.607, flipping F_latt_b sign; rotation-vector audit required before normalization changes.


## 2025-11-19 (galph loop - CLI L3g invariants setup)
- Refreshed input.md (Parity) to drive Phase L3g evidence: rerun φ=0 harness, generate `rot_vector/invariant_probe.md`, and capture pytest collect.
- Parsed new rot_vector artifacts: real-space vectors drift O(1e-2 Å) while reciprocal vectors align ≈1e-9 Å⁻¹; computed volumes (C 24682.25663 Å³ vs Py 24682.25998 Å³) and dot products (C deviates ≤4.4e-4, Py ≈1.0) to focus on reciprocal→real reconstruction.
- Directed Ralph to update `analysis.md` plus fix_plan Attempt #88 with invariant metrics and to keep snippets under reports/rot_vector/ before any simulator edits.
- Next follow-up: after invariants are logged, decide whether Crystal.get_real_from_reciprocal needs instrumentation or spindle-axis normalization fixes before code changes.

## 2025-11-20 (galph loop - Vectorization Phase C kickoff)
- `git pull --rebase` clean; no new conflicts encountered.
- Reviewed long-term goals: CLI parity remains in Phase L3f (rotation vectors outstanding), while vectorization backlog stalled at Phase C. Determined VECTOR-TRICUBIC-001 needs refreshed guidance before Ralph can implement C1.
- Updated `plans/active/vectorization.md` (lines 1-120) with 2025-11-20 gap snapshot plus explicit artifact paths and pytest/benchmark commands for Phase C1–C3. Mirrored instructions in `docs/fix_plan.md:1796-1810` so Next Actions now reference gather_notes.md, diff_snapshot.json, and new test selectors.
- Authored `input.md` (Perf mode, 101 lines) directing Ralph to tackle Phase C1: collect-only run, implement batched `(S,F,4,4,4)` gather, capture diff/runtime artifacts, rerun targeted tricubic tests (including fallback + gradient smoke), and log results under `reports/2025-10-vectorization/phase_c/` before staging.
- Follow-up expectations: Ralph executes Do Now, populates gather_notes + Attempt entry, and leaves polynomial work for later phases. Next supervisor loop should verify new artifacts, ensure docs/fix_plan Attempt logged, and then pivot to CLI L3f or Phase C2 depending on progress.

## 2025-11-20 (galph loop - CLI L3g spindle audit prep)
- Reviewed CLI-FLAGS-003 status: Phase L3f/L3g remain open despite prior rot_vector artifacts; residual k_frac drift traced to Y-component deltas and potential spindle/volume mismatch.
- Captured current artifacts (rot_vector_comparison.md, invariant_probe.md) and confirmed trace_harness.py emits full TRACE_PY data; next evidence must log spindle-axis norm + V_formula/V_actual for PyTorch vs C.
- Authored input.md (Parity mode) directing Ralph to refresh the trace, build spindle_probe + volume_probe outputs under reports/2025-10-cli-flags/phase_l/rot_vector/, rerun collect-only pytest, and update docs/fix_plan.md Attempt with quantified deltas.
- No plan rewrites needed yet; expect Ralph to append new evidence then adjust plan L3 items if hypotheses shift.

## 2025-11-20 (galph loop - CLI spindle instrumentation setup)
- Recorded new context line in `plans/active/cli-noise-pix0/plan.md` for Attempt #89 (spindle + volume probe). Marked L3f ✅, kept L3g `[P]` with explicit instruction to surface `TRACE_PY: spindle_axis` before simulator edits; L3h now depends on that evidence.
- Updated `docs/fix_plan.md` Next Actions (CLI-FLAGS-003) to focus on spindle-axis instrumentation → doc/plan sync → eventual nb-compare rerun. input.md refreshed accordingly.
- Expect Ralph to extend `trace_harness.py` (or TRACE_PY hooks) with raw/normalized spindle logging, rerun the φ=0 trace, append results to `spindle_audit.log`, and update fix_plan/plan entries before shifting to implementation.
## 2025-11-20 (galph loop - CLI-FLAGS MOSFLM probe setup)
- Updated `plans/active/cli-noise-pix0/plan.md` Phase L3 with new tasks L3h–L3j covering MOSFLM matrix probe, corrective memo, and implementation checklist; prior L3a–L3g remain [D].
- Adjusted `docs/fix_plan.md` Next Actions for CLI-FLAGS-003 to align with the new Phase L3h–L3j workflow (probe → memo → checklist).
- Authored `input.md` (Parity mode, 100 lines) directing Ralph to capture `mosflm_matrix_probe.log/md`, log env metadata, and prepare outlines for `mosflm_matrix_correction.md` + `fix_checklist.md` before any code edits.
- Expectation for Ralph: run the harness with MOSFLM vector dumps, document the deltas, update fix_plan Attempt history, and leave code untouched until the memo/checklist exist.
- No production code changes made; commit 3232549 contains plan/fix_plan/input refresh (tests: not run).
## 2025-11-20 (galph loop - CLI L3i corrective memo)
- Authored `reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_correction.md` summarizing nanoBragg.c vs PyTorch MOSFLM pipeline; plan L3i marked [D] with instrumentation marching orders.
- Updated `docs/fix_plan.md` Next Actions to focus on C TRACE_C taps, Py harness dumps, and diff memo before implementation; input.md now directs Ralph to capture those traces and document deltas.
- Expect Ralph to instrument `golden_suite_generator/nanoBragg.c`, run the supervisor command to generate `c_trace_mosflm.log`, extend the Py harness for raw/tensor dumps, and produce `mosflm_matrix_diff.md` prior to touching simulator code.

## 2025-11-20 (galph loop - CLI L3j checklist alignment)
- Extended `plans/active/cli-noise-pix0/plan.md` Phase L3 with sub-tasks L3j.1–L3j.3 (memo refresh, fix checklist, plan/fix_plan sync) so implementation has explicit gates.
- Updated `docs/fix_plan.md` Next Actions to point at the new L3j workflow; removed stale L3i instrumentation steps.
- Authored `input.md` (Parity mode, 100 lines) instructing Ralph to update mosflm_matrix_correction.md, draft `fix_checklist.md`, run pytest --collect-only, and log artifacts under rot_vector/ before touching code.
- No production code changes performed; expect Ralph’s Attempt #94 to document memo/checklist completion plus collect-only log before proceeding to φ-rotation implementation.

## 2025-11-21 (galph loop - VECTOR-TRICUBIC-001 Phase C2 prep)
- Updated `plans/active/vectorization.md:5-36` to record Phase C1 completion and spotlight C2/C3 as the remaining blockers before polynomial work.
- Refreshed `docs/fix_plan.md:1889-1892` Next Actions so they now call out C2, C3, and the Phase C close-out handoff instead of repeating the already-finished gather task.
- Replaced `input.md` with a Docs-mode memo steering Ralph toward authoring `tests/test_tricubic_vectorized.py::test_oob_warning_single_fire`, logging the targeted pytest run, and parking artifacts under `reports/2025-10-vectorization/phase_c/`.
- No production code changes; edits limited to planning docs and supervisor memo. Expect Ralph to execute Phase C2 next and log a new Attempt entry once the regression test and warning evidence land.

## 2025-11-21 (galph loop - CLI L3k implementation prep)
- Added Phase L3k to `plans/active/cli-noise-pix0/plan.md` with tasks for memo, code fix, gate execution, and logging prior to Phase L4.
- Updated `docs/fix_plan.md:450-463` (Attempt #95) so Next Actions now target L3k.1–L3k.4 and the new checklist-driven workflow.
- Replaced `input.md` (Docs mode, 100 lines) to steer Ralph toward executing Phase L3k, running pytest/nb-compare with the canonical command, and documenting VG-1⇢VG-5 artifacts.
- Expect Ralph to draft the implementation memo, add the docstring reference, implement the φ rotation patch, drive `fix_checklist.md` to ✅, and log Attempt #96 before attempting Phase L4 parity.
## 2025-11-21 (galph loop - CLI-FLAGS L3k triage)
- Reviewed Phase L3k memo + recent traces; PyTorch still rotates reciprocal vectors during φ, yielding k_frac drift (≈−0.59 vs C −0.607) and F_latt sign flip (+1.35 vs −2.38) in `trace_py_scaling_20251117.log`. Root cause remains mismatched φ rotation pipeline.
- Identified secondary nuisance: per-φ harness already built; thresholds summarized (k_frac Δ≤1e-6, F_latt sign match, b_Y Δ≤1e-6) for VG-1; instrumentation command retained.
- Selected Debug/Parity focus on CLI-FLAGS-003; next confirm step is to implement Phase L3k reciprocal recompute, then re-run per-φ traces, targeted pytest lattice selector, and ROI nb-compare per checklist.
- Authored `input.md` (Parity) directing Ralph to add the nanoBragg.c docstring, rotate only real vectors, recompute reciprocals, run harness + pytest + nb-compare, update fix_checklist + fix_plan, and archive old traces. Artifacts to land under `reports/2025-10-cli-flags/phase_l/rot_vector/` subfolders.
- No new plans required; vectorization plan already current (Phase C2/C3). Await Phase L3k evidence before scheduling Phase L4 rerun.
## 2025-11-21 (galph loop - CLI-FLAGS Next Actions refresh)
- Validated Phase L3k memo + plan remain authoritative; noted docs/fix_plan.md still referenced L3k.1 even though memo is complete.
- Updated `docs/fix_plan.md:458-460` so Next Actions now point at L3k.2 implementation, L3k.3 verification, and L3k.4 logging; no other ledger edits.
- Rewrote `input.md` (Parity mode) to focus Ralph on executing L3k.2 with the targeted pytest selector and checklist-driven nb-compare/trace steps; artifacts to stay under `reports/2025-10-cli-flags/phase_l/`.
- Expect Ralph to deliver the φ-rotation patch next loop, follow fix_checklist VG-1..VG-5, and record a new Attempt before we reopen Phase L4 parity testing.
## 2025-11-21 (galph loop - L3k.3 evidence prep)
- Refreshed CLI-FLAGS-003 Next Actions (docs/fix_plan.md:458) to focus on completing VG-1/VG-3/VG-4 and the VG-5 doc updates before logging L3k.4.
- Marked VG-2 ✅ in rot_vector/fix_checklist.md and updated status block with 2025-11-21 timestamp; remaining gates explicit for Ralph.
- Rewrote input.md (Parity mode) steering Ralph through per-φ harness capture, compare_per_phi_traces.py, nb-compare metrics, checksum/env snapshots, and documentation updates.
- Expect Ralph to generate new per_phi_postfix/ artefacts, flip VG-1⇢VG-5, append Attempt entry, then proceed to Phase L4 rerun next loop.
## 2025-11-21 (galph loop - L3k φ=0 parity evidence request)
- Re-read Phase L3k evidence: Py per-φ traces still show `rot_b_y` ≈ 0.7173 and `k_frac` ≈ −0.589 at φ=0 (reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling_20251119.log:15-20) vs C’s 0.671588/−0.607256 (c_trace_scaling.log:266-277). Root cause for VG-1 failure is upstream of φ rotation, likely the real-vector reconstruction.
- Noted nb-compare summary (reports/2025-10-cli-flags/phase_l/nb_compare_phi_fix/summary.json) still reports sum_ratio ≈ 1.16e5, so we cannot trust intensity metrics until φ=0 parity is fixed.
- Authored new input.md directing Ralph to capture a failing pytest (`TestPhiZeroParity::test_rot_b_matches_c`) plus fresh Py/C traces under reports/.../base_vector_debug/ before touching simulator code.
- No repo hygiene performed; tree contains only input.md modifications staged later.
## 2025-11-21 (galph loop - CLI axis triage)
- Investigated Phase L3k VG-1 failure: PyTorch `rot_b` at φ=0 equals 0.7173 Å, but C trace plateau lists 0.6716 Å. Confirmed via `Crystal.get_rotated_real_vectors` that φ=9 (0.09°) reproduces the 0.6716 Å value, implying the current pytest harness is misaligned with the supervisor spindle axis / φ indexing.
- Found `tests/test_cli_scaling_phi0.py:87` still initializes `spindle_axis=[0.0, 1.0, 0.0]`, diverging from the supervisor command (`-spindle_axis -1 0 0`). Logged this mismatch as the leading hypothesis for VG-1 drift.
- Refreshed `input.md` (Parity mode) directing Ralph to realign the φ=0 test with spindle_axis = (-1,0,0), rerun the targeted pytest selector, and capture new per-φ artifacts under `reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/` before touching nb-compare again.

## 2025-11-21 (galph loop - Vectorization Phase C3 prep)
- Reviewed `plans/active/vectorization.md` and `reports/2025-10-vectorization/phase_c/` artifacts; confirmed C1/C2 are complete and only C3 remains before polynomial work.
- Updated plan snapshot and added a Phase C3 verification checklist (assertions, cache audit, targeted pytest logs) so evidence expectations are explicit.
- Synced `docs/fix_plan.md` Next Actions with the new checklist, dropping the stale C2 reminder and focusing on C3 deliverables + Attempt logging.
- Rewrote `input.md` (Perf mode) steering Ralph to implement the C3 updates, run the two targeted selectors, update implementation notes, and flip checklist items before moving to Phase D.
- Expect Ralph to land Phase C3 code/tests, capture logs under `reports/2025-10-vectorization/phase_c/`, and append a new Attempt entry prior to starting D1 polynomial vectorization.
## 2025-11-22 (galph loop - L3k.3b φ drift diagnosis)
- Confirmed repo synced; reviewed docs/index, spec shards, arch.md, c_to_pytorch_config_map.md, debugging guide, testing strategy, fix_plan, and plan CLI notes.
- Refreshed `plans/active/cli-noise-pix0/plan.md` Gap snapshot to capture Attempt #99 VG failures and Attempt #100 spindle-axis alignment; added an L3k.3 recovery checklist (tasks L3k.3a–L3k.3e) spelling out φ-trace regeneration, ROI fix, and documentation gates.
- Updated `docs/fix_plan.md` Next Actions to target L3k.3b diagnosis, L3k.3d ROI repair, and the L3k.3e→L3k.4 documentation/logging handoff.
- Authored new `input.md` (Parity mode) directing Ralph to regenerate per-φ traces via `trace_harness.py`, move the per_phi outputs into `base_vector_debug/20251122/`, run `compare_per_phi_traces.py`, log findings in diagnosis.md, update fix_checklist VG-1.4, and capture pytest collect-only evidence.
- Follow-up for Ralph: execute L3k.3b per instructions, store artifacts under the 20251122 subdir, update `fix_checklist.md` + diagnosis memo, and keep tests red until physics fix lands.
## 2025-11-22 (galph loop - L3k.3b instrumentation guard)
- Detected Attempt #101 left per-φ comparison artifacts claiming parity despite missing C TRACE_C_PHI data; `comparison_summary.md` showed ✅ with an empty table.
- Updated `plans/active/cli-noise-pix0/plan.md` to require C instrumentation before any per-φ diff, explicitly mandating BLOCKED status when C entries are absent.
- Synced `docs/fix_plan.md` Next Actions with the new instrumentation guard so L3k.3b focuses on emitting TRACE_C_PHI and regenerating traces under a fresh timestamp.
- Replaced `input.md` (Parity) directing Ralph to add TRACE_C_PHI prints in `golden_suite_generator/nanoBragg.c`, rebuild, rerun the supervisor command, regenerate PyTorch traces, fix the misleading comparison summary, and capture updated diagnosis + checklist notes.
- Follow-up: Expect Ralph to land the instrumentation, produce `c_trace_phi_<timestamp>.log`, update comparison_summary to BLOCKED (until data present), refresh VG-1.4, and only then proceed toward VG-3/VG-4.
## 2025-10-07 (galph loop - L3k.3c prep)
- Synced repo (no conflicts) and reviewed docs/specs per SOP; coin flip→heads so Ralph’s last commit ee83081 confirmed TRACE_C_PHI instrumentation success (φ_tic=0 delta only).
- Updated `plans/active/cli-noise-pix0/plan.md` to mark L3k.3b DONE and clarified L3k.3c guidance (refresh comparison summary, hold φ_tic=0 focus). Input.md now steers Ralph to land the φ=0 rotation fix, regenerate per-φ traces, and flip VG-1.4 once Δk ≤1e-6.
- No code changes made; staged plan/input updates committed (`ddf68e4`).
- Follow-up for Ralph: implement L3k.3c φ=0 parity fix, capture new per-φ traces/tests per input.md, then proceed to L3k.3d nb-compare work once VG-1 is green.
## 2025-10-07 18:24 UTC (galph loop)
- Re-synced plan for CLI-FLAGS-003 Phase L3k.3c after reviewing Attempt #102.
- Updated plans/active/cli-noise-pix0/plan.md to require restoring C-aligned φ=0 tests before further work; added L3k.3c.1–.3 checklist.
- Marked Attempt #102 in docs/fix_plan.md as INVALID (masked failure) and listed required follow-up steps.
- Authored parity-mode input.md directing Ralph to reinstate the failing φ=0 test and log artifacts under reports/2025-10-cli-flags/phase_l/rot_vector/.
- Expect Ralph to restore the C-referenced pytest assertions, capture the resulting failure log, and update diagnosis.md plus fix_plan Attempts before implementing the actual φ=0 fix.

## 2025-11-22 (galph loop - φ=0 carryover evidence prep)
- Confirmed PyTorch `Crystal.get_rotated_real_vectors` returns `rot_b_phi0_y=0.71732 Å` while C trace holds `0.671588 Å` because nanoBragg.c:3040 skips resetting `ap/bp/cp` when `phi==0`. Python snippet recorded under this loop’s notes (see console command history).
- Noted commit 6f822dd introduced a Python loop over `phi_steps` (src/nanobrag_torch/models/crystal.py:1057-1084); plan instructs Ralph to document vectorized remediation so we can restore batched flow post-fix.
- Updated input.md to drive CLI-FLAGS-003 Phase L3k.3c.2 evidence capture: new artifacts to land under `reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/`, add delta_metrics.json + hashes, and extend diagnosis.md with vectorized fix outline.
- No code edits made; awaiting Ralph’s documentation run before authorising implementation of the carryover emulation.

## 2025-11-23 (galph loop - L3k.3b rerun planning)
- Reviewed Attempt #108 (commit 526f56d) — evidence captured the Py φ=0 probe but `delta_metrics.json` stayed BLOCKED because no fresh TRACE_C_PHI log accompanied the new timestamp; prior c-trace lives under 202510070839.
- Updated `plans/active/cli-noise-pix0/plan.md` (L3k.3 row + checklist) to reopen L3k.3b and mark L3k.3c.1 complete, with L3k.3c.2 now pointing at the pending Δk computation once C trace is regenerated.
- Refreshed `docs/fix_plan.md` Next Actions to (1) rerun TRACE_C_PHI for 20251123, (2) compute Δb_y/Δk_frac, (3) then return to nb-compare repairs.
- Authored new input.md steering Ralph to rebuild the C binary, rerun the supervisor command with `-trace_pixel 685 1039`, regenerate Py per-φ traces, run `scripts/compare_per_phi_traces.py`, update `delta_metrics.json`, and log the results before moving back to nb-compare.
- Feedback on Ralph’s recent work: Attempt #103 correctly restored the red guard tests; Attempt #108 gathered Py-only data but stalled without the paired C trace. Next loop should focus on producing the coeval TRACE_C_PHI artifact so VG-1.4 can flip from ⚠️ to actionable metrics.

## 2025-11-23 (galph loop - vectorization plan refresh)
- Synced repo (no conflicts). Action type: Planning; refreshed `plans/active/vectorization.md` context to note Phase C completion and queued Phase D polynomial vectorization.
- Updated `docs/fix_plan.md` › VECTOR-TRICUBIC-001: added Attempt #7 documenting Phase C3 assertions/device audit and rewrote Next Actions toward Phase D1–D3.
- Reissued `input.md` (Parity mode) directing Ralph to rerun Phase L3k.3b TRACE_C_PHI with full artifact capture; command map mirrors previous loop with typo fixes.
- Expect Ralph to produce the 20251123 C trace, update diagnosis + delta metrics, then proceed to L3k.3d per plan. Vectorization tasks now gate on new Phase D notes once CLI work unblocks.

## 2025-10-07 19:37 UTC (galph loop - L3k.3c.2 prep)
- Confirmed Attempt #109 artifacts: Δk(φ₀)=1.8116e-2, φ>0 deltas ≤2.845e-5; updated plans/active/cli-noise-pix0/plan.md (L3k.3b [D], refreshed L3k.3c.2 guidance).
- Refreshed docs/fix_plan.md Next Actions to focus on documenting Δk/Δb_y and follow-on carryover fix; added Attempt #109 summary.
- Issued new input.md (Parity mode) directing Ralph to run compare_per_phi_traces.py, compute Δb_y, update diagnosis/fix_checklist, and capture pytest collect-only evidence before implementation.
- Follow-up for Ralph: capture Δb_y via helper snippet, document metrics in diagnosis.md + fix_checklist.md, log Attempt for L3k.3c.2, keep artifacts under base_vector_debug/20251123/.

## 2025-11-23 (galph loop - φ carryover evidence synthesis)
- Verified VG-1 deltas: C `rot_b_y(φ₀)=0.671588233999813` vs PyTorch `0.7173197865486145` from reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/{c_trace_phi_20251123.log,trace_py_rot_vector_20251123.log}; Δk(φ₀)=1.8116e-02 captured in delta_metrics.json.
- Found tooling bug: `src/nanobrag_torch/simulator.py:1444` divides osc_range by `(phi_steps-1)` for TRACE_PY_PHI, yielding φ=0.011111° samples; added requirement to align with C loop formula when Ralph refreshes traces.
- Marked L3k.3c.2 DONE and updated plan/fix_plan Next Actions to focus on L3k.3c.3 carryover implementation + instrumentation fix before nb-compare work resumes.
- input.md now directs Ralph to implement φ carryover, adjust instrumentation, rerun compare_per_phi_traces.py, and close the red pytest guard.

## 2025-11-24 (galph loop - φ=0 carryover audit)
- Reopened CLI-FLAGS-003 L3k.3c.3 after spotting device/dtype + gradient regression in commit 6487e46 (`_phi_last_cache` stays on CPU and `torch.tensor(last_phi_deg, …)` detaches).
- Updated plans/active/cli-noise-pix0/plan.md guidance and docs/fix_plan.md Next Actions/Attempts to keep VG-1 blocked until cache migration + gradient fix land.
- Refreshed input.md (Parity mode) instructing Ralph to patch `Crystal.get_rotated_real_vectors`/`Crystal.to`, rerun trace_harness (CPU + optional CUDA), compare per-φ traces, and run gradcheck + φ=0 guard tests.

## 2025-11-26 (galph loop - φ=0 tolerance + spec memo)
- Verified commits 3fb29a4/5098d64: Δk remains 2.845e-05 (>1e-6) and Δb_y ≈ 4.57×10⁻² Å; `test_k_frac_phi0_matches_c` still red, so VG-1 not satisfied despite “success” claim.
- Updated `plans/active/cli-noise-pix0/plan.md` (lines 309-310) to keep L3k.3c.3 open, add spec alignment note, and introduce L3k.3c.4 documentation task (spec vs parity contract).
- Refreshed `docs/fix_plan.md` Next Actions (line 460+) and logged Attempt #114 noting reopened status, required memo, and artifact issues (duplicate per_phi/reports path).
- Issued new 110-line `input.md` (Docs mode) directing Ralph to regenerate per-φ traces with ≤1e-6 tolerances, document spec-vs-parity strategy, and log evidence (TRACE_TAG workflow, memo, tests).
- No code changes made; focus was planning/docs alignment ahead of the next engineering loop.

## 2025-11-27 (galph loop - φ=0 spec audit)
- Confirmed spec mandate (`specs/spec-a-core.md:211`) requires fresh φ rotations each step; C-PARITY-001 documents nanoBragg.c’s stale-vector carryover (`docs/bugs/verified_c_bugs.md:166`).
- PyTorch currently mirrors the bug via `_phi_last_cache` in `src/nanobrag_torch/models/crystal.py:1115-1198`; this contradicts the spec and the long-term goal to eliminate the carryover.
- CLI plan still instructs emulating the bug (L3k.3c.3). Issued new input.md directing Ralph to refresh `diagnosis.md` (L3k.3c.4) with spec-vs-parity guidance, log an Attempt, and run collect-only pytest. Expect next loop to revise the plan and design a spec-compliant default plus optional parity shim.

## 2025-10-07 (galph loop - φ=0 spec alignment)
- Reconfirmed spec mandate (`specs/spec-a-core.md:211-214`) that every φ step re-rotates the lattice and that C’s carryover bug is quarantined in `docs/bugs/verified_c_bugs.md:166-204`.
- Noted PyTorch still mirrors the bug via `_phi_last_cache` (`src/nanobrag_torch/models/crystal.py:1097-1198`); updated `docs/fix_plan.md` Next Actions and `plans/active/cli-noise-pix0/plan.md` context to call this out and require a parity shim decision.
- Issued new `input.md` (Docs mode) directing Ralph to refresh `reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md`, log the attempt, cross-link the plan, and run the collect-only selector with `KMP_DUPLICATE_LIB_OK=TRUE`.
- No tests run; repo clean after commit `10333c0`.

## 2025-10-07 22:16 UTC (galph loop - VECTOR-TRICUBIC-001 planning refresh)
- Rewrote `plans/active/vectorization.md` with phased structure (A–G) and explicit Phase D/F checklists; added D1–D4/D5 guidance and future absorption tasks.
- Updated `docs/fix_plan.md:2194-2210` Next Actions to align with the refreshed plan (Phase D1–D4 plus Phase E staging).
- Issued new `input.md` (Docs mode) directing Ralph to complete Phase D1 documentation, capture collect-only proof, and log tensor-shape/C-reference requirements.
- Follow-up: Ralph to author `reports/2025-10-vectorization/phase_d/polynomial_validation.md`, run collect-only selector, and prepare tap_points.md if needed before coding D2.


## 2025-11-27 (galph loop - φ rotation plan refresh)
- Rebased with origin (no conflicts) and reviewed CLI-FLAGS-003 scope vs long-term goal #1.
- Updated `plans/active/cli-noise-pix0/plan.md` L3k.3c tasks: default path now mandates spec-compliant φ rotation (no `_phi_last_cache`), added new rows for parity shim design (L3k.3c.4) and dual-mode docs/tests (L3k.3c.5), preserved documentation row as L3k.3c.6.
- Synced `docs/fix_plan.md` Next Actions to match the new gating order (spec fix → parity shim → docs/tests) and clarified historical attempt references.
- Issued fresh `input.md` (Parity mode) directing Ralph to implement L3k.3c.3, regenerate per-φ traces, and run the targeted φ parity tests; parity shim + doc refresh queued under Next Up.
- Commit `5eda539` pushed on `feature/spec-based-2`. No tests run in supervisor loop (planning only).
- Follow-up for Ralph: remove `_phi_last_cache` from the default rotation path, capture new Δk/Δb_y ≤1e-6 artifacts, then proceed to design the opt-in carryover shim per plan.

## 2025-11-27 (galph loop - spec baselines + test tightening)
- Reviewed Ralph’s commit 518fd75: spec rotation landed, but `test_k_frac_phi0_matches_c` only asserts divergence from the C bug. Need exact spec constants recorded before VG-1 can close.
- Updated `plans/active/cli-noise-pix0/plan.md` L3k.3 and L3k.3c.3 guidance to focus on locking rot_b_y=0.7173197865 Å and k_frac=1.6756687164 with ≤1e-6 deltas on CPU+CUDA, plus explicit artifact expectations.
- Adjusted `docs/fix_plan.md` Next Actions (Phase L3k.3c.3 → “lock spec φ=0 baselines”) to remove stale `_phi_last_cache` language.
- Replaced `input.md` with a Parity-mode memo directing Ralph to regenerate per-φ traces via `trace_harness.py`, update pytest expectations to the spec numbers, run targeted selectors, and archive new `delta_metrics.json` under a timestamped directory before flipping VG-1.
- Next supervisor checkpoint: confirm new artifacts exist, pytest asserts the spec constants, and plan row L3k.3c.3 is marked [D] before proceeding to the parity shim design tasks.

## 2025-11-27 (galph loop - φ=0 spec baselines evidence push)
- Re-read spec/core docs + CLI-FLAGS plan; confirmed Next Action remains L3k.3c.3 despite historic success notes because VG-1 artifacts need fresh capture post-rotation refactor.
- Selected focus = CLI-FLAGS-003 L3k.3c.3; staying in Parity mode, evidence-only loop (no code edits planned).
- Rewrote input.md (102 lines) directing Ralph to regenerate per-φ traces under a new timestamp, run compare_per_phi_traces.py + summarise_phi_deltas.py, rerun TestPhiZeroParity selectors on CPU (and CUDA if available), and update diagnosis.md, fix_checklist.md, and docs/fix_plan.md with ≤1e-6 deltas (rot_b_y 0.7173197865 Å, k_frac 1.6756687164).
- Emphasised reuse of the 202510070839 C trace, protected-assets compliance, SHA256 logging, and deferral of L3k.3c.4 shim/nb-compare work until VG-1 evidence is archived.
- No repository code or docs changed beyond input.md/memory update.
- Expect Ralph to execute the outlined evidence capture, mark VG-1 rows complete, and advance plan/fix_plan focus to L3k.3c.4 for the next engineering loop.

## 2025-11-28 (galph loop - parity shim planning)
- Added dedicated plan `plans/active/cli-phi-parity-shim/plan.md` with Phases A–D covering design, implementation, and documentation for the φ=0 carryover shim; Phase B now gates API selection and validation strategy.
- Updated `plans/active/cli-noise-pix0/plan.md:L3k.3c.4-5` to point at the new plan and clarified evidence expectations (reports/2025-10-cli-flags/phase_l/parity_shim/...).
- Refreshed `docs/fix_plan.md:450-463` Next Actions to align with the new plan (execute Phases B–D before resuming nb-compare work).
- Issued `input.md` (Docs mode) directing Ralph to author the design note, choose the opt-in trigger, and run the collect-only selector before coding. Command: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py --collect-only -q`.
- Commit `7ef88d2` pushed on `feature/spec-based-2`; no tests run in supervisor loop.


## 2025-11-28 (galph loop - CLI parity shim push)
- Re-synced (no upstream changes) and reviewed CLI-FLAGS-003 + parity-shim plan; spec remains φ=0 carryover-free (specs/spec-a-core.md:211-214) while C bug stays quarantined in docs/bugs/verified_c_bugs.md:166-182.
- Selected focus = CLI-FLAGS-003 Phase L3k.3c.4; no new plan needed. Input memo now steers Ralph to implement the opt-in φ carryover shim (Plan Phase C1–C5) with per-φ trace evidence and dual-mode tests.
- No fix_plan or plan edits required this turn; parity shim plan already authoritative. Next supervisor check: confirm reports/2025-10-cli-flags/phase_l/parity_shim/... artifacts exist, docs/fix_plan attempt logged, and tests cover both spec/parity modes before advancing to L3k.3c.5.

## 2025-11-28 (galph loop - vectorization plan sync)
- Reviewed spec/core docs for tricubic interpolation (specs/spec-a-core.md:230, 595) and confirmed φ carryover bug remains quarantined in docs/bugs/verified_c_bugs.md.
- Marked Phase D1 as complete in `plans/active/vectorization.md` (Attempt #8 worksheet) and refreshed status snapshot to reference `reports/2025-10-vectorization/phase_d/polynomial_validation.md`.
- Updated `docs/fix_plan.md` VECTOR-TRICUBIC-001 Next Actions to drop the stale D1 todo and point Ralph toward D2–D4 with the new evidence requirements.
- Issued Perf-mode `input.md` directing Ralph to author failing `TestTricubicPoly` coverage (Phase D3) before implementing vectorized helpers.
- Follow-up: Expect next loop to land D2 vectorized polynomials, record CPU/CUDA pytest logs under phase_d/, and log a new Attempt once tests go green.

## 2025-11-29 (galph loop - Phase D2 kickoff)
- Reconfirmed VECTOR-TRICUBIC-001 status: Phase D1 complete, D3 xfail tests present (`tests/test_tricubic_vectorized.py:332-735`). Scalar helpers in `src/nanobrag_torch/utils/physics.py:315-443` still unvectorized; `_tricubic_interpolation` continues to fall back to nearest-neighbour for B>1.
- Action: Maintained existing plan, but issued new Perf-mode `input.md` directing Ralph to implement `polint_vectorized`/`polin2_vectorized`/`polin3_vectorized`, wire them into the batched path, remove the fallback warning, and capture CPU/CUDA pytest logs under `reports/2025-10-vectorization/phase_d/`.
- Expectations logged: update `implementation_notes.md`, rerun `tests/test_tricubic_vectorized.py::TestTricubicPoly`, then hit `tests/test_at_str_002.py::TestStructureFactorInterpolation::test_tricubic_interpolation_enabled`, and record a new Attempt in `docs/fix_plan.md` marking plan row D2 [D].
- Follow-up for Ralph: land D2 implementation, produce the requested artifacts/logs, and be ready to progress to Plan Phase D4 once the vectorized helpers pass.

## 2025-11-29 (galph loop - vectorization D4 prep)
- Confirmed CLI parity plans remain pending; spec shards still reject the φ=0 carryover bug (specs/spec-a-core.md:211-214) so no spec edits required this turn.
- Reviewed Ralph’s Phase D2 commit (f796861): vectorized polin* helpers landed with correct docstrings/tests; noted residual 4-iteration Python loops in polin2/polin3_vectorized—acceptable for now but flag for Phase E perf review.
- Updated `plans/active/vectorization.md` (D2 marked [D], D4 guidance clarified) and refreshed `docs/fix_plan.md` Next Actions to focus on D4 evidence + Phase E staging.
- Issued new Perf-mode `input.md` directing Ralph to capture Phase D4 CPU/CUDA pytest logs, update polynomial_validation.md with timings, and log a new Attempt when done.
- Expect Ralph to run the specified selectors, archive logs under `reports/2025-10-vectorization/phase_d/`, and advance plan row D4 to [D] before moving into Phase E.

## 2025-11-30 (galph loop - parity evidence focus)
- Reviewed CLI-FLAGS-003 progress: parity shim code/tests already landed (docs/fix_plan.md Attempt #120) but plan rows still open.
- Updated `plans/active/cli-phi-parity-shim/plan.md` C1–C3 to [D] with artifact references; marked `plans/active/cli-noise-pix0/plan.md` L3k.3c.4 as [D] and refreshed Next Actions to target Phase C4 evidence capture.
- Revised `docs/fix_plan.md` Next Actions so L3k.3c.4 emphasises per-φ trace collection + targeted pytest logs before documentation work.
- Issued new `input.md` (Parity mode) directing Ralph to extend the trace harness with a `--phi-mode` toggle, record spec vs c-parity per-φ traces, rerun tests, and log artifacts under `reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/`.
- Expect Ralph to produce VG-1 parity evidence, update parity plan rows C4/C5, and then proceed toward Phase L3k.3d nb-compare once traces pass tolerances.

## 2025-10-08 (galph loop - L3k.3c.4 parity regression)
- Ran parity trace harness (spec & c-parity) into `reports/2025-10-cli-flags/phase_l/parity_shim/20251008T011326Z/`; spec mode still diverges at φ₀ as expected, c-parity plateau remains Δk≈2.845e-05 > 1e-6.
- TRACE_C_PHI logging missing in current golden binary; reused older log to complete comparison. Logged this gap and marked plan row L3k.3c.4 as [P].
- Updated `plans/active/cli-phi-parity-shim/plan.md` + `docs/fix_plan.md` Attempt #122 with metrics and next steps (restore instrumentation, diagnose residual drift).
- Issued new Parity-mode input directing Ralph to tighten shim tolerances and regenerate traces with fresh C instrumentation.

## 2025-11-30 (galph loop - vectorization Phase E kickoff)
- Synced `plans/active/vectorization.md` to note Phases A–D complete and rewrote Phase E task guidance (CPU/CUDA pytest logs, perf summary expectations).
- Updated `docs/fix_plan.md` Next Actions for VECTOR-TRICUBIC-001 so Ralph targets Phase E1–E3 evidence and begins Phase F design once parity/perf metrics land.
- Issued new Perf-mode `input.md` pointing Ralph at Phase E1 (`tests/test_tricubic_vectorized.py` + `tests/test_at_str_002.py`) with explicit log destinations under `reports/2025-10-vectorization/phase_e/`.
- Follow-up: Expect Ralph to produce Phase E1 CPU/GPU logs, capture env metadata, and append Phase E notes to `polynomial_validation.md` before proceeding to E2 benchmarks.

## 2025-10-08 (galph loop - parity shim evidence refresh)
- Captured fresh C and PyTorch per-φ traces under `reports/2025-10-cli-flags/phase_l/parity_shim/20251008T021659Z/` using the supervisor command + trace harness (spec + c-parity modes).
- New C log includes 10 `TRACE_C_PHI` lines; c-parity rot_b_y now matches C exactly, but Δk stays at 2.8451466e-05 and ΔF_latt_b at 4.36e-03, leaving VG-1 unmet.
- Updated `plans/active/cli-phi-parity-shim/plan.md` C4 row and `docs/fix_plan.md` (Attempt #124, line ~684) to record metrics + next diagnostic steps (instrument scattering vector taps, audit reciprocal recompute).
- Issued Parity-mode `input.md` directing Ralph to add scattering-vector/V_actual taps, rerun harness, and regenerate comparison artifacts before trying another shim tweak.
- Expect Ralph to extend instrumentation (while citing nanoBragg.c:3044-3058), run both spec and parity harness passes, update `delta_metrics.json`, and iterate until Δk ≤ 1e-6.

## 2025-10-08 02:47:39Z (galph loop - pix0 parity evidence)
- Ran trace diff on c-parity φ=0 logs; new artifacts under `reports/2025-10-cli-flags/phase_l/parity_shim/20251008T023956Z/`.
- First divergence now confirmed at `pix0_vector_meters` (2.85 µm along detector normal), cascading to scattering vector and Δk≈2.845e-05.
- Updated `docs/fix_plan.md` (Attempt #128 + Next Actions) to focus Phase L3k.3c.4 on eliminating pix0_z offset before re-running parity.
- Refreshed `input.md` (Parity mode) directing Ralph to regenerate traces via `trace_harness.py`, capture C trace with `-trace_pixel 685 1039`, rerun `compare_per_phi_traces.py`, and keep docs/spec references aligned.
- Follow-up: Ralph to audit detector pix0 pipeline (distance/pivot math) so VG-1 hits ≤1e-6, then progress to plan Phase C5.

## 2025-12-01 (galph loop - φ=0 spec audit)
- Reviewed specs/spec-a-core.md:211-224 and confirmed φ loop remains spec-compliant (fresh rotations every step); no C carryover language in specs.
- Verified docs/bugs/verified_c_bugs.md:166 continues to quarantine C-PARITY-001 as a defect and the PyTorch default path (`Crystal.get_rotated_real_vectors` lines ~1080-1170) keeps `phi_carryover_mode="spec"` as default.
- `tests/test_cli_scaling_phi0.py` still enforces the spec baseline; instructed Ralph via input.md to rerun these selectors and capture fresh logs under `reports/2025-12-cli-flags/phase_l/spec_baseline_refresh/` before touching parity shim math.
- Next actions for Ralph: execute the mapped tests, write `summary.md` + `commands.txt` in the new report directory, and log an Attempt update in docs/fix_plan.md so Phase C4 (parity shim traces) can resume with up-to-date documentation evidence.

## 2025-12-?? (galph loop - parity diagnostics refresh)
- Added C4 diagnostic checklist to `plans/active/cli-phi-parity-shim/plan.md` so Ralph regenerates per-φ traces via `trace_per_phi.py`, reruns `compare_per_phi_traces.py`, and captures detector geometry comparisons before touching implementation.
- Updated `docs/fix_plan.md` Next Actions for CLI-FLAGS-003 to point explicitly at the checklist and geometry table deliverable.
- Issued Parity-mode `input.md` directing Ralph to produce new artifacts under `reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/`, append geometry data to `rot_vector/diagnosis.md`, and log collect-only pytest output.
- Expect Ralph to follow C4b–C4d, then update diagnosis.md and attempt history once Δk ≤ 1e-6.

## 2025-10-07 (galph loop - parity evidence prep)
- Re-read specs/spec-a-core.md:211-214 and confirmed φ rotation stays spec-compliant; no carryover language leaked into specs/spec-a-cli.md.
- Cross-checked docs/bugs/verified_c_bugs.md:166-204 to ensure C-PARITY-001 remains quarantined; architecture notes (arch.md:204-216) align with spec.
- Issued new Parity-mode input (Phase L3k.3c.4) instructing Ralph to regenerate per-φ traces via `trace_per_phi.py` and `compare_per_phi_traces.py`, capture artifacts under `reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/`, and update diagnosis/fix_plan attempts.
- Next expectation: Ralph delivers fresh Δk/ΔF_latt_b metrics; if thresholds met, proceed to Phase L3k.3c.5 documentation/tests before nb-compare rerun.

## 2025-12-01 (galph loop - dtype plateau probe setup)
- Refreshed `plans/active/cli-phi-parity-shim/plan.md` to reflect post-Attempt #127 state: parity shim landed, pix0 parity confirmed, residual Δk≈2.845e-05 treated as precision issue; C4 checklist now targets float32/float64 sweeps (rows C4b–C4d).
- Updated `docs/fix_plan.md` Next Actions for CLI-FLAGS-003 to point at the dtype sensitivity pass instead of the old pix0 offset work; annotated Attempts #128/#129 with notes that later evidence supersedes the pix0 focus.
- Issued `input.md` (Parity mode) directing Ralph to run `trace_harness.py` for supervisor pixel (685,1039) across float32/float64 c-parity runs, capture compare_per_phi outputs under `reports/2025-10-cli-flags/phase_l/parity_shim/20251201_dtype_probe/`, and append findings to `diagnosis.md` before making the VG-1 tolerance call.
## 2025-12-02 (galph loop - parity doc sync setup)
- Updated `plans/active/cli-phi-parity-shim/plan.md` to reflect the dtype probe decision: C4 marked [D], C4b/C4c done, C4d left [P] pending checklist/plan sync, and Current Status refreshed with the |Δk| ≤5e-5 tolerance for c-parity.
- Refreshed `docs/fix_plan.md` Next Actions for CLI-FLAGS-003 to focus on syncing plans/checklists, updating diagnosis + bug docs, and rerunning nb-compare afterward.
- Issued new Docs-mode `input.md` directing Ralph to update diagnosis.md, fix_checklist.md, cli-noise plan, and docs/bugs with dual-threshold notes, capture collect-only evidence under `reports/2025-10-cli-flags/phase_l/rot_vector/20251201_dual_threshold/`, and log a new Attempt before advancing to Phase L3k.3d.
- Expect Ralph to close out plan row C4d, complete the doc updates, run the mapped collect-only pytest, and append the evidence + Attempt entry so we can tackle nb-compare next loop.
## 2025-12-02 (galph loop - CLI-FLAGS-003 plan refresh)
- Rebuilt `plans/active/cli-noise-pix0/plan.md` around new Phases L–O so tolerance/doc sync (L1–L3), scaling parity (M1–M4), nb-compare (N1–N3), and supervisor rerun (O1–O3) are explicit. Prior phases collapsed into a completed summary for easier navigation.
- Updated `docs/fix_plan.md:460-463` Next Actions to align with the new phase IDs (L1–L3, M1–M3, N1–N3) and staged `input.md` with Docs-mode guidance pointing Ralph at Phase L1–L3 deliverables.
- Expect Ralph to produce artifacts under `reports/2025-10-cli-flags/phase_l/rot_vector/20251202_tolerance_sync/`, update diagnosis/checklists/bug log, add a fresh Attempt entry, and run the mapped collect-only pytest before we revisit scaling parity (Phase M).

## 2025-12-02 (galph loop - CLI docs sync + pyrefly backlog)
- Updated `docs/fix_plan.md` Next Actions for CLI-FLAGS-003 to remove the stale blocker note and focus on Phase L documentation sync, Phase M scaling parity, and Phase N/O readiness while reaffirming spec shards + bug quarantine references.
- Annotated Attempt #135 in `docs/fix_plan.md` as historical, clarifying that the referenced plans/tests now exist post-sync.
- Added new fix-plan entry `[STATIC-PYREFLY-001]` to capture the impending static-analysis baseline (verify tool availability, run `pyrefly check src`, delegate fixes).
- Authored Docs-mode `input.md` (~100 lines) directing Ralph to execute Phase L1–L3 doc updates, run collect-only selectors, refresh plans/checklists/bug doc, and store artifacts in a new `reports/2025-10-cli-flags/phase_l/rot_vector/<timestamp>/` folder before advancing to Phase M.
- Next expectations: Ralph completes the documentation sync, logs a fresh CLI-FLAGS-003 Attempt with commands + artifact links, keeps spec untouched, and lines up Phase M scaling parity work for the following loop.

## 2025-10-08 04:33:06Z (galph loop)
- Updated docs/fix_plan.md CLI-FLAGS-003 next actions to focus on scaling audit tasks M1–M4 (trace harness + regression test).
- Issued Parity-mode input.md directing Ralph to capture new CPU scaling traces via trace_harness.py and compare_scaling_traces.py, storing artifacts under scaling_validation/.
- Outstanding follow-up: after CPU evidence, expand to CUDA trace and implement scaling fix + regression test per plan.

## 2025-12-03 (galph loop - CLI-FLAGS-003 Phase M1 triage)
- Replayed scaling evidence from Attempt #137: PyTorch I_before_scaling is 21.9% low even though F_cell matches C.
- Diagnosis: trace_harness.py still instantiates CrystalConfig in spec mode; per-φ log (`reports/2025-10-cli-flags/phase_l/per_phi/reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T043438Z/trace_py_scaling_cpu_per_phi.log:1`) shows φ₀ F_latt=+1.379 vs C’s −2.383. Existing c-parity shim (`trace_py_c_parity_per_phi.log:1 (reports/2025-10-cli-flags/phase_l/per_phi)`) reproduces the C values.
- Action for Ralph: add a `--phi-mode` override (default spec, parity run uses c-parity), rerun the harness + compare_scaling_traces.py, and capture new artifacts under `phase_l/scaling_validation/<timestamp>/` before moving to Phase M2.
- No other assets touched; docs/index.md remains authoritative.
## 2025-12-03 (galph loop - CLI-FLAGS-003 Phase M1 evidence refresh)
- Updated `plans/active/vectorization.md` context to the 2025-12-02 snapshot and marked Phase E1 [D]; remaining work now tracks E2/E3 perf validation before detector absorption vectorization.
- Issued new Parity-mode input.md directing Ralph to rerun the scaling harness with `--phi-mode c-parity`, capture trace/summary/metrics under a fresh timestamp, and hold compare_scaling_traces tolerance at 1e-6 per Phase M1.
- Reinforced evidence-only expectations (no prod edits) and enumerated required artifacts (commands.txt, metrics.json, env.json, sha256.txt) so Phase M2 debugging starts with clean data; flagged follow-up for Phase M2/M3 and vectorization Phase E2/E3 once scaling parity stabilises.
## 2025-12-03 (galph loop - CLI-FLAGS-003 Phase M instrumentation)
- Identified that the 8.7% `I_before_scaling` delta is purely an instrumentation mismatch: PyTorch logs the post-polarization value while the C trace logs pre-polarization. C value × polar reproduces the PyTorch number.
- Added debug memo `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T044933Z/galph_debug_20251203.md` documenting the finding and the expected pre- vs post-polar values.
- Updated `docs/fix_plan.md` (CLI-FLAGS-003 first divergence + Next Actions bullet) to call out the polarization offset and require trace tap updates before continuing Phase M.
- Issued Parity-mode `input.md` directing Ralph to emit both pre/post polarization trace lines, refresh the harness, rerun compare_scaling_traces, and keep evidence under a new timestamped directory.
- Next supervisor follow-up: confirm Ralph captures the new trace, updates compare script if needed, and logs Attempt before moving to structure-factor parity (Plan M2/M3).

## 2025-12-03 (galph loop - Pyrefly planning bootstrap)
- Authored `plans/active/static-pyrefly.md` with Phases A–E covering tool verification, baseline scan, triage, delegation hooks, and closure criteria for STATIC-PYREFLY-001.
- Updated `docs/fix_plan.md:2943-2954` to reference the new plan, set status to in_progress, and align next actions with plan phases.
- Rewrote `input.md` (Docs mode) instructing Ralph to execute Phase A (tool audit + artifact scaffold) before any pyrefly run; emphasized artifact paths under `reports/pyrefly/`.

## 2025-10-08 (galph loop - STATIC-PYREFLY-001 Phase B setup)
- Coin flip→heads: reviewed Ralph’s recent commits (`ef1f716`, `e97a66c`) and found them productive; Phase M1 instrumentation landed cleanly and pyrefly Phase A evidence captured without regressions.
- Chosen focus: STATIC-PYREFLY-001 Phase B baseline run; no new plan required since `plans/active/static-pyrefly.md` already governs the workflow.
- Actions this loop: refreshed `input.md` with Docs-mode guidance covering Phase B1–B3 deliverables (pyrefly.log, env.json, summary.md, fix_plan Attempt update) and reiterated artifact/timestamp reuse under `reports/pyrefly/20251008T053652Z/`.
- No changes to docs/fix_plan.md this turn; expect Ralph to record Attempt #2 after the baseline run and keep the working tree clean.
- Follow-up: next supervisor loop should inspect the new summary, decide on Phase C triage scope, and ensure pyrefly findings are mapped to owners/tests before delegating fixes.

## 2025-12-04 (galph loop - CLI-FLAGS-003 Phase M1 refresh)
- Re-ran `trace_harness.py` in both spec and c-parity modes (float64/CPU) and stored evidence under `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T055257Z/` (spec) and `.../20251008T055533Z/` (c-parity). Spec path diverges 14.6% as expected; c-parity delta shrank to 0.2086%.
- Added Attempt #140 to `docs/fix_plan.md:510` capturing the new metrics plus the crash encountered when invoking `scripts/validation/compare_scaling_traces.py` on these traces.
- Updated `plans/active/cli-noise-pix0/plan.md:53` with the fresh timestamps and noted that Phase M1 remains open pending ≤1e-6 parity.
- `compare_scaling_traces.py` currently exits via SIGKILL on the new traces; manual summaries were generated as a stopgap. Ralph needs to debug the script before Phase M2 lattice fixes proceed.
- Next steps for Ralph: fix the comparison script, regenerate the scaling summary in a new timestamped directory (CPU float64, c-parity), then continue Phase M2 by targeting the φ₀ lattice-factor drift.
- Working tree note: legacy galph log (`logs/feature-spec-based-2/galph/iter-00141_20251008_054647.log`) stayed untouched per policy; left uncommitted.

## 2025-10-08 (galph loop - Phase M1 lattice delta audit)
- Captured fresh c-parity trace via `trace_harness.py` (float64/CPU) and stored manual summary + metrics under `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T060721Z/`; F_latt drift is ~0.13% and drives the 0.2086% `I_before_scaling` deficit.
- `scripts/validation/compare_scaling_traces.py` still dies via SIGKILL; left the failing command in commands.txt and regenerated the summary with inline Python.
- Updated `docs/fix_plan.md` (Attempt #141) and `plans/active/cli-noise-pix0/plan.md` Phase M1 guidance to reference the new evidence and emphasise tricubic neighbourhood instrumentation.
- `input.md` now pushes Ralph to extend the harness with 4×4×4 weight logging and to stabilise the comparison script before moving to Phase M2.

## 2025-12-04 (galph loop - Phase M0 instrumentation hygiene setup)
- Coin flip=heads: reviewed Ralph commit 9a8c2f5; instrumentation stores `_last_tricubic_neighborhood` tensors and forces CPU tensors in trace path — flagged need for guarded usage before Phase M proceeds.
- Updated guidance by reinforcing plan CLI-FLAGS-003 Phase M0 (already codified) and issuing Parity-mode input.md directing Ralph to audit/guard the tricubic cache before rerunning scaling parity.
- Key expectations: capture new trace evidence under `reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/`, verify device/dtype neutrality, document results in instrumentation_audit.md, and log Attempt for M0a–M0c.
- Follow-up: next loop confirm M0 tasks marked [D], ensure guard prevents memory bloat on production runs, and decide when to resume Phase M1 HKL parity.
- Working tree note: `logs/feature-spec-based-2/galph/iter-00142_20251008_062157.log` remains modified from prior runs; left uncommitted per log-retention policy.

## 2025-12-05 (galph loop - C5 documentation prep)
- Reviewed spec/arch/testing documents plus plans: confirmed φ rotation spec (specs/spec-a-core.md:205-233) is bug-free and parity shim remains optional.
- Re-validated `plans/active/cli-phi-parity-shim/plan.md` Phase C5/D3 guidance (evidence checklist already present) and highlighted it in supervision notes instead of editing the plan.
- Added Next Action bullet in `docs/fix_plan.md:460` reminding Ralph to complete parity shim summary before returning to Phase M runs; refreshed `input.md` Do Now for Phase M0 instrumentation hygiene with references to the checklist.
- Expect Ralph to capture instrumentation audit artifacts under `reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/`, guard `_last_tricubic_neighborhood`, and then proceed to C5 summary per existing checklist.
- Next follow-up: verify docs/fix_plan Attempt log records the C5 checklist completion and that `reports/2025-10-cli-flags/phase_l/scaling_validation/` gains the new summary.md before advancing Phase M metrics.

## 2025-12-06 (galph loop - CLI-FLAGS-003 Phase M1 tooling focus)
- Synced with origin (no conflicts); reviewed core docs, CLI-FLAGS plan, and latest instrumentation evidence before analysis.
- Focus: CLI-FLAGS-003 Phase M1 follow-up. Marked plan Phase M0 tasks [D] with Attempt #144 artifact references and refreshed docs/fix_plan Next Actions to prioritize the compare_scaling_traces.py repair.
- Rewrote input.md (Parity mode, 100 lines) directing Ralph to fix the scaling comparison script, capture a new RUN_DIR trace, rerun targeted pytest suites, and log artifacts for Phase M2.
- Working tree now holds plan/fix_plan/input updates; expect Ralph to stabilise the script, produce new scaling_validation artifacts, update plan Attempt log, and then advance to lattice investigation next loop.

## 2025-12-06 (galph loop - Phase M1 checklist reopen)
- `git pull --rebase` clean; re-read specs/index/arch/config/testing docs plus CLI-FLAGS plan + fix_plan before analysis.
- Found `plans/active/cli-noise-pix0/plan.md` still marked M1 [D] even though compare_scaling_traces.py regressed to SIGKILL (Attempts #140/#141, commands.txt). Reopened M1 → [P], added checklist M1a–M1d, and refreshed status snapshot with 2025-12-06 context.
- Updated `docs/fix_plan.md` Next Actions (2025-12-06 refresh) and logged Attempt #146 documenting the plan reopen; no code/tests run.
- Replaced input.md with Parity-mode memo pointing Ralph to execute M1a first: capture fresh crash evidence under a new timestamp, record exit codes, and log artifacts before touching the script.
- Follow-up for Ralph: deliver M1a artifacts (commands.txt, trace, stdout, env, sha catalog), update plan M1a row + fix_plan Attempt; stop before implementing script fix so next supervisor loop can review.

## 2025-12-06 (galph loop - Phase M2 prep)
- Verified `compare_scaling_traces.py` stability via `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T072513Z/validation_report.md`; M1 checklist re-closed.
- Updated `plans/active/cli-noise-pix0/plan.md` status snapshot, marked M1 [D], and added M2a–M2c analysis checklist.
- Refreshed `docs/fix_plan.md` Next Actions (Phase M2 forward) and logged Attempt #147 documenting the verification.
- Replaced supervisor memo with Phase M2 parity focus (new RUN_DIR, sincg analysis script, hypotheses capture).
- Expect Ralph to execute M2a–M2c commands, produce `manual_sincg.md` + `lattice_hypotheses.md`, and update plan/Fix Plan attempts accordingly.

## 2025-12-06 (galph loop - Phase M2 lattice hypotheses)
- Authored `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md` summarising F_latt vs HKL deltas and three follow-up probes (rotated-vector taps, V_actual check, float64 rerun). Plan `cli-noise-pix0` M2c now [D]; logged Attempt #149 in docs/fix_plan.md.
- Input memo (Parity mode) directs Ralph to add φ-step trace taps + run float64 harness with new flag; artifacts to land under fresh timestamp before lattice fixes begin.

## 2025-12-07 (galph loop - Phase M2 lattice debug)
- Reconfirmed CLI-FLAGS-003 Phase M2 focus after sync; reviewed specs/index/arch/config/testing docs plus recent traces.
- Evidence review: `trace_py_scaling_per_phi.log` vs `c_trace_scaling.log` shows constant k_frac offset (~−6.78e-06) and |F_latt| rel error ≈1.3e-3; reciprocal components differ (`a_star_y` +1.69e-05, `b_star_y` −5.16e-05, `c_star_y` −1.66e-05).
- Scattering vector deltas (S_x+5.24e3, S_y+3.04e3, S_z+331) line up with those reciprocal drifts, pointing at MOSFLM ingestion rather than φ carryover.
- Hypothesis: `Crystal.compute_cell_tensors()` MOSFLM branch not enforcing nanoBragg reciprocal/real recomputation sequence; need to re-derive from MOSFLM vectors using exact C formulas so metric duality holds. Secondary: verify no residual pix0/close_distance rounding after fix.
- Wrote Parity-mode input.md targeting CLI-FLAGS-003 Phase M2 fix: reproduce drift, correct MOSFLM reciprocal vectors, rerun trace harness, run targeted pytest, update evidence/logs.
- Next supervisor follow-up: confirm new timestamp under `reports/2025-10-cli-flags/phase_l/scaling_validation/`, metrics.json shows first_divergence=None, docs/fix_plan attempt logged, and plan Phase M2 marked [D] before advancing to Phase M3.

## 2025-12-07 (galph loop - Phase M2 carryover focus)
- Identified that residual F_latt delta stems from c-parity shim copying the current pixel’s φ-final vectors instead of the previous pixel’s state; added 2025-12-07 note to `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md`.
- Updated `plans/active/cli-noise-pix0/plan.md` (M2 row retargeted to carryover parity, new checklist item M2d for consecutive-pixel traces).
- Refreshed `docs/fix_plan.md` Next Actions to require the carryover probe + simulator fix.
- Rewrote input.md directing Ralph to capture the carryover evidence, update the shim to persist prior-pixel φ state, rerun the trace harness, and close with the targeted pytest.
- Expect Ralph to log new artifacts under `reports/.../carryover_probe/`, implement the stateful cache, and bring `I_before_scaling` into the ≤1e-6 envelope before moving to Phase M3.

## 2025-12-07 (galph loop - Phase M2 cache redesign planning)
- Reviewed commit 3269f6d (carryover cache + parity test); identified that cache never engages during vectorised run and `.detach().clone()` would break gradients even if it did. Latest trace (reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T081932Z/) still shows F_latt=-2.380134 vs C=-2.383196653 (ΔI=-1968.57, -0.209%).
- Updated plans/active/cli-noise-pix0/plan.md (Status Snapshot 2025-12-07 refresh, M2→[P], M2d→[P], new M2e test task) and docs/fix_plan.md Next Actions + Attempt #150 documenting the partial fix and remaining gaps.
- Authored input.md (Parity mode, 97 lines) directing Ralph to capture new carryover evidence, redesign the cache for vectorised execution without `.detach()`, rerun scaling metrics, and keep the new regression test failing until Δ≤1e-6.
- Follow-up for Ralph: produce consecutive-pixel traces under a new timestamp, refactor the cache logic to achieve ≤1e-6 parity, update metrics.json/test logs, and log outcomes in docs/fix_plan.md + plan checklist before advancing to Phase M3.

## 2025-12-07 (galph loop - Phase M2 Option 1 planning refresh)
- Coin flip=heads → Reviewed Ralph commits 3269f6d (carryover cache) and 89dcd66 (diagnosis). Confirmed cache never fires within a run, `.detach().clone()` breaks gradients, and Option 1 pixel-indexed cache is required.
- Updated `plans/active/cli-noise-pix0/plan.md` status snapshot and Phase M2: added M2 Implementation checklist (M2f–M2i) covering design, vectorised plumbing, gradient validation, and post-fix traces; noted Attempt #151 diagnosis.
- Refreshed `docs/fix_plan.md` Next Actions to align with new checklist (cross-pixel probe, Option 1 design detail, implementation + validation bundle, downstream scaling/nb-compare).
- Authored new `input.md` (Parity mode) directing Ralph to run the consecutive-pixel trace harness (M2d), archive artifacts, extend `phi_carryover_diagnosis.md` with Option 1 tensor shapes, and keep work evidence-only this loop.
- No production code touched; focus stays on evidence/design prep before cache reimplementation.

## 2025-12-07 (galph loop - Phase M2e prep)
- Git sync clean; refreshed required specs/arch/testing docs plus CLI-FLAGS plan before analysis.
- Verified Ralph’s recent commits 89dcd66 and 0d22aa8: productive evidence/test updates, no regressions (targeted test intentionally red pending cache redesign).
- Updated `plans/active/cli-noise-pix0/plan.md` (Status Snapshot + Next Actions + M2 checklist) to mark M2d/M2f [D] and focus forward work on M2e–M2i.
- Refreshed `docs/fix_plan.md` Next Actions to match new plan (capture failing test log, then Option 1 implementation + trace reruns).
- Authored new `input.md` (Parity mode) directing Ralph to log the failing scaling-parity test (M2e) under a fresh timestamp before touching code.
- Follow-up for Ralph: execute Do Now command, store artifacts in `reports/.../parity_test_failure/`, update plan/fix_plan attempt entries, keep regression test red-but-documented for Option 1 implementation loop.

## 2025-12-08 (galph loop - Phase M2g planning refresh)
- Expanded `plans/active/cli-noise-pix0/plan.md` Phase M2 with detailed M2g/M2h/M2i subtables and updated guidance for Option 1 pixel-indexed cache work (cache allocation, helper wiring, CUDA probe, gradcheck, documentation sync).
- Synced `docs/fix_plan.md` Next Actions to point at the new sub-checklists (M2g–M2i) so Ralph’s next loop focuses on implementing the cache and capturing validation artifacts.
- Rewrote `input.md` to direct Ralph to implement the cache, run the targeted parity/gradcheck commands, capture CUDA/trace evidence, and archive outputs under the refreshed carryover folders.
- Follow-up for Ralph: implement M2g cache plumbing, produce carryover_cache_validation + carryover_probe artifacts, update phi_carryover_diagnosis.md, and flip M2g–M2i to [D] before moving to Phase M3.

## 2025-12-08 (galph loop - Phase M2g regression correction)
- Coin flip=heads → Reviewed Ralph commit f3f66a9; `_run_sequential_c_parity()` replaces the vectorised c-parity flow and violates the runtime checklist’s no-loop guardrail.
- Updated `plans/active/cli-noise-pix0/plan.md` status snapshot, Next Actions, and M2g checklist to require deleting the sequential fallback (new M2g.2) before building the pixel-indexed cache.
- Synced `docs/fix_plan.md` Next Actions with the rollback requirement and logged Attempt #154 capturing the plan correction.
- Authored new `input.md` (Parity mode) instructing Ralph to remove the sequential branch, implement the Option 1 cache tensors, run the mapped parity pytest, capture artifacts under `reports/.../carryover_cache_validation/`, and document the change in `phi_carryover_diagnosis.md`.
- Follow-up for Ralph: restore unified vectorised execution, add the pixel-indexed cache with device/dtype neutrality, refresh trace harness + diagnosis notes, run the targeted pytest selector, and update docs/fix_plan.md once evidence is captured.

## 2025-12-08 (galph loop - M2g regression supervision)
- Coin flip=heads → reviewed Ralph commit f3f66a9; sequential `_run_sequential_c_parity()` branch still present and violates vectorisation guardrail, no new evidence since Attempt #153.
- Action type: Review/housekeeping on CLI-FLAGS-003 M2g; refreshed input.md (Parity mode) directing Ralph to remove the sequential fallback, implement the Option 1 pixel-indexed cache, and rerun the targeted parity pytest.
- No plan/fix_plan edits required today; both already call for M2g regression cleanup. Input now cross-references the same checkpoints and adds detailed cache implementation steps.
- Follow-up for Ralph: excise sequential branch, land pixel-indexed cache per Option 1 design, capture pytest + trace artifacts under new timestamp, update docs/fix_plan.md Attempt.

## 2025-12-08 (galph loop - CLI-FLAGS-003 doc check)
- Verified `specs/spec-a-core.md:205-233` still enforces fresh φ rotations; no carryover semantics crept into the spec or parity shim docs.
- Updated `plans/active/cli-phi-parity-shim/plan.md` (lines 11-12, C5a row) to record the spec review and remind Ralph that C5 `summary.md` must cite those lines when documenting the shim.
- Synced `docs/fix_plan.md` Next Actions bullet 4 with the same citation so the documentation follow-up stays on the radar alongside the Option 1 cache work.
- Authored `input.md` directing Ralph to complete M2g.1 (Option 1 design refresh) as a docs-only loop with collect-only pytest and a new memo under `reports/2025-10-cli-flags/phase_l/scaling_validation/20251208_option1_refresh/`.
- Follow-up for Ralph: run the collect-only command, revisit `phi_carryover_diagnosis.md`, produce the updated analysis memo citing the spec section, and prepare to propose the Option 1 architecture decision next loop.

## 2025-12-09 (galph loop - Phase M2g Option B setup)
- Re-read core docs plus `phi_carryover_diagnosis.md` and the 20251208 Option 1 refresh memo; confirmed we will pursue Option B (batch-indexed cache) for CLI-FLAGS-003.
- Updated `plans/active/cli-noise-pix0/plan.md` Status Snapshot and Next Actions to note sequential fallback removal (Attempt #155) and to direct Option B cache plumbing; marked M2g.2 [D] and rewrote M2g description to emphasise batched `(slow_indices, fast_indices)` support.
- Synced `docs/fix_plan.md` CLI-FLAGS-003 Next Actions with the Option B decision so the ledger matches the refreshed plan.
- Authored new `input.md` (Parity mode) instructing Ralph to implement the batch-indexed cache, thread pixel indices through the simulator, update trace tooling, run the targeted pytest selector, capture gradcheck/trace artifacts, and document the work in diagnosis notes plus fix_plan Attempt.
- Follow-up for Ralph: land Option B cache plumbing (M2g.3–M2g.6), update tooling + documentation, complete the validation bundle (M2h, M2i), and log artifacts under new timestamped directories before moving to Phase M3.

## 2025-10-08 14:24:13Z (galph loop - M2g wiring evidence)
- Focused on CLI-FLAGS-003 Phase M2g; reviewed `src/nanobrag_torch/models/crystal.py:195-386` and `simulator.py:730-1090` confirming `apply_phi_carryover`/`store_phi_final` remain single-pixel helpers and are never invoked, with `.item()` based cache validity that blocks vectorized batches.
- Updated `plans/active/cli-noise-pix0/plan.md` status snapshot (Attempt #155 note now highlights missing simulator wiring) and expanded M2g.4 guidance to call out deriving `(slow_indices, fast_indices)` from ROI tensors using pure tensor indexing.
- Rewrote `input.md` (Parity mode) to direct Ralph to batch the cache helpers, thread indices through `_compute_physics_for_position`, replace `.item()` logic with tensor masks, run the targeted parity pytest, and capture Option B artifacts (`optionB_impl`, `carryover_cache_validation`, `carryover_probe`).
- Follow-up: Ralph to implement Option B cache plumbing per new memo, then execute M2h validation steps (pytest/gradcheck/trace) before advancing to scaling rerun.

## 2025-12-10 (galph loop - M2g.2b scalar regression review)
- Coin flip=heads → reviewed Ralph’s most recent code commit f84fd5e; it reverted `apply_phi_carryover`/`store_phi_final` to scalar indices and introduced a `.item()` validity gate, breaking the Option B batch plan and the differentiability rule.
- Updated `plans/active/cli-noise-pix0/plan.md` status snapshot with the regression note and added checklist row M2g.2b to demand tensor `(slow_indices, fast_indices)` signatures without `.item()` before further wiring.
- Refreshed `docs/fix_plan.md` Next Actions bullet 0 so undoing the scalar regression is explicitly the first task under CLI-FLAGS-003.
- Authored `input.md` (Parity mode, 100 lines) instructing Ralph to complete M2g.2b: restore batched signatures, remove the `.item()` gate, capture artifacts under `reports/.../carryover_cache_plumbing/`, run the targeted parity pytest, and update diagnosis docs/attempt logs.
- Follow-up for Ralph: refactor the helpers back to tensor indices, keep vectorised execution intact, archive logs + plan updates, then proceed to M2g.3 wiring once the parity test and documentation landing pads are ready.

## 2025-12-10 (galph loop - M2g cache wiring prep)
- Coin flip=heads → reviewed Ralph commits 678cbf4/1de347c; batched cache signatures restored and Attempt #160 logged with docs update.
- Updated `plans/active/cli-noise-pix0/plan.md` status snapshot to acknowledge commit 678cbf4 and flipped checklist item M2g.2b to [D]; emphasised that wiring (M2g.3+) remains the blocker.
- Synced `docs/fix_plan.md` Next Actions (lines 3383-3391) with the new focus on Option B cache plumbing so the ledger mirrors the plan after M2g.2b completion.
- Authored fresh `input.md` (Parity mode) directing Ralph to execute M2g.3-M2g.4: allocate per-pixel caches, thread `(slow_indices, fast_indices)` through the simulator, run the mapped pytest selector, and archive artifacts under `reports/.../carryover_cache_plumbing/` with env metadata.
- Follow-up for Ralph: build the Option B cache tensors, wire them through `_compute_physics_for_position`, capture the targeted parity test output, then proceed to M2g.5 tooling updates once cache hits are proven.

## 2025-12-10 (galph loop - M2g Option B design gating)
- Re-read required specs/arch/testing docs plus artifacts: `plans/active/cli-noise-pix0/plan.md`, `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T145905Z/m2g_blocker/analysis.md`, `reports/.../20251208_option1_refresh/analysis.md`, `docs/fix_plan.md`, `specs/spec-a-core.md:205-233`, `docs/bugs/verified_c_bugs.md:166-204`.
- Coin flip=heads → reviewed Ralph’s recent commits (`5fbda7a`, `678cbf4`, `1de347c`); Attempt #161 reverted after documenting Option B blocker, no regressions.
- Determined plan drift: fix_plan still waiting on architecture decision despite Option B selection; plan lacked pre-implementation design steps.
- Updated `plans/active/cli-noise-pix0/plan.md` Next Actions to add M2g.2c design memo + M2g.2d ROI prototype prerequisites before wiring, inserted new checklist rows, and noted Attempt #161 blocker context.
- Synced `docs/fix_plan.md` Next Actions with the new design/prototype requirements and clarified downstream sequencing.
- Authored new `input.md` (Mode: Docs) directing Ralph to produce the Option B batch-design memo + 4×4 ROI prototype, capture artifacts, and run the collect-only pytest selector before further implementation.
- Follow-up for Ralph: create the timestamped design/prototype artifacts, update fix_plan Attempts with findings, then resume M2g.3 cache allocation once the design is validated.

## 2025-12-10 16:05Z (galph loop - M2g cache implementation kickoff)
- Git already synced; reread core specs/arch/testing docs plus Option B design/prototype artifacts before planning per SOP.
- Coin flip=heads → reviewed Ralph commit 2cbbf65 (Option B design + prototype). Work productive and aligned with plan.
- Updated `plans/active/cli-noise-pix0/plan.md` Status Snapshot with Attempt #162 completion, marked M2g.2c/M2g.2d [D], and expanded M2g.1 checklist guidance to reference the new design memo.
- Refreshed `docs/fix_plan.md` Next Actions to emphasise M2g.1 checkpoint, M2g.3 cache allocation, and M2g.4 simulator wiring before tooling/docs steps.
- Authored `input.md` (Mode: Parity, 101 lines) instructing Ralph to implement Option B cache tensors/wiring, capture artifacts under `carryover_cache_plumbing/<ts>/`, run the targeted pytest selector, and log diagnostics for M2g.5 preparation.
- Commit `1ac720e` pushed (`SUPERVISOR: CLI-FLAGS-003 M2g planning update - tests: not run`).
- Follow-up: Ralph to deliver M2g.3/M2g.4 implementation with artifacts + pytest log, update fix_plan Attempts, and prep notes for upcoming M2g.5 tooling changes.

## 2025-12-11 (galph loop - M2h evidence redirect)
- Confirmed commit `fa0167b` wires Option B cache but parity still fails (`F_latt` rel err 1.57884) and omega trace tap crashes; ran targeted pytest locally to verify.
- Updated `plans/active/cli-noise-pix0/plan.md` status snapshot with Attempt #163, set M2g.3/M2g.4 to [P], and rewrote Next Actions toward M2h diagnostics.
- Refreshed `docs/fix_plan.md` (First Divergence + Next Actions) and logged Attempt #163 with artifact paths and failure analysis.
- Replaced `input.md` to direct Ralph to build a new `carryover_cache_validation/<ts>/` bundle (CPU pytest log, env metadata, diagnostics) before touching simulator code.
- Follow-up for Ralph: capture the CPU parity log with full metadata, document current F_latt/omega issues, append results to fix_plan Attempts, then proceed to CUDA/gradcheck probes once evidence is archived.

## 2025-10-08 16:24Z (galph loop - M2h CUDA/gradcheck prep)
- Reviewed latest repo state; no upstream sync changes. Coin flip=heads → inspected Ralph commits fa0167b and 6c0d163; wiring landed but parity still fails with F_latt sign flip.
- Analysis: row-wise Option B cache currently indexes the current `(slow, fast)` slot; no evidence of previous-pixel substitution, explaining carryover failure. Plan/fix_plan Next Actions updated with new Step 4 cache-index audit.
- Authored input.md (Mode: Parity) directing Ralph to capture CUDA parity + gradcheck evidence under a new carryover_cache_validation timestamp, snapshot cache tensors pre/post, and log whether cached data reflects previous pixels.
- Reminders for next loop: review new diagnostics bundle, confirm cache-index conclusions, then advance to M2i trace rerun once M2h.2/M2h.3 marked [D].
## 2025-10-08 16:37Z (galph loop - M2h.2 device fix gating)
- Focused on CLI-FLAGS-003 Phase M2h after reviewing core docs, plans, and latest diagnostics; confirmed CUDA trace blocker stems from `_apply_debug_output` creating CPU tensors via bare `torch.tensor(...)` (lines 1487-1519).
- Catalogued three hypotheses: HKL tensor factories lacking device/dtype, interpolation debug tensors inheriting CPU defaults, and sincg inputs running off-device; triage via code review + python snippets (`torch.tensor(...).device` + compiled sincg warning) corroborated each.
- Authored new input.md directing Ralph to patch simulator debug tensor factories, rerun the CUDA trace harness, capture CPU+CUDA artifacts, and log cache snapshots before proceeding to gradcheck. `input.md` Do Now now points at the CUDA harness command and collect-only pytest selector.
- No plan edits needed; M2h.2 guidance in plans/active/cli-noise-pix0/plan.md already reflects the blocker. Fix_plan remains aligned.
- Follow-up for Ralph: implement device/dtype-neutral tensor creation in `_apply_debug_output`, rerun CUDA + CPU harness runs into timestamped directories, update diagnostics/env logs, and keep docs/fix_plan.md Attempts current with outcomes.

## 2025-10-08 16:56Z (galph loop - M2h.3 gradcheck directive)
- Marked CLI-FLAGS-003 Phase M2h.2 complete and shifted plan focus to M2h.3 gradcheck; updated plans/active/cli-noise-pix0/plan.md lines 29 & 74 to reference Attempt #166 and new artifact expectations.
- Refreshed docs/fix_plan.md Next Actions to highlight the gradcheck probe (M2h.3) now that CUDA evidence is archived.
- Authored input.md (Mode: Parity) directing Ralph to build a timestamped gradcheck harness, archive CUDA/CPU logs, capture metadata, and keep the loop evidence-only.
- Follow-up for Ralph: execute M2h.3 gradcheck per input.md, store artifacts under reports/.../<timestamp>_carryover_cache_validation/, and log results in docs/fix_plan.md Attempts before moving to M2i.1.

## 2025-12-12 (galph loop - M2i.1 trace directive)
- Coin flip=heads → reviewed Ralph commits 8255686 and 4c4b62b; device-neutral debug tensors landed and gradcheck evidence now archived.
- Updated `plans/active/cli-noise-pix0/plan.md` status snapshot (lines 20-33) to record Attempt #167 and rewrote Next Actions around M2i.1–M2g.6; Phase M2h.3 set to [D].
- Added Attempt #167 to `docs/fix_plan.md` with gradcheck metrics and refreshed Next Actions (lines 461-467) to prioritise the CPU ROI trace, cache tooling patch, and documentation sync.
- Authored `input.md` (Mode: Parity, 100 lines) directing Ralph to run the ROI harness, archive a complete evidence bundle under `carryover_probe/<ts>/`, and log results before touching simulator code.
- Follow-up: Ralph to execute the harness command, capture trace/diff/metrics + provenance files, update docs/fix_plan.md Attempts with the new timestamp, and keep the workspace clean for the next parity diagnostics.

## 2025-12-12 (galph loop - M2i.2 metrics prep)
- Sync clean; coin flip=HEADS → reviewed Ralph commits 4c4b62b/882dd04 (evidence bundles only, no regressions).
- Marked CLI-FLAGS-003 Phase M2i.1 complete in `plans/active/cli-noise-pix0/plan.md` (artifact 20251008T172721Z) and refreshed Next Actions to spotlight M2i.2 metrics work.
- Updated `docs/fix_plan.md` CLI-FLAGS-003 Next Actions with the same completion note so downstream loops stop re-running M2i.1.
- Authored new Parity-mode `input.md` directing Ralph to run M2i.2 (compare_scaling_traces.py + diff bundle) and update `lattice_hypotheses.md`; artifact pattern specified under metrics_refresh/.
- Pending follow-up: Ralph to execute the metrics refresh, produce diff/metrics + ledger updates, then we can tackle trace tap fixes (M2g.5).

## 2025-10-08 (galph loop - M2g.5 tooling directive)
- Regenerated `compare_scaling_traces.py` metrics using `carryover_probe/20251008T172721Z/trace_py.log`; new evidence stored under `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T174753Z/` with commands, metrics, metadata, and SHA256 bundle.
- Appended 2025-10-08T17:47:53Z entry to `lattice_hypotheses.md` noting the rerun still diverges (I_before_scaling rel δ ≈ -0.9999995) and pointing next work toward trace tooling.
- Added Attempt #170 to `docs/fix_plan.md` and refreshed Next Actions bullet 1 plus plan rows (M2i table) to reference the new artifacts while keeping M2i.2 gate open.
- Authored new input.md (Parity mode) directing Ralph to implement M2g.5 trace tooling patch, rerun CPU/CUDA harnesses into `trace_tooling_patch/<timestamp>/`, and update fix_plan attempts after capturing artifacts.
- Follow-up: Ralph to patch `trace_harness.py` for cache-aware taps, produce the new trace_tooling_patch bundle, and log Attempt #171 before moving on to M2g.6/M2g.5 documentation.

## 2025-12-12 (galph loop - M2g.6 documentation prep)
- Git already up to date; reviewed required spec/arch/testing docs plus active plans before analysis. Coin flip=heads → commit review limited to evidence-only Attempt #171 (trace tooling verification) and prior sync commits; no regressions observed.
- Updated `plans/active/cli-noise-pix0/plan.md` status snapshot to acknowledge Attempt #171 and rewrote the Next Actions list to remove the completed M2g.5 tooling task. M2g.6, cache index audit, and Phase N prep are now the leading items; M2g.5 row marked [D] with artifact path `trace_tooling_patch/20251008T175913Z/`.
- Revised `docs/fix_plan.md` CLI-FLAGS-003 Next Actions to mirror the plan (emphasising documentation sync, cache index diagnostics, and Phase N preparation). Authored a new 100-line input.md (Mode: Docs) directing Ralph to update `phi_carryover_diagnosis.md`, flip plan row M2g.6 to [D], add a ledger attempt entry, and rerun collect-only pytest for CLI scaling tests.
- Follow-up for Ralph: perform the M2g.6 documentation sync citing Attempt #171 evidence, update plan/fix_plan accordingly, and keep M2i.2 metrics gate noted as red before advancing to the cache index audit bundle.

## 2025-10-08 (galph loop - M2i.2 parity trace directive)
- Logged Attempt #173 in docs/fix_plan.md with new rotated-lattice divergence analysis (reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T182512Z/).
- Updated plans/active/cli-noise-pix0/plan.md Next Actions bullet 0 to reference the new memo; M2i.2 remains gated pending c-parity trace.
- Authored relocation of input.md directing Ralph to rerun trace_harness.py with --phi-mode c-parity and refresh scaling metrics once rot_* vectors align.
- Follow-up: Ralph to capture c-parity trace + compare_scaling_traces bundle, then update fix_plan Attempts with new timestamp and metrics before advancing to Phase N.

## 2025-12-13 (galph loop - Shim removal planning pivot)
- Created `plans/active/phi-carryover-removal/plan.md` to retire the φ carryover shim (Phase-format context + A–E roadmap).
- Updated docs/fix_plan.md (CLI-FLAGS-003 status/next actions now reference the new plan) and refreshed `plans/active/cli-noise-pix0/plan.md` Next Actions to delegate to the removal effort.
- Authored input.md (Mode: Docs, 109 lines) directing Ralph to execute Phase A inventory tasks (collect-only pytest + baseline inventory artifacts under `reports/.../phase_phi_removal/phase_a/`).
- Follow-up: Ralph to produce Phase A artifacts (collect log, baseline_inventory.md, commands/env/sha256) and log a freeze note next loop before Phase B prep begins.

## 2025-12-13 (galph loop - Phase B shim removal planning)
- Expanded `plans/active/phi-carryover-removal/plan.md` Phase B into B0–B5 tasks (design bundle, CLI/config removal, tooling cleanup, regression sweep, ledger sync) with artifact expectations under `reports/2025-10-cli-flags/phase_phi_removal/phase_b/`.
- Refreshed `docs/fix_plan.md` CLI-FLAGS-003 Next Actions and `plans/active/cli-noise-pix0/plan.md` Next Actions to align with the new Phase B checklist.
- Rewrote `input.md` (Mode: Docs) to have Ralph execute Plan B0 (design review + collect-only baseline) prior to code edits.
- Follow-up: Expect Ralph next loop to produce the Phase B design bundle and update fix_plan Attempts before starting B1–B3 implementation.

## 2025-12-14 (galph loop - Phase B1 directive refresh)
- Verified git baseline (already up to date) and reviewed B0 design bundle `reports/2025-10-cli-flags/phase_phi_removal/phase_b/20251008T185921Z/` plus plan/fix_plan context.
- Marked `plans/active/phi-carryover-removal/plan.md` Phase B0 as [D] with explicit status line, and updated `plans/active/cli-noise-pix0/plan.md` Next Actions to start at B1 now that the design artifact exists.
- Authored new 129-line `input.md` (Mode: Docs) directing Ralph to execute Phase B1 CLI surface removal with detailed artifact/test cadence and doc touchpoints; committed as `SUPERVISOR: Phase B1 directive refresh - tests: not run`.
- Follow-ups: Ralph to remove the CLI flag per Phase B1, capture the specified artifact bundle, update docs/fix_plan.md Attempt logs, and prep inventory notes for B2 targets.

## 2025-12-14 (galph loop - Phase B2 handoff prep)
- Coin flip=heads → reviewed Ralph’s latest implementation commit (340683f). Change cleanly removes the CLI flag, keeps targeted tests green, and deferred doc sync; no regressions spotted.
- Updated `plans/active/phi-carryover-removal/plan.md` to note B1’s partial completion (code done, docs pending) and kept B2/B3 guidance intact; `plans/active/cli-noise-pix0/plan.md` Next Actions now call out B1 doc sync + B2/B3 execution explicitly.
- Revised `docs/fix_plan.md` CLI-FLAGS-003 Next Actions to break out B1 documentation, B2/B3 removals, B4 regression sweep, and B5 ledger sync as separate bullets.
- Replaced `input.md` (Mode: none, ~110 lines) directing Ralph to finish the B1 doc cleanup and execute Phase B2 plumbing removal, with explicit artifact/test cadence.
- Follow-up: Ralph to update README_PYTORCH.md / prompts/supervisor.md / docs/bugs entry, delete the remaining `phi_carryover_mode` plumbing plus associated tests, capture the Phase B bundle, and log the attempt before we evaluate B3.

## 2025-12-14 (galph loop - C1 coverage audit setup)
- Confirmed repo synced (feature/spec-based-2) and reviewed phi-carryover removal artifacts (`reports/2025-10-cli-flags/phase_phi_removal/phase_b/20251008T193106Z/`).
- Updated `plans/active/phi-carryover-removal/plan.md` to mark rows B0–B5 done and shift focus to row C1 coverage audit (plan lines 29-49).
- Refreshed `plans/active/cli-noise-pix0/plan.md` status snapshot/Next Actions to call out row C tasks (lines 17-33) and keep scaling work gated pending coverage/doc cleanup.
- Revised `docs/fix_plan.md` CLI-FLAGS-003 Next Actions (lines 451-465) so Ralph now targets the row C1 audit + documentation sweeps; legacy B-phase bullets removed.
- Authored new `input.md` (Mode: Docs) instructing Ralph to run collect-only pytest for row C1, capture artifacts under `reports/.../phase_phi_removal/phase_c/<ts>/`, and log coverage findings.
- Follow-up: Ralph to execute the coverage audit per plan row C1, document gaps in `coverage_audit.md`, and update fix_plan Attempts with the new evidence; next loops can tackle rows C2/C3 once the audit passes.

## 2025-12-14 (galph loop - Phase C2/C3 prep)
- Confirmed residual shim references: `docs/bugs/verified_c_bugs.md:166-192` still says plumbing "in progress", `tests/test_cli_scaling_parity.py` instantiates deleted `phi_carryover_mode`, and `src/nanobrag_torch/models/crystal.py:1238-1274` docstrings describe cache-based c-parity.
- Refreshed `plans/active/phi-carryover-removal/plan.md` Phase C rows with explicit file targets (docs entry, parity test retirement, crystal docstrings) and synced `docs/fix_plan.md` Next Actions accordingly.
- Authored new `input.md` (Mode: Docs) directing Ralph to execute Phase C2/C3 sweep, capture artifacts under `reports/.../phase_phi_removal/phase_c/<ts>/`, run collect-only on `tests/test_cli_scaling_phi0.py`, and update fix_plan attempts.
- Follow-up: Ralph to update docs/tests per Phase C guidance, drop or rewrite `tests/test_cli_scaling_parity.py`, scrub parity-shim diagnosis reports, and log summary + SHA256 in the new Phase C timestamp before progressing to Phase D evidence.

## 2025-12-14 (galph loop - Phase D proof-of-removal planning)
- Coin flip=heads → reviewed Ralph’s latest commit 85dc304 (Phase C2/C3 doc sweep); work remains aligned with plan and introduced no regressions.
- Expanded `plans/active/phi-carryover-removal/plan.md` Phase D/E sections with concrete D1a–D1c checklist items (trace harness command, pytest proof, rg sweep) and optional watch tasks; refreshed `docs/fix_plan.md:451-467` Next Actions to point at the new checklist.
- Replaced `input.md` (Mode: Parity) instructing Ralph to execute Phase D1a spec-mode trace runs, gather targeted pytest evidence, collect the `rg` scan, and stash artifacts under `reports/2025-10-cli-flags/phase_phi_removal/phase_d/${STAMP}/`.
- Follow-up: Expect Ralph to produce the Phase D bundle next loop, update fix_plan Attempts with the timestamped directory, and prepare for D2 ledger sync.

## 2025-12-14 (galph loop - Phase D harness unblock)
- Git synced clean (feature/spec-based-2 up to date) and reviewed Attempt #181 blocker before planning.
- Updated `plans/active/phi-carryover-removal/plan.md` Phase D with new row D0 requiring the trace harness to drop `phi_carryover_mode` plumbing; refreshed `docs/fix_plan.md` and `plans/active/cli-noise-pix0/plan.md` next actions to point Ralph at D0→D1 sequence.
- Rewrote `input.md` (Mode: Parity) directing Ralph to patch the harness, rerun Py/C traces into a fresh Phase D timestamp, execute `pytest -v tests/test_cli_scaling_phi0.py`, and capture the ``rg "phi_carryover"`` sweep.
- Follow-up: expect Ralph to land the harness edit, produce the Phase D artifact bundle, and then update ledger entries before we pivot back to the scaling parity work.

## 2025-12-14 (galph loop - D1 proof bundle setup)
- Git already synced with origin; core docs + active plans reviewed per SOP before analysis.
- Coin flip=heads → inspected Ralph commits 9f462ab (blocker summary) and 946226e (harness cleanup). Harness now spec-only; no regressions observed.
- Updated `plans/active/phi-carryover-removal/plan.md` row D0 to [D] so the checklist reflects the completed harness refresh.
- Authored new `input.md` (Mode: Parity) directing Ralph to capture the D1 proof-of-removal bundle: fresh Py trace via `trace_harness.py`, matching C trace with `-trace_pixel 685 1039`, run `scripts/validation/compare_scaling_traces.py`, execute `pytest -v tests/test_cli_scaling_phi0.py`, perform the `rg "phi_carryover"` sweep, and store everything under `reports/2025-10-cli-flags/phase_phi_removal/phase_d/$STAMP/` with summary/metrics/sha256.
- Follow-up for Ralph: generate the new artifact bundle, then proceed to ledger sync (docs/fix_plan.md update + plan archival) once the proof is logged.

## 2025-12-14 (galph loop - Phase D2 ledger prep)
- Updated `plans/active/phi-carryover-removal/plan.md:53-72` to mark D1a–D1c [D] and record the Attempt #183 evidence path; added status snapshot so remaining work clearly shows D2–D3.
- Refreshed `docs/fix_plan.md:459-465` Next Actions to highlight D2 (ledger sync) and D3 (handoff) as the only open items while referencing the Phase D bundle.
- Authored a new `input.md` (Mode: Docs, 104 lines) directing Ralph to execute Phase D2: update fix_plan attempts, archive `plans/active/cli-phi-parity-shim/plan.md`, append a ledger note in `reports/2025-10-cli-flags/phase_phi_removal/phase_d/`, run pytest collect-only, and log results.
- Next loop expectation: Ralph performs the ledger sync per plan (update fix_plan attempts, move the shim plan to archive, add ledger_sync.md + commands/logs), runs `pytest --collect-only -q tests/test_cli_scaling_phi0.py`, and records the outcome before we tackle Phase D3 handoff.
## 2025-10-08 (ralph loop i=181 — Phase D2 ledger sync)
- Executed documentation-only loop per input.md Mode: Docs directive.
- Updated `docs/fix_plan.md` CLI-FLAGS-003 section: added Attempt #184 entry (Phase D2 complete), updated Next Actions to mark D2 ✅ and leave only D3 open, changed refresh date from 2025-12-14 to 2025-10-08.
- Archived shim plan: `git mv plans/active/cli-phi-parity-shim/plan.md → plans/archive/cli-phi-parity-shim/plan.md` with comprehensive 19-line closure note prepended (references Phase D1 bundle, explains archival rationale, provides cross-links).
- Updated `plans/active/phi-carryover-removal/plan.md`: marked row D2 [D] with completion summary (line 64), refreshed Status Snapshot (line 56) to note D2 done.
- Verified pytest collection: `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py` → 2 tests in 0.79s.
- Created `reports/2025-10-cli-flags/phase_phi_removal/phase_d/ledger_sync.md` documenting changes, verification checklist, and next actions.
- Phase D2 exit criteria met: fix_plan shows Attempt #184, Next Actions updated, shim plan archived with closure note, pytest collection verified.
- Follow-up for next supervisor loop: Prepare Phase D3 `input.md` handoff directing Ralph to `plans/active/cli-noise-pix0/plan.md` Phase L scaling tasks; shim removal work complete, focus shifts entirely to `-nonoise`/`-pix0` deliverables.

## 2025-12-14 (galph loop - D3 handoff + scaling pivot)
- Reviewed phi-carryover removal plan and fix_plan; only D3 remained open while CLI scaling tasks waited. Long-term Goal 1 now satisfied after this handoff.
- Updated `plans/active/phi-carryover-removal/plan.md:109` marking D3 [D] with note that today’s input redirects work to the scaling track and logs closure in galph_memory.
- Refreshed `docs/fix_plan.md:461-466` Next Actions to record D3 completion and elevate Phase M2g/M2h as the active blockers (Option B cache fix + grad/device validation).
- Authored new `input.md` (Mode: Parity) guiding Ralph to execute Phase M2g Option B cache plumbing, re-run the trace harness, capture metrics under `reports/2025-10-cli-flags/phase_l/scaling_validation/20251214_optionB_patch/`, and update fix_plan attempts post-fix.
- Follow-up for Ralph: implement the pixel-indexed φ-cache per Option B design, rerun CPU/CUDA parity evidence and targeted pytest, then log Attempt # next with artifact paths before progressing to M2h.
## 2025-12-15 (galph loop - Phase M1 spec baseline reset)
- Rewrote `plans/active/cli-noise-pix0/plan.md` to reflect post-shim spec-only workflow; Phase M now directs fresh spec-mode baseline (M1), analysis (M2), probes (M3), fix (M4), validation (M5), and ledger sync (M6). Optional guardrails captured under Phase P.
- Updated `docs/fix_plan.md:451-470` Next Actions to match the new plan (Phase M1–M6) and removed stale Option B cache guidance.
- Authored `input.md` (Mode: Parity) instructing Ralph to execute Phase M1: generate a new spec-mode scaling bundle via `trace_harness.py`, run `compare_scaling_traces.py`, capture pytest collect logs, and store artifacts under `reports/2025-10-cli-flags/phase_l/scaling_validation/$STAMP/spec_baseline/`.
- Follow-up expectation: Ralph completes Phase M1 bundle, records metrics/analysis, and updates `lattice_hypotheses.md` before we move to Phase M2 diagnostics.

## 2025-10-08 (galph loop - M2 analysis directives)
- Refreshed `plans/active/cli-noise-pix0/plan.md` Phase M snapshot: marked M1 [D], noted 14.643% I_before_scaling deficit from bundle `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/`, and tightened M2 guidance (analysis_20251008T212459Z.md + lattice_hypotheses.md update + summary refresh).
- Authored new `input.md` (Mode: Docs, 100 lines) directing Ralph to execute CLI-FLAGS-003 Phase M2 analysis: regenerate summary via `compare_scaling_traces.py`, document factor breakdown, update hypotheses ledger, refresh sha256/commands/run_metadata, log Attempt #186, and run pytest collect-only.
- No code changes expected next loop; focus is evidence bundling under the existing spec_baseline directory.

## 2025-10-08 (galph loop - Phase M3 probe planning)
- Updated `plans/active/cli-noise-pix0/plan.md` to mark M2 [D] and expand Phase M3 into tasks M3a–M3d (per-φ logging, sincg sweep, single-φ run, rotation audit). Status snapshot now cites Attempt #186 evidence.
- Synced `docs/fix_plan.md:461-467` Next Actions with the new M3 task bundle; emphasis on storing probes under `phase_m3_probes/` with sha256 + summary.
- Authored `input.md` (Mode: Parity) directing Ralph to execute those probes, capture fresh traces, and update fix_plan Attempt #187 after running targeted pytest.
- Follow-up: Ralph to produce the Phase M3 artifact bundle (trace_py_phi, sincg_sweep, phistep1, rotation_audit, summary) and log results before M4 implementation begins.

## 2025-12-16 (galph loop - Phase M4 normalization planning)
- Synced with origin (no conflicts) then re-read `docs/index.md`, `specs/spec-a-core.md`, `arch.md`, `docs/development/c_to_pytorch_config_map.md`, `docs/debugging/debugging.md`, `docs/development/testing_strategy.md`, and `docs/fix_plan.md` per SOP before analysis.
- Assessed long-term goals: φ-carryover removal closed through Phase D; CLI-FLAGS-003 Phase M normalization remains the top blocker, with vectorization/delegations queued post-parity.
- Updated `plans/active/cli-noise-pix0/plan.md:60-71` to add a detailed Phase M4 checklist (M4a–M4d) covering design memo, simulator patch, parity tests, and evidence capture.
- Refreshed `docs/fix_plan.md:461-468` Next Actions bullet to reference the checklist and fix_<timestamp> artifact bundle requirements.
- Authored new `input.md` (Mode: Parity) instructing Ralph to execute M4a–M4d, run targeted pytest + compare_scaling_traces commands, and store artifacts under `reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/`.
- Follow-up for Ralph: implement the normalization division in `src/nanobrag_torch/simulator.py` with required `nanoBragg.c` snippet, extend per-φ logging, regenerate traces, update fix_plan/plan entries, then advance to Phase M5 after evidence is green.
## 2025-12-17 (galph loop - Phase M4d evidence planning)
- Coin flip = heads; reviewed Ralph commits 8b4c15a (initial normalization patch), d8648be (docs refresh), and fe3a328 (double-division fix). No regressions; final commit restores single `/ steps` division while preserving vectorization.
- Updated `plans/active/cli-noise-pix0/plan.md` to mark M4b/M4c [D], keep M4 overall [P], and narrow M4d guidance to the outstanding compare_scaling_traces + hypotheses artifacts.
- Refreshed `docs/fix_plan.md` CLI-FLAGS-003 section to acknowledge Attempts #188–#189 landing the fix, reframe Next Actions around M4d evidence capture, and remove obsolete double-division warnings.
- Authored new `input.md` (Mode: Parity, 100 lines) directing Ralph to rerun `trace_harness.py`, execute `scripts/validation/compare_scaling_traces.py`, capture diff_trace + updated lattice_hypotheses, refresh sha256 manifests, and log Attempt #190 before moving to Phase M5.
- No new plan files opened; focus stays on completing Phase M4d evidence before CUDA/gradcheck (M5) begins.
- Follow-up: Ralph to populate `reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/` with trace, metrics, diff summary, updated commands/env/sha256, close Hypothesis H4, and update fix_plan/galph_memory accordingly.

## 2025-12-16 (galph loop - Phase M4 normalization planning)
- Git sync remained clean; revisited core spec/arch/testing docs plus active plans per SOP.
- Authored Phase M4a design memo (`reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T223046Z/design_memo.md`) confirming Attempt #188’s double `/ steps` regression and restating the C contract.
- Updated `plans/active/cli-noise-pix0/plan.md` (M4a marked [D]) and logged CLI-FLAGS-003 Attempt #192 in `docs/fix_plan.md`, reopening M4b–M4d with explicit normalization fix guidance.
- Rewrote `input.md` (Mode: Parity) steering Ralph to land the single-division normalization fix, rerun targeted pytest + compare_scaling_traces, and publish a fix_<timestamp> bundle.
- Follow-up next loop: verify the new Phase M4 evidence bundle, then schedule CUDA/gradcheck work for Phase M5 before moving to nb-compare.

## 2025-12-18 (galph loop - Phase M5a instrumentation kickoff)
- Git pull --rebase returned "Already up to date"; repo clean before edits.
- Coin flip = heads: reviewed recent Ralph commit 65a9dd2 (reports-only) — normalization evidence captured, no regressions.
- Updated `plans/active/cli-noise-pix0/plan.md` by clarifying M4d [P] requirements and introducing Phase M5 (M5a–M5e) for φ-rotation realignment.
- Synced `docs/fix_plan.md` Next Actions with the new Phase M5 sequence and adjusted M4d guidance to require a parity-green rerun before closure.
- Authored `input.md` (Mode: Parity) directing Ralph to execute Phase M5a: extend trace harness output, capture enhanced per-φ rot_* traces under `fix_${TS}`, run pytest collect-only, and log artifacts/attempts.
- Follow-up: Expect enhanced rot_* traces plus updated fix_plan Attempt entry next loop; queue M5b rotation design memo afterward.

## 2025-10-08 (galph loop - Phase M5b design memo)
- git pull --rebase returned clean; reviewed core docs plus active plans before analysis per SOP.
- Coin flip = heads: inspected Ralph commits 279b5e0 (enhanced per-φ traces) and 65a9dd2 (reports upload). Evidence loop productive; noted duplicated `reports/2025-10-cli-flags/phase_l/per_phi/reports/...` subtree to address during parity closure.
- Authored `reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T232018Z/rotation_fix_design.md` capturing φ rotation parity plan (Rules #12/#13, C snippet, verification steps).
- Updated `plans/active/cli-noise-pix0/plan.md` marking M5b [D] with new artifact reference; docs/fix_plan.md Attempt #194 logs design memo + action items for M5c.
- Replaced `input.md` with Parity-mode instructions directing Ralph to implement M5c (dual-rotation pipeline), rerun compare_scaling_traces, and document results; highlighted nested reports duplication for follow-up.

## 2025-12-19 (galph loop - Phase M5c implementation prep)
- Sync: `timeout 30 git pull --rebase` returned "Already up to date"; no conflicts. Re-read mandatory docs (`docs/index.md`, `specs/spec-a-core.md`, `arch.md`, `docs/development/c_to_pytorch_config_map.md`, `docs/debugging/debugging.md`, `docs/development/testing_strategy.md`, `docs/fix_plan.md`) plus `plans/active/phi-carryover-removal/plan.md` and `plans/active/cli-noise-pix0/plan.md` before analysis.
- Long-term goals: φ-carryover removal closed through Phase D with only watch tasks E1/E2 pending; primary blocker remains CLI-FLAGS-003 Phase M5 (rotation parity). Vectorization and pyrefly initiatives stay deferred until scaling parity is green.
- Coin flip = heads: reviewed Ralph commits 279b5e0 (Phase M5a traces) and 7ad8f60 (Phase M5d evidence run); artifacts consistent, no regressions, but duplicated `reports/.../per_phi/reports/...` tree still outstanding for cleanup during M5d.
- Focus selection: stayed on CLI-FLAGS-003 Phase M5c since Phase M5a/M5b deliverables now complete and M5c is the next gating step toward resolving the `I_before_scaling` deficit (~14.6%). No new plan needed; existing `plans/active/cli-noise-pix0/plan.md` already captures detailed checklist.
- Actions: refreshed `input.md` (Parity mode) directing Ralph to implement the dual real/reciprocal rotation pipeline, rerun trace harness + compare_scaling_traces, execute targeted pytest, update lattice_hypotheses, and log Attempt #195 with full artifact bundle. Highlighted required evidence paths and risk mitigations (device neutrality, Rule #12/#13, duplicate reports note).
- Follow-up for Ralph: land M5c code changes in `crystal.py`, produce fix_<timestamp> bundle with parity-green compare output, close H4/H5 in lattice_hypotheses, update docs/fix_plan Attempt log, and document whether the per_phi directory duplication was resolved or deferred.

## 2025-11-17 (galph loop - Phase M5 pre-debug)
- Focused on CLI-FLAGS-003 M5 φ-rotation parity. Compared spec-baseline traces: PyTorch `rot_b` y-component differs by +4.6e-02 and drives `k_frac` shift (reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/trace_py_scaling.log:15 vs c_trace_scaling.log:266-271).
- Logged that PyTorch still reports tricubic `F_cell` despite supervisor command using `-nointerpolate` (trace_py_scaling.log:29 vs c_trace_scaling.log:278). Ralph must confirm flag plumbing while instrumenting per-φ traces.
- Issued input.md directing Phase M5a work: extend trace harness to emit `TRACE_PY_PHI` (k_frac, F_latt_b, F_latt) and rerun spec-mode harness into reports/.../per_phi/<stamp>/ before tackling M5c lattice fix.

## 2025-12-19 (galph loop - Phase M5c φ rotation guidance)
- Re-read mandatory specs/arch/testing docs plus Phase M5 plan; focused on CLI-FLAGS-003 scaling parity.
- Debug assessment: confirmed `Crystal.get_rotated_real_vectors` still skips dual real/reciprocal recomputation (uses static `self.V`), causing per-φ `b_star_y` drift (fix_20251008T231211Z traces) and F_latt sign flip vs C baseline (`c_trace_scaling.log`).
- Logged hypotheses: primary fix is enforcing Rule #12/#13 per-slice duality; alternative hypotheses (sincg, spindle axis normalization) deprioritized after trace review.
- Authored new `input.md` (Parity mode, 100 lines) directing Ralph to implement the duality pipeline, regenerate traces under `fix_<timestamp>`, rerun compare_scaling_traces, update lattice_hypotheses, and run targeted pytest (CPU/CUDA).
- Follow-up for Ralph: implement Phase M5c vectorized rotation + duality, capture new artifacts, update docs/fix_plan Attempt & plan row to [D], and prepare for M5d verification.

## 2025-12-20 (galph loop - Option 1 spec compliance planning)
- Git already up to date; re-read core docs (docs/index.md, specs/spec-a-core.md:204-214, arch.md, docs/development/c_to_pytorch_config_map.md, docs/debugging/debugging.md, docs/development/testing_strategy.md) plus plans/active/cli-noise-pix0/plan.md and latest reports before analysis.
- Long-term Goal 1 (φ carryover removal) verified complete through Phase D; remaining watch items E1/E2 noted. Attempt #195 landed Phase M5c rotation fix; Attempt #196 flagged C-PARITY-001 conflict.
- Selected focus: CLI-FLAGS-003 Phase M5 Option 1 bundle. Adopted Option 1 (accept spec compliance, document C bug) and refreshed plan/fix_plan to steer work toward documentation rather than more simulator edits.
- Updated `plans/active/cli-noise-pix0/plan.md` Phase M5 (M5c marked [D]; new M5d–M5g tasks for Option 1 evidence, validation script updates, regression rerun, and plan sync).
- Refreshed `docs/fix_plan.md`: new Active Focus bullet for CLI-FLAGS Option 1, updated Next Actions, and annotated Attempt #196 with the supervisor decision.
- Replaced `input.md` (Docs mode) directing Ralph to publish `option1_spec_compliance/<timestamp>/` bundle, update lattice_hypotheses & docs/fix_plan, and rerun targeted pytest; provided explicit metadata commands and compare_scaling guidance.
- Next follow-up: Ralph to execute Option 1 documentation tasks (M5d–M5g), then we reassess whether optional Phase M6 shim work is needed.

## 2025-10-09 (galph loop - M5c C-reference capture)
- Evidence task: captured nanoBragg.c snippets for misset duality and per-φ reciprocal regeneration under `reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251009T005448Z/` (includes `c_phi_rotation_reference.md`, `summary.md`, `env.json`, `commands.txt`, `sha256.txt`).
- docs/fix_plan.md: added Attempt #191 logging the new evidence bundle and rationale; CLI-FLAGS-003 history now points Ralph at the snippet before coding.
- plans/active/cli-noise-pix0/plan.md: M5c guidance now cites the captured snippet explicitly for Rule #11 docstrings.
- input.md rewritten (Parity mode) directing Ralph to implement M5c with the new reference, regenerate scaling traces, and run pytest CPU/CUDA.
- Follow-up: Ralph to implement dual rotation pipeline, produce fresh compare_scaling_traces output + per-φ trace under new timestamp, run targeted pytest, update lattice_hypotheses, and mark plan row M5c [D] once parity is green.

## 2025-10-09 (galph loop - M5e/M5f planning refresh)
- Git up to date; re-read docs/index.md, specs/spec-a-core.md, arch.md, docs/development/c_to_pytorch_config_map.md, docs/debugging/debugging.md, docs/development/testing_strategy.md, plans/active/cli-noise-pix0/plan.md, and latest Option 1 bundle before analysis.
- Focused on CLI-FLAGS-003 Phase M5 follow-ups: marked plan row M5d [D] (Attempt #196 evidence) and tightened M5f guidance to require pytest logs under option1_spec_compliance/<stamp>/tests/.
- Updated docs/fix_plan.md Next Actions to note M5d completion and highlight remaining tasks (validation-script note + archived pytest logs) ahead of optional Phase M6.
- Rewrote input.md (Docs mode, 100+ lines) instructing Ralph to update compare_scaling_traces.py docstrings, regenerate an Option 1 bundle with compare output + env/sha + test logs, run targeted pytest (CPU and GPU smoke when available), and sync plan/fix_plan once artifacts exist.
- Committed as `SUPERVISOR: CLI-FLAGS Option1 follow-up - tests: not run`; no physics changes.
- Follow-up: Ralph to execute M5e/M5f per new input, then we can close M5g and queue Phase N nb-compare once evidence lands.

## 2025-12-20 (galph loop - Phase N1 staging)
- Closed out CLI-FLAGS Phase M bookkeeping: marked Phase M4d and M5g [D] in plans/active/cli-noise-pix0/plan.md and refreshed the Status Snapshot to 2025-12-20 with Option 1 notes.
- Updated docs/fix_plan.md Active Focus + Next Actions to reflect the Phase M6 decision gate; logged that M5e–M5g are done and the next step is choosing (or skipping) the optional C-parity shim before moving to Phase N.
- Authored new input.md (105 lines, Parity mode) instructing Ralph to document the Phase M6 skip, regenerate C/PyTorch ROI float files under reports/2025-10-cli-flags/phase_l/nb_compare/<timestamp>/inputs/, and append the corresponding Attempt in docs/fix_plan.md.
- No new artifacts generated this loop (docs-only). Working tree pending commit of docs/fix_plan.md, plans/active/cli-noise-pix0/plan.md, and input.md.
- Follow-up for Ralph: execute input.md Do Now (Phase N1 ROI prep + Phase M6 skip logging), keep targeted pytest logs in the bundle, and update plan/ledger once artifacts exist.

## 2025-12-21 (galph loop - CLI nb-compare ledger prep)
- Refreshed `plans/active/cli-noise-pix0/plan.md` Phase N exit criteria to accept the documented C-PARITY-001 divergence (correlation ≥0.98, sum_ratio noted) and marked N2 [D]; N3 now directs ledger updates before the supervisor rerun.
- Updated `docs/fix_plan.md` Next Actions to call out the Option 1 acceptance ledger entry and plan sync; no new Attempt appended yet (reserved for Ralph’s loop).
- Authored new `input.md` (Docs mode) instructing Ralph to close N3 by adding the Attempt, marking N3 [D], running pytest --collect-only, and logging the decision in galph_memory.
- Next steps for Ralph: execute the N3 ledger update, sync plan + memory, then we can queue the supervisor command rerun (Phase O).

## 2025-12-22 (galph loop - Phase O supervisor prep)
- Git remained clean; re-read required spec/arch/testing docs, CLI plan, and 20251009T020401Z nb-compare analysis before selecting focus.
- Focus set to CLI-FLAGS-003 Phase O. Updated `plans/active/cli-noise-pix0/plan.md` Status Snapshot with expected Option 1 metrics and expanded O1–O3 guidance to include the exact nb-compare command, artifact checklist, and archival notes.
- Refined `docs/fix_plan.md` Next Actions bullet to spell out the supervisor rerun command, required captures, and expectation that correlation≈0.985 / sum_ratio≈1.16e5 (C-PARITY-001) be documented in the forthcoming Attempt.
- Regenerated `input.md` (Docs mode, 115 lines) directing Ralph to run the supervisor nb-compare with threshold 0.98, capture analysis/test artifacts, update plan + ledger (VG-5), and mirror the bundle to the archive; appended detailed checklists for pre-run, outputs, analysis, and optional CUDA evidence.
- Working tree clean post-commit `SUPERVISOR: CLI-FLAGS Phase O prep - tests: not run`; ready for Ralph to execute Phase O1–O3.

## 2025-12-22 (galph loop - Phase O callchain directive)
- Git up to date; reread required spec/arch/testing docs plus CLI plan and the supervisor analysis bundle before selecting focus.
- Chose Review/housekeeping on CLI-FLAGS-003 (Plan Phase O). Added a "Phase O Blocker Diagnostics" bullet in docs/fix_plan.md:475 directing Ralph to run the callchain workflow (initiative_id cli-flags-o-blocker) and compare steps/normalization between Option 1 ROI and supervisor bundles.
- Authored input.md (Parity mode, 100 lines) instructing Ralph to execute prompts/callchain.md with the specified analysis question, capture artifacts under reports/cli-flags-o-blocker/, diff steps values, run pytest --collect-only, and log a new Attempt summarising findings.
- Follow-up for Ralph: complete the callchain deliverables, document effective steps/normalization factors across ROI vs supervisor runs, update docs/fix_plan.md Attempt history, and leave the bundle ready for the next implementation loop.

## 2025-12-22 (galph loop - Phase O closure prep)
- Updated docs/fix_plan.md Active Focus to reflect Phase O wrap-up and bumped the ledger timestamp to this loop (2025-12-22, galph #204).
- Refreshed plans/active/cli-noise-pix0/plan.md status snapshot: Phase O supervisor rerun now accepted; O1 marked [D]; O2/O3 describe ledger + archive tasks with Attempt #202/#203 references.
- Authored new input.md (Docs mode) directing Ralph to log the VG-5 Attempt, update the supervisor analysis banner, mirror the 20251009T024433Z bundle into reports/archive, and mark O2/O3 once complete; pytest collect-only proof remains the testing requirement.
- No new artifacts generated; waiting on Ralph to execute the archival/ledger updates before closing CLI-FLAGS Phase O.

## 2025-12-22 (galph loop - Phase P watch scaffolding)
- Reviewed long-term goals; identified remaining tasks as CLI-FLAGS Phase P (watch cadence) and phi-carryover removal Phase E (hygiene guard). No new plan required.
- Updated docs/fix_plan.md Active Focus to call out Phase P watch work plus phi-carryover Phase E, and rewrote CLI-FLAGS Next Actions to point at P1/P2 alongside logging requirements.
- Authored input.md (Docs mode) instructing Ralph to extend fix_plan hygiene guidance with the `rg "phi_carryover"` + trace cadence, create `reports/archive/cli-flags-003/watch.md` with the nb-compare smoke metrics, update plan rows P1/P2 & E1/E2, and run `pytest --collect-only -q`.
- Expect Ralph to produce the new watch.md, update fix_plan guidance, and record a fresh Attempt covering the completed watch tasks.

## 2025-12-22 (galph loop - Phase E handoff for vectorization)
- Updated docs/fix_plan.md Active Focus so CLI-FLAGS and PHI-CARRYOVER now describe ongoing monitoring (Phase P/E complete) instead of re-running finished tasks.
- Confirmed plans/active/cli-noise-pix0/plan.md and plans/active/phi-carryover-removal/plan.md already mark P1/P2 and E1/E2 [D]; no plan edits required.
- Authored new input.md (Perf mode) directing Ralph to execute VECTOR-TRICUBIC-001 Phase E2/E3: run cpu(+cuda) tricubic_baseline benchmarks with repeats=200 into reports/2025-10-vectorization/phase_e/perf/$STAMP/, write perf_summary.md + summary.md, then log the Attempt with timings and pytest evidence.
- Next steps for Ralph: follow the Perf-mode memo, capture benchmarks and summaries, update docs/fix_plan.md with the artifact bundle, and leave detector absorption Phase F ready for the following loop once perf evidence is in hand.

## 2025-12-22 (galph loop - Vectorization Phase F planning)
- Git already up to date. Reviewed required spec/arch/testing docs plus VECTOR-TRICUBIC plan + Phase E summary before selecting focus.
- Heads coin flip → Reviewed Ralph commits df50298 and 7358fe1 (docs/artifacts only, no regressions detected).
- Identified stale plan snapshot (Phase E2/E3 still open) and selected Planning action on VECTOR-TRICUBIC-001.
- Updated `plans/active/vectorization.md` status snapshot to mark Phases A–E complete and marked E2/E3 [D] with Attempt #12 artifact paths; refreshed docs/fix_plan.md Next Actions to note the plan update.
- Authored new input.md (Docs mode) directing Ralph to execute Phase F1 design memo with commands/env/checksums artifacts and pytest collect-only proof.
- No tests run; tree updated with plan/fix_plan/input changes only.

## 2025-12-22 (galph loop - Phase F2/F3 execution prep)
- Focused on VECTOR-TRICUBIC-001 Phase F absorption validation per docs/fix_plan.md:3364-3378; confirmed design notes already scoped the “validate existing vectorised path” shift.
- Updated docs/fix_plan.md Next Actions to drop Phase F1 (now complete) and emphasise F2 validation, F3 perf benchmarks, and F4 summarisation with explicit artifact directories (`reports/2025-10-vectorization/phase_f/...`).
- Regenerated input.md (Perf mode, 110 lines) instructing Ralph to add the nanoBragg.c absorption snippet to `_apply_detector_absorption`, extend tests/test_at_abs_001.py with CPU/CUDA + oversample parametrisation, run targeted pytest, and capture CPU/CUDA benchmarks into `phase_f/validation/` and `phase_f/perf/` bundles.
- No commands beyond git diff/status; working tree contains updated docs/fix_plan.md and input.md awaiting commit.

## 2025-12-22 (galph loop - Supervisor guard Phase A evidence)
- Ran git sync (already up to date) then captured supervisor.sh regression snapshot (Phase A1/A2) in `reports/routing/20251009T043816Z-supervisor-regression.txt`.
- Updated `docs/fix_plan.md` Attempt #2 under ROUTING-SUPERVISOR-001 with artifact path and observations; Phase A evidence now logged.
- Authored `input.md` (Docs mode) directing Ralph to deliver Phase B1 design memo, update plan/fix_plan, and run `pytest --collect-only -q` after documentation.
- Focus remains on supervisor guard plan; no code changes made this loop.

## 2025-12-22 (galph loop - Static pyrefly Phase C prep)
- Re-ran pyrefly availability checks (`rg` for `[tool.pyrefly]`, `pyrefly --version`); logged commands in new staging bundle `reports/pyrefly/20251009T044937Z/commands.txt`.
- Refreshed `plans/active/static-pyrefly.md`: Phase A/B rows marked [D], added Status Snapshot noting 20251008 baseline + new staging directory, clarified Phase C deliverables.
- Added Attempt #3 under `docs/fix_plan.md` STATIC-PYREFLY-001 summarising plan refresh and pointing at the 20251009 staging bundle.
- Authored `input.md` (Docs mode) directing Ralph to execute Phase C triage, populate severity/owner table in `reports/pyrefly/20251009T044937Z/summary.md`, validate selectors with `pytest --collect-only -q`, and update ledger/plan rows accordingly.
- Next Ralph step: complete Phase C triage using existing 20251008 pyrefly log, record severity buckets + owner selectors in 20251009 summary, update fix_plan & plan checklist, then run the collect-only proof.

## 2025-12-22 (galph loop - Phase F3 CPU perf handoff)
- Marked `plans/active/vectorization.md` Phase F2 as [D] with Attempt #14 context and clarified F3 CPU-only scope while CUDA remains blocked; focus now squarely on perf evidence capture.
- Replaced input.md (Mode: Perf) instructing Ralph to run the Phase F3 CPU benchmark, deposit artifacts under `reports/2025-10-vectorization/phase_f/perf/<timestamp>/`, rerun CPU absorption tests, and log metrics in docs/fix_plan.md Attempt + plan.
- Next supervisor follow-up: confirm Ralph lands the perf bundle, updates ledger/plan consistently, and evaluate whether throughput stays within ≤5% of the Phase A3 baseline before scheduling Phase F4 documentation.

## 2025-12-22 (galph loop - Phase F4 summary prep)
- Reviewed Ralph commit e15be51 (Attempt #15): Phase F3 CPU benchmarks completed with 0 % delta vs Phase A baseline; artifacts logged under `reports/2025-10-vectorization/phase_f/perf/20251009T050859Z/` and docs/fix_plan Attempt updated accordingly.
- Updated `plans/active/vectorization.md` Status Snapshot to reflect Phases A–F3 complete and marked row F3 [D] citing the 20251009 perf bundle; remaining work scoped to F4 summary + CUDA blocker follow-up.
- Adjusted `docs/fix_plan.md` [VECTOR-TRICUBIC-001] status to “in_progress” (Phases A–F3 complete) and rewrote Next Actions to focus on F4 summary, CUDA perf rerun once unblocked, and Phase G prep.
- Authored new input.md (Mode: Docs, 102 lines) directing Ralph to write `reports/2025-10-vectorization/phase_f/summary.md`, append commands + collect-only proof, flip plan row F4 [D], add Attempt #16, and capture `pytest --collect-only -q` output under reports/.
- Follow-up for Ralph: keep this loop documentation-only, cite both Phase F2/F3 bundles, update commands.txt, log the collect-only proof, and ensure fix_plan + plan align before marking F4 done. CUDA benchmarks remain deferred until the device-placement defect is fixed.

## 2025-12-22 (galph loop - Gradcheck Phase A audit setup)
- Re-read docs/index.md, specs/spec-a-core.md lines 204-240, docs/bugs/verified_c_bugs.md:166-204, arch.md §15, docs/development/c_to_pytorch_config_map.md, docs/debugging/debugging.md, docs/development/testing_strategy.md, docs/fix_plan.md before selecting focus; verified spec still mandates fresh φ rotations and the C-only φ-carryover bug remains quarantined in docs/bugs.
- Focus: `[AT-TIER2-GRADCHECK]` Phase A baseline audit (Mode: none, Action: Review/housekeeping). Confirmed plan `plans/active/gradcheck-tier2-completion/plan.md` still awaiting A1–A3 and that no additional plan refresh needed.
- Updated `input.md` (101 lines) directing Ralph to create a timestamped `reports/gradients/<STAMP>/` bundle with tier2_baseline.md, gradcheck_phaseA.log, env.json, commands.txt, sha256.txt (collect-only optional), then mark plan rows A1–A3 [D] and log a new Attempt in docs/fix_plan.md after running `env KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest tests/test_suite.py::TestTier2GradientCorrectness -vv`.
- No repository files besides input.md were modified; committed as `SUPERVISOR: gradcheck Phase A handoff - tests: not run` and pushed.
- Follow-up for Ralph: execute the Phase A audit exactly per input.md (capture artifacts, update plan/ledger). After completion, next loops can proceed to Phase B misset_rot_x gradcheck.

## 2025-12-22 (galph loop - Vectorization Phase G planning)
- Synced with origin (already up to date); reviewed required spec/arch/testing docs plus `plans/active/vectorization.md`, `docs/fix_plan.md`, and Phase F summary before selecting focus.
- Focused on `[VECTOR-TRICUBIC-001]` Phase G documentation closure (Action: Planning, Mode: Docs) to align with long-term Goal 3.
- Updated `plans/active/vectorization.md` Status Snapshot (2025-12-22) and expanded Phase G checklist (G1a–G2c) with detailed doc, checklist, and CUDA delegation tasks.
- Refreshed `docs/fix_plan.md` `[VECTOR-TRICUBIC-001]` Next Actions to point Ralph at the new Phase G steps and clarify that the CUDA rerun stays under PERF-PYTORCH-004 Attempt #14.
- Authored `input.md` (Docs mode, 98 lines) instructing Ralph to execute Phase G1 (doc updates + collect-only proof), log artifacts under `reports/2025-10-vectorization/phase_g/<timestamp>/`, and update ledger/plan accordingly.
- Outstanding follow-up for Ralph: perform Phase G1-G2 tasks per updated plan, record new Attempt in docs/fix_plan.md, and document CUDA follow-up delegation.

## 2025-12-22 (galph loop - Vectorization Phase G closure + Pyrefly Round 1 delegation)
- Verified HEAD already contained Ralph’s Phase G1 documentation commit (95eab47); plan still listed G1/G2 as open. Updated `plans/active/vectorization.md` Status Snapshot to mark Phases A–G2 complete and recorded CUDA rerun dependency under PERF-PYTORCH-004. Adjusted `[VECTOR-TRICUBIC-001]` Next Actions in `docs/fix_plan.md` to focus solely on GPU follow-up and noted that G2 tasks closed in this loop.
- Selected `STATIC-PYREFLY-001` Phase D Round 1 as the next focus. Authored new `input.md` (100 lines, Mode none) instructing Ralph to fix BL-1/BL-2 None guards, run targeted pytest selectors, capture a fresh pyrefly log under `reports/pyrefly/20251222T<stamp>/`, and update both the plan (Phase D1–D3) and fix_plan attempts.
- No code changes this loop; pending follow-up for Ralph: implement detector/simulator safeguards, archive artifacts with commands/env summaries, log Attempt #5 in `[STATIC-PYREFLY-001]`, flip Phase D checklist to [D], and report remaining blocker counts (expect BL-3..BL-6 outstanding).

### 2025-12-22 (galph loop - VECTOR-GAPS Phase A3 prep)
- Git synced clean; reviewed required spec/arch/testing docs plus `plans/active/vectorization-gap-audit.md`, `plans/active/vectorization.md`, and docs/fix_plan.md before selecting focus. Coin flip=heads → audited Ralph commits 37964e3 (loop inventory tooling) and 90c3379 (source vectorization). Logged GPU-device neutrality risk for the latter (torch.arange/tensor allocations defaulting to CPU) for future review.
- Focused on `[VECTOR-GAPS-002]` Phase A3 (Mode: Docs, Action: Planning). Updated `plans/active/vectorization-gap-audit.md` to mark A1/A2 [D], clarify A3 deliverables (analysis.md + annotated summary), and refreshed status snapshot. Adjusted `docs/fix_plan.md` Next Actions to center on the A3 annotation before profiling.
- Replaced `input.md` (100 lines, Docs mode) directing Ralph to produce a new Phase A3 report stamp with loop classifications, collect-only proof, and updated fix_plan attempt notes. Artifact paths now point at `reports/2026-01-vectorization-gap/phase_a/<STAMP>/` for summary, analysis, commands, and pytest log.
- Follow-up for Ralph: execute Phase A3 per input.md, log vectorized/safe/todo counts in docs/fix_plan.md, call out loops needing Phase C design packets, and capture collect-only evidence. After A3 lands we can supervise Phase B profiling.

### 2025-12-22 (galph loop - Weighted source evidence handoff)
- Updated docs/fix_plan.md `[SOURCE-WEIGHT-001]` to in_progress and tied `[VECTOR-GAPS-002]` CUDA follow-up to the weighting fix; clarified Phase A artifact expectations.
- Added status snapshot to `plans/active/source-weight-normalization.md` highlighting the correlation block.
- Replaced `input.md` (Parity mode) instructing Ralph to execute Phase A1–A3: build the weighted two-source fixture, run PyTorch vs C CLI commands, archive artifacts under `reports/2025-11-source-weights/phase_a/<STAMP>/`, and log commands/env/collect-only proof.
- Follow-up: After Ralph captures the parity evidence, expect fix_plan Attempt update + plan Phase A rows to flip [D], then resume `[VECTOR-GAPS-002]` Phase B2 hotspot correlation.

### 2025-12-22 (galph loop - Source weighting Phase C kickoff)
- Synced clean; reviewed spec/arch/testing docs plus `plans/active/source-weight-normalization.md`, `docs/fix_plan.md`, and existing TC-A through TC-E scaffolding in `tests/test_cli_scaling.py` before selecting focus (tails on coin flip, no commit audit).
- Action: Review/housekeeping in Parity mode for `[SOURCE-WEIGHT-001]` — updated plan C1 guidance to require a tensor-based normalization divisor (no `.item()`), refreshed fix_plan Next Actions, and issued a new `input.md` directing Ralph to implement Phase C1–C3, run the targeted TestSourceWeights suite under NB_RUN_PARALLEL=1, and archive artifacts under `reports/2025-11-source-weights/phase_c/` and `/phase_d/`.
- Follow-up for Ralph: implement the normalization change in `Simulator.run` keeping device/dtype neutrality, ensure parity tests pass, capture env/metrics logs, then update plan/fix_plan attempts; this unblocks VECTOR-GAPS-002 Phase B profiling once artifacts land.
### 2025-12-22 (galph loop - Source weight spec realignment)
- No upstream changes; branch `feature/spec-based-2` already up to date.
- Re-read spec/core architecture docs plus `plans/active/source-weight-normalization.md`; discovered plan still assumed sum-of-weights normalization.
- Audited recent commits (47822ce, 321c91e) and confirmed `_compute_physics_for_position` still multiplies intensities by `source_weights`, giving correlation 0.9155 / sum_ratio 0.7281 even after dividing by `n_sources`.
- Rewrote `plans/active/source-weight-normalization.md` into phased format targeting spec-aligned behaviour (weights ignored) and added Phase B/C/D/E guidance with explicit artifact expectations.
- Updated `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` status, Next Actions, and Attempts (#4) to reflect the new evidence path; annotated earlier attempts as superseded.
- Authored new `input.md` (Mode: Docs) directing Ralph to execute Phase B1–B3 evidence capture (spec quote, PyTorch call-chain, refreshed CLI metrics) before implementation.
- Follow-up: Expect Ralph to populate `reports/2025-11-source-weights/phase_b/<STAMP>/` with the new analysis bundle, then proceed to Phase C implementation loop.

#### 2025-12-23 (galph loop - Vectorization Phase H prep)
- Rebuilt `plans/active/vectorization.md` with phased tables (A–H) and new Phase H checklist for CUDA follow-up; captured outstanding tasks H1–H3.
- Updated `docs/fix_plan.md` [VECTOR-TRICUBIC-001] status/Next Actions to align with the new plan (Phase H focus, CUDA evidence pending).
- Issued input.md (Parity mode) directing Ralph to fix simulator device placement (incident_beam_direction caching) and rerun CUDA vectorization tests/benchmarks.
- Follow-up: Once device placement is corrected, expect Attempt #18 with CUDA logs under `reports/2025-10-vectorization/phase_h/<STAMP>/`, then archive the plan.

## 2025-12-23 (galph loop - Source weight Phase C handoff)
- Status Snapshot refreshed in `plans/active/source-weight-normalization.md` to record Phases A–B complete and highlight Phase C implementation + Phase D parity as the gating work for VECTOR-GAPS-002 / PERF-PYTORCH-004.
- Updated `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` Next Actions to direct Phase C1–C3 implementation, Phase D1–D2 parity runs, and documentation notifications once metrics land.
- Replaced `input.md` (Mode: Parity) with Phase C execution guidance: simulator update, TestSourceWeights expansion, targeted parity pytest, CLI metric captures, and artifact paths under `reports/2025-11-source-weights/phase_c|phase_d/<STAMP>/`.
- Follow-up for Ralph: implement Phase C tasks, capture parity metrics, update plan + fix_plan attempts, then notify `[VECTOR-GAPS-002]` when correlation ≥0.999 & sum_ratio≈1.0.

### 2025-12-24 (galph loop - SOURCE-WEIGHT divergence parity planning)
- Coin flip came up heads; reviewed recent Ralph commits (`ba9ec28`, `f93098a`) — great evidence capture but parity still blocked by divergence grid auto-selection mismatch (C builds 4 sources even with sourcefile, PyTorch only 2).
- Refreshed `plans/active/source-weight-normalization.md` with new Phase D (divergence auto-selection parity) and shifted prior validation tasks to Phase E/F. Tasks D1–D3 now cover evidence synthesis, design decision, and harness prep before implementation.
- Updated `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` Next Actions to align with the new plan sequencing (analysis doc → design proposal → implementation bundle) and keep `[VECTOR-GAPS-002]` blocked until correlation evidence returns.
- Issued `input.md` (Mode: Parity) directing Ralph to execute Phase D1: create a fresh timestamped `reports/2025-11-source-weights/phase_d/<STAMP>/divergence_analysis.md`, reuse the 20251009 artifacts, and capture `pytest --collect-only -q` to prove collection still passes.
- Follow-up for Ralph: produce divergence_analysis.md + commands log + collect-only proof this loop, then report findings and open questions in docs/fix_plan.md Attempt history so we can approve the Phase D2 design direction next turn.
### 2025-12-24 (galph loop - Source-weight Phase D3 harness prep)
- Reviewed recent Ralph commit `b8d16b5` (SOURCE-WEIGHT-001 Phase D2 design) — documentation-only, aligns with Option B recommendation and adds Attempt #5; no regressions spotted.
- Marked Phase D2 complete in `plans/active/source-weight-normalization.md` and refreshed D3 guidance (commands.txt + pytest log expectations) so the plan reflects the new status snapshot.
- Updated `docs/fix_plan.md` Next Actions for `[SOURCE-WEIGHT-001]` to focus on D3 harness capture and subsequent Phase E implementation under Option B.
- Reissued `input.md` (Mode: Docs) directing Ralph to create the Phase D3 artifact bundle (timestamped folder, commands.txt, collect-only log, targeted pytest log, warning capture, summary with acceptance metrics).
- Follow-up for Ralph: deliver the D3 harness artifacts under `reports/2025-11-source-weights/phase_d/<STAMP>/`, document results in summary.md, and update Attempts History once complete so Phase E implementation can begin and unblock `[VECTOR-GAPS-002]` profiling.

### 2025-12-24 (galph loop - Source-weight Phase E kickoff)
- Confirmed Ralph’s most recent commits (b8d16b5, 6252357) delivered Phase D2 design + Phase D3 harness; no regressions noted.
- Updated `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` Next Actions to focus on Phase E1–E3 implementation + parity metrics and Phase E4/F1 documentation/notifications; removed stale D3 wording.
- Issued new `input.md` (Mode: Parity) directing Ralph to implement Option B divergence parity, add the `TestSourceWeightsDivergence` suite, reuse Phase D3 CLI commands, and capture CPU parity metrics ≥0.999 with |sum_ratio−1| ≤1e-3 under `reports/2025-11-source-weights/phase_e/<stamp>/`.
- Follow-up for Ralph: deliver Phase E artifacts/metrics, update fix_plan Attempts and the plan status snapshot, then notify VECTOR-GAPS-002 once parity evidence lands so profiler work can resume next loop.

### 2025-12-24 (galph loop - Source-weight Phase E guard prep)
- Synced clean; reviewed Ralph commits 6252357 (Phase D3 harness) and 22f1a4d (Phase E test scaffolding). Tests TC-D1/D3/D4 exist, TC-D2 still skips pending warning guard.
- Updated `plans/active/source-weight-normalization.md` Phase E status to reflect partial progress and clarified that the Option B warning must live in `__main__.py`; marked E2 as `[P]` while TC-D2 remains skipped.
- Refreshed `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` Next Actions to call out the CLI guard location, removal of the TC-D2 skip, and parity evidence requirements (corr ≥0.999, |sum_ratio−1| ≤1e-3, warning capture).
- Issued new `input.md` (Mode: Parity) directing Ralph to implement the guard, reactivate TC-D2, rerun the Phase D3 command bundle, and archive metrics/warning logs under `reports/2025-11-source-weights/phase_e/<stamp>/` before updating the ledger.
- Follow-up for Ralph: complete Phase E1/E2 guard + test activation, capture parity artifacts + env snapshot, update fix_plan attempt history, and notify VECTOR-GAPS-002 once evidence meets thresholds; CUDA parity can remain optional but must be documented if skipped.
### 2025-12-24 (galph loop - SOURCE-WEIGHT Phase E parity triage)
- Coin flip (heads) review: commits 3140629 (Phase E1 warning guard) and 5a44772 (TC-D2 pytest.warns + parity attempt) landed cleanly; guard works but TC-D1/TC-D3 still fail with 140–300× intensity, so physics fix remains outstanding despite productive evidence capture.
- Updated `plans/active/source-weight-normalization.md` status snapshot to note TC-D2 completion and pinpoint the remaining bug at `src/nanobrag_torch/__main__.py:1005`, where divergence sources are still generated when a sourcefile is present.
- Refreshed `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` Next Actions so they now direct the `sourcefile` gate fix, rerun of `TestSourceWeightsDivergence`, and documentation/notification once fresh parity metrics meet corr ≥0.999 and |sum_ratio−1| ≤1e-3.
- Replaced `input.md` (Mode: Parity) with guidance to patch the guard, rerun the mapped pytest selector under NB_RUN_PARALLEL + NB_C_BIN, capture a new `reports/2025-11-source-weights/phase_e/<STAMP>/` bundle, and update the plan/ledger on success.
- Follow-up for Ralph: implement the guard fix, regenerate parity evidence that meets the thresholds, archive the artifacts, and log the attempt so VECTOR-GAPS-002 profiling can unblock once the metrics land.
### 2025-12-24 (galph loop - Source-weight normalization evidence reset)
- Ran local CLI reproduction of TC-D1 configuration; confirmed runtime prints `Loaded 2 sources` and no divergence auto-generation occurs, so the guard fix is already active.
- Updated `docs/fix_plan.md` Next Actions (lines 4026-4029) to focus Phase E2/E3 on capturing fresh PyTorch-only diagnostics plus synchronized PyTorch+C parity bundles, then a pixel-trace investigation for the normalization gap.
- Refreshed `plans/active/source-weight-normalization.md` status snapshot and Phase E rows to document the guard success and reframe blockers around normalization evidence instead of divergence auto-generation.
- Issued new `input.md` directing Ralph to capture a timestamped TC-D1 PyTorch run (stdout, `.bin`) and simulator diagnostics (`n_sources`, `steps`, `fluence`) under `reports/2025-11-source-weights/phase_e/<STAMP>/` before attempting C parity reruns.
- Follow-up for Ralph: execute the PyTorch command + diagnostics, archive artifacts in the new report folder, and log the attempt in docs/fix_plan.md so we can proceed to the TC-D1/TC-D3 parity reruns next loop.

### 2025-12-24 (galph loop - SOURCE-WEIGHT lambda sweep prep)
- Confirmed via inline CLI plumbing script that `_source_wavelengths_A` is `[6.2, 6.2]` for TC-D1 while C stdout still reports `wave=9.768e-11` (0.9768 Å) and counts 4 sources, explaining the 140–300× parity gap. Steps denom also differs (PyTorch=2 vs C=4) because of the extra zero-weight divergence placeholders.
- Added Attempt #13 to `docs/fix_plan.md` capturing this evidence, and inserted a new Next Action (lambda sweep) plus E2/E3 guidance updates so the first task is to run paired PyTorch jobs with 6.2 Å vs 0.9768 Å fixtures.
- Updated `plans/active/source-weight-normalization.md` Phase E status to reflect the wavelength mismatch and blocked tasks now require the lambda sweep artifact bundle.
- Replaced `input.md` (Mode: Parity) directing Ralph to perform the lambda sweep, capture diagnostics/metrics under `reports/2025-11-source-weights/phase_e/<STAMP>/lambda_sweep/`, and retain collect-only pytest proof.
- Follow-up: Ralph should execute the lambda sweep commands, archive metrics for both wavelength variants, and update the fix plan attempt history once the hypothesis is confirmed.

### 2025-12-24 (galph loop - VECTOR-TRICUBIC Phase A0 alignment)
- Added Phase A0 row to `plans/active/vectorization.md` (lines 23-26) capturing the new requirement to document the CLI `-lambda` override + steps reconciliation before requesting fresh parity runs; Status snapshot now references the 20251009T130433Z lambda sweep evidence.
- Refreshed `docs/fix_plan.md` entries for `[VECTOR-TRICUBIC-002]` (lines 3764-3781) and `[SOURCE-WEIGHT-001]` (lines 4046-4050) so Next Actions explicitly call for the lambda semantics design note and tie back to the updated plan.
- Marked `plans/active/source-weight-normalization.md` Phase E2 complete (lines 65-68) and clarified that E3 stays blocked pending the lambda/steps fix path.
- New `input.md` (Docs mode) directs Ralph to author `reports/2025-11-source-weights/phase_e/<STAMP>/lambda_semantics.md` plus collect-only proof, aligning with VECTOR-TRICUBIC-002 Phase A0.
- Coin review (heads): Ralph’s recent commits 303a284 → 1959182 delivered parity evidence and the lambda sweep; productive progress with no regressions, but physics fix still outstanding.

### 2025-12-24 (galph loop - Option B implementation handoff)
- Recorded Option B consensus in docs/fix_plan.md:4046-4052 and added Attempt #16 so SOURCE-WEIGHT-001 now points at concrete override/steps tasks.
- Refreshed plans/active/vectorization.md Phase A (ascii cleanup + explicit A0-A3 guidance) tying lambda_semantics.md to the parity gate.
- Replaced input.md with Parity-mode instructions directing Ralph to implement the override, add TC-E tests, rerun parity, and archive artifacts under reports/2025-11-source-weights/phase_e/<STAMP>/.
- Follow-up: Ralph implements Option B, adds tests/test_at_src_003.py, runs targeted pytest + parity script, updates docs per plan, then logs results in fix_plan attempts.
### 2025-12-24 (galph loop - Source-weight parity handoff)
- Updated `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` Next Actions (lines 4046-4050) to focus on rerunning TC-D1/TC-D3 via explicit PyTorch/C CLI commands and recording parity metrics; refreshed `[VECTOR-TRICUBIC-002]` checklist to depend on the new parity bundle.
- Refreshed `plans/active/source-weight-normalization.md` Phase E status to note Option B is already merged, unblocked E3, and clarified documentation follow-up; `plans/active/vectorization.md` Phase A0 marked done and A1 now points at the updated parity workflow.
- Rewrote `input.md` directing Ralph to run `tests/test_at_src_003.py`, capture both PyTorch and C floatfiles under a fresh STAMP, compute correlation/sum_ratio, and archive artifacts/commands in `reports/2025-11-source-weights/phase_e/<STAMP>/`.
- Next steps for Ralph: follow the new input.md (parity commands + metrics capture), then log results in `[SOURCE-WEIGHT-001]` and propagate unblock signals once thresholds are met.

### 2025-12-24 (galph loop - SOURCE-WEIGHT Phase E parity run prep refresh)
- Updated `plans/active/source-weight-normalization.md` status snapshot to acknowledge Option B is merged/tested and that Phase E is now blocked solely on capturing fresh TC-D1/TC-D3 parity metrics (corr ≥0.999, |sum_ratio−1| ≤1e-3) and propagating unblocks to vectorization plans.
- Rewrote `input.md` (Mode: Parity) with an expanded Do Now: run targeted pytest selectors, regenerate TC-D1/TC-D3 PyTorch+C floatfiles using the canonical CLI arguments, capture diagnostics/metrics via the embedded Python helper, and archive artifacts under `reports/2025-11-source-weights/phase_e/<STAMP>/` before logging results in `[SOURCE-WEIGHT-001]`.
- Follow-up for Ralph: execute the new handoff verbatim, ensure metrics hit thresholds, then update docs/fix_plan.md attempts and flip the corresponding plan rows so VECTOR-GAPS-002 Phase B can unblock.

### 2025-12-24 (galph loop - SOURCE-WEIGHT Phase E parity rerun directive)
- Re-reviewed docs/fix_plan.md:4046 and plans/active/source-weight-normalization.md; Source-weight plan still blocked solely on fresh TC-D1/TC-D3 metrics (corr ≥0.999, |sum_ratio−1| ≤1e-3).
- No ledger/plan edits this loop; evidence capture remains outstanding. Focus stays on SOURCE-WEIGHT-001 Phase E.
- Replaced input.md with a parity-mode handoff that (a) reruns the targeted pytest selectors, (b) regenerates PyTorch/C CLI outputs for TC-D1/TC-D3, and (c) runs a Python metrics script that stores metrics.json, diagnostics.json, correlation.txt, sum_ratio.txt, and simulator_diagnostics.txt under a new timestamped folder.
- Follow-up for Ralph: execute the updated input.md exactly, ensure thresholds pass, then log metrics + artifact path in `[SOURCE-WEIGHT-001]` Attempts and flip the plan Phase E rows so VECTOR-GAPS-002 Phase B can finally unblock.

### 2025-12-24 (galph loop - SOURCE-WEIGHT trace directive)
- Reviewed Ralph’s recent parity attempts (commits 779ac9a, 73e5e2f); metrics still fail (corr ≈0.05, sum_ratio ≈47–120) and he committed large report bundles without resolving steps mismatch.
- C logs show `created a total of 4 sources` for TC-D1 (two zero-weight placeholders) whereas PyTorch diagnostics report `n_sources=2`/`steps=2`; missing placeholders explain a 2× gap but not the full 47× inflation.
- Read `golden_suite_generator/nanoBragg.c:2570-2720` and `src/nanobrag_torch/simulator.py:824-878`; PyTorch ignores `source_I` completely while C seeds `I` with `source_I[source]`, and steps normalization differs when placeholders are absent—need trace to locate first numeric divergence.
- Updated input.md (Mode: Parity) to capture a TC-D1 slow/fast trace at pixel (slow=158, fast=147) for both PyTorch and C, recording outputs under `reports/2025-11-source-weights/phase_e/<STAMP>/trace/` plus an automated first-diff log. Ralph now runs collect-only proofs, traces, and Python diff before updating fix_plan attempts.
- Next loop depends on trace results: once the first divergence line is known, direct code fixes (placeholder source injection / weight handling) and rerun TC-D1/D3 parity.

### 2025-10-09 (galph loop - SOURCE-WEIGHT trace gate refresh)
- Updated docs/fix_plan.md Next Actions to add the TC-D1 trace capture as step 1 before parity reruns (aligns with Phase E row E2a).
- Inserted new Phase E row E2a in plans/active/source-weight-normalization.md and refreshed the status snapshot to flag the trace as the active gate.
- Regenerated input.md (Mode: Parity) directing Ralph to execute the trace bundle and log artifacts under reports/2025-11-source-weights/phase_e/<STAMP>/trace/.
- Follow-up: Ralph runs the Do Now command, records diff.txt first divergence, and logs the Attempt referencing the new trace artifacts.

### 2025-10-09 (galph loop - SOURCE-WEIGHT trace analysis refresh)
- Confirmed TC-D1 trace bundle (`reports/2025-11-source-weights/phase_e/20251009T192746Z/trace/`) shows steps mismatch (PyTorch=2, C=4) and ~1.5e8 vs 1.0e5 pre-polar intensity gap; polarization logged as 0.999 vs 0.5.
- Updated `plans/active/source-weight-normalization.md` status snapshot to mark Phase E2a [D] and refocused Phase E on diagnosing scaling/polarization gaps before rerunning parity.
- Refreshed `docs/fix_plan.md` Next Actions for `[SOURCE-WEIGHT-001]` to require a per-source trace (source index 2) and a design note for zero-weight placeholder parity prior to code edits.
- Next loop for Ralph: capture the source-index trace bundle + design rationale, then revisit simulator normalization once evidence narrows the 1.5e8 vs 1.0e5 divergence.
### 2025-12-24 (galph loop - SOURCE-WEIGHT per-source trace directive)
- Added bullet 7 to `[SOURCE-WEIGHT-001]` Next Actions (docs/fix_plan.md:4049) to require PyTorch trace instrumentation that logs per-source F_cell/F_latt/polarization before further simulator edits.
- Replaced `input.md` with a parity-mode handoff directing Ralph to extend `_apply_debug_output` for `TRACE_PY_SOURCE` blocks, rerun TC-D1 with `-trace_pixel 158 147`, and capture aligned C/Py traces under `reports/2025-11-source-weights/phase_e/<STAMP>/trace_per_source/`.
- Follow-up for Ralph: implement the new trace logging, run the mapped collect-only selector plus TC-D1 trace commands, diff against `TRACE_C_SOURCE2`, and record the new STAMP + observations in `[SOURCE-WEIGHT-001]` Attempts.

### 2025-12-24 (galph loop - SOURCE-WEIGHT spec decision prep)
- Reworked `plans/active/source-weight-normalization.md` into Phases E–H focused on the spec-first decision, test realignment, evidence capture, and documentation sync; added reporting expectations and clarified artifact paths.
- Updated `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` status/next-actions to reference the forthcoming spec_vs_c decision memo and mark C correlation gaps as expected (`C-PARITY-001`).
- Adjusted `plans/active/vectorization.md` Phase A to wait on the spec decision + spec-compliance tests instead of C correlation, documenting the new dependency chain.
- Issued `input.md` (Mode: Docs) directing Ralph to author spec_vs_c_decision.md, run collect-only selectors, and stage artifacts under `reports/2025-11-source-weights/phase_e/<STAMP>/`.
- Follow-up: Ralph to produce the decision memo per Phase E1, log the attempt in fix_plan, then proceed to Phase F test_plan.md once the memo is approved.
### 2025-12-24 (galph loop - SOURCE-WEIGHT Phase F design prep)
- Logged Attempt #25 in `docs/fix_plan.md:4053` for Ralph’s spec_vs_c_decision memo and refreshed Next Actions so Phase E now points at ledger/dependency updates followed by the Phase F design packet.
- Marked Phase E1 complete in `plans/active/source-weight-normalization.md:11-33` and updated the status snapshot to highlight that Phases E2/E3 remain before implementation resumes.
- Propagated the spec-first gate to dependent plans: `plans/active/vectorization.md:21-26` now has A1 `[D]`, and `plans/active/vectorization-gap-audit.md:11-35` swaps the correlation blocker for the upcoming spec-compliance bundle.
- Replaced `input.md` with Docs-mode guidance directing Ralph to author Phase F1–F3 (`reports/2025-11-source-weights/phase_f/<STAMP>/test_plan.md`) after validating selectors via collect-only.
- Follow-up for Ralph: execute Phase F1–F3 per new input, archive artifacts under the phase_f path, and update `[SOURCE-WEIGHT-001]` attempts once the design packet is ready.

### 2025-12-24 (galph loop - SOURCE-WEIGHT Phase G kickoff)
- Marked Phase E2/E3 complete and Phase F rows `[X]` in `plans/active/source-weight-normalization.md`, highlighting Phase G as the active gate with design packet archived (20251009T203823Z).
- Updated `docs/fix_plan.md:4035-4053` to record the spec-first ledger sync, retire the old parity bullets, and direct Next Actions to Phase G1–G3 with explicit pytest/CLI commands.
- Refreshed dependency plans (`plans/active/vectorization.md`, `plans/active/vectorization-gap-audit.md`) to note Phase G evidence as the remaining blocker for profiler work.
- Replaced `input.md` (Mode: Docs+Parity) handing Ralph the Phase G1/G2 execution plan: rewrite `tests/test_cli_scaling.py::TestSourceWeights*`, run the mapped pytest selector, rerun TC-D1/TC-D3 CLI bundles, and capture metrics/json artifacts under `reports/2025-11-source-weights/phase_g/<STAMP>/`.
- Follow-up for Ralph: implement the test updates per design packet, gather the Phase G evidence bundle, then log a new Attempt in `[SOURCE-WEIGHT-001]` (Phase G3) before pinging for Phase H documentation sync.

### 2025-12-24 (galph loop - vectorization gating update)
- Updated `docs/fix_plan.md` `[VECTOR-TRICUBIC-002]` Next Actions to reference Phase G spec-compliance evidence instead of the obsolete C-correlation thresholds; notes now point at `reports/2025-11-source-weights/phase_g/<STAMP>/` and refresh instructions for `[VECTOR-GAPS-002]` when Phase G attempt lands.
- Reissued `input.md` (Mode: Docs+Parity) guiding Ralph through Phase G1–G2 test rewrites and artifact capture, including collect.log/notes.md expectations and explicit reminder that C divergence is expected (C-PARITY-001).
- Follow-up: Ralph should execute Phase G test updates per the design packet, archive the evidence bundle, and log the Attempt so we can unblock VECTOR and PERF plans next loop.
### 2025-12-24 (galph loop - SOURCE-WEIGHT Phase G evidence refresh)
- Verified `tests/test_cli_scaling.py` already reflects spec-first behaviour; marked Phase G1 ✅ in `plans/active/source-weight-normalization.md` and clarified that G2/G3 remain open until a new evidence bundle lands.
- Updated `docs/fix_plan.md` Next Actions so Phase G2 now calls for a fresh timestamped pytest+CLI bundle and Phase G3 records the Attempt before Phase H documentation begins.
- Replaced `input.md` with Docs+Parity guidance focused on capturing the new artifacts (`reports/2025-11-source-weights/phase_g/<STAMP>/...`) and logging the Attempt.
- Follow-up for Ralph: execute the evidence run, populate metrics/notes, update `[SOURCE-WEIGHT-001]` Attempts, then Phase H1 doc updates can proceed next loop.
### 2025-12-24 (galph loop - SOURCE-WEIGHT parity anomaly response)
- Re-synced plan `plans/active/source-weight-normalization.md`: expanded Phase G guidance (expect parity ≥0.999, added G4 segfault triage) and introduced new Phase H parity reassessment + Phase I docs hand-off.
- Updated `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` Next Actions to reflect the new parity targets, segfault diagnosis, and memo/test alignment tasks; legacy C-parity note now marked provisional pending Phase H.
- Rewrote `input.md` (Mode: Docs) instructing Ralph to rebuild the debug C binary, rerun the evidence bundle, capture gdb backtrace if TC-D3 segfaults, and archive metrics for the forthcoming parity memo.
- Follow-up for Ralph: execute Phase G2/G4 per new guidance, archive artifacts under a fresh STAMP, then transition to Phase H parity memo + test rewrite once parity metrics are confirmed.

### 2025-12-25 (galph loop - SOURCE-WEIGHT Phase G bundle reset)
- Confirmed `tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_c_divergence_reference` still XPASSes (`NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest -q ...`), so parity anomaly persists and must be documented in the next evidence run.
- Rebuilt `golden_suite_generator/nanoBragg`; noted the PyTorch-only `-mosaic_dom` shorthand and added fix-plan guidance to invoke the C CLI with `-mosaic_domains` while running commands from the STAMP directory to contain SMV/PGM side outputs.
- Updated `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` Next Actions (bullet 4) plus a new `input.md` (Mode: Docs+Parity) that scripts the refreshed Phase G2 bundle: targeted pytest, corrected CLI commands, metrics/NaN audit, and instructions to capture gdb traces on failure.
- Follow-up for Ralph: execute the new `input.md` workflow, populate `reports/2025-11-source-weights/phase_g/<STAMP>/` with pytest logs + Py/C metrics, record the XPASS outcome, and then queue Phase H parity memo work once evidence is complete.

### 2025-12-25 (galph loop - SOURCE-WEIGHT parity plan refresh)
- Rewrote `plans/active/source-weight-normalization.md` to reflect the new Phase G parity recovery focus (G1–G3 open, G4 done) and staged follow-on Phase H/H3 + Phase I tasks once fresh evidence lands.
- Updated `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` next actions to match the plan (canonical commands, new bundle, memo/test refresh) and replaced the obsolete "expected divergence" narrative.
- Issued `input.md` (Mode: Parity) directing Ralph to capture a new Phase G bundle with `-nointerpolate`, compute correlation/sum ratio locally, and log results plus any segfault diagnostics before advancing to the parity memo.
- Follow-up for Ralph: execute Phase G1–G3 per input, archive artifacts under a new `<STAMP>`, update `[SOURCE-WEIGHT-001]` attempts, then we can move on to Phase H memo/test updates.
### 2025-12-25 (galph loop - SOURCE-WEIGHT G bundle prep refresh)
- Updated `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` Next Actions and `plans/active/source-weight-normalization.md` G1/G4 guidance to prefer `-interpolate 0` for the C CLI so the tricubic crash is avoided during parity capture.
- Rewrote `input.md` (Mode: Parity) with an OUTDIR-based workflow: mapped pytest selectors, explicit Py/PyTorch + C CLI commands, metrics script, and reminder to log a new Attempt once thresholds are met.
- Follow-up for Ralph: execute the refreshed instructions verbatim—collect pytest logs, run both CLIs with `-interpolate 0`, emit `metrics.json` in the new STAMP directory, and append the Attempt summary to `[SOURCE-WEIGHT-001]` before moving on to the Phase H memo.
### 2025-12-25 (galph loop - SOURCE-WEIGHT G0 prep + comment-bug plan)
- Updated `plans/active/source-weight-normalization.md` Phase G to include G0/G5 tasks (sanitised fixture + comment-bug linkage) and refreshed status snapshot; reporting expectations now require logging the fixture path + checksum.
- Added new plan `plans/active/c-sourcefile-comment-parsing.md` and fix_plan entry `[C-SOURCEFILE-001]` so the C-only bug is tracked separately; cross-referenced from `[SOURCE-WEIGHT-001]` Next Actions.
- Replaced `input.md` (Mode: Docs) with instructions to run collect-only selectors, generate the comment-free fixture under `reports/2025-11-source-weights/fixtures/`, diff against the original, and capture notes/sha256 before parity reruns.
- Follow-up for Ralph: execute Phase G0 per new input, archive the fixture bundle under a fresh STAMP, and update `[SOURCE-WEIGHT-001]` attempts with sanitised fixture details + `[C-SOURCEFILE-001]` reference.
### 2025-12-25 (galph loop - VECTOR-GAPS parity re-audit & SOURCE-WEIGHT handoff)
- Reran the 4096² warm-run benchmark (`reports/benchmarks/20251009-161714/`; command in fix_plan Attempt #5) and confirmed C↔PyTorch correlation now 0.999998 (sum_ratio 0.9999876), so the old 0.721 metric was stale. Logged Attempt #5 under `[VECTOR-GAPS-002]` and updated Next Actions to keep Phase B1 blocked only on SOURCE-WEIGHT parity.
- Refreshed input.md (Mode: Parity) to drive SOURCE-WEIGHT-001 Phase G1–G3: rebuild C, run the mapped pytest selectors, execute PyTorch + C CLIs with the sanitised fixture, compute metrics, and capture a new `<STAMP>` bundle before updating the ledger.
- Expect Ralph to follow the new How-To map, store artifacts under `reports/2025-11-source-weights/phase_g/<STAMP>/`, and append the Phase G Attempt referencing `[C-SOURCEFILE-001]` once correlation ≥0.999 and |sum_ratio−1| ≤3e-3 are confirmed.
### 2025-12-25 (galph loop - TEST-INDEX-001 planning kickoff)
- Authored `plans/active/test-suite-index.md` with phased roadmap (inventory → outline → doc authoring → maintenance) and added `[TEST-INDEX-001]` entry to `docs/fix_plan.md` (Medium priority, in_planning) so the documentation effort is now tracked.
- Refreshed `input.md` (Mode: Parity) to keep SOURCE-WEIGHT-001 Phase G front-and-centre; noted the new plan under Pointers/Next Up so Ralph can pivot once the parity bundle lands.
- Follow-up for Ralph: finish the SOURCE-WEIGHT-001 parity capture per input.md; after logging the Attempt, begin TEST-INDEX-001 Phase A by collecting pytest inventory with subagent support.

### 2025-12-26 (galph loop - SOURCE-WEIGHT Phase G handoff refresh)
- Rechecked `plans/active/source-weight-normalization.md` G0–G3 and `docs/fix_plan.md:4047-4175`; no ledger edits needed, but confirmed sanitised fixture (`reports/2025-11-source-weights/fixtures/two_sources_nocomments.txt`) and checksum are in place for the rerun.
- Left plan statuses unchanged (Review mode only) and refreshed `input.md` with explicit checksum verification, clarified `$STAMP` artifact paths, and reiterated metrics thresholds + `[C-SOURCEFILE-001]` linkage before Ralph updates the ledger.
- Follow-up for Ralph: execute Phase G1–G3 exactly as scripted (collect-only proof, pytest selectors, Py/C CLI runs, metrics.json), log the new Attempt, and block further work if correlation or sum ratio fail the thresholds.
### 2025-12-26 (galph loop - SOURCE-WEIGHT parity focus)
- Reviewed docs/fix_plan.md `[SOURCE-WEIGHT-001]` and Phase G plan; confirmed parity evidence still missing after sanitizer work. Re-ran collect-only for the mapped selectors (8 tests) to validate command provenance.
- Gathered geometry details from `tests/test_cli_scaling.py:600-665` and spec refs (`specs/spec-a-core.md:151-153`) so the next bundle can mirror the XPASS configuration.
- Replaced `input.md` (Mode: Parity) with explicit guidance to build a fresh Phase G `<STAMP>` bundle using the test geometry, capture pytest XPASS + CLI outputs, compute `metrics.json`, and log a new Attempt referencing the sanitized fixture and `[C-SOURCEFILE-001]`.
- Follow-up for Ralph: execute the new Phase G2–G3 instructions verbatim, store artifacts under `reports/2025-11-source-weights/phase_g/<STAMP>/`, ensure metrics meet corr ≥0.999 / |sum_ratio−1| ≤3e-3, then update docs/fix_plan.md attempts before moving on to Phase H.
### 2025-12-26 (galph loop - SOURCE-WEIGHT Phase H3/H4 prep)
- Repo already up to date. Reviewed spec/arch/testing docs plus active plans before analysis.
- Confirmed Phase H1 memo + test PASS exist (`reports/2025-11-source-weights/phase_h/20251010T002324Z/`, `tests/test_cli_scaling.py:585-692`); focus shifts to H3/H4 ledger propagation.
- Updated `plans/active/source-weight-normalization.md` status snapshot (H1/H2 marked done) and flipped H1/H2 table entries to `[D]`.
- Refreshed `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` status/Next Actions to emphasise H3/H4 tasks; trimmed outdated text referencing C-PARITY-001.
- Revised `plans/active/vectorization.md` (Phase A rows now cite the Phase H memo/tolerance) and `plans/active/vectorization-gap-audit.md` (status + B1 dependency now point at Phase H3/H4).
- Rewrote `input.md` (Mode: Docs) directing Ralph to execute Phase H3/H4: tidy ledger + bug doc references and update VECTOR-TRICUBIC-002/VECTOR-GAPS-002/PERF-PYTORCH-004 gating language with the new parity memo.
- Follow-up: Ralph to perform the ledger/doc updates per input.md, ensuring all dependent plans quote corr ≥0.999 and |sum_ratio−1| ≤5e-3 thresholds before we open Phase I documentation work.

### 2025-12-27 (galph loop - SOURCE-WEIGHT Phase I kickoff)
- Repo already up to date; reviewed spec/arch/testing docs plus active plans before analysis. No new commits from Ralph since last supervisor handoff.
- Action type: Review/housekeeping (Mode: Docs) on `[SOURCE-WEIGHT-001]`. Verified docs/bugs/verified_c_bugs.md#169 already scoped C-PARITY-001 correctly; focus shifted to aligning plans/ledger with Phase H completion and staging Phase I.
- Updated `docs/fix_plan.md` row for `[SOURCE-WEIGHT-001]` to note Phase H completion, refreshed Next Actions for Phase I1–I3, and bumped Owner timestamp to 2025-12-27.
- Marked `plans/active/source-weight-normalization.md` Phase H3/H4 as [D], flipped Phase H header to “Complete”, set Phase I header to “Active”, and refreshed the status snapshot to highlight remaining doc/archival work.
- Synced dependent plans: `plans/active/vectorization.md` status snapshot now references Phase H1–H4 parity and notes the pending Phase I doc patch; `plans/active/vectorization-gap-audit.md` likewise marks Phase B unblocked pending the documentation update.
- Rewrote `input.md` (Mode: Docs) directing Ralph to execute Phase I1 doc updates (pytorch_design.md, pytorch_runtime_checklist.md, specs/spec-a-core.md) with artifacts under `reports/2025-11-source-weights/phase_i/<STAMP>/` and a collect-only pytest proof.
- Next supervisor follow-up: confirm Ralph lands the Phase I docs, then handle Phase I2 ledger propagation + plan archival.
### 2025-12-27 (galph loop - SOURCE-WEIGHT Phase I2 prep)
- Repo already up to date via timeout git pull. Reviewed spec/arch/testing docs plus active plans; saw Phase I1 doc patch landed (Attempt #38) but plan still showed I1 open.
- Action type: Review/housekeeping (Mode: Docs) on `[SOURCE-WEIGHT-001]` Phase I. Updated `plans/active/source-weight-normalization.md` context/status snapshot and marked I1 [D] with artifact references (`reports/2025-11-source-weights/phase_i/20251010T005717Z/`).
- Replaced `input.md` (Mode: Docs) instructing Ralph to execute Phase I2: refresh `[VECTOR-TRICUBIC-002]`/`[VECTOR-GAPS-002]`/`[PERF-PYTORCH-004]` entries and associated plans with citations to pytorch_design §1.1.5 + runtime checklist item #4, log new Attempt under `[SOURCE-WEIGHT-001]`, and archive artifacts under `reports/2025-11-source-weights/phase_i/<STAMP>/` with collect-only proof.
- Follow-up: Once Ralph completes Phase I2, next supervisor step is Phase I3 archival (close plan, document residual C comment bug, update galph memory + move plan to archive). Also prepare vectorization Phase A3 readiness note after ledger propagation.
### 2025-12-28 (galph loop - SOURCE-WEIGHT Phase I3 staging)
- Repo already in sync (git pull --rebase no-op). Reviewed required spec/arch/testing docs and active plans before analysis.
- Coin flip = heads → audited Ralph’s recent commits (`4dbe4e31`, `9b4cddf3`, `3122916`). Phase I2 propagation is healthy and limited to docs/plan updates; no regressions detected.
- Focus: Review/housekeeping on `[SOURCE-WEIGHT-001]` Phase I3 prep. Updated `plans/active/source-weight-normalization.md` to mark Phase I2 complete (Attempt #39) so the status snapshot now leaves only Phase I3 open.
- Replaced `input.md` (Mode: Docs) directing Ralph to build the Phase I3 archive bundle, land `plans/archive/source-weight-normalization.md`, flip `[SOURCE-WEIGHT-001]` to done, and capture collect-only proof under `reports/2025-11-source-weights/phase_i/<STAMP>/`.
- Follow-up: Ralph to execute Phase I3 per the new input, then next supervisor loop can record the galph_memory readiness note for VECTOR-TRICUBIC-002 Phase A3 and archive the plan.
### 2025-12-28 (galph loop - VECTOR-TRICUBIC Phase B staging)
- Logged readiness note: SOURCE-WEIGHT parity locked to spec (corr ≥0.999, |sum_ratio−1| ≤5e-3) with memo `reports/2025-11-source-weights/phase_h/20251010T002324Z/parity_reassessment.md` and selector `tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_c_divergence_reference`.
- Marked `plans/active/vectorization.md` Phase A3 [D] and refreshed Status Snapshot; synced `plans/active/vectorization-gap-audit.md` snapshot to match the 2025-12-28 galph readiness note.
- Updated `docs/fix_plan.md` `[VECTOR-TRICUBIC-002]` to in_progress with new Next Actions and Attempt #1 (planning) entry.
- Rewrote `input.md` (Mode: Perf) steering Ralph to execute Phase B1–B2 pytest + benchmark refresh under `reports/2026-01-vectorization-refresh/phase_b/<STAMP>/`.
- Follow-up: expect Attempt #2 with fresh regression/benchmark logs before resuming VECTOR-GAPS-002 profiler work.

### 2025-12-29 (galph loop - VECTOR-GAPS Phase B1 relaunch)
- Git already synced; coin flip = heads → reviewed Ralph commit 9e278ad (Phase B regression refresh) and upstream archival commit a04bb9f; both are documentation/artifact adds with no regressions.
- Focused on `[VECTOR-GAPS-002]` Phase B1. Re-read plans/active/vectorization-gap-audit.md lines 27-36 and fix_plan entry docs/fix_plan.md:3791-3793 confirming profiling is unblocked post SOURCE-WEIGHT parity.
- Updated input.md (Mode: Perf) instructing Ralph to capture a fresh 4096² CPU profiler trace via benchmark_detailed.py, assert correlation_warm ≥0.999, and log artifacts under reports/2026-01-vectorization-gap/phase_b/$STAMP/.
- Next actions for Ralph: follow the new Do Now, store metrics/summary, and update fix_plan attempts; if success, proceed to Phase B2 hotspot mapping per plan guidance.
### 2025-12-30 (galph loop - VECTOR-GAPS Phase B1 handoff)
- Synced repo via timeout git pull (noop). Reviewed spec/arch/testing docs plus vectorization plans to confirm Phase B1 profiler rerun is still the front gate for `[VECTOR-GAPS-002]`.
- Action type: Review/housekeeping (Mode: Perf) on `[VECTOR-GAPS-002]`. Corrected `docs/fix_plan.md` index drift (VECTOR-TRICUBIC-002, STATIC-PYREFLY-001 → in_progress; SOURCE-WEIGHT-001 → done) so ledger status matches detailed entries.
- Rewrote `input.md` directing Ralph to rerun the 4096² CPU profiler (`benchmark_detailed.py`) with fresh `$STAMP`, capture metrics/summary/env, and update fix_plan + plan references. Thresholds reiterated: corr ≥0.999, |sum_ratio−1| ≤5e-3 per parity memo.
- Follow-up: Expect Ralph to execute Phase B1 command set, archive artifacts under `reports/2026-01-vectorization-gap/phase_b/<STAMP>/`, and log the attempt. Next supervisor loop should review metrics; if green, move to Phase B2 hotspot mapping guidance.

### 2025-12-29 (galph loop - VECTOR-GAPS Phase B1 prep refresh)
- Repo already synced; reviewed spec/arch/testing docs and active plans before analysis.
- Action type: Review/housekeeping (Mode: Perf) on `[VECTOR-GAPS-002]` to retire stale “await parity” guidance now that SOURCE-WEIGHT-001 Phase H memo is archived.
- Updated `docs/fix_plan.md:3791-3810` Next Actions to instruct an immediate Phase B1 profiler rerun with parity thresholds explicit; refreshed risks note to treat correlation_warm <0.999 or |sum_ratio−1|>5e-3 as blockers.
- Rewrote `input.md` directing Ralph to capture the new 4096² profiler trace (with metrics logging + collect-only proof) and to escalate if thresholds fail; artifacts to land under `reports/2026-01-vectorization-gap/phase_b/$STAMP/`.
- Follow-up: Expect Ralph to execute the profiler run per updated memo, then log Attempt in `[VECTOR-GAPS-002]`; supervisor to review metrics next loop and, if green, push Phase B2 hotspot mapping guidance.
### 2025-12-31 (galph loop - VECTOR-GAPS Phase B1 follow-up)
- Repo already synced; reviewed docs/index, specs/arch/testing strategy, and vectorization plans.
- Verified no new profiler bundles beyond 20251010 under `reports/2026-01-vectorization-gap/phase_b/`; Phase B1 evidence still outstanding.
- No plan edits needed: `docs/fix_plan.md` and `plans/active/vectorization-gap-audit.md` already call for the refreshed B1 run with corr ≥0.999 and |sum_ratio−1| ≤5e-3.
- Rewrote `input.md` (Mode: Perf) to restate the 4096² CPU profiler command, artifact checklist, and blocked protocol; evidence-only loop, thresholds enforced via summary script.
- Follow-up: expect Ralph to execute the new B1 bundle, deposit artifacts under a fresh `$STAMP`, and update `[VECTOR-GAPS-002]`/plan rows before we advance to Phase B2 hotspot mapping.

### 2025-12-30 (galph loop - VECTOR-PARITY baseline plan)
- Synced repo (already up to date), reviewed docs/index, specs, arch, testing_strategy, relevant plans, and fix_plan before analysis.
- Identified persistent 0.721 correlation regression blocking VECTOR-GAPS-002/ PERF-PYTORCH-004 despite repeated profiler attempts; coin flip = heads — recent Ralph commits are evidence-only (no regressions).
- Authored `plans/active/vectorization-parity-regression.md` (Phases A–E) to drive parity diagnosis and added `[VECTOR-PARITY-001]` entry to docs/fix_plan.md (index + section at 4007) with status, next actions, and Attempt #0.
- Replaced input.md (Mode: Parity) directing Ralph to execute Phase A1–A3: build artifact matrix/parameter diff under `reports/2026-01-vectorization-parity/phase_a/$STAMP/`, capture open questions, then log Attempt #1 in fix_plan.
- Follow-up: expect Ralph to populate the Phase A bundle, update `[VECTOR-PARITY-001]` attempts, and leave downstream phases blocked until parity evidence lands.
### 2026-01-01 (galph loop - VECTOR-PARITY Phase B1 rally)
- Repo already up to date; reviewed required spec/arch/testing docs plus vectorization plans before selecting focus. Coin flip = tails (skipped commit audit).
- Focused on `[VECTOR-PARITY-001]` housekeeping: updated fix_plan status to note Phase B1 reproduction outstanding and refreshed Next Actions with explicit step-by-step commands for the new 4096² benchmark, nb-compare sum_ratio capture, parity selectors, and ROI checks.
- Rewrote `input.md` (Mode: Parity) instructing Ralph to re-run Phase B1 on current HEAD, copy the benchmark bundle into `reports/2026-01-vectorization-parity/phase_b/$STAMP/`, record git/env metadata, and regenerate summary.md with correlation/sum_ratio prior to advancing to B2.
- Expect next loop to confirm receipt of a fresh Phase B1 bundle (correlation + sum_ratio) and, if captured, push the plan toward Phase B2 selectors; if thresholds unexpectedly pass, pause and reassess before moving to trace work.

### 2026-01-02 (galph loop - VECTOR-PARITY Phase B1 alignment)
- Repo already on feature/spec-based-2; coin flip = tails so skipped commit audit. Reviewed docs/index, spec shards, arch.md, testing_strategy, runtime checklist, and active vectorization plans before selecting focus.
- Focused on `[VECTOR-PARITY-001]` Phase B1: inspected existing phase_b bundles (20251010T024911Z / 20251010T025909Z) showing benchmark correlation 0.721 vs nb-compare 0.059 with sum_ratio ≈236. Determined a fresh HEAD reproduction must log both benchmark and nb-compare metrics for direct comparison.
- Updated `docs/fix_plan.md:4016` Next Actions to require recording correlation data from `benchmark_results.json` alongside nb-compare metrics in summary.md.
- Rewrote `input.md` (Mode: Parity) instructing Ralph to rerun Phase B1, copy the benchmark bundle, run nb-compare, and populate summary.md with both benchmark correlations and nb-compare totals plus observations. Artifacts to land under `reports/2026-01-vectorization-parity/phase_b/$STAMP/`.
- Next follow-up: Expect Ralph to execute the refreshed Phase B1 loop and update `[VECTOR-PARITY-001]` Attempt history. Supervisor should then review the new metrics delta and decide whether to progress to Phase B2 parity selectors or escalate to trace work.

### 2026-01-04 (galph loop - VECTOR-PARITY Phase B3 decision)
- Repo already synced; reviewed required spec/arch/testing docs plus active plans before selecting focus. Coin flip = heads → audited recent Ralph commit cab99e1 (Phase B2 evidence-only) confirming no active 4096² pytest coverage.
- Updated `plans/active/vectorization-parity-regression.md` status snapshot and Phase B table: B2 marked [D] with deselected-test evidence; added new Phase B3 decision task and shifted ROI work to B4.
- Refreshed `docs/fix_plan.md` `[VECTOR-PARITY-001]` status/Next Actions to require a written validation-path memo (options A–C) before further parity runs; status now reflects Phase B3 as the blocker.
- Rewrote `input.md` (Mode: Docs) directing Ralph to author the Phase B3 validation-path memo under `reports/2026-01-vectorization-parity/phase_b/$STAMP/` summarising options and recommending a path.
- Follow-up: Expect Attempt #6 documenting the memo; supervisor to review recommendation and, if approved, unblock Phase B4 ROI checks and trace prep.
### 2026-01-05 (galph loop - VECTOR-PARITY Phase B4 wrap)
- Repo already up to date; reviewed required spec/arch/testing docs plus active vectorization plans. Coin flip = tails (skipped commit audit).
- Focused on `[VECTOR-PARITY-001]` Phase B4b: authored `reports/2026-01-vectorization-parity/phase_b/20251010T035732Z/roi_compare/roi_scope.md` summarising full-frame vs ROI metrics, spec thresholds, hypotheses, and follow-up recommendations.
- Updated `plans/active/vectorization-parity-regression.md` (B4b → [D]) and refreshed `docs/fix_plan.md` Next Actions to pivot toward Phase C trace staging; Attempt #7 notes now reference the completed ROI scope doc.
- Replaced `input.md` (Mode: Docs) directing Ralph to draft the Phase C trace plan (`reports/2026-01-vectorization-parity/phase_c/<STAMP>/trace_plan.md`) before any instrumentation.
- Follow-up: Expect new Attempt logging with trace_plan.md; supervisor to review Phase C staging output, then greenlight C/Py trace capture.
### 2026-01-06 (galph loop - Phase C1 C-trace kickoff)
- Repo sync clean; reviewed core docs plus active parity/vectorization plans before selecting focus. Coin flip = heads → inspected Ralph commit 4a502f42 (Phase C1 profiler rerun). Outcome unchanged: evidence-only bundle confirming corr=0.721; no new regressions.
- Focused on `[VECTOR-PARITY-001]` Phase C instrumentation. Updated `plans/active/vectorization-parity-regression.md` row C1 with explicit λ=0.5 Å, distance=500 mm, pixel=0.05 mm command context. Refreshed `reports/2026-01-vectorization-parity/phase_c/20251010T040739Z/trace_plan.md` to lock pixel set {(2048,2048),(1792,2048),(4095,2048)}, corrected command templates, and marked pixel-selection question resolved.
- Tweaked `docs/fix_plan.md` Next Actions to reference the authoritative 4096² command parameters for Phase C1.
- Replaced `input.md` (Mode: Parity) directing Ralph to instrument `golden_suite_generator/nanoBragg.c`, rebuild, and capture `TRACE_C` logs for the three approved pixels under a fresh `reports/2026-01-vectorization-parity/phase_c/<STAMP>/` bundle (logs + commands + env metadata). Expect Attempt update with artifact paths before progressing to Py traces.
### 2026-01-06 (galph loop - Phase C2 Py trace handoff)
- Verified Ralph's Phase C1 attempt (20251010T053711Z); C traces exist for all three pixels but sit in background (F_cell=0).
- Updated `docs/fix_plan.md` (lines 19-45) to log Attempt #8, mark Phase C1 complete, and note the need for an on-peak pixel if Py traces also read zero; refreshed Last Updated date.
- Marked Phase C1 as [D] in `plans/active/vectorization-parity-regression.md` with artifact path and background-intensity note; status snapshot now calls out pending C2/C3 work.
- Authored new `input.md` (Mode: Parity) instructing Ralph to extend `scripts/debug_pixel_trace.py`, capture Py traces for the three pixels, and store artifacts under `reports/2026-01-vectorization-parity/phase_c/<STAMP>/` with commands/env metadata; added guard to pick an on-peak pixel next if everything stays zero.
- Reminder: avoid creating `phase_c/unknown/` folders—`STAMP` env var must be set before trace runs.
- Follow-up expectations: Ralph to deliver py_traces + summary + pytest collect log; supervisor to review numeric diffs and progress to Phase C3.
### 2025-10-10 06:14 UTC (galph loop - Vectorization plan refresh)
- Refreshed `plans/active/vectorization.md` into phased format (Phases A–G) emphasising Phase C parity gate + downstream implementation batches.
- Updated `docs/fix_plan.md` `[VECTOR-TRICUBIC-002]` Next Actions to mirror new plan (await first_divergence, then profiler/backlog, then tricubic delegation).
- Authored input.md (Mode: Parity) instructing Ralph to produce Phase C3 `first_divergence.md` using existing trace logs and `compare_c_python_traces.py`; artifacts go under `reports/2026-01-vectorization-parity/phase_c/$STAMP/`.
- Follow-up: Expect next Ralph attempt to deliver divergence summary + supporting diffs; supervisor to review and decide on unlocking Phase D profiling.
### 2026-01-06 (galph loop - Vectorization plan realignment)
- Updated `plans/active/vectorization.md` Phase C to closed status (C1–C3 [D], new C4 blocker) and flagged Phase D rows [B] pending `[VECTOR-PARITY-001]` Phase D/E parity fixes; status snapshot now reflects first_divergence completion.
- Refreshed `docs/fix_plan.md` `[VECTOR-TRICUBIC-002]` section: status notes Phase C satisfied, Next Actions now monitor parity Phase D/E before rerunning profiler; observations cite Attempt #10/11.
- Marked `plans/active/vectorization-parity-regression.md` D1 as [D] with Attempt #11 context to keep parity plan in sync.
- Authored `input.md` (Mode: Parity) directing Ralph to execute Phase D2 fluence remediation with trace capture under `reports/2026-01-vectorization-parity/phase_d/$STAMP/` and to document `fluence_parity.md`.
- Next follow-up: expect fluence parity artifacts (Phase D2) then reassess C4 unblock and update vectorization/backlog plans.
### 2026-01-07 (galph loop - Phase D2 fluence briefing)
- Confirmed repo synced; reviewed parity/vectorization docs per SOP. Coin flip = tails (skip commit audit).
- Focused on `[VECTOR-PARITY-001]` Phase D2. Pulled spec + C references and quantified the TRACE_PY vs TRACE_C fluence gap (≈9.89e+08 ratio) for pixel (1792,2048).
- Authored `reports/2026-01-vectorization-parity/phase_d/fluence_gap_analysis.md` summarising the mismatch and noting that the simulator already carries the spec-compliant value—issue isolated to `scripts/debug_pixel_trace.py` re-deriving fluence from flux.
- Updated docs/fix_plan.md observations to point at the new evidence and rewrote input.md (Mode: Parity) instructing Ralph to emit `beam_config.fluence`, rerun the trace, and record `fluence_parity.md` under a fresh stamp.
- Expect next attempt: code touch in `scripts/debug_pixel_trace.py`, refreshed TRACE_PY log (≤1e-3 rel err), `pytest --collect-only` log, and updated Attempt history.
### 2026-01-07 (galph loop - Phase D3 handoff prep)
- Verified Ralph Attempt #12 (`reports/2026-01-vectorization-parity/phase_d/20251010T070307Z/fluence_parity.md`) closed Phase D2; TRACE_PY fluence now matches C (rel_err≈7.9e-16).
- Updated `plans/active/vectorization-parity-regression.md` (row D2 → [D]) and `plans/active/vectorization.md` (C4 note) to reflect D1/D2 completion, leaving D3/F_latt as the active blocker.
- Refreshed `docs/fix_plan.md` Next Actions: D1/D2 marked ✅ with Attempt references; item 8 now instructs F_latt parity memo + ROI guard.
- Authored `input.md` (Mode: Parity) directing Ralph to implement Phase D3, regenerate TRACE_PY with STAMPed artifacts, write `f_latt_parity.md`, rerun ROI nb-compare, and execute the mapped parity test selector.
- Follow-up: Expect Attempt #13 containing f_latt parity evidence (`reports/2026-01-vectorization-parity/phase_d/<STAMP>/f_latt_parity.md`) plus updated trace/roi outputs; supervisor to review and then unlock Phase D4.

### 2026-01-07 (galph loop - Phase D4 simulator instrumentation)
- Updated docs/fix_plan.md (lines 19-55) with Attempt #13 summary, new D4 next action, and refreshed Active Focus for simulator F_latt regression.
- Refreshed plans/active/vectorization-parity-regression.md (Status Snapshot + Phase D table) to add D4 simulator diagnosis row and shift parity smoke to D5; vectorization.md now tracks Phase D1–D5.
- Authored input.md (Mode: Parity) directing Ralph to add env-guarded taps in Simulator._compute_physics_for_position, rerun the pixel probe, and capture logs under reports/2026-01-vectorization-parity/phase_d/$STAMP/.
- Open questions: need simulator tap artifacts (simulator_f_latt.log/md) confirming where the 32× loss occurs before proceeding to D5 parity smoke.
### 2026-01-07 (galph loop - Phase D5 prep)
- Closed out D3/D4 bookkeeping: updated `plans/active/vectorization-parity-regression.md` status snapshot + Phase D table (rows D3–D5) to record Attempt #14’s Miller-index unit diagnosis and funnel work into Phase D5 conversion/parity.
- Refreshed `docs/fix_plan.md` `[VECTOR-PARITY-001]` section — Attempt #13 now marked ✅, observations cite the Å→m⁻¹ requirement, Next Actions item 10 rewritten for the conversion + ROI rerun.
- Authored `input.md` (Mode: Parity) directing Ralph to scale `rot_a/b/c` by 1e10, regenerate NB_TRACE_SIM_F_LATT evidence, rerun the ROI nb-compare, and execute the high-res pytest before retiring the instrumentation.
- Follow-up: expect Attempt bundle under `reports/2026-01-vectorization-parity/phase_d/$STAMP/` with updated traces, `roi_compare_post_fix`, `phase_d_summary.md`, and pytest log; once corr≥0.999 and |sum_ratio−1|≤5×10⁻³ we can unlock Phase E in the parity plan.
### 2026-01-07 (galph loop - Phase D6 cleanup prep)
- Updated `plans/active/vectorization-parity-regression.md` status snapshot to reflect Attempt #15 ROI parity success (1e-10 lattice scaling) and added Phase D6 row directing NB_TRACE_SIM_F_LATT removal + ROI recheck; plan now queues Phase E once cleanup holds.
- Refreshed `plans/active/vectorization.md` snapshot/Phase C4 to note D6/E gating so tricubic relaunch stays blocked until cleanup and full-frame validation finish.
- Authored new `input.md` (Mode: Parity) instructing Ralph to execute `[VECTOR-PARITY-001]` Phase D6: strip simulator instrumentation, rerun `pytest --collect-only`, rerun the 512² ROI nb-compare into `reports/2026-01-vectorization-parity/phase_d/$STAMP/cleanup/`, and document corr/sum_ratio in `phase_d_summary.md`.
- Expect Attempt bundle with cleanup artifacts + updated fix_plan entry before approving Phase E1 benchmark/pytest reruns.
### 2026-01-07 (galph loop - Phase E validation kickoff)
- Confirmed Ralph’s Attempt #16 (commit 9dd1c73d) removed NB_TRACE_SIM_F_LATT and preserved ROI parity; noted large artifact bundle but parity evidence sound.
- Updated `docs/fix_plan.md` Active Focus + attempts to log D6 success and emphasise Phase E sweep; marked D6 as [D] in `plans/active/vectorization-parity-regression.md` and refreshed status snapshot to point at full-frame validation.
- Authored `input.md` (Mode: Parity) directing Ralph to run the 4096² benchmark + nb-compare bundle and the high-resolution pytest into `reports/2026-01-vectorization-parity/phase_e/$STAMP/`, then summarise metrics in `phase_e_summary.md`.
- Follow-up: Expect Phase E artifact bundle (benchmark_results.json, nb_compare summary, pytest log, phase_e_summary.md). Once validated, proceed with ledger updates (Phase E2) and unblock downstream vectorization plans.

### 2026-01-07 (galph loop - TEST-GOLDEN Phase B prep)
- Updated `docs/fix_plan.md` Active Focus to prioritise `[TEST-GOLDEN-001]` Phase B regeneration ahead of VECTOR-PARITY Phase E; refreshed `[VECTOR-PARITY-001]` and `[TEST-GOLDEN-001]` Next Actions to reference Phase B/C sequencing (target Attempt #19).
- Marked Phase A tasks [D] in `plans/active/test-golden-refresh.md` and added status snapshot pointing to Attempt #18 scope audit.
- Replaced `input.md` with Mode Parity instructions directing Ralph to regenerate all five golden datasets, capture command logs/checksums under `reports/2026-01-golden-refresh/phase_b/$STAMP/`, and prepare README provenance updates.
- Follow-up: Expect Attempt bundle documenting Phase B regeneration outputs plus updated golden binaries/README; once landed, queue Phase C parity reruns to unblock VECTOR-PARITY Phase E.

### 2026-01-07 (galph loop - Phase C parity prep handoff)
- Confirmed Attempt #19 landed commit `ebc140f2` with regenerated golden data + README provenance.
- Updated `plans/active/test-golden-refresh.md` (Status Snapshot + Phase B table) to mark regeneration complete and highlight Phase C parity validation as the active gate.
- Refreshed `docs/fix_plan.md` Active Focus/Next Actions to call for ROI nb-compare + targeted pytest using the refreshed assets; noted Phase B completion.
- Adjusted `plans/active/vectorization-parity-regression.md` status snapshot to reflect that `TEST-GOLDEN-001` now blocks only on Phase C validation.
- Authored new `input.md` (Mode: Parity) instructing Ralph to capture ROI nb-compare metrics under `reports/2026-01-golden-refresh/phase_c/$STAMP/` and run the AT-PARALLEL-012 high-resolution pytest with NB_RUN_PARALLEL=1.
- Follow-up: Expect Attempt with `phase_c_summary.md`, ROI summary assets, and `pytest_highres.log`; review results before scheduling broader selector sweeps.
### 2026-01-10 (galph loop - Phase E gating prep)
- Refreshed `plans/active/vectorization.md` status snapshot + Phase D table to gate profiler relaunch on `[VECTOR-PARITY-001]` Phase E evidence and `[TEST-GOLDEN-001]` ledger updates; added note that Phase E/F design packets stay paused until D1 unlocks.
- Updated `docs/fix_plan.md` `[VECTOR-TRICUBIC-002]` Next Actions to mirror the new gating (wait for phase_e_summary, then rerun profiler/backlog).
- Replaced `input.md` with Mode Parity instructions for Ralph to execute `[VECTOR-PARITY-001]` Phase E1: run the 4096² benchmark + full-frame nb-compare + high-res pytest into `reports/2026-01-vectorization-parity/phase_e/$STAMP/` and summarise metrics.
- Observed that legacy commits still have large `reports/` artifacts tracked (e.g., high_res ROI PNGs); flag for future hygiene sweep once protected assets checklist is ready.
### 2026-01-10 (galph loop - Phase E0 kickoff)
- Added Phase E0 “Edge Residual Diagnosis” section to `plans/active/vectorization-parity-regression.md` (lines 68-81) capturing callchain deliverables before reattempting full-frame parity; marked E1 as blocked pending those artifacts.
- Updated `docs/fix_plan.md` `[VECTOR-PARITY-001]` Next Actions (line 54) to focus on drafting the callchain brief, executing the trace for an edge pixel, and summarising the first tap.
- Replaced `input.md` with Mode Parity instructions directing Ralph to follow `prompts/callchain.md` (initiative_id=vectorization-parity-edge) and stage outputs under `reports/2026-01-vectorization-parity/phase_e0/$STAMP/`.
- Expect Attempt #21a to deliver the Phase E0 callchain bundle (static map, tap plan, summary) plus ledger updates before scheduling any new 4096x4096 runs.
### 2026-01-10 (galph loop - VECTOR-PARITY Phase E tap prep)
- Reviewed Ralph’s recent commits (`5d708d55`, `7863be99`) — evidence-only bundles, no regressions found.
- Rewrote `plans/active/vectorization-parity-regression.md` to add Phase E (omega taps) and Phase F remediation guidance; Phase E0 tasks marked [D], new E1–E4 checklists map to Tap 2/3 workflow.
- Updated `docs/fix_plan.md` Next Actions to align with the refreshed plan (omega tap execution → C trace → comparison → remediation → ledger updates).
- Issued `input.md` (Mode: Parity) instructing Ralph to run Next Action #1 with the debug trace command and capture `omega_analysis.md` in a new `$STAMP`.
- Follow-up: expect PyTorch omega tap artifacts + fix_plan Attempt update next run before proceeding to C instrumentation.

### 2026-01-10 (galph loop - Phase E1 PyTorch tap review)
- Captured PyTorch omega tap per plan (Attempt #23) and stored results in `reports/2026-01-vectorization-parity/phase_e0/20251010T095445Z/{py_taps/omega_metrics.json,omega_analysis.md}` → edge bias only ≈0.003 % (last/mean≈1.000028), so last-value ω alone can’t explain corr≈0.721.
- Updated `plans/active/vectorization-parity-regression.md` (Phase E table + status snapshot) and `docs/fix_plan.md` (Attempt history + Next Actions) to mark E1 done and pivot Phase E toward C taps plus HKL/background diagnostics.
- Refreshed `plans/active/vectorization.md` snapshot to note the negligible ω bias; profiling remains gated until new evidence lands.
- Issued `input.md` (Mode: Parity) directing Ralph to instrument `golden_suite_generator/nanoBragg` for Tap 3, run the single-pixel `nb-compare` command, and archive C omega traces under a fresh `reports/.../c_taps/` bundle.
- Follow-up: Expect Attempt logging the C tap outputs + `omega_comparison.md`; next supervisor action is to triage Tap 4 (HKL defaults) vs water background hypothesis once C evidence arrives.
### 2026-01-10 (galph loop - Phase E Tap 4 pivot)
- Logged Attempt #24 outcome in docs/fix_plan.md and marked Phase E2/E3 complete; refreshed Next Actions to focus on Tap 4 HKL/default_F diagnostics.
- Updated plans/active/vectorization-parity-regression.md (E4→[D], added E5–E7) and plans/active/vectorization.md status snapshot to reflect the omega hypothesis being refuted and the new F_cell priority.
- Issued input.md (Mode: Docs) directing Ralph to extend `scripts/debug_pixel_trace.py` with `--oversample/--taps` support, capture Tap 4 PyTorch stats for pixels (0,0)/(2048,2048), and archive outputs under `reports/2026-01-vectorization-parity/phase_e0/$STAMP/py_taps/`.
- Expect next loop to confirm tooling updates landed, then delegate Phase E6 C-side Tap 4 instrumentation.

### 2026-01-10 (galph loop - Phase E5 PyTorch tap handoff)
- Confirmed tooling commit `d1dd79cf` landed; E5 remains open because Tap 4 metrics were not yet captured. Updated `input.md` (Mode: Parity) to direct Ralph to run the new `scripts/debug_pixel_trace.py` Tap 4 flow for pixels (0,0) and (2048,2048) with a shared $STAMP, archive JSON/metadata under `reports/2026-01-vectorization-parity/phase_e0/$STAMP/py_taps/`, and summarise results in `f_cell_summary.md` before logging Attempt #26 in fix_plan.
- Coin flip audit (heads) reviewed commits `d1dd79cf` and `632d9fe0`; tooling change looks healthy, but note that `632d9fe0` introduced tracked PNGs under `comparisons/20251010-030139-d46877f6/` (≈1.3 MB each). Flag this for a future hygiene sweep once we plan repo cleanup—do not delete yet, but record the path when scoping cleanup work.
- No plan edits this loop; `plans/active/vectorization-parity-regression.md` already enumerates E5–E7. Next supervisor check: verify Ralph's Phase E5 bundle (Tap 4 metrics + summary) and, if satisfactory, prep Phase E6 instructions for C instrumentation.

### 2026-01-10 (galph loop - Phase E6 C tap handoff)
- Reviewed Attempt #25 artifacts (`reports/2026-01-vectorization-parity/phase_e0/20251010T102752Z/`) confirming PyTorch Tap 4 refutes the default_F hypothesis; refreshed `plans/active/vectorization-parity-regression.md` (E5→[D], E6/E7 guidance) and `plans/active/vectorization.md` status snapshot to steer focus toward C instrumentation + Tap 5/6 decision.
- Updated `docs/fix_plan.md` Next Actions (lines 61-64) to point Ralph at C Tap 4 capture → comparison → branch selection; recorded same priorities in `input.md`.
- Authored `input.md` (Mode: Parity) instructing Ralph to instrument `golden_suite_generator/nanoBragg` for Tap 4 counters, stash outputs under `reports/2026-01-vectorization-parity/phase_e0/<STAMP>/c_taps/`, and verify with pytest collect-only after restoring the binary.
- Follow-up: Expect Attempt log with C tap metrics + notes; next supervisor loop should assign `f_cell_comparison.md` drafting and decide between Tap 5 (pre-normalisation intensity) vs Tap 6 (water background).
### 2026-01-10 (galph loop - Tap 4 comparison prep)
- Updated docs/fix_plan.md Active Focus + Next Actions: Tap 4 C/Py discrepancy now the priority; Next Actions #1-3 cover `f_cell_comparison.md`, default_F audit, and next-tap selection.
- Marked plans/active/vectorization-parity-regression.md Phase E6 as [D] with Attempt #27 notes; E7 now explicitly requires the comparison + audit before choosing Tap 5/6.
- Refreshed plans/active/vectorization.md status snapshot to reflect the centre-pixel F_cell mismatch blocking Phase D profiling work.
- Replaced input.md (Mode: Parity) directing Ralph to generate `f_cell_comparison.md` + `default_f_audit.md` under a fresh `reports/.../comparison/` bundle, using the provided Python helper and code-inspection steps.
- Expect Attempt update logging the new comparison/audit artifacts plus preliminary recommendation on Tap 5 vs Tap 6.

### 2026-01-10 (galph loop - Tap 5 PyTorch instrumentation prep)
- Logged Attempt #28 in `docs/fix_plan.md` and rewrote `[VECTOR-PARITY-001]` Next Actions to drive Tap 5 (`intensity_pre_norm`) for PyTorch and C; Active Focus now points at capturing Tap 5 evidence before considering water background.
- Updated `plans/active/vectorization-parity-regression.md` (Phase E7→[D], added E8–E10) and `plans/active/vectorization.md` snapshot to reflect the default_F hypothesis closure and new Tap 5 priority.
- Issued `input.md` (Mode: Parity) instructing Ralph to extend `scripts/debug_pixel_trace.py` with `--taps intensity`, capture edge/centre JSON under `reports/2026-01-vectorization-parity/phase_e0/<STAMP>/py_taps/`, summarise in `pre_norm_summary.md`, and run `pytest --collect-only -q`.
- Next follow-up: supervisor to review Tap 5 PyTorch bundle, then delegate C instrumentation (Next Action #2) and the comparison write-up (Next Action #3).
### 2026-01-10 (galph loop - Phase E9 C Tap 5 kickoff)
- Logged Ralph’s Attempt #29 (PyTorch Tap 5) in `docs/fix_plan.md`, updated Active Focus to shift from tool bring-up to C instrumentation, and pruned the stale “extend tap tooling” Next Action.
- Refreshed `[VECTOR-PARITY-001]` Next Actions to call for a `TRACE_C_TAP5`-guarded capture plus comparison write-up; plan `vectorization-parity-regression.md` already marks E8 done/E9 pending so no edits required.
- Replaced `input.md` (Mode: Parity) with instructions to add a runtime `TRACE_C_TAP5` block in `golden_suite_generator/nanoBragg.c`, run the oversample=2 traces for pixels (0,0)/(2048,2048), archive logs under `reports/2026-01-vectorization-parity/phase_e0/$STAMP/c_taps/`, and maintain commands/env metadata.
- Expect Attempt #30 to deliver `pixel_*_tap5.log`, `trace_env.json`, and a brief `intensity_pre_norm_c_notes.md` so we can line up Tap 5 metrics before deciding on Tap 6 vs Phase F.
### 2026-01-11 (galph loop - Tap 5.1 PyTorch audit planning)
- Updated `plans/active/vectorization-parity-regression.md` Phase E rows: E10/E11 marked [D]; added E12–E14 for Tap 5.1 PyTorch/C and Tap 5.2 bounds work. Status snapshot now notes Attempt #31 centre-pixel HKL fallback.
- Refreshed `docs/fix_plan.md` Next Actions to focus on Tap 5.1 PyTorch, Tap 5.1 C mirror, and Tap 5.2 bounds parity; synced `plans/active/vectorization.md` status to reflect new evidence queue.
- Authored `input.md` (Mode: Parity) directing Ralph to extend `scripts/debug_pixel_trace.py` with an `hkl_subpixel` tap and capture the centre-pixel HKL audit bundle before we touch the C binary.
- Follow-up: Expect Attempt logging under `reports/2026-01-vectorization-parity/phase_e0/<STAMP>/py_taps/` with `tap5_hkl_audit.md`. Next supervisor loop should review the PyTorch tap output, then delegate the C instrumentation (plan E13) and HKL bounds capture (E14).
### 2026-01-11 (galph loop - Tap 5.1 C mirror prep)
- Verified Ralph’s last two commits (Attempt #32/#33) land the PyTorch Tap 5.1 HKL audit; no regressions spotted.
- Updated `docs/fix_plan.md` Next Actions to drop the completed PyTorch tap and emphasise C Tap 5.1 → Tap 5.2 → hypothesis refresh.
- Marked `plans/active/vectorization-parity-regression.md` E12 as [D] with Attempt #32/#33 references and refreshed the status snapshot; `plans/active/vectorization.md` snapshot now reflects Tap 5 evidence through Attempt #33.
- New `input.md` (Mode: Parity) directs Ralph to instrument `TRACE_C_TAP5_HKL`, capture edge/centre logs, and run pytest collect-only before tackling Tap 5.2.
- Expect Attempt log delivering `$STAMP/c_taps/pixel_*_hkl.log` + summary; next supervisor pass should review the C tap output and queue the HKL bounds check.
### 2026-01-11 (galph loop - Tap 5.2 bounds prep)
- Located Attempt #34 bundle (`reports/2026-01-vectorization-parity/phase_e0/20251010T121436Z/`) confirming C Tap 5.1 HKL parity; updated `docs/fix_plan.md` (Last Updated stamp, Active Focus, Attempt #34 entry) and marked plan `vectorization-parity-regression` E13 as [D] with new E15 placeholder for oversample accumulation.
- Refreshed `plans/active/vectorization.md` status snapshot to reference Attempts #29–#34 and new gating tasks (Tap 5.2 bounds + Tap 5.3 accumulation).
- Replaced input.md with Parity-mode instructions for Tap 5.2: add `TRACE_PY_HKL_BOUNDS`/`TRACE_C_HKL_BOUNDS`, archive logs under `bounds/`, summarise in `tap5_hkl_bounds.md`, then run pytest collect-only.
- Next loop: expect Attempt log containing PyTorch/C bounds logs + summary before drafting Tap 5.3 instrumentation brief.
### 2026-01-11 (galph loop - Tap 5.2 synthesis prep)
- Confirmed Attempt #35 semantics: PyTorch per-pixel vs C global HKL bounds; both keep (0,0,0) in range with default_F.
- Updated docs/fix_plan.md Next Actions (Tap 5.2 synthesis → Tap 5.3 instrumentation) and added new Phase E rows E15–E18 in plans/active/vectorization-parity-regression.md; vectorization.md snapshot now references Attempt #35.
- Authored input.md (Mode: Docs) instructing Ralph to retire H1 in tap5_hypotheses.md, integrate Tap 5.2 evidence, and prep for Tap 5.3 instrumentation next loop.
- Next follow-up: Expect Attempt entry detailing updated tap5_hypotheses.md + collect-only run; supervisor to scope Tap 5.3 instrumentation brief afterwards.
### 2026-01-12 (galph loop - test suite triage planning kickoff)
- Focus issue: [TEST-SUITE-TRIAGE-001] Full pytest run + triage (Action: Planning, Mode: Docs) — recorded pre-edits per Step 3.1.
- Pending: draft phased plan + update docs/fix_plan.md before authoring new input.md.
- Authored `plans/active/test-suite-triage.md` with four-phase structure (Preflight → Full run → Triage → Handoff); aligned references to testing_strategy + runtime checklist.
- Updated `docs/fix_plan.md` Last Updated, Active Focus, index, and added `[TEST-SUITE-TRIAGE-001]` section marking other initiatives paused pending triage artifacts.
- Replaced `input.md` directing Ralph to execute Phase A preflight (env capture + `pytest --collect-only`) and archive outputs under `reports/2026-01-test-suite-triage/phase_a/<STAMP>/`.
- Reviewed latest Ralph commits (ae9a19ea, 21c42e73): documentation-only Tap 5 evidence; no regressions detected but work now paused until test triage completes.
- Next supervisor follow-up: verify Phase A artifacts + Attempt log, then queue Phase B full-suite execution.

### 2026-01-12 (galph loop - test suite triage Phase B handoff)
- Repo already up to date; reviewed required docs (docs/index.md, specs/spec-a.md shard refs, arch.md, testing_strategy, runtime checklist, c_to_pytorch_config_map) plus `plans/active/test-suite-triage.md` & `docs/fix_plan.md` before analysis. Coin flip = heads → inspected latest Ralph commit b103d3f7 (Phase A artifacts) — evidence-only, no regressions.
- Focus issue: `[TEST-SUITE-TRIAGE-001]` (Action: Planning, Mode: none). Marked Phase A checklist complete in `plans/active/test-suite-triage.md` (added status snapshot, A1–A4 ⇒ [D]) and refreshed Phase B prerequisites.
- Updated `docs/fix_plan.md` Next Actions to concentrate on Phase B full-suite run → failure inventory → Phase C triage prep.
- Rewrote `input.md` directing Ralph to execute Phase B canonical command (`pytest tests/ -v --durations=25 --maxfail=0`) with new timestamped artifact bundle and `failures_raw.md` summary.
- Follow-up: Expect Attempt #2 under `[TEST-SUITE-TRIAGE-001]` delivering Phase B logs (`reports/2026-01-test-suite-triage/phase_b/<STAMP>/`) plus failure inventory; next supervisor iteration should review artifacts and script Phase C triage worksheet.

### 2026-01-12 (galph loop - Test suite triage Phase C prep)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase C triage (Action: Review/housekeeping, Mode: Docs).
- Added triage classification bundle `reports/2026-01-test-suite-triage/phase_c/20251010T134156Z/triage_summary.md` (cluster table + follow-ups). No new commands executed.
- Updated `plans/active/test-suite-triage.md` Phase C rows (C1 → [D], C2 → [P]) and `docs/fix_plan.md` Attempt #3 + refreshed Next Actions to require cluster→fix-plan mapping.
- Authored input.md (Docs mode) directing Ralph to complete Phase C3/C4 mapping via placeholder fix-plan entries and pending-actions table.
- Next supervisor check: ensure Ralph records cluster ownership + placeholder IDs, then decide on Phase B rerun strategy.

### 2026-01-12 (galph loop - Test suite Phase B rerun prep)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase B rerun (Action: Review/housekeeping, Mode: Docs).
- Updated plans/active/test-suite-triage.md B2 guidance to mandate the 60-minute budget and refreshed docs/fix_plan.md Last Updated + Next Actions with the explicit `timeout 3600` command.
- Rewrote input.md directing Ralph to run the extended Phase B suite, capture a fresh `phase_b/<STAMP>/` bundle, and log Attempt #5 metrics.
- Expect Ralph to execute the rerun, archive junit/log outputs, and update fix_plan Attempts before we draft the Phase D handoff.
- <Action State>: [ready_for_implementation]
### 2026-01-13 (galph loop - Test suite Phase C refresh)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase C triage refresh after Attempt #5 (Action: Planning, Mode: Docs).
- Notes: Initial focus recorded prior to edits. Detailed summary to follow after plan/input updates.
- Reviewed Attempt #5 bundle (`reports/2026-01-test-suite-triage/phase_b/20251010T135833Z/`) confirming 50 failures across 18 clusters; no new test execution performed.
- Updated `plans/active/test-suite-triage.md` status snapshot (Phase B marked done) and added Phase C tasks C5–C7 to capture the refreshed triage requirements (new `phase_c/20251010T135833Z/` bundle, updated summary, ledger sync).
- Refreshed `docs/fix_plan.md` Active Focus + Next Actions to emphasise Phase C5–C7, including explicit task list for staging the new artifacts before remediation proceeds.
- Authored `input.md` (Docs mode) directing Ralph to produce the updated triage summary + pending actions using existing Attempt #5 evidence; Do Now references the canonical pytest command but notes reuse of the captured bundle.
- <Action State>: [ready_for_implementation]
### 2026-01-13 (galph loop - Phase D handoff prep)
- Pre-edit note: Selected focus issue `[TEST-SUITE-TRIAGE-001] Phase D handoff` with Action=Planning, Mode=Docs.
- Completed Phase D3 ledger refresh: `docs/fix_plan.md` now carries the nine new fix-plan stubs and links to `reports/2026-01-test-suite-triage/phase_d/20260113T000000Z/handoff.md`; plan snapshot updated (`plans/active/test-suite-triage.md:14,60-65`).
- Authored Phase D handoff bundle (priority ladder + commands) at `reports/2026-01-test-suite-triage/phase_d/20260113T000000Z/handoff.md`.
- Rewrote `input.md` to launch Phase D Attempt #1 (reproduce `[CLI-DEFAULTS-001]` failure) with explicit artifact expectations.
- Follow-up for Ralph: capture targeted pytest logs under a fresh `phase_d/<STAMP>/attempt_cli_defaults/` folder before attempting any fix.
- <Action State>: [ready_for_implementation]

### 2026-01-13 (galph loop - CLI defaults remediation launch)
- Focus issue: `[TEST-SUITE-TRIAGE-001]` Phase D follow-through (Action: Review/housekeeping, Mode: Parity).
- Updated `plans/active/test-suite-triage.md` status snapshot (Phase D now ✅) and marked D4 as complete with reference to input stamp 20251010T153734Z.
- Refreshed `docs/fix_plan.md` Active Focus + Next Actions to track `[CLI-DEFAULTS-001]` remediation and queue `[DETERMINISM-001]` once ready.
- Authored new `input.md` (Parity mode) directing Ralph to implement the default_F fallback, rerun AT-CLI-002, and archive artifacts under `phase_d/<STAMP>/attempt_cli_defaults_fix/`.
- Expect Ralph to deliver Attempt #2 for `[CLI-DEFAULTS-001]` with passing targeted test, float stats evidence, and fix_plan attempt update before moving to determinism cluster.
- <Action State>: [ready_for_implementation]

### 2025-10-10 15:52:37Z (galph loop - Pre-plan note)
- Focus issue selection (pre-edit): [CLI-DEFAULTS-001] minimal -default_F CLI fix
- Action type: Planning
- Mode: Parity
- Note: Recording focus/action/mode before plan drafting per Step 3.1.

### 2025-10-10 15:56:17Z (galph loop — CLI defaults Phase A planning)
- Authored `plans/active/cli-defaults/plan.md` with Phase A–D structure; artifacts to land under `reports/2026-01-test-suite-triage/phase_d/<STAMP>/cli-defaults/`.
- Updated `docs/fix_plan.md` (Last Updated header, Active Focus, `[CLI-DEFAULTS-001]` section now in_progress with plan reference and refreshed Next Actions).
- Replaced `input.md` with Parity-mode instructions directing Ralph to execute Phase A capture (pytest selector, `-show_config`, `debug_default_f.py`) and store summaries.
- Next loop: verify Phase A artifacts + attempt log, then advance plan Phase B callchain tracing.
- <Action State>: [ready_for_implementation]

### 2025-10-10 16:03:57Z (galph loop - Pre-edit note)
- Focus issue: [CLI-DEFAULTS-001] Phase A plan alignment
- Action type: Review/housekeeping
- Mode: Docs
### 2025-10-10 16:07:38Z (galph loop - Phase B callchain setup)
- Reviewed Ralph commit 7622ab88; Phase A artifacts confirm CLI vs API divergence with identical configs.
- Marked Phase A tasks complete in `plans/active/cli-defaults/plan.md` and added status snapshot; updated `docs/fix_plan.md` focus/Next Actions to drive Phase B callchain tracing.
- Rewrote `input.md` (Docs mode) instructing Phase B callchain evidence capture with prompts/callchain deliverables under `reports/2026-01-test-suite-triage/phase_d/<STAMP>/cli-defaults/phase_b/`.
- Follow-up for Ralph: execute Phase B B1–B4 callchain tasks, log Attempt #4, then prep Phase C blueprint once divergence is nailed down.
- <Action State>: [ready_for_implementation]

### 2026-01-14 (galph loop - pre-plan note)
- Focus issue: [CLI-DEFAULTS-001] Phase C remediation blueprint
- Action type: Planning
- Mode: Docs

### 2026-01-14 (galph loop - CLI defaults Phase C blueprint)
- Authored Phase C artifacts under `reports/2026-01-test-suite-triage/phase_d/20251010T161925Z/cli-defaults/phase_c/` (remediation_plan.md, tests.md) per plan tasks C1–C2.
- Updated `plans/active/cli-defaults/plan.md:14-52` (Phase C now [D]) and refreshed `docs/fix_plan.md` header, Next Actions, and Attempts History (Attempt #5 recorded).
- Rewrote `input.md` (Mode: Parity) to launch `[CLI-DEFAULTS-001]` implementation Attempt #6 with explicit test/command mapping and artifact policy.
- Next follow-up for Ralph: implement HKL guard fix in `src/nanobrag_torch/__main__.py` and validate AT-CLI-002 using the new blueprint.
- <Action State>: [ready_for_implementation]

### 2026-01-15 (galph loop - pre-plan note)
- Focus issue: [DETERMINISM-001] RNG determinism remediation plan
- Action type: Planning
- Mode: Docs

### 2026-01-15 (galph loop - Determinism Phase A planning)
- Authored `plans/active/determinism.md` with Phase A–D structure for RNG seed remediation; artifacts to land under `reports/2026-01-test-suite-triage/phase_d/<STAMP>/determinism/`.
- Refreshed `docs/fix_plan.md` header + Active Focus; marked `[CLI-DEFAULTS-001]` done and set `[DETERMINISM-001]` status to in_progress with plan reference + Phase A next steps.
- Rewrote `input.md` (Mode: Parity) directing Attempt #1 to capture determinism failure evidence per plan Phase A.
- Follow-up for Ralph: execute Phase A run (collect-only + AT-PARALLEL-013/024 reproductions), archive under the new determinism reports tree, and log Attempt #1.
- <Action State>: [ready_for_implementation]

### 2026-01-16 (galph loop - pre-plan note)
- Focus issue: [DTYPE-NEUTRAL-001] dtype neutrality guardrail plan scaffolding
- Action type: Planning
- Mode: Parity
### 2026-01-16 (galph loop - dtype neutrality plan issued)
- Authored `plans/active/dtype-neutral.md` with Phase A–E structure to eliminate Detector cache dtype mismatch gating determinism.
- Updated `docs/fix_plan.md` Active Focus + `[DTYPE-NEUTRAL-001]` entry (priority↑, status=in_progress, plan reference, new Next Actions); linked `[DETERMINISM-001]` to dependency.
- Rewrote `input.md` (Parity mode) to launch Phase A evidence capture (collect-only + targeted determinism selectors + minimal reproducer) under `reports/2026-01-test-suite-triage/phase_d/<STAMP>/dtype-neutral/`.
- Follow-up: expect Attempt #1 artifacts (env.json, pytest logs, summary) next loop before scoping Phase B audit.
- <Action State>: [ready_for_implementation]
### 2025-10-10 (galph loop - pre-evidence note)
- Focus issue: [DTYPE-NEUTRAL-001] Phase A evidence capture kickoff
- Action type: Evidence collection
- Mode: Parity
### 2025-10-10 (galph loop - dtype Phase A evidence logged)
- Captured `[DTYPE-NEUTRAL-001]` Phase A artifacts under `reports/2026-01-test-suite-triage/phase_d/20251010T172810Z/dtype-neutral/phase_a/` (collect-only env snapshot, AT-PARALLEL-013/024 logs, minimal repro, summary).
- Marked Phase A rows [D] and added status snapshot in `plans/active/dtype-neutral.md`; fix_plan entry now records Attempt #1 (20251010T172810Z) with findings.
- Rewrote `input.md` (Mode=Docs) directing Ralph to execute Phase B static audit (B1–B5) and stage artifacts under phase_b/.
- Follow-up for Ralph: produce phase_b analysis/tap summaries, update fix_plan attempt log per plan task B5.
- <Action State>: [ready_for_implementation]

### 2026-01-16 (galph loop - pre-plan note)
- Focus issue: [DTYPE-NEUTRAL-001] Phase C remediation blueprint
- Action type: Planning
- Mode: Docs

### 2026-01-16 (galph loop - dtype Phase C blueprint handoff)
- Reviewed Phase B artifacts; updated plans/active/dtype-neutral.md status snapshot with Attempt #2 completion and rewrote Phase C table for the 4-line cache fix blueprint.
- Refreshed docs/fix_plan.md Active Focus to call for the Phase C document bundle; input.md now directs Ralph to author remediation_plan/tests/docs_updates under a new phase_c stamp (docs-only).
- Next Ralph loop: produce the phase_c blueprint docs, log Attempt #3 in fix_plan, then we can green-light Phase D implementation.
- <Action State>: [ready_for_implementation]
### 2026-01-16 (galph loop - pre-plan note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase F failure classification refresh
- Action type: Planning
- Mode: Docs
### 2026-01-16 (galph loop - TEST-SUITE-TRIAGE classification setup)
- Logged Attempt #7 outcome (49 failures, CLI defaults resolved) and shifted plan focus to the new phase_f bundle.
- Marked Phase E tasks [D] and rewrote `plans/active/test-suite-triage.md` guidance for the triage refresh (F1–F3 deliverables now emphasise triage_summary, cluster_deltas, pending_actions).
- Updated `docs/fix_plan.md` Next Actions to call for Attempt #8 (phase_f artifacts) and refreshed the header/active focus summary; `input.md` now points Ralph at producing the documentation set under `reports/2026-01-test-suite-triage/phase_f/$STAMP/`.
- Follow-up for Ralph: create the phase_f/ triage_summary.md + cluster_deltas.md + pending_actions.md bundle, record Attempt #8, and update ledger references per Do Now.
- <Action State>: [ready_for_implementation]

### 2026-01-16 (galph loop - dtype Phase D handoff prep)
- Focus issue: [DTYPE-NEUTRAL-001] dtype neutrality guardrail (Action: Review/housekeeping, Mode: Parity).
- Updated `docs/fix_plan.md` header to point at Phase D execution (Phase C blueprint noted complete) and rewrote Next Actions for `[TEST-SUITE-TRIAGE-001]` to launch Phase G handoff addendum.
- Refreshed `[DTYPE-NEUTRAL-001]` Next Actions to list Phase D1–D4 implementation + validation steps and the dependency release workflow for `[DETERMINISM-001]`.
- Issued new `input.md` directing Ralph to apply the 4-line cache dtype fix and run the authoritative AT-013/024 + detector geometry suite with artifacts under phase_d/.
- <Action State>: [ready_for_implementation]

### 2026-01-16 (galph loop - pre-edit note)
- Focus issue: [DTYPE-NEUTRAL-001] ledger/plan alignment
- Action type: Review or housekeeping
- Mode: Docs

### 2026-01-16 (galph loop - dtype Phase E alignment & determinism rerun setup)
- Updated `docs/fix_plan.md` Active Focus + `[DTYPE-NEUTRAL-001]` entry to reflect Phase D completion and Phase E pending tasks; refreshed `[DETERMINISM-001]` Next Actions to demand a fresh Phase A rerun (lines 1-8, 90-104).
- Marked Phase D checklist entries in `plans/active/dtype-neutral.md` as executed and captured a new status snapshot highlighting the outstanding Phase E validation bundle (lines 12-33, 64-79).
- Added status snapshot to `plans/active/determinism.md` noting the dtype dependency is cleared and Phase A artifacts need refreshing (lines 14-28).
- Reissued `input.md` (Mode: Parity) directing Ralph to rerun AT-013/024 plus collect-only under a new phase_a stamp, logging results per fix_plan guidance.
- Follow-up for Ralph: execute the deterministic test reruns, archive logs + summary, and update fix_plan Attempt #2 before we author Phase B callchain tasks.
- <Action State>: [ready_for_implementation]


### 2025-10-11 (galph loop - pre-review note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase G coordination (Action: Review/housekeeping, Mode: Docs).
### 2025-10-11 (galph loop - Phase G addendum + dtype validation prep)
- Published Phase G addendum at `reports/2026-01-test-suite-triage/phase_g/20251011T030546Z/handoff_addendum.md` and marked G1/G2 complete in `plans/active/test-suite-triage.md`.
- Updated `docs/fix_plan.md` header + `[TEST-SUITE-TRIAGE-001]` Attempt #9/logistics and corrected `[DTYPE-NEUTRAL-001]` status/next steps (Phase E outstanding).
- Replaced `input.md` with Parity-mode Do Now for `[DTYPE-NEUTRAL-001]` Phase E validation; baton now points Ralph at CPU-only rerun + docs updates.
- <Action State>: [ready_for_implementation]

### 2026-01-17 (galph loop - planning note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase H relaunch
- Action type: Planning
- Mode: Docs
- Updated `plans/active/test-suite-triage.md` with Phase H–J relaunch workflow and refreshed status snapshot (2026-01-17 directive).
- Refreshed `docs/fix_plan.md` Active Focus + `[TEST-SUITE-TRIAGE-001]` Next Actions to mandate Attempt #10 suite rerun before other initiatives resume.
- Replaced `input.md` with Parity-mode instructions for Ralph to run the full `pytest tests/` suite (Phase H) and stage Phase I triage scaffolding.
- <Action State>: [ready_for_implementation]

### 2026-01-17 (galph loop - Phase I classification kickoff)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase I classification (Action: Review/housekeeping, Mode: Docs).
- Confirmed Ralph’s Attempt #10 full-suite rerun (reports/2026-01-test-suite-triage/phase_h/20251011T033418Z/) and refreshed plan snapshot to mark Phase H complete.
- Updated docs/fix_plan.md Active Focus + Next Actions to pivot entirely to Phase I (Attempt #11) and queued Phase J prep.
- Refined plans/active/test-suite-triage.md status lines to show Phase I active, Phase J pending; preserved Phase H table as completed.
- Authored input.md directing Ralph to build the new phase_i/<STAMP>/triage_summary.md + classification_overview.md bundle and log Attempt #11.
- <Action State>: [ready_for_implementation]

### 2026-01-17 (galph loop - Phase J remediation prep)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase J remediation tracker (Action: Review/housekeeping, Mode: Docs).
- Updated `docs/fix_plan.md` header + Active Focus to call for Phase J bundle, expanded Next Actions with explicit tracker/sequence artifacts (lines 1-60, 44-52).
- Refreshed `plans/active/test-suite-triage.md` status snapshot to mark Phase I complete and Phase J active; no structural plan edits beyond status realignment.
- Authored `input.md` (Docs mode) directing Ralph to create `reports/2026-01-test-suite-triage/phase_j/<STAMP>/` with `remediation_tracker.md`, `remediation_sequence.md`, and `commands.txt`, and to log Attempt #12 in fix_plan.
- Follow-up for Ralph: build Phase J documentation bundle, update fix_plan attempts/Next Actions, and keep commands.txt referencing Phase I artifacts.
- <Action State>: [ready_for_implementation]

### 2026-01-17 (galph loop - pre-edit note)
- Focus issue: [DETERMINISM-001] Phase A repro gate
- Action type: Evidence collection
- Mode: Parity

### 2026-01-17 (galph loop - Pre-Sprint gate dispatch)
- Reviewed remediation_sequence.md Pre-Sprint requirements and confirmed [DTYPE-NEUTRAL-001] marked done; focus set on `[DETERMINISM-001]` Phase A reproductions per test-suite tracker.
- No plan edits required; pointed Ralph at the smoke test gate via new input.md and specified artifact layout for reports/2026-01-test-suite-triage/phase_j/<STAMP>/pre_sprint/.
- Directed updates to docs/fix_plan.md Attempts and remediation_tracker.md once the smoke output is captured to record the go/no-go decision.
- <Action State>: [ready_for_implementation]


### 2026-01-17 (galph loop - determinism Phase A reproduction kickoff)
- Focus issue: [DETERMINISM-001] Phase A reproduction
- Action type: Evidence collection (Callchain tracing not yet invoked)
- Mode: Parity
- Notes: Beginning reproduction pass for AT-PARALLEL-013/024 to unblock Sprint 1 remediation. Detailed summary to follow end-of-loop.
- <Action State>: [gathering_evidence]
- Evidence captured under reports/2026-01-test-suite-triage/phase_d/20251011T045211Z/determinism/phase_a/ (collect-only + AT-013/024 logs, env snapshot).
- TorchDynamo still queries CUDA device metadata when cuda_available==True but device_count==0, causing the same IndexError as Attempt #2; mosaic_rotation_umat dtype mismatch persists.
- Next loop should choose between disabling Dynamo for determinism selectors or provisioning a stub CUDA device before launching Phase B callchain.
- <Action State>: [planning]

### 2026-01-17 (galph loop - scratch note)
- Focus issue: [DETERMINISM-001] Phase B callchain
- Action type: Evidence collection (Callchain)
- Mode: Parity
- NOTE: Preliminary selection recorded before artifact updates.

### 2026-01-17 (galph loop - determinism Phase B callchain summary)
- Captured Phase B1-B2 callchain evidence for [DETERMINISM-001]; artifacts in `reports/determinism-callchain/` (static/taps/summary/env).
- Updated `plans/active/determinism.md` (B1/B2/B4 → [D]) and logged Attempt #4 in `docs/fix_plan.md` noting mosaic_seed gap.
- Issued new `input.md` directing Ralph to execute Phase B3 C-reference sweep under `reports/determinism-callchain/phase_b3/<STAMP>/`.
- Next for Ralph: follow input.md to document nanoBragg.c seed propagation, capture commands + summary, and update Attempts History.
- <Action State>: [gathering_evidence]
### 2026-01-17 (galph loop - determinism doc handoff refresh)
- Focus issue: [DETERMINISM-001] Phase C documentation bundle (Action: Review/housekeeping, Mode: Docs).
- Updated `plans/active/determinism.md` status snapshot and Phase B row to mark the C seed contract complete; re-scoped Phase C tasks to the new remediation_summary/docs_updates/testing_strategy notes deliverables (C1–C4 pending).
- Refreshed `docs/fix_plan.md` Next Actions/Exit Criteria to call for the Phase C artifact trio before marking the item done.
- Replaced `input.md` with Docs-mode instructions directing Ralph to create the timestamped Phase C bundle under `reports/determinism-callchain/phase_c/`.
- <Action State>: [ready_for_implementation]

### 2025-10-11 05:39:47Z (galph loop - determinism Phase D planning focus)
- Focus issue: [DETERMINISM-001] Phase D validation gate
- Action type: Planning
- Mode: Parity

- Updated `plans/active/determinism.md` with new Phase D (documentation integration) and Phase E (validation) checklists; status snapshot now flags doc work as the active gate.
- Refreshed `[DETERMINISM-001]` Next Actions in `docs/fix_plan.md` to align with the new phases (Phase D docs integration, Phase E validation).
- Issued `input.md` (Docs mode) directing Ralph to execute Phase D Task D1 and capture provenance under `reports/determinism-callchain/phase_d/<STAMP>/docs_integration/`.
- No code changes; planning only.
- <Action State>: [ready_for_implementation]


### 2026-01-17 (galph loop - Determinism Phase D docstring prep)
- Focus issue: [DETERMINISM-001] Phase D doc integration (Action: Review/housekeeping, Mode: Docs).
- Recorded D1 completion: updated `plans/active/determinism.md` status snapshot + Phase D table (D1→[D]) using Attempt #8 artifacts (`reports/determinism-callchain/phase_d/20251011T054542Z/docs_integration/`).
- Refreshed `[DETERMINISM-001]` ledger entry with Next Actions ladder (D2–D4 pending) and logged Attempt #8 details so provenance stays traceable.
- Rewrote input.md to direct Ralph toward Phase D2 docstring updates with collect-only verification and mirrored artifact layout.
- Heads review: inspected Ralph’s latest commits (a4322195, c114c86a); documentation work looks solid, no regressions spotted.
- <Action State>: [ready_for_implementation]

### 2026-01-17 (galph loop - Determinism doc sync prep)
- Focus issue: [DETERMINISM-001] doc integration status (Action: Review/housekeeping, Mode: Docs).
- Synced docs/fix_plan.md header to move Sprint 1 into ACTIVE status and mark `[DETERMINISM-001]` Phase D2 complete; refreshed Next Actions to target D3–D4 doc edits and downstream validation.
- Rewrote input.md (Mode: Docs) instructing Ralph to update `arch.md` ADR-05 + testing_strategy determinism workflow, capture new Phase D/Phase E bundles, and run the guarded determinism pytest command.
- Action State: [ready_for_implementation]

### 2026-01-17 (galph loop - Phase J alignment prep)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase J remediation tracker sync
- Action type: Review/housekeeping
- Mode: Docs
- Summary: Determinism closure verified and logged — updated docs/fix_plan.md header + Next Actions to pivot Sprint 1 toward `[SOURCE-WEIGHT-002]`, refreshed `[DETERMINISM-001]` checklist as complete, synced remediation tracker (C2/C15 counts→0 with resolution notes), and rewrote input.md instructing Ralph to author the source-weighting plan + capture baseline logs.
- Open Questions: none; expect Attempt #14 delivering plan + failing baseline before moving to Detector Config.
- <Action State>: [ready_for_implementation]

### 2026-01-17 (galph loop - pre-edit focus note)
- Focus issue: [SOURCE-WEIGHT-002] Phase B implementation planning
- Action type: Planning
- Mode: Parity + Docs
- Note: Recording focus/mode prior to plan updates. Detailed summary to follow end-of-loop.

### 2026-01-17 (galph loop - Source weighting Phase B brief setup)
- Aligned `[SOURCE-WEIGHT-002]` with Phase B focus: updated docs/fix_plan.md header + Next Actions to demand semantics/design artifacts and logged Attempt #15 placeholder.
- Refreshed plans/active/source-weighting.md to phased template (Phase A marked [D], new Phase B–D tables with deliverables/exit criteria).
- Replaced input.md with Docs+Parity guidance instructing Ralph to produce the Phase B semantics bundle (semantics.md, implementation_map.md, verification_checklist.md) under a fresh phase_j/<STAMP>/ directory; no tests this loop.
- Follow-up for Ralph: execute Phase B tasks B1–B4, archive artifacts, and record Attempt #15 before requesting implementation approval.
- <Action State>: [ready_for_implementation]

### 2026-01-17 (galph loop - focus note pre-work)
- Focus issue: [SOURCE-WEIGHT-002] Phase B status alignment
- Action type: Review/housekeeping
- Mode: Docs

### 2026-01-17 (galph loop - Source weighting Phase C kickoff)
- Reviewed reports/2026-01-test-suite-triage/phase_j/20251011T062955Z/source_weighting/{semantics.md,implementation_map.md,verification_checklist.md} plus specs/spec-a-core.md:142-166 and docs/architecture/pytorch_design.md:95-116; no matching entries in docs/findings.md.
- Approved Option A and refreshed plans/active/source-weighting.md to mark Phase B complete, re-scope Phase C tasks (parser dtype fix, regression test, AT-SRC-001 alignment), and update Phase D gate to full-suite delta.
- Updated docs/fix_plan.md `[SOURCE-WEIGHT-002]` ledger with new Next Actions/Exit Criteria and noted supervisor approval; top-level Active Focus now targets Phase C implementation.
- Rewrote input.md (Mode Parity) instructing Ralph to execute Phase C1–C3 with targeted pytest runs and artifact capture under phase_j/<STAMP>/source_weighting/.
- <Action State>: [ready_for_implementation]

### 2026-01-18 (galph loop - pre-focus note)
- Focus issue: [TEST-SUITE-TRIAGE-001] full-suite rerun & triage realignment
- Action type: Review/housekeeping
- Mode: Parity
- Note: Recording focus/action/mode before artifact edits; full summary will follow end-of-loop.
### 2026-01-18 (galph loop - Phase K relaunch prep)
- Reviewed docs/findings.md for test-suite keywords — no prior findings to reconcile.
- Updated docs/fix_plan.md (lines 1-160, 152-160) to prioritise Phase K full-suite rerun, pause `[SOURCE-WEIGHT-002]`, and refresh Next Actions with new artifact expectations.
- Refreshed plans/active/test-suite-triage.md (lines 11-155) with Phase K status + checklist; marked K1–K3 pending.
- Marked source-weighting plan paused (plans/active/source-weighting.md:3-92) so Ralph stays off that surface until Phase K data lands.
- Rewrote input.md with Parity-mode Phase K instructions, artifact layout, and tracker update steps.
- <Action State>: [ready_for_implementation]


### 2025-10-11 (galph loop - pre-focus note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase K classification refresh
- Action type: Review/housekeeping
- Mode: Parity

### 2025-10-11 (galph loop - Phase K analysis prep)
- Reviewed Phase K artifacts (summary/log) — 31 failures remain; no matching entries in docs/findings.md.
- Updated plans/active/test-suite-triage.md (Status Snapshot + K1→[D], refreshed K2/K3 guidance) to steer analysis work toward existing STAMP 20251011T072940Z.
- Refreshed docs/fix_plan.md header/Next Actions for `[TEST-SUITE-TRIAGE-001]`, setting focus on analysis bundle, tracker refresh, and logging Attempt #16.
- Rewrote input.md instructing Ralph to build Phase K triage_summary/classification_overview and update remediation tracker (docs-only, no pytest).
- Follow-up for Ralph: execute K2/K3 per plan, write Attempt #16 entry with artifact links once complete.
- <Action State>: [ready_for_implementation]

### 2026-01-18 (galph loop - focus note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase K closure + remediation planning
- Action type: Planning
- Mode: Docs
- Updated plans/active/test-suite-triage.md with Phase K2 completion snapshot and queued K3 tracker work; docs/fix_plan.md Next Actions now target tracker refresh and SOURCE-WEIGHT-002 restart gating. Input.md directs Ralph to execute Phase K3 docs-only updates (remediation_tracker.md, remediation_sequence.md, ledger). No new findings in docs/findings.md.
- Follow-up for Ralph: finish Phase K3 tracker refresh, extend Attempt #16 entry, then unpause SOURCE-WEIGHT-002 per sprint sequence.
- <Action State>: [ready_for_implementation]
### 2026-01-19 (galph loop - pre-edit focus note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase K follow-through
- Action type: Review/housekeeping
- Mode: Docs

- Synced Phase K documentation and fix_plan: refreshed `docs/fix_plan.md` (Next Actions now point at Source Weighting Phase C), `plans/active/test-suite-triage.md` status snapshot (Phase K marked complete), and `reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/summary.md` (K3 now documented as complete).
- Re-activated `[SOURCE-WEIGHT-002]` execution path: updated `docs/fix_plan.md` (§[SOURCE-WEIGHT-002]) and `plans/active/source-weighting.md` to move Phase C tasks from paused → active with Attempt #17 expectations.
- Reissued `input.md` guiding Ralph to deliver Phase C1–C3 (dtype-neutral parser + regression test) with targeted pytest runs and artifact bundle under a fresh Phase C stamp.
- Follow-up: Expect Attempt #17 delivering parser fix + targeted tests + artifact paths, then refresh Sprint 1 tracker counts.
- <Action State>: [ready_for_implementation]


### 2026-01-19 (galph loop - Source Weighting Phase C evidence prep)
- Focus issue: [SOURCE-WEIGHT-002] Phase C dtype implementation
- Action type: Evidence collection
- Mode: none

### 2026-01-19 (galph loop - Source Weighting Phase D handoff)
- Verified Attempt #17 artifacts (`reports/2026-01-test-suite-triage/phase_j/20251011T064811Z/`) already deliver Phase C Option A fixes; reran `pytest` targets (test_at_src_001*.py) locally (10/10 passing) to confirm baseline.
- Updated `docs/fix_plan.md:155-171` with Attempt #17 summary, refreshed Next Actions to Phase D1–D4 (acceptance sweep, full suite delta, spec/runtime checklist updates, ledger closure).
- Refreshed `plans/active/source-weighting.md:6-92` status snapshot + Phase C table (marked C1–C4 [D]) and plan status text—Phase D validation now the active gate.
- Rewrote `input.md` (Docs mode) directing Ralph to capture Phase D artifacts under `reports/2026-01-test-suite-triage/phase_d/<STAMP>/`, update spec AT-SRC-001 text, refresh runtime checklist, and rerun `pytest tests/ --maxfail=5`.
- Outstanding: spec still reflects legacy per-source weighting wording (must be updated in Phase D3); documentation + tracker sync pending after next loop.
- <Action State>: [ready_for_implementation]

### 2025-10-11 (galph loop - pre-focus note)
- Focus issue: [SOURCE-WEIGHT-002] Phase D2 regression delta
- Action type: Review/housekeeping
- Mode: Docs

### 2025-10-11 (galph loop - Phase D2 prep)
- Updated `docs/fix_plan.md` `[SOURCE-WEIGHT-002]` status + Next Actions to focus on Phase D2 regression run and D4 closure (dropping the completed D1/D3 bullets).
- Reissued `input.md` (Mode: Docs) directing Ralph to capture the Phase D2 full-suite run with timestamped artifacts and tracker updates.
- No conflicts with existing findings; ready for Ralph to execute the regression sweep and log Attempt #18 follow-up.
- Action State: [ready_for_implementation]

### 2026-01-19 (galph loop - Focus selection note)
- Focus issue: [SOURCE-WEIGHT-002] Phase D2 full-suite regression
- Action type: Review/housekeeping
- Mode: Parity

### 2026-01-19 (galph loop - Source weighting D2 prep summary)
- Reviewed Phase D evidence bundle `reports/2026-01-test-suite-triage/phase_d/20251011T091844Z/source_weighting/`; confirmed `test_sourcefile_parsing` still hard-codes float32, triggering dtype failures when the global default shifts to float64.
- Updated `docs/fix_plan.md` (`[SOURCE-WEIGHT-002]` section) to add the dtype-neutral testing task + explicit rerun plan and clarified Attempt #18 root cause.
- Adjusted `plans/active/source-weighting.md` Phase D2 row to gate the regression run on those dtype fixes.
- Rewrote `input.md` with Parity-mode guidance covering the test edits, targeted AT-SRC-001 run, and full-suite command (no `--maxfail`).
- Action State: [ready_for_implementation]

### 2025-10-11 (galph loop - focus selection note)
- Focus issue: [SOURCE-WEIGHT-002] Phase D4 closure alignment
- Action type: Planning
- Mode: Docs

- Updated plans/active/source-weighting.md to record Attempt #19 (Phase D2 complete) and define D4 tracker/ledger closure tasks.
- Refreshed docs/fix_plan.md header + [SOURCE-WEIGHT-002] Next Actions for D4 tracker sync and closure memo.
- Replaced input.md with Docs-mode instructions directing Ralph to produce the Phase D4 closure bundle (no pytest).
- Outstanding: Ralph must update Phase J/K tracker docs, author closure.md under a new Phase D stamp, then mark `[SOURCE-WEIGHT-002]` done.
- <Action State>: [ready_for_implementation]


### 2026-01-20 (galph loop - focus selection note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase K/D refresh
- Action type: Planning
- Mode: Docs

- Updated plans/active/test-suite-triage.md Phase L checklist + status snapshot (27 failures baseline, Sprint 1.3 pending).
- Refreshed docs/fix_plan.md active focus + Next Actions to point Ralph at Phase L detector-config rerun; corrected detector-config entry and reproduction command.
- Issued input.md instructing targeted pytest run and artifact capture for Phase L kickoff.
- <Action State>: [ready_for_implementation]

### 2025-10-11 (galph loop - focus selection note)
- Focus issue: [DETECTOR-CONFIG-001] MOSFLM beam-center offset remediation plan
- Action type: Planning
- Mode: Docs

### 2025-10-11T10:55:20Z (galph loop - Detector MOSFLM offset plan)
- Authored `plans/active/detector-config.md` with Phase A–C roadmap covering MOSFLM +0.5 offset remediation, regression testing, and docs/tracker updates.
- Updated `docs/fix_plan.md` [DETECTOR-CONFIG-001] to reference the new plan and align next actions with Phase B/C sequencing.
- Rewrote `input.md` to direct Ralph through Phase B1–B3 & C1–C2: implement MOSFLM pixel offset fix, extend detector-config tests, and capture targeted pytest artifacts under a fresh Phase L stamp.
- Key references: specs/spec-a-core.md:68-73, arch.md ADR-03, reports/2026-01-test-suite-triage/phase_l/20251011T104618Z/detector_config/analysis.md.
- <Action State>: [ready_for_implementation]

### 2025-10-11 (galph loop - focus selection pre-edit note)
- Recorded focus/action/mode before edits: focus=`[DETECTOR-CONFIG-001] MOSFLM offset remediation`, action=Planning, mode=Docs.
- <Action State>: [planning]

- Updated `plans/active/test-suite-triage.md` to mark Phase L complete, added Phase M post-fix validation gate, and noted tracker sync still pending until MOSFLM remediation closes.
- Expanded `plans/active/detector-config.md` Phase B guidance with explicit file references and testing expectations; fix_plan now points Ralph at Phase C1–C3 execution.
- Refreshed `docs/fix_plan.md` Active Focus, Next Actions (both `[TEST-SUITE-TRIAGE-001]` + `[DETECTOR-CONFIG-001]`), and issued `input.md` (Parity mode) directing MOSFLM offset implementation + detector-config pytest rerun.
- <Action State>: [ready_for_implementation]

### 2026-01-20 (galph loop - focus selection note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase M relaunch
- Action type: Planning
- Mode: Parity

### 2026-01-20 (galph loop - Phase M0 directive alignment)
- Refocused `[TEST-SUITE-TRIAGE-001]` on the 2026-01-20 mandate: added Phase M0 section to plans/active/test-suite-triage.md (lines 168-177) with preflight/full-run/triage checklist.
- Updated docs/fix_plan.md (lines 44-52) to point reproduction + Next Actions at Phase M0 artifacts and to park `[DETECTOR-CONFIG-001]` follow-up until the new baseline lands.
- Reissued input.md steering Ralph to capture collect-only + full-suite runs under phase_m0/$STAMP and refresh triage_summary.md before resuming detector work.
- Action State: [ready_for_implementation]

### 2025-10-11 (galph loop - focus selection note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase M0 chunk rerun
- Action type: Review/housekeeping
- Mode: Parity

### 2025-10-11T15:37:41Z (galph loop - Phase M0 housekeeping recap)
- Logged Attempt #20 in docs/fix_plan.md capturing the env-prefix failure (artifacts: reports/2026-01-test-suite-triage/phase_m0/chunks/chunk_01/).
- Refreshed plans/active/test-suite-triage.md runtime guard + chunk commands to require `env CUDA_VISIBLE_DEVICES=-1 ...` and STAMP export before rerunning Phase M0b.
- Reissued input.md with env-prefixed preflight/chunk commands, explicit STAMP setup, and env capture snippet for Ralph's redo.
- Action State: [ready_for_implementation]


### 2026-01-21 (galph loop - focus selection note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase M1 remediation planning
- Action type: Planning
- Mode: Docs

### 2026-01-21 (galph loop - Phase M1 sprint kickoff)
- Phase M0 Attempt #21 triage reviewed; logged in docs/fix_plan.md:681 with summary and failure deltas.
- Updated plans/active/test-suite-triage.md:202-233 with Phase M1/M2/M3 sections and refreshed exit criteria; Phase M prerequisites now reference M1/M2 completion.
- docs/fix_plan.md:3-7,41-47 now steer Sprint 0 quick fixes + gradient guard; Attempt #21 recorded with artifact path.
- input.md rewritten for Phase M1a CLI fixture fix, mapped selectors, artifact cadence under phase_m1/$STAMP.
- <Action State>: [ready_for_implementation]

### 2025-10-11T16:16:08Z (galph loop - focus selection note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase M1 plan alignment
- Action type: Review/housekeeping
- Mode: Docs

### 2025-10-11T16:19:01Z (galph loop - Phase M1 alignment recap)
- Marked Phase M1a complete in plans/active/test-suite-triage.md (row M1a) and refreshed status snapshot so Sprint 0 now highlights remaining C3/C4/C5/C7 work.
- Updated docs/fix_plan.md Next Actions to call out that Phase M1 quick fixes continue with C3+ clusters only.
- Issued fresh input.md directing Ralph to execute M1b (detector dtype conversion) with stamped artifact capture per triage_summary.md:92-122.
- <Action State>: [ready_for_implementation]

### 2025-10-11T16:25:32Z (galph loop - focus selection note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase M1c debug trace scope
- Action type: Review/housekeeping
- Mode: Parity

### 2025-10-11T16:28:22Z (galph loop - Phase M1c briefing)
- Updated plans/active/test-suite-triage.md to mark M1b [D] with Attempt #22 evidence and noted C4/C5/C7 as remaining Sprint 0 tasks.
- Refreshed docs/fix_plan.md Next Actions to drop C3 from the remaining cluster list; emphasised C4/C5/C7 path.
- Rewrote input.md directing Ralph to execute Phase M1c (Cluster C4) with stamped artifact capture and fix_plan logging.
- Expect Ralph to create reports/2026-01-test-suite-triage/phase_m1/$STAMP/debug_trace/ with baseline/fix/regression logs, update docs/fix_plan Attempt #23, and flip plan row M1c to [D].
- Action State: [ready_for_implementation]


### 2025-10-11T16:35:06Z (galph loop - focus selection note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase M1c debug trace guard (Cluster C4)
- Action type: Review/housekeeping
- Mode: none

### 2025-10-11T16:39:55Z (galph loop - Cluster C4 refresh)
- Ran env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_debug_trace.py (reports/2026-01-test-suite-triage/phase_m1/20251011T163812Z/debug_trace/pytest_failed.log) confirming new failure: TRACE output lacks "Final intensity" when only -trace_pixel is supplied.
- Updated plans/active/test-suite-triage.md M1c guidance to require emitting the summary line and pointed to the new baseline log.
- docs/fix_plan.md: added context to Next Actions and logged Attempt #24 (regression still open).
- Rewrote input.md directing Ralph to add the missing summary print and close Cluster C4.
- <Action State>: [ready_for_implementation]

### 2026-01-21 (galph loop - focus selection note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase M1 cluster progression
- Action type: Review/housekeeping
- Mode: Parity
### 2026-01-21 (galph loop - Phase M1d briefing)
- Reviewed Ralph commits 84a67719 and 4e6dad19; Cluster C4 debug trace fix landed cleanly, existing `.item()` usage stays confined to debug-only paths.
- Updated plans/active/test-suite-triage.md status snapshot + row M1c to reflect Attempt #25 closure and expanded M1d/M1e guidance.
- Refreshed docs/fix_plan.md Next Actions to focus on clusters C5/C7.
- Rewrote input.md for Phase M1d with parity-mode instructions, authoritative selectors, and artifact cadence.
- Expect Ralph to execute CUDA-graphs fixture updates next loop and log Attempt #26 under phase_m1/$STAMP/simulator_api/.
- Action State: [ready_for_implementation]

### 2026-01-21 (galph loop - Focus Setup)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase M1 Cluster C7
- Action type: Review/housekeeping
- Mode: Parity
- Reviewed Ralph commits 4e6dad19 and eb1247f6 (Step 2 coin flip): fixtures + debug trace changes look healthy; no regressions spotted.
- Updated plans/active/test-suite-triage.md status snapshot + row M1d to mark Attempt #26 done; Phase M1 bullet now highlights only Cluster C7 remaining.
- Adjusted docs/fix_plan.md Next Actions to remove C5 and reference the lattice-shape cluster; ensured reproduction pointer matches triage_summary.md lines 218-243.
- Rewrote input.md for Phase M1e (Cluster C7) with stamped artifact cadence and Detector fixture guidance.
- No semantic changes this loop; awaiting Ralph to implement test fixture updates and log Attempt #27.
- <Action State>: [ready_for_implementation]

### 2026-01-21 (galph loop - focus selection note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase M1 ledger refresh
- Action type: Review/housekeeping
- Mode: Docs
### 2026-01-21 (galph loop - Phase M1f prep recap)
- Marked Sprint 0 complete in plans/active/test-suite-triage.md (lines 11-26) and row M1e now [D]; M1f guidance refreshed with summary/ledger instructions.
- Updated docs/fix_plan.md (lines 3-52) so Next Actions call for Phase M1f summary + Phase M2 brief; Active Focus reflects Sprint 0 closure.
- Rewrote input.md directing Ralph to produce the new summary bundle, sync remediation_tracker.md, and draft the Phase M2 guard strategy.
- Action State: [ready_for_implementation]

### 2025-10-11T17:24:49Z (galph loop - focus selection note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase M2 gradient guard
- Action type: Review/housekeeping
- Mode: none
### 2025-10-11T17:24:49Z (galph loop - Phase M2 briefing)
- Updated `plans/active/test-suite-triage.md` status snapshot to mark Phase M1 complete and flipped M2a to [D] referencing strategy bundle 20251011T171454Z.
- Refreshed `[TEST-SUITE-TRIAGE-001]` Next Actions in `docs/fix_plan.md` to target Phase M2b–M2d (compile guard implementation, gradcheck reruns, documentation sync).
- Replaced `input.md` with guard-implementation instructions: implement `NANOBRAGG_DISABLE_COMPILE` path, run targeted gradcheck selector(s), capture artifacts under `phase_m2/$STAMP/`, and update docs/tracker.
- Follow-up for Ralph: execute Phase M2b CPU run first, extend to CUDA if available, then update docs/ledger per strategy.
- <Action State>: [ready_for_implementation]
### 2026-01-21 (galph loop - focus selection note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase M2 follow-through
- Action type: Planning
- Mode: Docs
### 2026-01-21 (galph loop - Phase M2d planning recap)
- Refreshed `plans/active/test-suite-triage.md` Phase M2 table (lines 216-226) to mark M2b done via Attempt #29, note optional M2c GPU run, and expand M2d guidance to cover doc updates + ledger sync.
- Updated `[TEST-SUITE-TRIAGE-001]` Next Actions in `docs/fix_plan.md` (around lines 44-50) to focus on Phase M2d documentation, optional GPU validation, and pivot prep for Phase M3 once docs land.
- Rewrote `input.md` to steer Ralph toward the Phase M2d documentation bundle and tracker refresh; Mode=Docs with artifacts under `phase_m2/$STAMP/{docs_diff,summary.md}`.
- Action State: [ready_for_implementation]

### 2026-01-21 (galph loop - focus selection note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase M2d documentation closure
- Action type: Review/housekeeping
- Mode: Docs

### 2026-01-21 (galph loop - Phase M3a prep recap)
- Updated `plans/active/test-suite-triage.md` Status Snapshot + M2d row to record Attempt #30 completion; M3a now queued for execution.
- Refreshed `docs/fix_plan.md` Next Actions to pivot from M2d docs to Phase M3 staging (MOSFLM sync, detector orthogonality notes, mixed-units handoff).
- Reissued `input.md` (Mode=Docs) directing Ralph to author the Phase M3a MOSFLM remediation sync bundle under `reports/2026-01-test-suite-triage/phase_m3/$STAMP/`.
- <Action State>: [ready_for_implementation]

### 2025-10-11T18:08:02Z (galph loop - focus selection note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase M3a MOSFLM sync refresh
- Action type: Review/housekeeping
- Mode: Docs
### $STAMP (galph loop - Phase M3a refresh recap)
- Reused detector-config pytest log (phase_m/current) and authored refreshed MOSFLM sync summary at `reports/2026-01-test-suite-triage/phase_m3/20251011T181150Z/mosflm_sync/summary.md`.
- Marked `plans/active/detector-config.md` task B3 [D] after auditing `detector.py:90-107` and `detector.py:522-549` to confirm no double +0.5 offset.
- Trimmed `[TEST-SUITE-TRIAGE-001]` Next Actions to M3b/M3c, logged Attempt #32 in `docs/fix_plan.md`, and rewrote `input.md` for Phase M3b detector_ortho notes.
- Action State: [ready_for_implementation]
### 2025-10-11T18:21:08Z (galph loop - focus selection note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase M3 next actions refresh
- Action type: Review/housekeeping
- Mode: Parity
### 2025-10-11T18:24:01Z (galph loop - Phase M3 steering recap)
- Updated docs/fix_plan.md next actions to launch MOSFLM fix attempt and flipped [DETECTOR-CONFIG-001] back to in_progress; index now matches plan (lines 38-58, 226-241).
- Reissued input.md with Parity-mode instructions for executing Phase C1–C3 (MOSFLM +0.5 offset, targeted selectors, doc/tracker updates).
- No new evidence gathered; awaiting Ralph to implement detector changes per detector-config plan (Phase C).
- <Action State>: [ready_for_implementation]

### 2026-01-22 (galph loop - focus selection note)
- Focus issue: [DETECTOR-CONFIG-001] Phase C ledger refresh
- Action type: Planning
- Mode: Docs

- Reviewed commit 804eb119 (MOSFLM offset) and found spec drift: DetectorConfig now holds 51.2 mm instead of `(detsize + pixel)/2` mm; tests updated to match the drift.
- Updated plans/active/detector-config.md Phase C rows to [P], flagging the spec mismatch, partial regression coverage, and incomplete full-suite gating.
- Logged Attempt #38 in docs/fix_plan.md with partial status and refreshed next actions to call for spec/C trace audit, doc sync, and chunked rerun.
- Rewrote input.md with Parity-mode guidance: update tests to spec values, adjust DetectorConfig + Detector mapping once, rerun targeted selectors, refresh docs/tracker, then redo chunked suite captures under a new STAMP.
- Action State: [ready_for_implementation]


### 2025-10-11 (current loop focus note)
- Focus issue: [DETECTOR-CONFIG-001] MOSFLM default alignment
- Action type: Review/housekeeping
- Mode: Docs

### 2025-10-11 (galph loop summary)
- Reviewed findings (API-001/API-002/CONVENTION-001) for detector offsets; no doc conflicts noted.
- Updated plans/active/detector-config.md Phase C to mark Attempt #39 completion and highlight need for chunked rerun.
- Refreshed docs/fix_plan.md next actions: capture new MOSFLM bundle, sync remediation tracker, execute Phase M chunked pytest rerun.
- Reissued input.md pointing Ralph at targeted detector tests + chunk workflow with STAMPed artefacts.
- Follow-up for Ralph: produce the new phase_m3/phase_m artefacts, update tracker + fix_plan attempts, and record parity deltas.
- <Action State> [ready_for_implementation]

### 2025-10-11T19:37:05Z (galph loop - Phase M2 chunk rerun prep)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase M2 chunk rerun
- Action type: Planning
- Mode: Parity
- Reviewed Attempt #34 partial log (`reports/2026-01-test-suite-triage/phase_m/20251011T191757Z/blocked.md`) and the latest Ralph commit (64680791; partial pytest log only) — confirmed we must abandon the single-command full suite because of the 600 s harness cap.
- Updated `plans/active/test-suite-triage.md` Phase M snapshot + M2 row (lines 240-266) to require the Phase M0 10-chunk ladder and captured the timeout note in the status snapshot.
- Refreshed `docs/fix_plan.md` Active Focus + Next Actions (lines 4-52) to prioritise the chunk rerun before tracker sync; recorded guidance to fold in Attempt #40 artifacts post-run.
- Rewrote `input.md` with the chunk ladder commands, STAMP setup, artifact expectations, and exit-code logging instructions for Ralph.
- Next for Ralph: execute the chunk ladder, capture exit codes & summary, then update tracker/analysis per fix-plan step 3.
- <Action State>: [ready_for_implementation]

### 2025-10-11T20:12:17Z (galph loop - focus selection note)
- Focus issue: [DETECTOR-CONFIG-001] MOSFLM explicit beam center handling
- Action type: Planning
- Mode: Docs

### 2025-10-11T20:16:04Z (galph loop recap)
- Refreshed `plans/active/detector-config.md` with phased Option A blueprint (Phase B pending design note, phases C/D staged).
- Updated `docs/fix_plan.md` Next Actions for [DETECTOR-CONFIG-001] to require Option A design + implementation + chunk rerun.
- Reissued `input.md` directing Ralph to author the design artifact under a fresh STAMP before coding.
- <Action State>: [planning]
### 2025-10-14T17:07:45-07:00 (galph loop - focus selection note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase M3 status update & Sprint 1 delegation (C16 tolerance)
- Action type: Review/housekeeping
- Mode: Parity
- Updated `plans/active/test-suite-triage.md` with Phase N (Sprint 1.2 detector orthogonality) checklist and added status snapshot note; new tasks N1–N4 capture baseline log, tolerance edit, regression run, and tracker sync.
- Refreshed `docs/fix_plan.md` Next Actions to launch Sprint 1.2 (C16) and queued C15 mixed-units as next focus.
- Rewrote `input.md` (Mode=Parity) directing Ralph to execute Phase N with STAMPed artifacts and uniform 1e-7 tolerance updates in `tests/test_at_parallel_017.py`.
- No orthogonality-related findings found in `docs/findings.md`; proceeding under assumption documentation remains current.
- Follow-up for Ralph: complete Phase N N1–N4, update remediation tracker, and log Attempt referencing new STAMP before moving to C15.
- <Action State>: [ready_for_implementation]
### 2025-10-15T00:19:46Z (galph loop - focus selection note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase N status sync & Sprint 1.3 gate
- Action type: Review/housekeeping
- Mode: Parity

### 2025-10-15T00:24:43Z (galph loop recap)
- Aligned `plans/active/test-suite-triage.md` Phase N with Attempt #44 (C16 tolerance closure), updated status snapshot, and pointed Phase O toward C15 mixed-units callchain.
- Refreshed `docs/fix_plan.md` Next Actions to mark Sprint 1.2 complete and staged Sprint 1.3 tasks (S1–S3) for mixed-units callchain evidence.
- Reissued `input.md` directing C15 reproduction plus callchain capture with STAMPed artifact expectations.
- Action State: [ready_for_implementation]


### 2025-10-15T00:33:25Z (galph loop - focus selection note)
- Focus issue: [TEST-SUITE-TRIAGE-001] Phase O focus realignment
- Action type: Planning
- Mode: Parity

### 2025-10-15T00:37:31Z (galph loop recap)
- Updated plans/active/test-suite-triage.md Phase O to pivot from C15 callchain to the post-Sprint chunked baseline; Phase snapshot now cites Attempt #45 and lists C2/C8/C17/C18 as remaining clusters.
- Refreshed docs/fix_plan.md Active Focus + Next Actions (item 4 marked complete, new item 5 for Phase O) and logged Attempt #45 redundancy evidence from reports/2026-01-test-suite-triage/phase_m3/20251015T002610Z/mixed_units/.
- Rewrote input.md with Phase O chunk ladder commands (env guards, STAMP scaffolding, 10 chunk commands, aggregation + tracker sync).
- Action State: [ready_for_implementation] (Phase O chunk rerun delegated to Ralph).
