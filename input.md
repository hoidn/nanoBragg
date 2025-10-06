timestamp: 2025-10-06T00:32:22Z
commit: 9f7b8cb
author: galph
focus: CLI-FLAGS-003 Phase D3 intensity audit
Summary: Diagnose the 2.6e2× intensity gap between C and PyTorch parity runs and capture evidence for plan D3.
Phase: Evidence
Focus: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_d/

Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — Phase D3 intensity gap analysis. Export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md; compare `reports/2025-10-cli-flags/phase_c/parity/c_img.bin` vs `torch_img.bin` (max/mean/sum RMS) using a Python notebook or script; inspect simulator normalization factors (steps, fluence, r_e_sqr) to pinpoint which scalar(s) inflate PyTorch output; summarize findings in `reports/2025-10-cli-flags/phase_d/intensity_gap.md` with hypotheses and next-step recommendations.
If Blocked: If numpy load or analysis fails, capture traceback to `reports/2025-10-cli-flags/phase_d/intensity_gap_FAIL.log`, note commands attempted, log a new Attempt entry under `[CLI-FLAGS-003]`, then pause for supervisor guidance.

- Priorities & Rationale:
- reports/2025-10-cli-flags/phase_c/parity/SUMMARY.md — Records the 115k vs 446 peak gap; we need quantitative backing before adjusting simulator scaling.
- plans/active/cli-noise-pix0/plan.md:112 — Phase D3 requires explicit analysis artifacts to close CLI parity.
- docs/fix_plan.md:664 — Next actions now point to D3; without intensity diagnosis the fix-plan item cannot close.
- docs/architecture/detector.md:205 — Defines meter-space pix0 handling; confirm override didn’t double-scale contributing to intensity jump.
- docs/development/c_to_pytorch_config_map.md:25 — Fluence/pivot parity expectations; cross-check PyTorch’s BeamConfig against C output.
- docs/development/testing_strategy.md:18 — Evidence loops must cite authoritative commands; keep logs reproducible before moving to implementation.
- src/nanobrag_torch/simulator.py:1050 — Final physical intensity scaling (r_e^2 * fluence); verify constants line up with C trace before concluding disparity cause.
- src/nanobrag_torch/simulator.py:969 — Normalized intensity accumulation before omega; confirm oversample handling matches C semantics to rule out extra factor of oversample².
- docs/architecture/pytorch_design.md:112 — Describes expected batching order; use as reference when reasoning about multi-source sums.
- reports/2025-10-cli-flags/phase_a/README.md — Baseline pix0 and noise behavior; ensures current discrepancy is new to Phase C.
- reports/2025-10-cli-flags/phase_b/detector/pix0_override_equivalence.txt — Confirms mm↔m conversion accuracy; double-check values when interpreting logged vectors.
- src/nanobrag_torch/models/detector.py:391 — Override assignment; verify r_factor adjustments aren’t part of intensity mismatch.
- docs/architecture/conventions.md:pix0-overrides — Guardrail for CUSTOM convention behavior relevant to this command.
- tests/test_at_parallel_012.py — Reference for acceptable correlation thresholds; helps gauge severity of intensity scaling beyond correlation.
- reports/benchmarks/20250930-180237-compile-cache/cache_validation_summary.json — Example of structured reporting; mimic format for intensity report where practical.

