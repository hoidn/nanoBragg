Summary: Add an opt-in φ=0 carryover shim so parity mode reproduces the C bug without regressing the spec-default rotation.
Mode: Parity
Focus: CLI-FLAGS-003 / Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_phi0.py (spec + parity cases)
Artifacts:
- reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/per_phi_pytorch.json
- reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/per_phi_summary.md
- reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/trace_diff.md
- reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/pytest_cpu.log
- reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/pytest_cuda.log (if GPU run)
- reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/summary.md + sha256.txt
Do Now: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm; run KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py -v
If Blocked: Capture fresh per-φ traces via scripts/trace_per_phi.py and compare_per_phi_traces.py; log findings under reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/attempts.md before adjusting code.
Priorities & Rationale:
- specs/spec-a-core.md:211-214 — Spec mandates fresh φ rotation each step; default path must stay compliant.
- docs/bugs/verified_c_bugs.md:166-182 — Documented C-PARITY-001 bug to emulate only when parity shim enabled.
- plans/active/cli-phi-parity-shim/plan.md:44-48 — Execute Phase C1–C5 implementation, tests, traces, summary.
- docs/fix_plan.md:460-463 — Current Next Actions block CLI-FLAGS-003 until shim evidence lands.
- src/nanobrag_torch/models/crystal.py:1051-1132 — Spec-compliant φ rotation to extend with opt-in caching.
- tests/test_cli_scaling_phi0.py:1-200 — Existing spec baselines; add parity assertions alongside.
- scripts/trace_per_phi.py:1-200 — Canonical trace harness for per-φ JSON capture.
- scripts/compare_per_phi_traces.py:1-120 — Diff tool verifying parity shim reproduces C values.
How-To Map:
- Environment: export KMP_DUPLICATE_LIB_OK=TRUE before running pytest or scripts; set PYTHONPATH=src for standalone tools.
- Implementation step 1 (Phase C1): Gate an optional parity branch in Crystal.get_rotated_real_vectors via config.phi_carryover_mode; ensure tensors stay batched.
- Implementation step 2 (Phase C1): Store φ=0 cached vectors without `.detach()`; reuse them through tensor indexing when parity mode active.
- Implementation step 3 (Phase C2): Extend CrystalConfig + SimulatorConfig dataclasses and CLI argparse (src/nanobrag_torch/__main__.py) with --phi-carryover-mode {spec,c-parity}; default to "spec".
- Implementation step 4 (Phase C2): Thread new mode through simulator instantiation and ensure JSON/attempt logs reflect choice.
- Testing step 1: KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py (confirm selectors before edits).
- Testing step 2: After adding parity cases, run KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py -v (CPU baseline).
- Testing step 3: If CUDA is available, run CUDA_VISIBLE_DEVICES=0 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py -v --maxfail=1 -k parity --device cuda (add device parameter inside tests accordingly).
- Trace step 1: PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/trace_per_phi.py --outdir reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/spec/ to refresh spec baseline JSON.
- Trace step 2: Repeat trace_per_phi.py with --phi-carryover-mode c-parity (invoke CLI or config override) storing outputs under .../parity/.
- Trace step 3: Run python scripts/compare_per_phi_traces.py reports/.../spec/per_phi_pytorch.json reports/.../c_trace_phi.log and again for parity JSON to document both modes.
- CLI smoke: Run nanoBragg --phi-carryover-mode c-parity <supervisor command args> -roi 100 156 100 156 -floatfile /tmp/spec.bin -nonoise to prove flag toggles output choice without noise.
- Evidence logging: Summarise metrics, tolerances, and SHA256 digests in reports/.../summary.md; copy highlights into docs/fix_plan.md Attempt entry.
Pitfalls To Avoid:
- Do not regress the spec-default φ rotation; shim must be opt-in and preserve device/dtype neutrality end-to-end.
- Avoid Python loops over φ or mosaic; rely on tensor broadcasting/masking when swapping cached values.
- Remember CLAUDE Rule #11: include the nanoBragg.c snippet when introducing parity-specific logic.
- Keep Protected Assets untouched (docs/index.md listings, e.g., loop.sh, supervisor.sh, input.md).
- Preserve gradient flow (no `.item()`, `.detach()`, `.cpu()` on differentiable tensors inside simulation path).
- Ensure new CLI flag honours config map conventions and updates help text; avoid silently enabling shim.
- Handle serialization: update config -> dict conversions so parity mode persists in saved configs/traces.
- Verify tests skip gracefully when A.mat or scaled.hkl missing; maintain existing skip messaging.
- When running CUDA tests, guard with torch.cuda.is_available() to prevent false failures.
- Document parity shim availability in reports/diagnosis.md without altering normative spec shards.
Pointers:
- plans/active/cli-phi-parity-shim/plan.md:44-59 — Phase C + D tasks and exit criteria.
- docs/fix_plan.md:460-463 — CLI-FLAGS-003 Next Actions referencing this shim.
- docs/bugs/verified_c_bugs.md:166-182 — Source of parity behaviour to emulate.
- specs/spec-a-core.md:211-214 — Normative φ rotation description (default path reference).
- src/nanobrag_torch/models/crystal.py:1051-1132 — Implementation hotspot for parity toggle.
- tests/test_cli_scaling_phi0.py:1-200 — Existing tests to extend with parity mode parameterisation.
- scripts/trace_per_phi.py:1-200 — Trace capture entry point.
- scripts/compare_per_phi_traces.py:1-120 — Diff harness for C vs PyTorch traces.
- docs/architecture/pytorch_design.md:94-142 — Vectorization and batching expectations to uphold.
- docs/development/testing_strategy.md:69-120 — Device/dtype discipline for targeted parity runs.
Next Up:
1. Phase L3k.3c.5 documentation + dual-mode test refresh (plans/active/cli-phi-parity-shim/plan.md:55-59).
2. Phase L3k.3d nb-compare ROI parity sweep once VG-1 & VG-3 pass with shim in place.
3. Phase L3k.4 final supervisor command rerun after parity + normalization gates succeed.
Execution Checklist:
- [ ] Phase C1 parity toggle coded with tensor indexing (spec path unchanged).
- [ ] Phase C2 CLI flag threads through CrystalConfig, SimulatorConfig, argparse help.
- [ ] Phase C3 tests updated with param to cover mode in {spec,c-parity} across CPU+CUDA.
- [ ] Phase C4 per-φ traces captured for both modes and compared against C log.
- [ ] Phase C5 summary.md + docs/fix_plan Attempt entry drafted with metrics + SHA references.
- [ ] CLI help text shows --phi-carryover-mode option with default spec.
- [ ] nanoBragg --phi-carryover-mode spec reproduces current spec baselines exactly.
- [ ] nanoBragg --phi-carryover-mode c-parity reproduces C-PARITY-001 metrics within ≤1e-6 for k_frac and rot_b.
- [ ] pytest logs archived under reports/.../pytest_cpu.log and pytest_cuda.log (when run).
- [ ] Collect-only log stored as reports/.../pytest_collect.log for traceability.
Verification Notes:
- Confirm the parity shim sets cached φ vectors only after spec rotations complete to avoid gradient discontinuities.
- Validate that cached tensors respect requested dtype (float32 default, float64 when CLI dtype override provided).
- Run torch.autograd.gradcheck on a reduced-size scenario (optional) to confirm graph continuity when shim toggled.
- Inspect config dumps to ensure phi_carryover_mode persists through serialization/deserialization paths.
- Use scripts/c_reference_utils.py if you need to regenerate the C command with parity flag context.
- Double-check that per-φ JSON includes phi_tic 0-9 entries; missing rows indicate upstream trace capture failure.
- Keep parity-mode tests marked or named clearly (e.g., test_k_frac_phi0_matches_c_parity) to distinguish from spec tests.
- After implementation, rerun nb-compare smoke on a tiny ROI (optional) to sanity-check intensity parity before larger sweeps.
Command Recap:
- Spec trace refresh: PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/trace_per_phi.py --outdir reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/spec/
- Parity trace refresh: PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE PHI_CARRYOVER_MODE=c-parity python scripts/trace_per_phi.py --outdir reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/parity/
- Trace diff: python scripts/compare_per_phi_traces.py reports/.../spec/per_phi_pytorch.json reports/.../c_trace_phi.log
- Trace diff parity: python scripts/compare_per_phi_traces.py reports/.../parity/per_phi_pytorch.json reports/.../c_trace_phi.log
- CPU pytest: KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py -v --maxfail=1
- CUDA pytest: CUDA_VISIBLE_DEVICES=0 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py -v --maxfail=1 -k parity --device cuda
- CLI smoke (spec): nanoBragg --phi-carryover-mode spec @commands/supervisor_cli_flags.txt -nonoise -roi 100 156 100 156 -floatfile /tmp/spec.bin
- CLI smoke (parity): nanoBragg --phi-carryover-mode c-parity @commands/supervisor_cli_flags.txt -nonoise -roi 100 156 100 156 -floatfile /tmp/parity.bin
- Collect-only: KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py > reports/.../pytest_collect.log
- Gradcheck probe (optional): PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_scaling_pipeline.py --phi-carryover-mode c-parity --device cpu --dtype float64
Observability Notes:
- Update reports/.../sha256.txt with hashes for per_phi_pytorch.json, per_phi_summary.md, trace_diff.md, pytest logs, and summary.md.
- Include metadata.json summarising command-line env vars (NB_C_BIN, PHI_CARRYOVER_MODE, devices) alongside traces.
- Capture stdout/stderr from nanoBragg smoke runs into reports/.../cli_spec.log and cli_parity.log for auditability.
- When editing docs/fix_plan.md, append Attempt entry with commit SHA, test commands, and artifact paths.
- Annotate summary.md with VG gate checklist (VG-1 through VG-5) marking pass/fail per mode.
- If nb-compare is exercised, stash outputs under reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/nb_compare/ with threshold metadata.
