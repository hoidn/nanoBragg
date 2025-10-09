Summary: Implement the φ rotation duality pipeline so spec-mode lattice parity matches the C trace before scaling factors.
Mode: Parity
Focus: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm (Phase M5c φ rotation realignment)
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/
Do Now: CLI-FLAGS-003 Phase M5c — Implement φ rotation duality fix; KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py
If Blocked: Capture fresh traces with current code (`trace_harness.py` command below) and diff vs C to isolate the failing tensor, then log findings under reports/2025-10-cli-flags/phase_l/scaling_validation/blockers_<timestamp>/ with metrics + env.

Priorities & Rationale:
- specs/spec-a-core.md:204 — φ steps must rotate the base lattice each tick; current per-φ traces violate the spec by letting reciprocal components drift.
- specs/spec-a-core.md:210 — Lattice factor definition assumes sincg argument uses spec-compliant Miller fractions, not φ-biased values.
- specs/spec-a-core.md:237 — Final intensity scaling presumes upstream `F_latt` parity; fixing φ rotation restores that prerequisite.
- docs/bugs/verified_c_bugs.md:166 — φ carryover is a C-only bug; our implementation must stay spec-compliant while matching C reciprocal updates.
- arch.md: Section 2.2 — Rotation pipeline ADR mandates misset → φ → mosaic with dual recalculation; existing code short-circuits that contract.
- docs/development/c_to_pytorch_config_map.md §Crystal — Confirms φ rotations operate on tensor parameters; runtime must keep tensor graph intact when recomputing vectors.
- docs/architecture/pytorch_design.md §Vectorization — Requires rotations stay batched; the fix must reuse broadcast shapes.
- plans/active/cli-noise-pix0/plan.md:103 — Phase M5c exit criteria require ≤1e-6 agreement for `rot_*_star` and `F_latt` across φ ticks.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T231211Z/trace_py_scaling_per_phi.log — Demonstrates `b_star_y` sliding from 1.043764e-02 to 1.038602e-02 while C stays constant to 1e-6.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/c_trace_scaling.log — Shows the C reciprocal values we must land on (e.g., `rot_b_star_A_inv` y=0.0104376433).
- src/nanobrag_torch/models/crystal.py:1248-1277 — Current code uses static `self.V` and never rebuilds real vectors, breaking metric duality (Rules #12/#13).
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md — Hypothesis H4 pins the divergence on φ rotation misalignment; closing it depends on this fix.
- galph_memory.md (2025-12-19 entry) — Supervisor already flagged M5c as the gating task; this loop should unblock subsequent CUDA/gradcheck work.
- docs/fix_plan.md:451-620 — Next actions explicitly point to implementing dual real/reciprocal recomputation before progressing to Phase M5d.

How-To Map:
- Export timestamp: `export FIX_TAG=fix_$(date -u +%Y%m%dT%H%M%SZ)`; reuse this for every artifact directory.
- Pre-create artifact tree: `mkdir -p reports/2025-10-cli-flags/phase_l/scaling_validation/$FIX_TAG`
- KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --device cpu --dtype float64 --emit-rot-stars --out reports/2025-10-cli-flags/phase_l/scaling_validation/$FIX_TAG/trace_py_scaling.log
- Include `--per-phi-json` (if not default) so `trace_py_scaling_per_phi.log` and `.json` land beside the main trace, satisfying plan M5d prerequisites.
- Optional sanity diff: `python scripts/tools/diff_per_phi.py --new .../$FIX_TAG/trace_py_scaling_per_phi.json --ref reports/.../per_phi/trace_py_spec_per_phi.json` if helper exists; otherwise use `jq` to check drift.
- Copy the C baseline trace into the new directory for quick diff: `cp reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/c_trace_scaling.log reports/2025-10-cli-flags/phase_l/scaling_validation/$FIX_TAG/`
- KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/c_trace_scaling.log --py reports/2025-10-cli-flags/phase_l/scaling_validation/$FIX_TAG/trace_py_scaling.log --out reports/2025-10-cli-flags/phase_l/scaling_validation/$FIX_TAG/compare_scaling_traces.md | tee reports/2025-10-cli-flags/phase_l/scaling_validation/$FIX_TAG/compare_scaling_traces.txt
- Inspect `metrics.json` under the same directory; confirm `first_divergence` is `null` and `num_divergent`=0 before moving on.
- Update `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md` by appending a new H4 resolution section referencing $FIX_TAG with numerical deltas.
- Capture per-φ summary: `cp reports/2025-10-cli-flags/phase_l/scaling_validation/$FIX_TAG/trace_py_scaling_per_phi.log reports/2025-10-cli-flags/phase_l/per_phi/trace_py_$FIX_TAG.log`
- Generate rotated reciprocal CSV if helpful: `python scripts/tools/export_rot_star.py --trace reports/.../$FIX_TAG/trace_py_scaling_per_phi.json --out reports/.../$FIX_TAG/rot_star.csv`
- KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py > reports/2025-10-cli-flags/phase_l/scaling_validation/$FIX_TAG/pytest_cpu.log
- If CUDA available: `KMP_DUPLICATE_LIB_OK=TRUE pytest -v -m gpu_smoke tests/test_cli_scaling_phi0.py > reports/.../$FIX_TAG/pytest_cuda.log`
- Record env + commands: `env > reports/.../$FIX_TAG/env.txt` and `history | tail -n 50 > reports/.../$FIX_TAG/commands.txt`
- Compute checksums: `find reports/2025-10-cli-flags/phase_l/scaling_validation/$FIX_TAG -maxdepth 1 -type f -print0 | sort -z | xargs -0 sha256sum > .../$FIX_TAG/sha256.txt`
- Refresh docs/fix_plan.md Attempt entry with $FIX_TAG, including compare_scaling_traces status and tests; flip plans/active/cli-noise-pix0/plan.md row M5c to [D].
- Append docstring in `Crystal.get_rotated_real_vectors` with the updated nanoBragg.c snippet covering lines 3042-3210 before committing code changes.
- Run `pytest --collect-only -q` if targeted tests err to ensure selectors remain valid, then re-run the targeted suite once fixed.
- Capture before/after diff snippet for `src/nanobrag_torch/models/crystal.py` and add to the Attempt note for reviewer context.
- Consider a quick gradcheck smoke (`python scripts/tools/run_gradcheck.py --case phi_rotation`) once parity holds to pre-empt Phase M5e.
- File a short note in reports/$FIX_TAG/summary.md explaining numerical agreement for `F_latt`, `k_frac`, and `b_star_y` across φ ticks.

Pitfalls To Avoid:
- Do not reintroduce the φ carryover cache or reference its comments; the shim was removed in Attempt #178.
- Avoid scalar loops over φ/mosaic — rely on tensor broadcasting for all recomputations.
- Keep spindle axis normalized (`config.spindle_axis` may need `torch.linalg.norm` guard) before building rotation matrices.
- Use actual reciprocal volume per slice: compute `V_star = dot(a_star_rot, cross(b_star_rot, c_star_rot))` and guard with `clamp_min(1e-18)`.
- Rebuild real vectors from the rotated reciprocal vectors before recalculating `a_star_final`; skip this and drift will persist.
- Ensure gradients stay connected; no `.detach()`, `.item()`, `.numpy()`, or implicit CPU moves.
- Maintain dtype neutrality; operations must respect `self.dtype`, including any `torch.arange` or `torch.eye` temporaries.
- Keep per-φ artifacts under one hierarchy; do not create nested `.../per_phi/reports/...` directories again.
- Update docstrings before implementation to satisfy CLAUDE Rule #11; failing to include the C snippet blocks review.
- When editing tests or docs, check docs/index.md before touching any protected assets (loop.sh, supervisor.sh, input.md, etc.).
- After changes, run `pytest --collect-only -q` if targeted tests fail unexpectedly to ensure selectors still resolve.
- If compare_scaling_traces still diverges, do not brute-force fix sincg; reassess φ rotation math first.
- Avoid reordering rotations (spindle vs mosaic); maintain the spec order misset → φ → mosaic for parity with C.
- Preserve batch dimensions when recomputing cross products; dropping the φ axis will break broadcasting in Simulator.
- Keep logging optional; do not enable full TRACE_* output unless `_enable_trace` is set by the harness.
- Do not hard-code float64; keep computations dtype-agnostic and rely on `self.dtype`.
- Ensure new helper tensors are created with `.to(self.device)` or via existing tensors to prevent silent CPU allocations.
- Use `torch.cross(..., dim=-1)` consistently; the default dim may shift if shapes change.
- Guard against `phi_steps=1` edge case by ensuring masks still behave; add a unit test if needed.

Pointers:
- specs/spec-a-core.md:204-240 — φ rotation + lattice factor contract to replicate.
- specs/spec-a-core.md:362-376 — Duality guidance for reciprocal recalculation using actual volume.
- docs/bugs/verified_c_bugs.md:166-204 — Historical carryover bug context.
- arch.md: Section 3 — Implementation guidelines for derived properties and @property usage.
- docs/development/pytorch_runtime_checklist.md — Device/dtype checklist to review before final testing.
- plans/active/cli-noise-pix0/plan.md:103-121 — Phase M5 task table you'll be closing.
- plans/active/cli-noise-pix0/plan.md:71 — M4d remains [P]; update once parity metrics are green.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T231211Z/summary.md — Latest per-φ evidence to compare against.
- reports/2025-10-cli-flags/phase_l/per_phi/trace_py_spec_per_phi.log — Historical spec-mode per-φ reference values.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/metrics.json — Baseline metric structure to mirror post-fix.
- src/nanobrag_torch/models/crystal.py:1238-1277 — Current φ rotation implementation to replace.
- scripts/validation/compare_scaling_traces.py:1-200 — CLI options and output artefacts.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T223805Z/blockers.md — Notes on the unresolved 14.6% deficit pre-fix.
- docs/fix_plan.md:451-620 — CLI-FLAGS-003 ledger entries to update with $FIX_TAG.
- galph_memory.md (2025-12-19 log) — Supervisor notes on M5c expectations and artifact requirements.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T221702Z/design_memo.md — Normalization fix memo to mirror formatting.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T232018Z/rotation_fix_design.md — Design reference for the duality pipeline you are implementing.
- src/nanobrag_torch/utils/geometry.py — Rotation helpers to reuse; ensure they stay differentiable.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T231211Z/metrics.json — Prior metrics showing `first_divergence="I_before_scaling"` for comparison.
- scripts/debugging/README.md (if present) — Reminder of trace schema consistency.

Next Up:
- Phase M5d verification: rerun compare_scaling_traces and update lattice_hypotheses once parity is achieved.
- Phase M5e CUDA + gradcheck sweep to ensure device neutrality before moving to nb-compare.
- Afterwards, Phase M6 (CUDA smoke + gradcheck ledger updates) is unblocked, enabling progression to Phase N nb-compare closure.
- Begin drafting cleanup notes for duplicated per-φ directories so M5d can also tidy the reports tree.
- Queue doc cleanup for duplicate per-φ directories once parity evidence is stored.
- Prepare the Attempt summary text while evidence is fresh so docs/fix_plan.md can be updated immediately after testing.
- Stage follow-on nb-compare command list so Phase N can launch immediately after M6 closes.
- Note any lingering TODOs for vectorization plan so they can be reprioritized once CLI parity is green.
