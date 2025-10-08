## Context
- Initiative: Long-term Goal 1 — remove the φ carryover reproduction path and associated technical debt introduced during CLI-FLAGS-003.
- Phase Goal: Retire the opt-in `--phi-carryover-mode c-parity` shim, delete dependent parity harnesses/tests, and realign documentation/plan inventory with the normative spec (fresh φ rotations each step).
- Dependencies:
  - `specs/spec-a-core.md:204-240` — authoritative φ rotation pipeline (no carryover allowed).
  - `docs/bugs/verified_c_bugs.md:166-204` — C-PARITY-001 bug dossier that must remain C-only after this effort.
  - `plans/active/cli-noise-pix0/plan.md` — currently orchestrates CLI-FLAGS-003 phases; requires reprioritisation once shim removal begins.
  - `tests/test_cli_scaling_phi0.py` & `tests/test_phi_carryover_mode.py` — acceptance and regression coverage that will be pruned or reshaped.
  - `docs/development/testing_strategy.md §§1.4–2` — authoritative test cadence and selector sourcing for handoffs to Ralph.
  - `prompts/supervisor.md` & `docs/fix_plan.md` — supervisor/engineer workflow docs that reference the parity shim today.
- Artifact Policy: Store new evidence under `reports/2025-10-cli-flags/phase_phi_removal/<phase>/<timestamp>/` (mirrors existing CLI-FLAGS-003 structure). Each bundle must include `commands.txt`, raw logs, `summary.md`, `env.json`, and `sha256.txt`.
- Guardrails: Preserve vectorization (no scalar φ loops), device/dtype neutrality, Protected Assets compliance (`docs/index.md`). Removal work must keep spec-mode regression tests green before deleting shim-related coverage.

### Phase A — Baseline Inventory & Freeze
Goal: Capture the current surface area of the carryover shim so removal work cannot regress default spec behavior or lose traceability.
Prereqs: Latest evidence bundles from `plans/active/cli-phi-parity-shim/plan.md` and `plans/active/cli-noise-pix0/plan.md` are reviewed.
Exit Criteria: Inventoried files/tests/docs recorded, authoritative baselines noted, and freeze memo published under `reports/.../phase_a/`.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Catalogue shim touchpoints | [X] | List code/tests/docs referencing `phi_carryover_mode` (CLI parser, configs, crystal model, debug harness, docs). Store table in `reports/.../phase_a/baseline_inventory.md` with file paths + rationale. **DONE:** See `reports/2025-10-cli-flags/phase_phi_removal/phase_a/20251008T184422Z/baseline_inventory.md` — catalogued 4 production files, 2 test files, 3 plans, 40+ reports. |
| A2 | Record normative baselines | [X] | Re-run `pytest --collect-only -q tests/test_cli_scaling_phi0.py` and capture latest passing logs that enforce spec mode tolerances. Verify no other suites depend on `c-parity` mode. **DONE:** See `reports/2025-10-cli-flags/phase_phi_removal/phase_a/20251008T184422Z/collect.log` — 2 tests collected successfully (test_rot_b_matches_c, test_k_frac_phi0_matches_c). |
| A3 | Log plan cross-links | [X] | Update `docs/fix_plan.md` (CLI-FLAGS-003) Attempts with a freeze note pointing to this plan and document that future work moves to shim removal. **DONE:** See `docs/fix_plan.md` Attempt #175 — freeze memo logged; CLI-FLAGS-003 Next Actions updated to reference removal plan; future work pivots to `-nonoise`/`-pix0` deliverables. |

### Phase B — Implementation De-scoping
Goal: Remove the shim entry points while gating runtime behavior to the spec-compliant path.
Prereqs: Phase A freeze published; Ralph briefed via `input.md` for execution loop; latest spec/docs references re-read.
Exit Criteria: CLI/config/model code no longer exposes `phi_carryover_mode`; default behavior confirmed unchanged via targeted tests; documentation/fix_plan synced with removal artifacts under `reports/.../phase_b/`.
Status: Phase B fully complete as of Attempt #178 (2025-10-08) with ledger/doc sync refreshed 2025-12-14; artifact bundle `reports/2025-10-cli-flags/phase_phi_removal/phase_b/20251008T193106Z/` is the canonical reference. Ready to begin Phase C realignment tasks.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B0 | Design review & artifact prep | [D] | Completed 2025-10-08 (design bundle + baseline under `reports/2025-10-cli-flags/phase_phi_removal/phase_b/20251008T185921Z/`). |
| B1 | Deprecate CLI surfaces | [D] | ✅ CLI flag removed in commit 340683f with doc updates captured in `reports/.../20251008T193106Z/doc_diff.md` (README_PYTORCH.md, prompts/supervisor.md, docs/bugs entry now mark the shim as historical). |
| B2 | Prune config/model plumbing | [D] | ✅ `phi_carryover_mode` parameters and cache hooks removed from config/crystal/simulator modules (see `reports/.../20251008T193106Z/summary.md`). Vectorised φ rotation path retained without carryover branches. |
| B3 | Retire shim tooling/tests | [D] | ✅ Deleted parity-only test `tests/test_phi_carryover_mode.py` and associated tooling; spec-mode coverage consolidated under `tests/test_cli_scaling_phi0.py`. Evidence in `reports/.../20251008T193106Z/`. |
| B4 | Targeted regression sweep | [D] | ✅ `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py` passes (CPU) with logs/sha256 stored in `reports/.../20251008T193106Z/pytest_cpu.log`. CUDA rerun not yet required; spec tolerances ≤1e-6 confirmed. |
| B5 | Ledger & plan sync | [D] | ✅ 2025-12-14: Updated `docs/fix_plan.md` (CLI-FLAGS-003) and `plans/active/cli-noise-pix0/plan.md` to pivot to Phase C, referencing artifact bundle `reports/.../20251008T193106Z/`. |

