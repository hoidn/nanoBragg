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
Status: Phase B0 completed 2025-10-08; B1 CLI flag removal landed in commit 340683f with artifacts under `reports/2025-10-cli-flags/phase_phi_removal/phase_b/20251008T191302Z/`, documentation sync still pending.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B0 | Design review & artifact prep | [D] | Completed 2025-10-08 (design bundle + baseline under `reports/2025-10-cli-flags/phase_phi_removal/phase_b/20251008T185921Z/`). |
| B1 | Deprecate CLI surfaces | [P] | ✅ CLI flag removed in commit 340683f (`reports/.../20251008T191302Z/`). Outstanding: update `README_PYTORCH.md`, `prompts/supervisor.md`, and `docs/bugs/verified_c_bugs.md` to reflect the shim removal, then capture doc-sync artifacts in the same bundle before marking [D]. |
| B2 | Prune config/model plumbing | [ ] | Delete `phi_carryover_mode` parameters from `CrystalConfig`/`SimulatorConfig` (if present) and drop `_apply_phi_carryover` branches in `src/nanobrag_torch/models/crystal.py` & `simulator.py`. Ensure vectorised φ rotation path stays intact; reference the nanoBragg.c snippet per CLAUDE Rule #11 when editing docstrings/comments. |
| B3 | Retire shim tooling/tests | [ ] | Remove parity-only helpers (e.g., `scripts/compare_per_phi_traces.py` flags) and delete or refactor `tests/test_phi_carryover_mode.py` so only spec-mode assertions remain (migrate reusable checks into `tests/test_cli_scaling_phi0.py`). Update any reports under `reports/2025-10-cli-flags/phase_l/` that the tooling depended on. |
| B4 | Targeted regression sweep | [ ] | Run `pytest --collect-only -q tests/test_cli_scaling_phi0.py` and `pytest -v tests/test_cli_scaling_phi0.py` on CPU; if CUDA available, rerun with `CUDA_VISIBLE_DEVICES=0`. Capture logs/SHA256 in the Phase B artifact directory; document any new tolerances required by spec-mode assertions. |
| B5 | Ledger & plan sync | [ ] | Append Attempt entry in `docs/fix_plan.md` (CLI-FLAGS-003) referencing Phase B artifacts, flip plan rows B0–B4 to `[D]`, and update `plans/active/cli-noise-pix0/plan.md` Next Actions to point at Phase C tasks. |

### Phase C — Test & Evidence Realignment
Goal: Adjust the automated test suite and parity expectations to reflect the non-buggy spec.
Prereqs: Phase B merged locally with passing targeted tests in developer loop.
Exit Criteria: Updated tests/docs focus exclusively on spec mode; parity harness tolerances relaxed/removed accordingly; artifacts captured under `reports/.../phase_c/`.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Update pytest coverage | [ ] | Delete `tests/test_phi_carryover_mode.py`; fold any remaining spec assertions into `tests/test_cli_scaling_phi0.py`. Validate selectors via `pytest --collect-only -q tests/test_cli_scaling_phi0.py`. |
| C2 | Refresh docs/bugs ledger | [ ] | Amend `docs/bugs/verified_c_bugs.md` C-PARITY-001 entry to emphasise "C-only" and note that PyTorch no longer exposes a reproduction mode. Record change in `summary.md`. |
| C3 | Adjust parity tooling docs | [ ] | Update `docs/development/testing_strategy.md` and `reports/.../diagnosis.md` to remove instructions for c-parity tolerance. Ensure `prompts/supervisor.md` and `plans/active/cli-noise-pix0/plan.md` no longer reference carryover phases. |

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
