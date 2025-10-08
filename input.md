Summary: Capture cache-enabled cross-pixel trace evidence (M2i.1) so we can isolate the first VG-2 divergence before touching simulator code.
Mode: Parity
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_l/carryover_probe/<timestamp>/{commands.txt,trace_py.log,trace_py_per_phi.log,trace_diff.md,trace_diff_manual.patch,metrics.json,env.json,observations.txt,README.md,sha256.txt}
Do Now: Run `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --roi 684 686 1039 1040 --phi-mode c-parity --dtype float64 --device cpu --out trace_py.log` and archive the outputs under a fresh `carryover_probe/<timestamp>/` directory.
If Blocked: Capture stdout/stderr to `attempt.log`, stash the partial directory with a note of the failure mode, and stop so we can debug it next loop.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:27 — Plan makes the CPU c-parity trace the first gate after gradcheck.
  This evidence is the prerequisite before touching cache wiring or scaling math again.
  Treat this as the unlock key for M2g.5/M2g.6; without it, those rows stay blocked.
- docs/fix_plan.md:461 — VG-2 stays red until we log a new ROI trace; running the harness satisfies the top action item.
  Without this entry, the parity initiative remains blocked.
  Update the Attempts table immediately so downstream loops can see the new timestamp.
- docs/debugging/debugging.md:22 — Parallel trace comparison is the mandated workflow for physics regressions.
  A clean PyTorch trace gives us the side we control; we already have the C trace archived.
  Following the SOP verbatim avoids the usual guesswork and keeps the audit trail intact.
- specs/spec-a-core.md:205 — φ rotations must start from the unrotated lattice each step.
  The new trace confirms whether cache substitution respects that spec clause.
  Any deviation here is a spec violation, not an implementation preference.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T165745Z_carryover_cache_validation/summary.md — Gradcheck success proves Option B cache is sound.
  Today’s trace needs to tie that success to a concrete VG-2 diagnosis.
  Use that summary to double-check gradient magnitudes if anything looks off.
- reports/2025-10-cli-flags/phase_l/scaling_validation/scaling_validation_summary.md — Shows the lingering F_latt sign flip we’re chasing.
  We will compare the new metrics against that summary to confirm progress.
  Keep the old JSON nearby so you can compute deltas without rerunning scripts.
Deliverable Expectations:
Capture the trace, diff, metrics, and commentary so the next loop can pinpoint the first clean divergence.
The attempt log should include timestamp, command, runtime, first_divergence, F_latt values, and any anomalies.
If the divergence moves or disappears, call it out explicitly—this is the signal we’ve been waiting for.
Store a one-line executive summary inside README.md; future parity sweeps rely on quick scanning.
Bundle cpu_info.txt, env.json, and commands.txt together so provenance never goes missing.
If a file is intentionally omitted, explain why in the attempt entry so reviewers aren’t left guessing.
Remember that these artifacts may feed automation later—consistency is more valuable than brevity.
How-To Map:
- Step 1 — Preflight environment.
  Ensure repo root is the CWD, git status is clean, and the venv Python (3.13.x) is active.
  Confirm `A.mat` and `scaled.hkl` exist; the harness aborts without them. NB_C_BIN is irrelevant for this step.
  This is also a good time to glance at the latest git SHA and note it for commands.txt.
- Step 2 — Prepare timestamped workspace.
  Create `ts=$(date -u +%Y%m%dT%H%M%SZ)` and make `reports/2025-10-cli-flags/phase_l/carryover_probe/$ts`.
  Verify no directory collision and note the value; every artifact will live under this folder.
  Keep the timestamp handy—you’ll reuse it when naming diff files and attempt notes.
- Step 3 — Execute the harness command.
  Use the Do Now command with CPU + float64; add `--emit-rot-stars` if ap/bp/cp are needed.
  Watch stdout to ensure ≈114 TRACE_PY lines and 10 TRACE_PY_PHI lines appear; rerun if the harness exits early.
  If the harness emits warnings, capture them immediately so you can document them later.
