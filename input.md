Summary: Complete CLI-FLAGS-003 Phase L documentation sync so spec vs c-parity tolerances, plan tasks, and public docs stay coherent before Phase M scaling parity work resumes.
Mode: Docs
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_spec (collect-only), tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_matches_spec (collect-only), tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c_parity (collect-only), tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_matches_c_parity (collect-only), tests/test_phi_carryover_mode.py::TestCarryoverCLI::test_cli_flag_defaults (collect-only), tests/test_phi_carryover_mode.py::TestCarryoverCLI::test_spec_mode_gradients (collect-only), tests/test_phi_carryover_mode.py::TestCarryoverCLI::test_c_parity_mode_accepts_flag (collect-only)
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md, reports/2025-10-cli-flags/phase_l/rot_vector/<timestamp>/collect.log, reports/2025-10-cli-flags/phase_l/rot_vector/<timestamp>/summary.md, reports/2025-10-cli-flags/phase_l/rot_vector/<timestamp>/sha256.txt, reports/2025-10-cli-flags/phase_l/parity_shim/20251201_dtype_probe/analysis_summary.md, docs/fix_checklist.md, plans/active/cli-noise-pix0/plan.md, plans/active/cli-phi-parity-shim/plan.md, docs/bugs/verified_c_bugs.md, docs/fix_plan.md, docs/development/testing_strategy.md:1.5 reference log
Do Now: CLI-FLAGS-003 Phase L (tasks L1–L3) — KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py tests/test_phi_carryover_mode.py
If Blocked: Create reports/2025-10-cli-flags/phase_l/rot_vector/<timestamp>/blocked.md capturing the failing command, stdout/stderr, and immediate hypothesis; update docs/fix_plan.md Attempts and wait for supervisor feedback before touching specs or code paths.
Priorities & Rationale:
- specs/spec-a-core.md:204 — Reinforce normative φ rotation (fresh lattice every step) so documentation does not imply the C bug is required behavior.
- specs/spec-a-cli.md §phi-flags — Keep CLI flag documentation aligned with spec semantics and ensure `--phi-carryover-mode` remains clearly marked as opt-in parity support.
- docs/bugs/verified_c_bugs.md:166 — Maintain the quarantine description and reference to the parity shim without diluting the bug report.
- plans/active/cli-noise-pix0/plan.md Phase L (L1–L3) — Update task states, checklist tables, and guidance to reflect the new documentation.
- plans/active/cli-phi-parity-shim/plan.md Phase D (D1–D3) — Mirror dual-threshold decisions and cite fresh artifacts so both plans stay synchronized.
- docs/fix_checklist.md VG-1 row — Capture tolerances (1e-6 spec vs 5e-5 c-parity), link the updated diagnosis doc, and highlight the collect-only command used.
- reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md — Rewrite summary + decisions to point to dtype probe evidence and log the new artifact directory.
- reports/2025-10-cli-flags/phase_l/parity_shim/20251201_dtype_probe/analysis_summary.md — Reference when justifying relaxed c-parity tolerance; ensure citing location remains accurate.
- docs/fix_plan.md (CLI-FLAGS-003 attempts) — Append attempt covering doc sync, command run, artifact paths, and how tolerances align with spec + bug docs.
- docs/development/testing_strategy.md §1.5 — Keep Do Now and collected commands consistent with authoritative guidance for documentation loops.
- docs/index.md — Confirm Protected Assets references remain untouched when editing doc paths.
- CLAUDE.md — Re-read Protected Assets + instrumentation rules before editing doc content that references C snippets.
- arch.md §2 + docs/architecture/detector.md §5 — Use for citations when restating pix0 vectors or pivot semantics in documentation.
- docs/development/pytorch_runtime_checklist.md §Runtime Guardrails — Mention when documenting CPU/CUDA expectations for the shim flag.
How-To Map:
- Export env var once: `export KMP_DUPLICATE_LIB_OK=TRUE` (keeps collect-only runs stable across shells).
- Run collect-only command, capture exit code, and tee output to `reports/2025-10-cli-flags/phase_l/rot_vector/<timestamp>/collect.log` for traceability.
- Record metadata: `python - <<'PY'` snippet to dump torch version, CUDA availability, and commit SHA into `env.json` under the same folder.
- Update `reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md` sections VG-1, Dual-Threshold Decision, and TODOs with new rationale and artifact references.
- Edit `plans/active/cli-noise-pix0/plan.md` — Mark L1 as [D] after doc sync, L2 as [P]/[D] depending on progress, update guidance table with artifact paths.
- Edit `plans/active/cli-phi-parity-shim/plan.md` — Reflect documentation updates in Phase D1–D3 and ensure summary references match the refreshed diagnosis doc.
- Update `docs/fix_checklist.md` VG-1 row with tolerance bullets, artifact path, collect-only command, and pointer to dtype probe.
- Modify `docs/bugs/verified_c_bugs.md` to add a single sentence referencing the new diagnosis doc location without altering the bug description.
- Append docs/fix_plan.md Attempt capturing documentation sync, collect-only command, env metadata, and new artifact directory.
- Generate `summary.md` in the new reports directory summarizing what changed, commands executed, env info, and direct links to updated docs.
- Produce `sha256.txt` via `shasum -a 256 *` so artifacts can be verified during audits.
- Re-run the collect-only command post edits to confirm selectors remain discoverable; append a short note if the second run differs.
- Stage documentation changes after review: `git add` targeted files only; avoid staging unrelated files.
- Update this memo’s Attempts History section in docs/fix_plan.md to reference the timestamped directory for future loops.
- Run `git diff --stat` before writing summary.md to capture file counts/sizes for the record.
- Cross-check that `docs/fix_checklist.md` renders properly by opening in markdown viewer; adjust column widths if needed.
- Drop a short changelog entry inside `summary.md` outlining each doc touched and reason.
- Optionally, capture a `tree` listing of the new reports folder (`tree -a -I "*.png" reports/.../<timestamp>`). Store in summary for completeness.
- When referencing commands in docs, wrap them in fenced code blocks with language hints (`bash`) to maintain formatting.
- After plan updates, run `rg -n "Phase L" plans/active/cli-noise-pix0/plan.md` to verify the updated sections read coherently.
- Verify that `tests/test_cli_scaling_phi0.py` docstrings remain accurate; adjust if documentation changes require updates.
- If multiple timestamps created, choose one canonical folder and delete unused empty directories to avoid confusion (document decision in summary).
- Check `docs/fix_plan.md` for trailing whitespace after edits; clean if necessary.
Pitfalls To Avoid:
- No production code edits; stay within documentation, plans, checklists, and reports.
- Do not weaken spec tolerances; spec mode remains 1e-6 and must be reflected consistently.
- Keep CLAUDE Rule #11 excerpts intact; when citing C lines, quote exact code and maintain formatting.
- Avoid ad-hoc directories outside `reports/2025-10-cli-flags/phase_l/rot_vector/`; use ISO timestamp naming for new folders.
- Do not touch files listed in docs/index.md without explicit supervisor approval.
- Preserve ASCII formatting—no smart quotes or non-ASCII characters in docs.
- Make sure collect-only command matches Do Now exactly; update both places if selectors change.
- Do not overwrite historical diagnosis content; add dated sections or append updates clearly.
- Ensure dtype probe evidence remains referenced; do not delete or move existing analysis directories.
- Keep environment metadata up to date; missing env.json makes future forensics harder.
- Double-check that `--phi-carryover-mode` default remains "spec" in docs; no implication that c-parity is default.
- Avoid mixing spec and parity tolerances in the same sentence without labeling which is which.
- Document commands with absolute clarity; future loops must be able to reproduce steps verbatim.
- When editing plans, maintain the checklist table structure (`ID | Task | State | Guidance`).
- No git commits until documentation edits ready; run `git status` before staging to avoid surprise code diffs.
- Do not skip updating docs/fix_plan.md; absence of attempt log will block closure.
- Avoid editing `docs/fix_checklist.md` alignment by mixing tabs/spaces; stick to spaces.
- Ensure new artifact directories include `commands.txt`; forgetting this slows audits.
- Do not leave collect-only output only in terminal; always persist to disk.
- If you notice discrepancies between plan + fix_plan, pause and reconcile under supervision rather than improvising.
Pointers:
- specs/spec-a-core.md:204
- specs/spec-a-cli.md:120
- docs/bugs/verified_c_bugs.md:166
- plans/active/cli-noise-pix0/plan.md#phase-l
- plans/active/cli-phi-parity-shim/plan.md#phase-d
- docs/fix_checklist.md#vg-1
- reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md
- reports/2025-10-cli-flags/phase_l/parity_shim/20251201_dtype_probe/analysis_summary.md
- docs/fix_plan.md#cli-flags-003-handle-nonoise-and-pix0_vector_mm
- docs/development/testing_strategy.md:1.5
- docs/development/pytorch_runtime_checklist.md:14
- arch.md:200
- docs/architecture/detector.md:310
- CLAUDE.md:Protected Assets Rule
- docs/index.md:Protected Assets list
- prompts/supervisor.md:pyrefly directive (for future STATIC-PYREFLY-001 work)
- prompts/pyrefly.md: static analysis SOP reference
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251007T231515Z/
- reports/2025-10-cli-flags/phase_l/parity_shim/20251008T032835Z/
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py
- reports/2025-10-cli-flags/phase_l/scaling_audit/scaling_comparison.md
- reports/2025-10-cli-flags/phase_l/nb_compare_phi_fix/
- reports/2025-10-cli-flags/phase_l/supervisor_command_rerun/
- reports/2025-10-cli-flags/phase_l/parity_shim/20251201_dtype_probe/commands.txt
- reports/2025-10-cli-flags/phase_l/rot_vector/20251202_tolerance_sync/blocked.md
- docs/fix_checklist.md#vg-2
- docs/fix_plan_archive.md
- docs/development/c_to_pytorch_config_map.md
- docs/architecture/conventions.md
- docs/architecture/pytorch_design.md#vectorization-strategy
- docs/user/known_limitations.md
- docs/user/rotation_usage.md
- docs/development/implementation_plan.md
- docs/development/checklists/checklist1.md
Next Up: After documentation sync lands, advance to `plans/active/cli-noise-pix0/plan.md` Phase M (M1–M3) to resolve the `F_cell` / `I_before_scaling` divergence, tap `trace_harness.py`, and prep nb-compare runs for Phase N.