- How-To Map:
- mkdir -p reports/2025-10-cli-flags/phase_d before writing new artifacts; place markdown summary under `intensity_gap.md` and include tables/metrics.
- Use `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python - <<'PY' ... PY` to load both float images (dtype=np.float32) and compute stats: max, min, mean, std, L2 norm, total photons. Save raw numbers to `intensity_gap_stats.json` alongside markdown.
- Compute ratio of per-pixel sums and identify whether difference equals `phi_steps`, `mosaic_domains`, or any other scalar in command config; log reasoning explicitly.
- Inspect simulator code paths by running a targeted debug snippet (no edits): instantiate `Simulator` via CLI helper, print `steps`, `fluence`, `r_e_sqr`, and applied omega to confirm expected magnitudes; capture output to `intensity_gap_simulator_dump.log`.
- Diff C log `c_cli.log` vs PyTorch `torch_stdout.log` focusing on fluence, solid-angle, scaling printouts. Note any values missing on PyTorch side and quote relevant log lines in markdown.
- Extract detector pix0 vectors from both implementations (C trace + PyTorch detector repr) to ensure they match within 1e-9 meters; log results in markdown appendix.
- Run a narrow ROI comparison (e.g., 10×10 window around C peak) and compute per-pixel residual histograms saved to `intensity_gap_peak_roi.png` to visualise scaling difference.
- Update `docs/fix_plan.md` `[CLI-FLAGS-003]` Attempts History` with a new entry summarizing measurements, conclusions, and whether additional implementation work is required.
- If investigation suggests missing normalization (e.g., phi_steps), draft remediation hypotheses but stop short of code edits—document them under “Proposed Fixes” in the markdown summary.
- Capture command snippets verbatim (with env vars) in the markdown so future loops can replay analysis without ambiguity.
- Use `numpy.fromfile` with explicit dtype and shape `(2527, 2463)` to avoid accidental reshaping errors; include snippet in appendix.
- Consider plotting radial profiles (mean intensity vs radius) for both images and save to `intensity_gap_radial_profile.png`; note any constant scale shift vs structural differences.
- Record runtime for each analysis command to help future loops gauge effort; add a small table in markdown with command + duration.
- Store any CSV/JSON intermediate files mentioned in markdown; link them via relative paths for quick review.
- After analysis, re-run the parity command if (and only if) a likely fix candidate emerges; otherwise document why rerun was deferred.
- For ROI extraction, reuse `scripts/compare_outputs.py` utilities if possible; otherwise implement ad-hoc slicing with care and log coordinates used.
- When printing simulator internals, wrap calls in `torch.no_grad()` to avoid autograd overhead and mention this choice in logs.
- Validate that both float images are read in column-major order consistent with C output; note any transpositions done for plotting.
- Include a concluding checklist in the markdown summarizing unresolved questions vs confirmed causes; mark items with [ ] / [x] for clarity.
- Push all artifacts only after verifying file sizes (e.g., `ls -lh`) and reference those sizes in the markdown for sanity checks.
- Note whether PyTorch run applied automatic scaling (e.g., `Simulator` warnings); grep logs and cite absence/presence explicitly in summary.
- If time permits, compute correlation coefficient between images to confirm alignment despite scale; record value next to scale factor.

- Pitfalls To Avoid:
- Do not edit simulator or CLI code during this evidence loop; limit work to analysis scripts and documentation.
- Avoid overwriting Phase C artifacts; copy data before manipulating if needed.
- Keep computations device-neutral (numpy or torch on CPU) and note dtype conversions explicitly.
- Do not assume missing normalization factors—prove gaps with numbers before suggesting fixes.
- Preserve Protected Assets (docs/index.md references) and avoid renaming reports directories.
- Refrain from running heavy pytest suites; only gather metrics necessary for D3.
- When using python snippets, guard file paths and close resources to prevent accidental binary truncation.
- Ensure markdown summary cites exact commands, file paths, and ratios for reproducibility.
- Log every analysis attempt (success or failure) in fix_plan to maintain traceability.
- Keep environment variables consistent; include them in summary for replicability.
- Coordinate with future loops by leaving TODOs in `intensity_gap.md` if deeper implementation work is required; do not silently defer findings.
- Verify that any temporary plots or JSON files stay under reports/ (not repo root) to avoid Protected Asset violations during cleanup.
- Avoid clipping float images when loading via numpy; always work on copies and retain originals untouched for re-analysis.
- If matplotlib is used for plots, set `Agg` backend to avoid GUI requirements and record the command in the markdown.
- Guard against accidentally normalizing arrays by number of pixels when computing sums; note formula used for each metric to prevent confusion.
- Do not compress large binaries into git history; keep any zipped derivatives within reports/ and mention them explicitly before removal.
- Avoid using random sampling for ROI comparisons; deterministic slices ease reproducibility and comparison with future loops.
- Remember that python’s default float is double precision—document any conversions to maintain transparency in calculations.
- If leveraging torch for computations, be explicit about device placement to avoid silent CPU↔GPU transfers when CUDA is available.
- Maintain separation between raw evidence and interpretation: keep calculations in scripts, reserve markdown for conclusions to ensure reproducibility.
- Avoid deleting intermediate notebooks/scripts after use; commit to reports/ or document their temporary nature and deletion rationale.

Pointers:
- reports/2025-10-cli-flags/phase_c/parity/c_cli.log — Source of C fluence/solid-angle stats.
- reports/2025-10-cli-flags/phase_c/parity/torch_stdout.log — PyTorch run details; compare with C log.
- plans/active/cli-noise-pix0/plan.md:101 — Phase D scope and new D3 checklist.
- docs/architecture/pytorch_design.md:vectorization-strategy — Reference for expected batched normalization.
- src/nanobrag_torch/simulator.py:827 — Current steps normalization (sources×phi×mosaic×oversample²); verify against C behavior.
- src/nanobrag_torch/config.py:491 — Fluence computation from flux/exposure/beamsize; confirm identical to C trace.
- reports/2025-10-cli-flags/phase_a/pix0_trace/trace.log — Ground-truth pix0 vector from instrumented C run for comparison.
- docs/architecture/c_parameter_dictionary.md:detector_flags — Update target for documentation task once intensity is resolved.
- tests/test_cli_flags.py:40 — Regression coverage verifying parser behavior; ensure findings do not contradict assumptions baked into tests.
- scripts/compare_outputs.py — Existing tooling for image comparison; assess whether it can accelerate stats extraction.
- prompts/supervisor.md — Canonical parity command reference; keep any reruns faithful to this script.
- src/nanobrag_torch/simulator.py:1250 — Debug trace section documenting normalized intensity; helpful for correlating with Step prints.
- docs/architecture/detector.md:312 — Explanation of CUSTOM pivot math; confirm parity when interpreting pix0_vector outputs.
- reports/2025-10-cli-flags/phase_b/detector/cache_handoff.txt — Evidence that cache invalidation keeps overrides; cite if re-running detectors during analysis.
- docs/debugging/debugging.md:parallel-trace-rule — Reminder that future implementation changes must start with trace comparisons.
- archive/fix_plan_archive.md — For precedent on documenting physics gaps; mirror structure when writing intensity report.

Next Up:
- Phase C3 documentation updates (specs/spec-a-cli.md + README_PYTORCH.md) once intensity scaling diagnosis is complete.
- Phase D1 regression sweep (noise + pix0 tests) after documentation and intensity report are in place, ensuring no cross-component regressions.
- Coordinate with PERF-PYTORCH-004 plan if intensity analysis implicates physics normalization shared with performance tasks.
