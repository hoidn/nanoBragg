Summary: Draft Tap 5.3 accumulation instrumentation brief before touching trace code.
Mode: Docs
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2026-01-vectorization-parity/phase_e0/<STAMP>/tap5_accum_plan.md; reports/2026-01-vectorization-parity/phase_e0/<STAMP>/commands.txt
Do Now: VECTOR-PARITY-001 Tap 5.3 instrumentation brief — pytest --collect-only -q
If Blocked: Capture the blocker in docs/fix_plan.md (Attempt log) and drop a stub tap5_accum_plan.md marked BLOCKED inside the stamped reports directory.

Priorities & Rationale:
- docs/fix_plan.md:75-78 — Next Actions now start with the Tap 5.3 instrumentation brief; we must land this before any code edits.
- plans/active/vectorization-parity-regression.md:13-24 — Status snapshot highlights Tap 5.3 evidence as the gating item for Phase F.
- plans/active/vectorization-parity-regression.md:97-100 — Phase E15-E18 table spells out the required deliverables for the brief and follow-on captures.
- reports/2026-01-vectorization-parity/phase_e0/20251010T113608Z/comparison/tap5_hypotheses.md:234-312 — Recommended action section formalises the Tap 5.3 plan and required schema.
- specs/spec-a-core.md:241-259 — Normative oversample accumulation and last-value scaling must be cited to anchor the brief.

How-To Map:
1. Set `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and create `reports/2026-01-vectorization-parity/phase_e0/$STAMP/{,py_taps,c_taps}` plus `commands.txt` placeholder; record the export command and mkdir sequence in commands.txt.
2. Author `tap5_accum_plan.md` in that directory summarising scope, logging schema, guard names, target pixels, acceptance thresholds, references (include specs/spec-a-core.md:241-259 and plan rows E15-E18), and explicit next-step checklist.
3. Note any command templates (PyTorch tap invocation, C binary rebuild) inside the plan plus commands.txt so future loops can copy without guessing.
4. Run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q` from repo root; append the command, exit code, and duration to commands.txt.
5. Update docs/fix_plan.md Attempt log after committing artifacts, referencing the stamped directory and summarising key decisions.

Pitfalls To Avoid:
- Do not touch simulator or trace code yet; this loop is planning-only.
- Keep the stamped report directory untracked (gitignore already covers reports/); do not stage artifacts.
- Ensure guard names (`TRACE_PY_TAP5_ACCUM`, `TRACE_C_TAP5_ACCUM`) match fix_plan wording exactly.
- Cite spec and plan sources verbatim; no paraphrased physics without references.
- Include both edge (0,0) and centre (2048,2048) pixels in the plan; skipping either breaks parity checks.
- Document expected tolerance (≤1e-6 relative for per-subpixel terms) so comparisons have clear pass/fail rules.
- Remember to log pytest collect-only even if nothing fails; omit only if the command cannot run.
- Avoid inventing new tap directories; reuse `phase_e0` cadence to keep history linear.
- Do not modify docs outside Tap 5 scope unless required to clear blockers.
- Confirm NB_C_BIN stays pointed at golden_suite_generator/nanoBragg in any future command templates.

Pointers:
- docs/fix_plan.md:3-6
- docs/fix_plan.md:75-78
- plans/active/vectorization-parity-regression.md:97-100
- reports/2026-01-vectorization-parity/phase_e0/20251010T113608Z/comparison/tap5_hypotheses.md:245-312
- specs/spec-a-core.md:241-259
- docs/development/testing_strategy.md:45-75

Next Up:
- Tap 5.3 PyTorch capture (`reports/.../py_taps/`) once the instrumentation brief is committed.
