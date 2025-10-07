Summary: Restore φ=0 parity guard so CLI-FLAGS-003 work resumes on a real failure signal.
Mode: Parity
Focus: CLI-FLAGS-003 / Phase L3k.3c φ=0 parity restoration
Branch: feature/spec-based-2
Mapped tests: env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c -vv
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/pytest_phi0_regression.log; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<timestamp>/; reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md updates; docs/fix_plan.md Attempt log entry
Do Now: CLI-FLAGS-003 (Handle -nonoise and -pix0_vector_mm) — restore the C-aligned assertions in tests/test_cli_scaling_phi0.py and capture the failing run via env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c -vv
If Blocked: Re-run the per-φ trace harness (reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/trace_py_rot_vector_202510070839.log) and annotate divergence in diagnosis.md; update Attempts History with findings before proceeding.
Priorities & Rationale:
- docs/fix_plan.md CLI-FLAGS-003: Attempt #102 is now flagged invalid; we need the regression visible so VG-1 gating drives the fix sequence.
- plans/active/cli-noise-pix0/plan.md L3k.3c.1: Mandates reinstating the C trace assertions before any implementation work resumes.
- specs/spec-a-parallel.md §Parallel Validation: Translation correctness requires PyTorch to match the C binary even when the reference reuses state; fixing parity is prerequisite to long-term Goal #1.
- specs/spec-a-core.md §Geometry & Sampling: Describes φ sweep semantics; test should align with those rules before diagnosing implementation gaps.
- docs/development/c_to_pytorch_config_map.md: Confirms spindle-axis and φ-step ordering; use it to sanity-check the restored assertions and trace harness inputs.
- docs/debugging/debugging.md §Parallel Trace SOP: Guides the evidence we expect in diagnosis.md once the test is red again.
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/202510070839/: Contains the authoritative C vs PyTorch traces for pixel (685,1039); leverage these when resetting expectations.
- prompts/supervisor_command.md (if present) & prompts/callchain.md: Ensure any additional tracing sticks to the documented instrumentation schema.
- docs/architecture/c_parameter_dictionary.md: Keep flag interpretations aligned when regenerating traces or revisiting the harness configuration.
How-To Map:
- Ensure editable install (`pip install -e .`) is still active; reinstall only if dependencies shifted since last loop.
- Inspect current `tests/test_cli_scaling_phi0.py` to note PyTorch-biased assertions; reintroduce the C reference values (`rot_b_y=0.6715882339`, `k_frac=-0.6072558396`) using pytest assertions with explicit tolerances.
- Remove the unconditional skip on `test_k_frac_phi0_matches_c`; convert it back to a real assertion tied to the same C trace.
- Once assertions are restored, run `env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c -vv | tee reports/2025-10-cli-flags/phase_l/rot_vector/pytest_phi0_regression.log`.
- Record the failing output (expected) and include command + SHA256 of the log in docs/fix_plan.md Attempts History entry.
- If additional context is required, run `python scripts/trace_harness.py --config prompts/supervisor_command.yaml --trace 685 1039 --out reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<timestamp>/` to regenerate PyTorch traces alongside the existing C logs.
- Update `diagnosis.md` within the same directory summarizing the restored delta (Δrot_b_y, Δk_frac) and linking to the failing pytest output.
- Before finishing the loop, append Attempt notes under CLI-FLAGS-003 documenting the restored red test and artifact paths.
- Keep environment variables `KMP_DUPLICATE_LIB_OK=TRUE` and `NB_RUN_PARALLEL=1`; set `NB_C_BIN=./golden_suite_generator/nanoBragg` if the harness requires explicit C binary selection.
- Coordinate with `plans/active/cli-noise-pix0/plan.md` checklist L3k.3c.1–L3k.3c.3; tick progress locally but leave final status updates for after passing evidence is captured.
- Use `git status` before committing to ensure only targeted test/docs files are staged; avoid touching production src until L3k.3c.1 is complete.
Pitfalls To Avoid:
- Do not attempt Phase L3k.3c.2 implementation work until the regression test is restored and documented as failing.
- Avoid reinterpreting the C trace as a bug without supervisor sign-off; parity with current binary is mandatory for the supervisor command goal.
- Do not drop the per-φ JSON artifacts already captured; reuse them and add new timestamps rather than overwriting.
- No `.item()` calls on tensors within the test updates; use float literals or `float(tensor)` only after cloning to CPU when needed.
- Maintain device/dtype neutrality in any helper computations; default to `dtype=torch.float64` only when explicitly required by the test.
- Keep Protected Assets intact (docs/index.md, loop.sh, supervisor.sh, input.md); double-check before staging changes.
- Resist touching vectorization or performance plans; stay scoped to CLI-FLAGS-003 Phase L3k.3c tasks.
- Do not run the full pytest suite; focus on the targeted selector and optionally `--collect-only` if import issues appear.
- Avoid editing prompt or plan files unless new evidence mandates it; coordinate with supervisor if additional plan tweaks seem necessary.
- Ensure Attempt logs capture both the failing command and artifact locations; missing metadata slows future diagnosis.
- Do not delete or relocate any reports captured on 2025-10-07; they are referenced by the plan and fix_plan entries.
- Avoid reusing old timestamps for new artifacts; create a fresh `<timestamp>` folder for clarity.
Pointers:
- specs/spec-a-cli.md §§CLI Interface, φ sampling
- specs/spec-a-core.md §3 (Rotation order) & §4 (Sampling loops)
- docs/development/c_to_pytorch_config_map.md (spindle axis, phi semantics)
- docs/fix_plan.md CLI-FLAGS-003 entry (Attempts #101–102 context)
- plans/active/cli-noise-pix0/plan.md L3k.3c tasks table
- docs/debugging/debugging.md §Parallel Trace Comparison Rule
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/202510070839/c_trace_phi_202510070839.log
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/202510070839/trace_py_rot_vector_202510070839.log
- tests/test_cli_scaling_phi0.py (restore assertions + drop skip)
- docs/architecture/c_parameter_dictionary.md (verify supervisor command flag semantics)
Next Up: Once φ=0 parity is red again with C-aligned expectations, proceed to L3k.3c.2 to diagnose the state carryover gap before coding a fix.