### Phase C — Test & Evidence Realignment
Goal: Adjust the automated test suite and parity expectations to reflect the non-buggy spec.
Prereqs: Phase B merged locally with passing targeted tests in developer loop.
Exit Criteria: Updated tests/docs focus exclusively on spec mode; parity harness tolerances relaxed/removed accordingly; artifacts captured under `reports/.../phase_c/`.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Update pytest coverage | [D] | ✅ Coverage audit complete (Attempt #179, 2025-10-08). Spec-mode tests in `tests/test_cli_scaling_phi0.py` (2 tests) adequately cover φ=0 identity rotation invariants. Artifacts: `reports/2025-10-cli-flags/phase_phi_removal/phase_c/20251008T125158Z/coverage_audit.md`. Analysis confirms 33 removed tests from `test_phi_carryover_mode.py` validated shim-specific behavior no longer needed. |
| C2 | Refresh docs/bugs ledger | [ ] | Amend `docs/bugs/verified_c_bugs.md` C-PARITY-001 entry (lines ~166-192) to mark the shim removal as **complete** (referencing commit `b9db0a3`) and strip residual pointers to `CrystalConfig.phi_carryover_mode`/"plumbing in progress". Capture diff + commands in `reports/.../phase_phi_removal/phase_c/<ts>/summary.md`. |
| C3 | Adjust parity tooling docs/tests | [ ] | Sweep remaining carryover references: retire or rewrite `tests/test_cli_scaling_parity.py` (now fails because `CrystalConfig` no longer accepts `phi_carryover_mode`), update `reports/2025-10-cli-flags/phase_l/parity_shim/*/diagnosis.md`, and scrub `src/nanobrag_torch/models/crystal.py:1238-1274` docstrings that still describe cache-based c-parity handling. Ensure `plans/active/cli-noise-pix0/plan.md`/`prompts/supervisor.md` point to spec-only flow. Log changes + SHA256 in Phase C bundle. |

### Phase D — Validation & Closure
Goal: Demonstrate that spec-mode parity is still on track and retire the old plan items cleanly.
Prereqs: Phases B and C complete, no dangling references to shim remain.
Exit Criteria: New evidence bundle confirms spec-mode traces/tests pass; fix_plan and plan archives updated; CLI-FLAGS-003 scope narrowed to `-nonoise`/`-pix0` deliverables.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Capture proof-of-removal bundle | [ ] | Run spec-mode trace harness (`scripts/trace_harness.py --phi-mode spec`) and store logs + metrics under `reports/.../phase_d/<ts>/`. Highlight absence of shim gating. |
| D2 | Update fix_plan + archive | [ ] | Rewrite `docs/fix_plan.md` CLI-FLAGS-003 Next Actions to drop shim tasks, link to this plan. Move `plans/active/cli-phi-parity-shim/plan.md` to archive once documentation is synced. |
| D3 | Supervisor handoff memo | [ ] | In the loop’s `input.md`, instruct Ralph to run the remaining CLI-FLAGS-003 scaling/nb-compare steps using spec mode only. Document final status in `galph_memory.md`. |

### Phase E — Post-removal Watch (Optional)
Goal: Define lightweight monitoring to ensure the carryover bug does not reappear.
Prereqs: Phase D closed.
Exit Criteria: Watch task documented; automation or manual checks scheduled.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E1 | Add lint/checklist item | [ ] | Extend `docs/fix_plan.md` hygiene notes to assert "No phi carryover codepath"; reference spec lines. |
| E2 | Schedule periodic audit | [ ] | Decide cadence (e.g., quarterly) to rerun spec-mode trace comparison; log in `reports/archive/cli-flags-003/watch.md`. |
