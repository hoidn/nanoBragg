Summary: Deliver the remaining Option 1 evidence (script guidance plus archived pytest logs) so Phase M5 can close and the CLI-FLAGS-003 initiative can proceed to optional parity shims.
Mode: Docs
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_phi0.py::TestCLIScalingPhi0::test_rot_b_matches_c; tests/test_cli_scaling_phi0.py::TestCLIScalingPhi0::test_k_frac_phi0_matches_c; -m gpu_smoke tests/test_cli_scaling_phi0.py::TestCLIScalingPhi0::test_rot_b_matches_c (if CUDA); -m gpu_smoke tests/test_cli_scaling_phi0.py::TestCLIScalingPhi0::test_k_frac_phi0_matches_c (if CUDA)
Artifacts:
 - reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/<new_timestamp>/summary.md (updated narrative covering script note + test results)
   - Include explicit references to specs/spec-a-core.md:204 and docs/bugs/verified_c_bugs.md:166 inside the prose.
 - reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/<new_timestamp>/compare_scaling_traces.txt (fresh run of validation script with contextual prose)
   - Capture the full table plus a short header describing the Option 1 expectation for I_before_scaling.
 - reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/<new_timestamp>/blocker_analysis.md (appended Option 1 follow-up section)
   - Leave historical sections untouched; append the new block under a clearly dated heading.
 - reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/<new_timestamp>/commands.txt (command log for this loop)
   - Document every command executed, including copy commands and sha256sum runs, so reproducibility is complete.
 - reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/<new_timestamp>/env.json (env snapshot including CUDA availability)
   - When CUDA missing, include `"cuda_available": false` so readers know the GPU log skip is intentional.
 - reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/<new_timestamp>/sha256.txt (checksums for all bundle artifacts)
   - Ensure relative paths appear exactly once and match the repo layout for quick verification.
 - reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/<new_timestamp>/tests/pytest_cpu.log (captured stdout/stderr for CPU targeted tests)
   - Preserve the pytest header/footer so exit codes and collected test counts are visible without rerunning.
 - reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/<new_timestamp>/tests/pytest_cuda.log (GPU smoke log; include note if skipped)
   - If skipped, add a one-line justification referencing torch.cuda.is_available().
 - reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/<new_timestamp>/tests/README.md (short index explaining log contents)
   - Mention where to find the compare_scaling_traces output and summary for cross-reference.
Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — expand the spec-mode φ=0 guidance inside the validation tooling, regenerate the Option 1 spec-compliance bundle with the new comparison notes, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py` (and `KMP_DUPLICATE_LIB_OK=TRUE pytest -v -m gpu_smoke tests/test_cli_scaling_phi0.py` when CUDA is available) capturing the outputs into the refreshed bundle.
If Blocked: Capture the failing command output under reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/<stamp>/attempts/<short_description>.log, annotate the obstacle in docs/fix_plan.md Attempt history for CLI-FLAGS-003 (include failure signature and reproducibility notes), and halt without partially edited docs.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md — Rows M5e–M5g remain unchecked; the plan explicitly calls for script guidance, archived tests, and ledger sync before Long-Term Goal 1 can close. Leaving them open blocks Phase N/O parity work.
- docs/fix_plan.md:452 — The CLI-FLAGS-003 Next Actions list still references the Option 1 follow-up bundle; updating the evidence keeps the authoritative ledger synchronized with our actual deliverables and prevents duplicate assignments next loop.
- scripts/validation/compare_scaling_traces.py:1 — This script is repeatedly invoked for VG-2 validation; without a conspicuous note that spec-mode φ=0 divergence is expected, future parity runs will treat the 14.6% delta as a regression and waste time re-investigating.
- reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/20251009T011729Z/summary.md — Serves as the prior reference point. It must be superseded with updated wording that mentions the validation-script doc change, the new comparison output, and the stored pytest logs so reviewers can audit the chain quickly.
- specs/spec-a-core.md:204 — Provides the normative "rotate every φ" rule; explicitly citing this clause underpins the Option 1 rationale and prevents drift back toward C-parity implementations.
- docs/bugs/verified_c_bugs.md:166 — Documents C-PARITY-001; referencing it in both script commentary and the refreshed summary clarifies that the persistent delta is an intentional divergence from buggy C semantics.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/metrics.json — This is the numerical source for the 14.6% delta; double-check values when writing the new summary so numbers stay consistent.
 - reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T231211Z/trace_py_scaling.log — Use this trace when quoting sample numbers in the documentation updates.
How-To Map:
1. Environment preparation:
   - `export KMP_DUPLICATE_LIB_OK=TRUE` before running any Python command so torch imports succeed.
   - If you use scripts directly, ensure `PYTHONPATH=src` is set or run via the CLI entry point.
   - Confirm availability of CUDA up front via a quick `python -c "import torch; print(torch.cuda.is_available())"` and record the result for summary.md.
   - Capture the torch version (`python -c "import torch; print(torch.__version__)"`) so the summary can report exact tooling.
2. Validation script documentation update:
   - Open `scripts/validation/compare_scaling_traces.py` and extend the module docstring with a short paragraph noting that spec-mode comparisons will retain a large I_before_scaling delta because C-PARITY-001 leaves φ=0 stale.
   - Update the Usage section to mention the Option 1 bundle as the canonical example and advise readers to adjust expectations based on the spec vs C decision.
   - Add an inline comment near the tolerance handling that references docs/bugs/verified_c_bugs.md so readers inspecting the code understand why 1e-6 fails for I_before_scaling in this mode.
   - Re-run `python scripts/validation/compare_scaling_traces.py --help` briefly to ensure argument descriptions render correctly after the docstring edit.
3. Prepare the new Option 1 directory:
   - `stamp=$(date -u +%Y%m%dT%H%M%SZ)`; `out=reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/$stamp`.
   - `mkdir -p "$out"/tests` and `mkdir -p "$out"/attempts` to store logs and any fallback diagnostics.
   - Copy prior bundle files (`summary.md`, `blocker_analysis.md`, `commands.txt`) into the new directory before editing to maintain continuity.
   - Optionally copy the old env.json into the new directory as a template before overwriting.
4. Generate refreshed compare summary:
   - Execute `python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/c_trace_scaling.log --py reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/trace_py_scaling.log --out "$out"/compare_scaling_traces.txt`.
   - Review the output and verify the I_before_scaling numbers (expect ≈9.436e5 vs 8.054e5). Mention these explicitly in summary.md so the reader does not need to open the txt file to see the magnitude.
   - Add a closing paragraph inside compare_scaling_traces.txt calling out that all other factors remain within ≤1e-6 tolerance.
5. Update documentation inside the bundle:
   - Edit `$out/summary.md` to include: a recap of the script doc change, the persisted delta explanation, CPU/GPU test results, and links to spec + bug references.
   - Append a section to `$out/blocker_analysis.md` titled "Option 1 follow-up (Phase M5e/M5f)" summarizing the new artifacts and stating that the remaining gap is intentional per spec.
   - Overwrite `$out/commands.txt` with the exact commands executed this loop (script run, pytest commands, env dumps).
   - Create or update `$out/tests/README.md` with bullet points for each log, expected result, and the command that produced it.
6. Capture environment and checksums:
   - Run `python - <<'PY' > "$out"/env.json` and serialize PWD, PYTHONPATH, KMP_DUPLICATE_LIB_OK, torch version, CUDA availability, and NB_C_BIN if set.
   - Generate `sha256.txt` with `find "$out" -type f -print0 | sort -z | xargs -0 sha256sum > "$out"/sha256.txt` (sorting ensures deterministic ordering).
   - Spot-check the checksum file to ensure both pytest logs appear; add missing entries immediately if necessary.
7. Execute targeted tests and store logs:
   - `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py | tee "$out"/tests/pytest_cpu.log` so stdout/stderr are preserved verbatim.
   - If CUDA is available, `KMP_DUPLICATE_LIB_OK=TRUE pytest -v -m gpu_smoke tests/test_cli_scaling_phi0.py | tee "$out"/tests/pytest_cuda.log`; otherwise create that file with a short "CUDA unavailable" note for completeness.
   - Add a short `tests/README.md` explaining which log corresponds to which command and the expected pass/skip status.
   - Verify the pytest exit code (0 == success); document any failure immediately before retrying.
8. Synchronize planning artifacts:
   - Edit `plans/active/cli-noise-pix0/plan.md` to mark rows M5e and M5f as [D], including a note pointing to `$out`.
   - Append a new Attempt entry to docs/fix_plan.md under CLI-FLAGS-003 summarizing the documentation work, referencing `$out`, and listing test results.
   - Update galph_memory.md with a brief entry documenting completion of M5e/M5f and the path to the new bundle.
   - If CUDA was unavailable, mention that explicitly in both fix_plan and galph_memory so reviewers know why the GPU log is a stub.
9. Verification steps before finishing:
   - Re-run `sha256sum -c` within the bundle to ensure checksums match the files you intend to commit.
   - Inspect `git status` to confirm only expected files are modified (script doc update, summary files, plan, fix_plan, galph_memory, plus new reports directory).
   - Skim `input.md` to guarantee it still reflects the completed work for the next loop (if tasks finish early, note readiness for M5g in Attempts History).
   - Review the diff for scripts/validation/compare_scaling_traces.py to ensure only comments/docstrings changed and no logic was modified.
Pitfalls To Avoid:
- Do not modify simulator physics; any code changes must be limited to docstrings/comments in the validation script.
- Avoid reusing the 20251009T011729Z directory; historical bundles must remain immutable for auditability.
- Keep all new text ASCII; special symbols in docstrings or markdown complicate downstream tooling.
- When copying previous documents, update timestamps and decisions to avoid confusion about which bundle is authoritative.
- Ensure citations point to stable file paths (specs/spec-a-core.md, docs/bugs/verified_c_bugs.md) rather than external references.
- Maintain device/dtype neutrality in all prose; explicitly note when GPU execution is optional rather than assumed.
- Capture complete pytest logs; partial copies or filtered excerpts violate evidence requirements.
- Do not delete prior blocker analysis content; append new material underneath so the historical trail remains intact.
- Respect files listed in docs/index.md — no renames or deletions of protected assets like loop.sh or input.md.
- Commit plan/fix_plan updates in the same change set to avoid supervisors seeing mismatched statuses.
- Double-check compare_scaling_traces.py still runs without the new Option 1 note interfering with parsing or CLI usage.
 - Do not skip env.json; missing environment snapshots make later audits impossible.
 - Avoid forgetting to update tests/README.md—future reviewers rely on that index to interpret the stored logs quickly.
Pointers:
- plans/active/cli-noise-pix0/plan.md (rows M5e–M5g)
- docs/fix_plan.md:452
- scripts/validation/compare_scaling_traces.py
- reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/20251009T011729Z/summary.md
- specs/spec-a-core.md:204
- docs/bugs/verified_c_bugs.md:166
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/metrics.json
 - reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T231211Z/trace_py_scaling.log
 - reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T231211Z/per_phi_trace.log
Next Up: Once M5e/M5f evidence is committed, outline the exact checklist for M5g (plan + ledger sync) and draft nb-compare commands for Phase N so the handoff is ready.
