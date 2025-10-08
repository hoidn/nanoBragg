Summary: Capture Phase M3 parity probes so we know whether the φ rotation pipeline or sincg evaluation causes the I_before_scaling gap.
Mode: Parity
Focus: CLI-FLAGS-003 / Phase M3 probes (plans/active/cli-noise-pix0/plan.md)
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py::TestCLIScalingPhi0::test_rot_b_matches_c tests/test_cli_scaling_phi0.py::TestCLIScalingPhi0::test_k_frac_phi0_matches_c
Artifacts:
- reports/2025-10-cli-flags/phase_l/scaling_validation/<stamp>/phase_m3_probes/trace_py_phi.log (PyTorch per-φ trace matching C schema)
- reports/2025-10-cli-flags/phase_l/scaling_validation/<stamp>/phase_m3_probes/trace_c_phi.log (fresh C reference for the same pixel)
- reports/2025-10-cli-flags/phase_l/scaling_validation/<stamp>/phase_m3_probes/sincg_sweep.md (table + plot for k ∈ [-0.61,-0.58])
- reports/2025-10-cli-flags/phase_l/scaling_validation/<stamp>/phase_m3_probes/phistep1/ (single-φ PyTorch & C traces + float images)
- reports/2025-10-cli-flags/phase_l/scaling_validation/<stamp>/phase_m3_probes/rotation_audit.md (side-by-side basis vectors vs nanoBragg.c)
- reports/2025-10-cli-flags/phase_l/scaling_validation/<stamp>/phase_m3_probes/summary.md (overview + open questions + git SHA)
- reports/2025-10-cli-flags/phase_l/scaling_validation/<stamp>/phase_m3_probes/commands.txt and sha256.txt (repro + integrity)
- reports/2025-10-cli-flags/phase_l/scaling_validation/<stamp>/phase_m3_probes/env.json (python/torch/pyrefly versions for reproducibility)
- reports/2025-10-cli-flags/phase_l/scaling_validation/<stamp>/phase_m3_probes/git_sha.txt (commit recorded after probes land)
- reports/2025-10-cli-flags/phase_l/scaling_validation/<stamp>/phase_m3_probes/pytest.log (stdout from mapped tests)
- reports/2025-10-cli-flags/phase_l/scaling_validation/<stamp>/phase_m3_probes/sincg_sweep.png (optional visualization referenced in sincg_sweep.md)
- reports/2025-10-cli-flags/phase_l/scaling_validation/<stamp>/phase_m3_probes/pytest_collect.log (collect-only output if needed)
- reports/2025-10-cli-flags/phase_l/scaling_validation/<stamp>/phase_m3_probes/diff_trace.md (first-delta narrative between PyTorch and C per-φ logs)
- reports/2025-10-cli-flags/phase_l/scaling_validation/<stamp>/phase_m3_probes/roi_metadata.json (pixel coordinates, detector geometry snapshot)
- reports/2025-10-cli-flags/phase_l/scaling_validation/<stamp>/phase_m3_probes/compare_scaling_traces.json (parser output for per-factor deltas post-probes)
- docs/fix_plan.md Attempt #187 with probe summary + artifact paths
Do Now: CLI-FLAGS-003 Phase M3 probes; KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py::TestCLIScalingPhi0::test_rot_b_matches_c tests/test_cli_scaling_phi0.py::TestCLIScalingPhi0::test_k_frac_phi0_matches_c
If Blocked: Record partial probes in phase_m3_probes/summary.md with blocker details, stash whatever trace data exists, run the mapped pytest in --collect-only mode to capture the failure or blockage, update docs/fix_plan.md Attempt with the partial bundle path, and stop.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:56-60 locks M3a–M3d as the gate before any simulator fix.
- docs/fix_plan.md:461-467 demands completion of M3 probes before M4 code edits.
- specs/spec-a-core.md:204-236 defines the φ rotation + sincg contract we need to audit.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/analysis_20251008T212459Z.md elevates Hypothesis H4 (rotation mismatch) and prescribes today’s probes.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/commands.txt captures the baseline harness invocation to reuse for new traces.
- scripts/validation/compare_scaling_traces.py output shows current divergence limited to I_before_scaling, so probes must target lattice math.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/metrics.json lists the 14.6% delta we must explain before nb-compare reruns.
- docs/architecture/pytorch_design.md:42-88 reiterates vectorization + device neutrality rules that the new instrumentation must respect.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md ranks H4 as HIGH confidence, making M3 probes the critical validation path.
- galph_memory.md latest entry (2025-10-08) commits the supervisor to deliver a Phase M3 handoff next.
- docs/development/testing_strategy.md:34-118 requires authoritative commands + artifact logs for parity evidence, so today’s bundle must be thorough.
- prompts/pyrefly.md reminds us to capture env metadata whenever instrumentation changes surface area (env.json task).
- reports/2025-10-cli-flags/phase_phi_removal/phase_d/20251008T203504Z/trace_py_spec.log confirms prior trace formats we must remain compatible with.
- scripts/validation/compare_scaling_traces.py:12 documents expected JSON schema; today’s probes should keep output consistent for downstream automation.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T070513Z/trace_tooling_audit.md shows prior trace gating; reuse its checklist when committing new hooks.
How-To Map:
- Reuse the baseline harness command from spec_baseline/commands.txt, adding a fresh timestamp env var, e.g.:
  STAMP=$(date -u +%Y%m%dT%H%M%SZ) && \
  KMP_DUPLICATE_LIB_OK=TRUE python scripts/trace_harness.py \
    --profile scaling --out reports/2025-10-cli-flags/phase_l/scaling_validation/${STAMP}/phase_m3_probes \
    --trace-pixel 685 1039 --device cpu --dtype float64 --emit-per-phi