- Step 4 — Collect logs and metadata.
  Copy `trace_py.log` (and any `trace_py_per_phi.log`) into the timestamped folder, keeping the raw stdout in `trace_harness_stdout.txt`.
  Write `commands.txt` (command, git SHA, timestamp) and capture environment metadata into `env.json`; add `lscpu | head -n 20 > cpu_info.txt` for hardware notes.
  Make sure commands.txt includes the ROI arguments and whether `--emit-rot-stars` was used; this avoids guesswork later.
- Step 5 — Generate diffs and metrics.
  Run `capture_live_trace.py --trace trace_py.log --out trace_diff.md` and also `diff -u <baseline>/trace_py.log trace_py.log > trace_diff_manual.patch`.
  Produce `metrics.json` with `first_divergence`, F_latt values, runtime, and validate it via `python -m json.tool`; record observations in `observations.txt` and a short README.
  If the diff still flags F_latt, note the sign and magnitude so we can line it up with the old summary.
- Step 6 — Finalise bundle and update docs.
  Compute `sha256sum * > sha256.txt`, list the directory to confirm expected files, and compress large logs if necessary.
  Update docs/fix_plan.md (Attempt #167+) with the timestamp, key metrics, and link; cross-reference in the plan status snapshot, then verify `git status` shows only doc edits.
  When logging the attempt, mention any additional files you created (README, cpu_info, manual diff) so reviewers know where to look.
Post-Run Notes:
Keep personal scratch notes on what looked suspicious (e.g., magnitude of F_latt delta, new warnings).
Flag anything that still feels off even if the diff looks unchanged—we may need that clue for M2g.5.
If runtime differs wildly from prior captures, jot it down; performance swings can hint at cache misuse.
Before wrapping, glance at previous `carryover_probe` runs so you can contextualise improvements or regressions.
Leave yourself a TODO in README.md if something needs follow-up in M2i.2 or M2g.5.
Share the timestamp and headline metric in Slack if the team needs visibility; more eyes help.
Archive your local scratch notes in `notes.txt` if they contain observations worth preserving.
Pitfalls To Avoid:
- Do not modify production code; this loop is evidence-only.
- Do not run the full pytest suite; no selectors are mapped for this step.
- Avoid GPU execution; plan explicitly wants CPU float64 parity first.
- Do not reuse prior timestamps; always create a fresh directory.
- Keep artifact names ASCII with underscores (no spaces or fancy characters).
- Include `git rev-parse HEAD` output in commands.txt for provenance.
- Do not skip env.json or cpu_info.txt; device/dtype neutrality must be documented.
- Ensure TRACE_PY and TRACE_PY_PHI lines are both present; rerun with `--emit-rot-stars` if needed.
- Archive any per-φ logs; missing files make comparisons impossible later.
- Keep the working tree clean after logging docs; revert accidental edits immediately.
Risk Watch:
Any missing artifact or undocumented warning will force us to rerun the harness and lose a loop.
Double-check directory names, hash outputs, and attempt summaries before leaving the branch.
If you see unexpected behaviour, escalate in the attempt notes rather than guessing.
When in doubt, err on the side of saving more context; discarding logs is almost always a regret.
Treat the evidence directory as immutable once you leave the loop—no retroactive edits without logging them.
Pointers:
- plans/active/cli-noise-pix0/plan.md:28
- docs/fix_plan.md:461
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:38
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/trace_py.log
- docs/debugging/debugging.md:22
- specs/spec-a-core.md:205
Reference Strategy:
Keep these tabs open while you work—the plan spells out success criteria, the fix-plan ledger records provenance, the harness script documents arguments, and the baseline trace shows what you’re trying to match.
The debugging SOP and spec clauses keep us honest about methodology and physics.
If you spot drift between plan and fix-plan, annotate it in your attempt so galph can reconcile next loop.
Bookmark the gradcheck summary as well; it’s the proof that gradients stayed intact while we diagnose parity.
Next Up (if you finish early):
1. M2i.2 metrics refresh — regenerate `metrics.json`/`trace_diff.md` and compare against 20251008T075949Z.
2. M2g.5 scaffolding — outline the cache-aware trace tap fixes needed to stop the CUDA IndexError (notes only, no code).
