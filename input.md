Summary: Capture the Option 1 spec-compliance bundle for φ rotation and document the C-PARITY-001 divergence.
Mode: Docs
Focus: CLI-FLAGS-003 Phase M5d–M5g — Option 1 spec compliance
Branch: feature/spec-based-2
Mapped tests: pytest -v tests/test_cli_scaling_phi0.py
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/<timestamp>/
Do Now: CLI-FLAGS-003 Phase M5d — publish the option1_spec_compliance bundle, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py` (CPU).
If Blocked: Re-run the trace harness (`PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_validation/trace_harness.py --config supervisor --device cpu --dtype float64 --pixel 685 1039`) and log findings under option1_spec_compliance/<timestamp>/notes.md; record the obstacle in docs/fix_plan.md Attempts.

Priorities & Rationale:
- specs/spec-a-core.md:204-214 — mandates fresh φ rotations, so the new bundle must show PyTorch aligns with the spec (no carryover).
- docs/bugs/verified_c_bugs.md:166-204 — documents C-PARITY-001; the bundle should cite it when explaining why the C trace diverges.
- plans/active/cli-noise-pix0/plan.md M5d–M5g — now the authoritative task list for this phase after Option 1 approval.
- docs/fix_plan.md: CLI-FLAGS-003 entry (Next Actions bullet) — expects the Option 1 artifacts before reopening parity work.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T235045Z/blocker_analysis.md — starting point for the Option 1 narrative; extend it instead of duplicating content.

How-To Map:
- export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md
- Generate new evidence directory: `stamp=$(date -u +%Y%m%dT%H%M%SZ)`; `out=reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/$stamp`
- Copy blocker analysis and append the decision: `mkdir -p "$out" && cp reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T235045Z/blocker_analysis.md "$out"/` then append the Option 1 update with clear "2025-12-20" heading.
- Capture refreshed traces (PyTorch only) for reference: `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_validation/trace_harness.py --config supervisor --device cpu --dtype float64 --pixel 685 1039 --per-phi-log "$out"/trace_py_scaling.log`
- Summarise compare_scaling output: `python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/c_trace_scaling.log --py "$out"/trace_py_scaling.log --out "$out"/compare_scaling_traces.txt`
- Record metadata: append the executed commands to `$out/commands.txt`, capture `env.json` via `python - <<'PY' > "$out"/env.json
import json, os
import sys
json.dump({k: os.environ[k] for k in ["PWD", "PYTHONPATH", "KMP_DUPLICATE_LIB_OK", "AUTHORITATIVE_CMDS_DOC", "NB_C_BIN"] if k in os.environ}, sys.stdout, indent=2)
PY`, and run `find "$out" -type f -print0 | xargs -0 sha256sum > "$out"/sha256.txt` once artifacts are ready.
- Update docs: edit `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md` (H4/H5 → CLOSED) and add the new bundle to docs/fix_plan.md Attempts.
- Run targeted regression: `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py` (CPU). If CUDA is available, queue `KMP_DUPLICATE_LIB_OK=TRUE pytest -v -m gpu_smoke tests/test_cli_scaling_phi0.py` and stash both logs in `$out`.

Pitfalls To Avoid:
- Do not resurrect the old `phi_carryover_mode` shim — Option 1 keeps the spec-only path.
- Keep tensors on the caller’s device/dtype; trace harness already respects this, so avoid `.cpu()` dumps in new snippets.
- Reference `c_phi_rotation_reference.md` rather than paraphrasing nanoBragg.c.
- Maintain Protected Assets (docs/index.md); do not move or rename listed files while updating docs.
- Be explicit that compare_scaling still reports I_before_scaling divergence (expected); note the reason in summary.md.
- Update lattice_hypotheses.md in-place — no duplicate files or unchecked-in drafts.
- Keep Option 1 artifacts under one timestamped directory with `commands.txt`, `env.json`, and `sha256.txt` for reproducibility.
- Mention the Option 1 decision in docs/fix_plan.md Attempts and link back to the new bundle.
- Verify `pytest --collect-only -q tests/test_cli_scaling_phi0.py` if the targeted run fails unexpectedly before diving into fixes.
- No nb-compare runs this loop; this is a documentation pass.

Pointers:
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T235045Z/blocker_analysis.md
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md
- plans/active/cli-noise-pix0/plan.md
- docs/fix_plan.md#cli-flags-003-handle-nonoise-and-pix0_vector_mm
- specs/spec-a-core.md:204-214
- docs/bugs/verified_c_bugs.md:166-204

Next Up: Optionally scope Phase M6 (opt-in C-parity shim) once Option 1 bundle is merged.
