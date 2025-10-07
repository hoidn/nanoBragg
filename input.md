Summary: Align HKL cache IO with nanoBragg C so structure-factor parity unblocks the supervisor command.
Mode: Parity
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_flags.py::TestHKLFdumpParity::test_scaled_hkl_roundtrip
Artifacts: reports/2025-10-cli-flags/phase_l/hkl_parity/L1c_roundtrip/
Do Now: docs/fix_plan.md#cli-flags-003-handle-nonoise-and-pix0_vector_mm Phase L1c — author failing parity test `tests/test_cli_flags.py::TestHKLFdumpParity::test_scaled_hkl_roundtrip`, confirm it fails, then run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestHKLFdumpParity::test_scaled_hkl_roundtrip -v`
If Blocked: Capture `reports/2025-10-cli-flags/phase_l/hkl_parity/L1c_roundtrip/blocked_l1c.md` with stdout/stderr excerpts, cache SHA256, and hypotheses; update docs/fix_plan.md Attempt log before escalating.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:200 positions Phase L1c as the gating task before scaling diagnostics resume.
- docs/fix_plan.md:456 lists L1c as the active next step given L1b evidence is archived.
- specs/spec-a-core.md:460 codifies the ordering of HKL indices and acceptable tolerances (<1e-6 electrons) for parity.
- golden_suite_generator/nanoBragg.c:2359-2486 prove the `(range+2)` padding and must be mirrored exactly to avoid latent mismatches.
- docs/architecture/pytorch_design.md:118 stresses device/dtype neutrality for IO layers that feed simulator tensors.
- docs/development/testing_strategy.md:80 mandates targeted pytest selectors prior to code edits landing.
- scripts/validation/analyze_fdump_layout.py:25 documents the padding diagnosis; L1c must make PyTorch honor that layout.
- reports/2025-10-cli-flags/phase_l/hkl_parity/layout_analysis.md:1 records the Δk/Δl offsets that disappear once L1c succeeds.
How-To Map:
- Step 1: Refresh cache inventory. List existing caches in `reports/2025-10-cli-flags/phase_l/hkl_parity/` and choose the latest timestamp. If a fresh cache is required, execute the supervisor command with `NB_C_BIN=./golden_suite_generator/nanoBragg` and record stdout to `c_fdump_<STAMP>.log`.
- Step 2: Compute and record SHA256 hashes for both `scaled.hkl` and the chosen Fdump binary; store them in `hashes_<STAMP>.txt` under the L1c artifact folder.
- Step 3: Create the new pytest class `TestHKLFdumpParity` inside `tests/test_cli_flags.py` (or a dedicated test file) and add a test that reads the HKL grid, reads the Fdump cache, and compares values after slicing out padding planes.
- Step 4: Ensure the test first fails by asserting equality before touching production code; capture the failure message and include it in Attempt history.
- Step 5: Modify `read_fdump` to reshape the raw buffer into `(h_extent+1, k_extent+1, l_extent+1)` using the C-style `range+1` definitions, then truncate the final plane along each axis before returning the tensor and metadata.
- Step 6: Update `write_fdump` to allocate a zero-initialised tensor with the padded dimensions, copy the in-bounds data into the leading block, and write the padded buffer exactly once; document the C reference (Rule #11) in the docstring or inline comment.
- Step 7: Re-run the new pytest selector `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestHKLFdumpParity::test_scaled_hkl_roundtrip -v` and confirm it now passes instead of failing.
- Step 8: Execute `env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_flags.py` to verify selector stability after the file edit.
- Step 9: Run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_structure_factors.py --hkl scaled.hkl --fdump <updated_cache> --out reports/2025-10-cli-flags/phase_l/hkl_parity/L1c_roundtrip/summary_<STAMP>.md --metrics reports/2025-10-cli-flags/phase_l/hkl_parity/L1c_roundtrip/metrics_<STAMP>.json` and confirm max |ΔF| ≤ 1e-6 and mismatches = 0.
- Step 10: Append a concise Attempt entry to docs/fix_plan.md with metrics, hashes, and artefact paths; update the plan table to mark L1c complete.
- Step 11: Stage artefacts under `reports/2025-10-cli-flags/phase_l/hkl_parity/L1c_roundtrip/`, including hashes, markdown summary, JSON metrics, and the command transcript.
- Step 12: Prepare for L1d by noting which cache will be re-used for the parity rerun and confirming the comparison script uses the same timestamp.
Pitfalls To Avoid:
- Do not strip padding from the on-disk cache—PyTorch must speak the exact binary format nanoBragg produces.
- Avoid hard-coded CPU or float64 behaviour; respect the dtype/device of tensors returned by IO helpers.
- Remember to set `KMP_DUPLICATE_LIB_OK=TRUE` in every script and test; missing it will crash under MKL.
- Keep new artefacts timestamped; never overwrite previous evidence in the reports hierarchy.
- Preserve Protected Assets; never move or delete files listed in docs/index.md.
- Ensure tests that invoke the C binary clean up temporary files or run in a temporary directory to avoid polluting the repo root.
- Resist restoring Python loops when trimming padded tensors; stay within vectorised tensor operations.
- Avoid `.item()` on tensors that might later require gradients; IO layers should remain graph-friendly.
- Validate file existence with pathlib before copying or deleting to prevent accidental data loss.
- Do not run the full pytest suite during this loop; keep execution targeted per the testing strategy.
- Document cache SHA256 hashes to maintain provenance for subsequent parity checks.
- If you add helper functions, place them under `scripts/validation/` and include brief comments for clarity.
- Confirm metadata integers remain unchanged when slicing padded planes; mismatched metadata invalidates parity.
- After edits, rerun `scripts/validation/analyze_fdump_layout.py` if needed to double-check padding alignment; keep results with L1c artefacts.
Pointers:
- plans/active/cli-noise-pix0/plan.md:200 lists task states for Phase L1 and expected outputs.
- docs/fix_plan.md:456 enumerates L1c/L1d next actions to keep fix_plan aligned with evidence.
- specs/spec-a-core.md:460 provides the normative HKL grid contract for parity comparisons.
- docs/architecture/pytorch_design.md:118 reiterates IO and vectorisation guardrails.
- docs/development/testing_strategy.md:80 captures supervisor evidence policies and targeted-test workflow.
- scripts/validation/compare_structure_factors.py:17 shows tolerance handling; mirror its thresholds.
- scripts/validation/analyze_fdump_layout.py:25 summarises the padding analysis leveraged by L1c.
- src/nanobrag_torch/io/hkl.py:1 houses the read/write logic that must be updated.
- golden_suite_generator/nanoBragg.c:2359 demonstrates the exact writer loops to cite in comments.
- reports/2025-10-cli-flags/phase_l/hkl_parity/layout_analysis.md:1 records Δh/Δk/Δl statistics prior to the fix.
- reports/2025-10-cli-flags/phase_l/hkl_parity/Fdump_scaled_20251006175946.bin is the latest cache awaiting parity validation.
Verification Checklist:
- [ ] Failing pytest recorded before code change with error message stored in Attempt log.
- [ ] `read_fdump` returns tensors matching HKL grid with no mismatches beyond tolerance.
- [ ] `write_fdump` produces identical binary size and SHA as the C-generated cache.
- [ ] Targeted pytest selector passes on CPU; CUDA optional but note availability.
- [ ] `compare_structure_factors.py` metrics report max |ΔF| ≤ 1e-6 and mismatches = 0.
- [ ] docs/fix_plan.md entry updated with metrics, artefact links, and new Attempt number.
- [ ] plans/active/cli-noise-pix0/plan.md marks L1c as [D] with guidance refreshed.
- [ ] Artefacts archived under L1c_roundtrip/ with hashes and command transcript.
- [ ] Input.md updated (done) and Do Now recorded in Attempts History when Ralph begins execution.
Notes:
- Keep command transcripts in plain text; avoid binary logs that cannot be diffed easily.
- Record environment variables used during cache generation for reproducibility.
- When adding imports to tests, maintain alphabetical order to keep lint clean.
- Reference existing CLI fixtures in `tests/test_cli_flags.py` to minimise boilerplate.
- Consider parameterising the new test to exercise both float32 and float64 read paths.
- Document any temporary workarounds inside the test with TODOs linked to plan entry L1c.
- Ensure temporary directories are cleaned via context managers so no stray files linger.
- Capture timing data for `read_fdump` before and after the change if performance shifts noticeably.
- Keep metadata dictionaries immutable (tuples) when returning from IO helpers to avoid accidental mutation.
- Run `python -m compileall src/nanobrag_torch/io/hkl.py` if syntax issues appear late in the loop.
- Validate that error messages remain informative when Fdump is missing or malformed; add tests if needed.
- Before staging, run `git diff --stat` to confirm only expected files changed.
- Keep commit messages under the SUPERVISOR scope per repository policy.
- Archive raw command outputs under the artifact directory to avoid relying on terminal scrollback.
- Tag Attempt entries with precise UTC timestamps for traceability across machines.
- Verify that the new test honours `NB_RUN_PARALLEL` expectations (skip when env var unset).
- Add a docstring to the new test class summarising its intent and linking to plan Phase L1c.
- Ensure helper functions introduced in tests remain private (prefix with `_`).
- Avoid global mutable state in tests; use fixtures instead for deterministic behaviour.
- Confirm the test gracefully skips if `scaled.hkl` or the cache is unavailable.
- Update `.gitignore` only after supervisor approval; unnecessary changes risk hiding artefacts.
- Wrap long documentation lines at ~100 characters to keep diffs readable.
- When regenerating caches, include the exact command string in docs/fix_plan.md Attempt log.
- Run `nb-compare --help` if any CLI syntax doubts arise before Phase L1d.
- Maintain consistent timestamp format `YYYYMMDDHHMMSS` across new artefact names.
- Check for stray `Fdump.bin` in repo root and relocate it into the artifact folder if present.
- Update `scripts/validation/README.md` if new validation helpers are introduced this loop.
- Verify `tests/__pycache__/` remains clean after pytest; delete residual files if necessary.
- Ensure all new files follow UTF-8 encoding without BOM.
- Confirm plan updates reference the correct Attempt numbers to avoid confusion.
- Keep noise-handling flags untouched; parity work should not regress -nonoise behaviour.
- If CLI parsing changes sneak in, rerun `pytest tests/test_cli_flags.py::TestCLINoiseFlag` to confirm safety.
- Log any differences between expected and observed padding counts in the artefact markdown.
- Snapshot the first few doubles of the updated cache using `hexdump -C` if anomalies persist.
- Add assertions ensuring padding planes remain zero after writing to catch regressions quickly.
- Explicitly set `dtype=np.float64` in NumPy usage to avoid platform-dependent defaults.
- Cross-check PyTorch vs NumPy reshape semantics so axes remain aligned.
- Watch memory usage when allocating padded tensors for large grids; note any spikes in the report.
- If CUDA is available, optionally run the new test on GPU and record whether parity holds there too.
- After editing docs/fix_plan.md, re-run any markdown linting to ensure formatting compliance.
- Leave breadcrumbs in `galph_memory.md` once work lands so future loops retain context.
- Notify supervisor via Attempt log if additional tooling becomes necessary mid-loop.
- Capture `git status` output after producing artefacts to demonstrate cleanliness before commit.
- Keep commit scope narrow; avoid bundling unrelated documentation edits.
- Double-check that `input.md` remains untouched by Ralph; only supervisor updates are allowed.
- Re-run the supervisor coin-flip step next loop before reviewing Ralph’s history to stay compliant.
- Stage any temporary scripts under `scratch/` and remove them before committing to keep tree tidy.
- Document expected runtime of the parity script to set expectations for future reruns.
- If the new test requires fixtures, colocate them with existing CLI fixtures for discoverability.
- Ensure Attempt numbering increments sequentially without gaps for auditability.
- After L1c completes, update `reports/README.md` (if present) with a short artefact summary.
- Validate the CLI still loads via `python -m nanobrag_torch --help` after IO changes.
- For Windows compatibility, avoid assumptions about newline handling in binary headers.
- Record any open questions or follow-ups in docs/fix_plan.md so the next supervisor loop can address them.
- Note CPU/GPU details in the artefact summary if relevant to parity results.
- Verify the new IO logic avoids in-place mutation of inputs, maintaining functional style.
- Add explicit unit assertions for metadata values if regression risk feels high.
- Remove any temporary logging before committing; keep final code clean.
- Ensure imports in the modified files align with project style (standard library, third-party, local).
- In docstrings, keep C-code references formatted using the project’s template with triple backticks.
- Choose test names that are grep-friendly (`hkldump` etc.) for quick reruns later.
- Stick to lowercase and underscores for new artefact folder names to maintain consistency.
- Confirm this `input.md` stays within the mandated 100–200 line envelope; adjust future edits accordingly.
Next Up: Phase L1d — rerun `compare_structure_factors.py` with the fixed IO path and capture refreshed evidence before tackling scaling-chain diagnostics.
