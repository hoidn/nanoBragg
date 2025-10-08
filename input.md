Header:
Summary: Refresh φ=0 parity evidence so the CLI parity shim can meet the ≤1e-6 Δk gate before we rerun the supervisor nb-compare command.
Mode: Parity
Focus: docs/fix_plan.md#CLI-FLAGS-003 (Phase L3k.3c.4 parity shim diagnostics)
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_cli_scaling_phi0.py tests/test_phi_carryover_mode.py
Artifacts: reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/
Do Now: docs/fix_plan.md#CLI-FLAGS-003 Phase L3k.3c.4 — set `OUTDIR=reports/2025-10-cli-flags/phase_l/parity_shim/$(date -u +%Y%m%dT%H%M%SZ)`; run `mkdir -p "$OUTDIR" && PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/trace_per_phi.py --outdir "$OUTDIR" 2>&1 | tee "$OUTDIR"/trace_per_phi.log`; then `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/compare_per_phi_traces.py "$OUTDIR"/per_phi_pytorch_*.json reports/2025-10-cli-flags/phase_l/parity_shim/20251008T021659Z/c_trace_phi.log 2>&1 | tee "$OUTDIR"/compare_per_phi.log`; capture a written summary + sha256 ledger under `$OUTDIR`.
If Blocked: If `compare_per_phi_traces.py` fails (missing C trace, schema mismatch, or Δk still pegged), record the failure in `$OUTDIR/blocked.md`, include stack traces, run `pytest --collect-only -q tests/test_cli_scaling_phi0.py tests/test_phi_carryover_mode.py | tee "$OUTDIR"/pytest_collect.log`, and stop so we can reassess instrumentation before touching implementation.
Priorities & Rationale:
- specs/spec-a-core.md:211-214 obligates every φ slice to rotate the lattice anew; parity evidence must prove the shim preserves spec path behaviour while still matching the C defect when toggled. Quote the spec sentence in your summary to reinforce the normative rule.
- specs/spec-a-cli.md §§3.2–3.4 confirm CLI flag semantics for -phi/-osc/-phisteps; referencing these ensures CLI documentation stays clean of the C bug.
- docs/bugs/verified_c_bugs.md:166-204 documents C-PARITY-001 and the `TRACE_C_PHI` anomaly; citing this helps reviewers understand why we emulate the bug only in parity mode.
- arch.md:204-216 reiterates phi-then-mosaic rotation ordering; parity shim must respect this to avoid vectorization regressions.
- docs/architecture/pytorch_design.md §§2.2–2.4 describe vectorization expectations; remind yourself that shim logic must remain batched.
- plans/active/cli-phi-parity-shim/plan.md Phase C4 requires refreshed traces and detector geometry taps before declaring VG-1 complete; mention which checklist entries (C4b–C4d) are satisfied or still open.
- plans/active/cli-noise-pix0/plan.md L3k.3 uses Δk ≤ 1e-6 and ΔF_latt_b ≤ 1e-4 as go/no-go; record status so future loops know whether to proceed.
- docs/fix_plan.md#CLI-FLAGS-003 Next Actions step 1 explicitly asks for a new per-φ run plus diff summary; completing it unblocks steps 2 and 3 (documentation + normalization follow-up).
- reports/2025-10-cli-flags/phase_l/parity_shim/20251008T021659Z/ shows the plateau at Δk≈2.845e-05; compare new metrics directly and note percent improvement.
- Long-term goal #1 (run the supervisor command) hinges on this parity gate; without satisfactory evidence, normalization/nb-compare tasks remain blocked.
- Verified spec guardrails (spec remains bug-free) depend on proving that parity shim is opt-in; include reassurance referencing docs/bugs lines.
- Keep an eye on phi-carryover-mode CLI flag semantics in `src/nanobrag_torch/__main__.py` (no code changes, but mention in summary if behaviour observed matches expectations).
How-To Map:
1. Environment prep:
   - Confirm `python -m nanobrag_torch --help` works (editable install intact).
   - Export `KMP_DUPLICATE_LIB_OK=TRUE` in your shell before running commands.
   - Verify `NB_C_BIN` still points at `./golden_suite_generator/nanoBragg`; if not, set it so parity docs remain reproducible.
   - Run `git status -sb` to ensure clean tree before starting.
2. Selector validation:
   - `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py tests/test_phi_carryover_mode.py | tee "$OUTDIR"/pytest_collect.log`.
   - Inspect the log for `TestPhiZeroParity::test_rot_b_matches_c`, `TestPhiZeroParity::test_k_frac_matches_spec`, and `TestPhiCarryoverMode::test_c_parity_matches_c`.
   - If collection fails, fix before proceeding.
3. PyTorch trace capture:
   - Execute `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/trace_per_phi.py --outdir "$OUTDIR" 2>&1 | tee "$OUTDIR"/trace_per_phi.log`.
   - Confirm console output includes the chosen pixel and dtype/device summary.
   - After completion, list `$OUTDIR` and ensure `per_phi_pytorch_*.json` and `per_phi_summary_*.md` exist.
4. Optional geometry tap (if deltas persist):
   - If plan checklist mentions pix0 geometry, run `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_detector_pix0_calc.py --outdir "$OUTDIR"/geometry 2>&1 | tee "$OUTDIR"/geometry.log`.
   - Compare outputs to C trace geometry data; note differences in summary.
