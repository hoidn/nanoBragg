Summary: Finish the φ-carryover cleanup by rewriting docs/tests to reflect spec-only rotations and prove collection stays green.
Mode: Docs
Focus: CLI-FLAGS-003 Phase C2/C3 doc sweep
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py
Artifacts: reports/2025-10-cli-flags/phase_phi_removal/phase_c/<timestamp>/
Do Now: [CLI-FLAGS-003] Phase C2/C3 doc sweep — after updating the targeted files run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py` and stash logs + metadata in the new Phase C directory.
If Blocked: Capture the unresolved doc/test notes in `summary.md`, include the failing collect output (if any), and diff against `reports/2025-10-cli-flags/phase_phi_removal/phase_b/20251008T193106Z/summary.md` to highlight what still references c-parity.

Priorities & Rationale
- docs/fix_plan.md:455-466 — Next Actions now call out docs/bugs rewrite and tooling/doc scrub (tests/test_cli_scaling_parity.py, crystal docstrings).
- plans/active/phi-carryover-removal/plan.md:40-58 — Phase C rows define the deliverables and cite the exact files that still mention carryover.
- docs/bugs/verified_c_bugs.md:166-192 — Still claims plumbing removal is "in progress" and links to the deleted shim code; must say removal is complete.
- tests/test_cli_scaling_parity.py:1-140 — Continues to instantiate `CrystalConfig(... phi_carryover_mode="c-parity")`, which now throws; retire or refactor during the sweep.
- src/nanobrag_torch/models/crystal.py:1238-1274 — Docstring still describes cache-based c-parity handling; needs to reflect the fresh-rotation-only path.

How-To Map
- mkdir -p `reports/2025-10-cli-flags/phase_phi_removal/phase_c/<timestamp>/` before edits; record shell history in `commands.txt` and capture `env.json` + `sha256.txt` when finished.
- Update `docs/bugs/verified_c_bugs.md` (lines ~166-192) to mark C-PARITY-001 as a C-only defect, reference commit `b9db0a3`, and remove references to deleted PyTorch plumbing.
- Sweep residual carryover references: address `tests/test_cli_scaling_parity.py`, `reports/2025-10-cli-flags/phase_l/parity_shim/*/diagnosis.md`, and the crystal rotation docstring so they describe spec-only behaviour.
- After edits, run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py > .../collect.log`; include stderr if the selector fails and note follow-up in `summary.md`.
- Update `docs/fix_plan.md` Attempts with the new timestamp + artifact path once the sweep is complete.

Pitfalls To Avoid
- Do not restore the carryover shim or reintroduce `phi_carryover_mode` arguments anywhere.
- Keep edits ASCII-only and leave protected files (docs/index.md, loop.sh, supervisor.sh, input.md) untouched beyond required updates.
- Maintain vectorization/dtype neutrality in any explanatory snippets; no `.cpu()` defaults.
- When removing the parity test, also remove stale imports/helpers so pytest discovery stays clean.
- Preserve historical evidence by moving any retired diagnosis notes to archive rather than deleting without mention.
- Capture SHA256 hashes for every artifact you add to `reports/`.
- Keep pytest scope targeted; no full-suite runs this loop.
- Document every filename you touch inside `summary.md` for traceability.

Pointers
- docs/fix_plan.md:451-466 — Active ledger guidance for CLI-FLAGS-003 Phase C.
- plans/active/phi-carryover-removal/plan.md:40-58 — Detailed Phase C tasks and evidence expectations.
- docs/bugs/verified_c_bugs.md:166-192 — C-PARITY-001 entry to rewrite.
- tests/test_cli_scaling_parity.py:1-140 — Shim-era test that now needs retirement or rewrite.
- src/nanobrag_torch/models/crystal.py:1238-1274 — Docstring referencing c-parity cache behaviour.

Next Up
- Phase D proof-of-removal bundle (trace harness with spec mode only) once docs/tests reference solely the fresh-rotation path.