- After wiring the PyTorch trace logging, regenerate the C trace with the same STAMP by exporting NB_C_BIN and running the supervisor command with -trace_pixel 685 1039 > trace_c_phi.log.
- Build the sincg sweep via a short notebook or script: load torch.float64 tensors, evaluate sincg(PI*k, Nb=47) using utils.physics.sincg, and write the table/plot to sincg_sweep.md (include CSV/PNG if generated).
- For the single-φ check, rerun both implementations with -phisteps 1 -osc 0, saving traces and float images under phistep1/ plus a note explaining observed F_latt.
- Rotation audit: instrument Crystal.get_rotated_real_vectors to dump basis vectors before/after φ, capture values in rotation_audit.md with references to nanoBragg.c line numbers.
- Run the mapped pytest command once probes are in place to ensure spec-mode tests still pass; capture stdout under phase_m3_probes/pytest.log.
- Finish by updating commands.txt, sha256.txt, and docs/fix_plan.md with the new Attempt number and artifact list.
- Guard the new trace hooks with the existing `enable_trace` context manager so normal runs stay silent.
- After generating each artifact, append its path + SHA256 to sha256.txt immediately to avoid omissions.
- Diff trace_py_phi.log vs trace_c_phi.log (e.g., `colordiff`) and cite first mismatch in summary.md to focus M4 work.
- Use `rg "TRACE_PY_PHI" src` before committing to confirm instrumentation only fires under the trace flag.
- Create env.json via `python - <<'PY'` snippet that serialises sys.version, torch.__version__, device availability, and git SHA.
- Update lattice_hypotheses.md with probe outcomes so future loops see which hypotheses remain viable.
- Copy the phistep1 float images into results/ alongside a checksum so nb-compare can reference them later if needed.
- Run `pytest --collect-only -q tests/test_cli_scaling_phi0.py` before the full selector if imports break; save output to pytest_collect.log in the probe bundle.
- Capture a short `notes.txt` in phistep1/ explaining how osc/phisteps were altered and whether any command-line deviations were necessary.
- Use `python -m scripts.validation.compare_scaling_traces` with `--emit-json` pointing at the new per-φ logs to verify parser compatibility before summarising.
- After each probe, update phase_m3_probes/summary.md with a numbered subsection so later readers can tie evidence to tasks M3a–M3d.
- Verify the new instrumentation respects `KMP_DUPLICATE_LIB_OK=TRUE` by running the harness once without the env var (expect failure) and logging that in summary.md.
- Stage only intentional code edits (`git add src/... scripts/...`) before running tests to avoid noise in Attempt logs.
- When finished, paste the exact harness command used into docs/fix_plan.md Attempt #187 for traceability.
- Record `torch.cuda.is_available()` status in env.json so later CUDA smoke tests can reuse the same environment expectations.
- After instrumentation changes, run `python -m nanobrag_torch --help` to confirm CLI help output is unchanged; note the result in summary.md.
- Package any helper scripts under scripts/validation/ if created, and link them from summary.md so they are easy to find.
Pitfalls To Avoid:
- Do not regress vectorization when adding trace hooks; reuse existing batched tensors and guard with trace flags.
- Keep device/dtype neutrality; no hard-coded .cpu()/.double() in production paths.
- Maintain CLAUDE Rule #11: include nanoBragg.c snippets in any new docstrings if you touch simulator/crystal code.
- Respect Protected Assets; do not move or delete files listed in docs/index.md.
- Ensure trace files distinguish Py vs C via prefixes (`TRACE_PY_PHI`, `TRACE_C_PHI`).
- Capture environment metadata (python -V, torch version) before leaving the bundle.
- Don’t forget to git add updated docs/fix_plan.md when logging Attempt #187.
- Avoid running full pytest; stick to the mapped selectors after code changes.
- Confirm hash files include every artifact you generate to keep bundles reproducible.
- Keep phistep1 experiment deterministic (seed reuse) so comparisons to the baseline remain meaningful.
- Avoid writing probe scripts outside scripts/validation/; keep everything inside the reports bundle or reusable tooling paths.
- Don’t check in large binary artefacts; keep float images under 5 MB and rely on sha256 for verification instead of Git LFS.
- Ensure sincg sweep uses float64 arithmetic; float32 will hide the zero-crossing we need to observe.
- When editing instrumentation, avoid mixing f-strings with `%` formatting to keep trace lines consistent with C.
- Keep summary.md concise but include direct links to every artifact so later reviewers do not hunt through the bundle.
- Double-check that trace files end with newlines; diff tools relying on POSIX text files require it.
Pointers:
- plans/active/cli-noise-pix0/plan.md:25,54-60 (status snapshot + M3 task definitions)
- docs/fix_plan.md:461-467 (Next Actions expectations for CLI-FLAGS-003)
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/analysis_20251008T212459Z.md:1 (hypotheses + required probes)
- specs/spec-a-core.md:204 (φ rotation + sincg contract)
- scripts/trace_harness.py: header (existing CLI flags for trace generation)
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md:5 (current hypothesis log)
- docs/architecture/pytorch_design.md:42 (vectorization guardrails relevant to instrumentation)
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/metrics.json:3 (numerical deficit to match)
- plans/active/phi-carryover-removal/plan.md:68 (post-shim guard context for trace tooling)
- docs/development/testing_strategy.md:45 (parity evidence workflow + trace storage rules)
- reports/2025-10-cli-flags/phase_phi_removal/phase_d/20251008T203504Z/rg_phi_carryover.txt:1 (verify no stray carryover traces return)
- scripts/validation/README.md:1 (baseline instructions for running validation helpers)
- docs/bugs/verified_c_bugs.md:166 (C-only φ-carryover write-up to cite when explaining probe scope)
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/summary_addendum.md:1 (prior bundle pointer structure to mirror)
Next Up: Phase M4 physics fix once probes confirm the rotation hypothesis.