5. Comparison against C trace:
   - Run `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/compare_per_phi_traces.py "$OUTDIR"/per_phi_pytorch_*.json reports/2025-10-cli-flags/phase_l/parity_shim/20251008T021659Z/c_trace_phi.log 2>&1 | tee "$OUTDIR"/compare_per_phi.log`.
   - Confirm `delta_metrics.json` reports `max_delta_k` and `max_delta_F_latt_b`; copy values and note whether thresholds met.
   - Review `diff_summary.md` for first divergent fields; mention them explicitly in summary.
6. Artifact hygiene:
   - Write `$OUTDIR/commands.txt` with both commands (include environment variables and working directory).
   - Run `cd "$OUTDIR" && sha256sum * > sha256.txt`; for nested files use `find "$OUTDIR" -type f -print0 | sort -z | xargs -0 sha256sum >> sha256.txt`.
   - Capture `ls -R "$OUTDIR" > "$OUTDIR"/tree.txt` for quick directory overview.
7. Documentation updates:
   - Append to `reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md` a subsection named after the timestamp; include Δ values, geometry observations, and next steps.
   - Update docs/fix_plan.md Attempt history with metrics, artifact path, hypotheses, and call out whether Phase C4 checklist items were satisfied.
   - If Δk remains high, explicitly state which instrumentation is next (reciprocal taps, normalization audit) referencing plan checklists.
   - (Optional) If geometry tap run, add bullet under diagnosis.md with pix0 vector comparison (C vs PyTorch).
8. Verification & guardrails:
   - Re-open `per_phi_summary_*.md` and ensure numbers match `delta_metrics.json`.
   - Confirm no code files changed (`git status -sb` should only list new reports and doc edits).
   - If tolerances met, draft bullet list for Phase L3k.3c.5 tasks so the next loop can jump straight to docs/tests.
   - Add quick note to `docs/fix_plan.md` Next Actions if Step 1 now complete (mark Step 2 as active).
   - Run `pytest --collect-only -q tests/test_cli_scaling_phi0.py` once more if you regenerated traces after doc edits, ensuring tests remain discoverable.
9. Communication:
   - When logging Attempt, reference spec lines and bug documentation to emphasise that the parity shim remains optional.
   - Mention whether additional instrumentation (pix0_z, reciprocal) is still pending so future loops know where to focus.
   - Note any differences between PyTorch trace script config and CLI parity command arguments to avoid drift.
Pitfalls To Avoid:
- Do not modify simulator/crystal code this loop; parity evidence only.
- Avoid overwriting prior timestamp directories; use fresh OUTDIR each attempt.
- Wildcard `per_phi_pytorch_*.json` carefully—if multiple matches exist, specify the exact filename.
- Do not rerun nb-compare yet; focus solely on φ=0 parity evidence.
- Keep dtype/device at float64 CPU; changing introduces noise and invalidates comparisons.
- Capture stderr with `tee`; missing logs hamper audits.
- Save raw command lines; missing provenance blocks fix_plan updates.
- Respect Protected Assets in docs/index.md when editing documentation.
- No commits until artifacts hashed, docs updated, and Attempt logged.
- If Δk improves but stays above threshold, state suspected root cause (pix0_z drift, reciprocal recompute, normalization) with references.
- Ensure `sha256.txt` lists every file (logs, json, md, tree, commands, optional geometry outputs).
- If you must regenerate the C trace, rebuild via `make -C golden_suite_generator` and stash the new log; document command and binary hash.
- When editing diagnosis.md, do not remove prior entries; append chronological note.
- Double-check that spec-mode tests remain green; parity shim must not regress the normative path.
- Mention docs/bugs/verified_c_bugs.md lines 166-204 in summary to reinforce bug classification.
- Do not forget to update `reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md` table of contents if the file uses anchors.
- Avoid editing `plans/active/cli-phi-parity-shim/plan.md` unless you are marking checklist items; no content rewrites mid-loop.
Pointers:
- plans/active/cli-phi-parity-shim/plan.md (Phase C4 diagnostic checklist C4b–C4d)
- plans/active/cli-noise-pix0/plan.md (Phase L3k.3 summary table)
- docs/fix_plan.md#CLI-FLAGS-003 (Next Actions + Attempts log)
- specs/spec-a-core.md:211-214 (normative φ rotation per step)
- specs/spec-a-cli.md:1-120 (CLI phi flag semantics)
- arch.md:204-216 (architecture loop order verifying φ rotation placement)
- docs/architecture/pytorch_design.md:120-220 (vectorization principles)
- docs/bugs/verified_c_bugs.md:166-204 (C-PARITY-001 documentation)
- reports/2025-10-cli-flags/phase_l/parity_shim/20251008T021659Z/ (previous Δk plateau evidence)
- scripts/trace_per_phi.py (command-line options, dtype/device assumptions)
- scripts/compare_per_phi_traces.py (comparison CLI, tolerance logic)
- scripts/debug_detector_pix0_calc.py (geometry tap utility if needed)
- docs/architecture/detector.md §5 (pix0/vector conventions for reference) 
Next Up: After Δk and ΔF_latt_b hit tolerance, tackle Phase L3k.3c.5 by updating docs/tests (`diagnosis.md`, `docs/bugs/verified_c_bugs.md`, parity-mode pytest evidence) before re-running nb-compare in Phase L4.
