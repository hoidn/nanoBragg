Summary: Quantify the cache-enabled trace against the C baseline (M2i.2) so we know exactly where VG-2 still diverges before touching simulator code.
Mode: Parity
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2025-10-cli-flags/phase_l/carryover_probe/<timestamp>/metrics_refresh/{commands.txt,summary.md,metrics.json,run_metadata.json,trace_diff.md,trace_diff_manual.patch,env.json,cpu_info.txt,sha256.txt,README.md}; reports/2025-10-cli-flags/phase_l/scaling_validation/lattice_hypotheses.md (updated section)
Do Now: Execute `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py reports/2025-10-cli-flags/phase_l/carryover_probe/20251008T172721Z/trace_py.log --out reports/2025-10-cli-flags/phase_l/carryover_probe/<timestamp>/metrics_refresh/summary.md` and archive the outputs under the new metrics_refresh timestamp.
If Blocked: Capture stdout/stderr to metrics_refresh/attempt.log, record the failing command in commands.txt, and stop so we can triage the tool next loop.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:29 — Plan pins M2i.2 as the next gate; without fresh metrics/diff we cannot progress to cache tap fixes.
- docs/fix_plan.md:463 — Ledger demands the metrics refresh before any new simulator edits; logging this attempt unblocks the remaining VG-2 work.
- reports/2025-10-cli-flags/phase_l/carryover_probe/20251008T172721Z/README.md:33 — Follow-up checklist explicitly calls for trace diff + metrics extraction off the new trace.
- scripts/validation/compare_scaling_traces.py:18 — Script already encapsulates tolerance checks; rerunning it against the new trace gives structured deltas.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md:1 — Baseline hypotheses need an updated entry so future loops can compare residuals.
How-To Map:
- Preflight: ensure repo root CWD, git status clean, PYTHONPATH=src, and `KMP_DUPLICATE_LIB_OK=TRUE` exported; run `pytest --collect-only -q` before touching artifacts.
- Timestamp: `ts=$(date -u +%Y%m%dT%H%M%SZ)` then `mkdir -p reports/2025-10-cli-flags/phase_l/carryover_probe/$ts/metrics_refresh` and note the value for all filenames.
- Run compare tool: execute the Do Now command with the new `$ts`, redirect stdout to `metrics_refresh/compare_stdout.log`, and keep stderr for troubleshooting.
- Diff generation: `diff -u reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log reports/2025-10-cli-flags/phase_l/carryover_probe/20251008T172721Z/trace_py.log > .../metrics_refresh/trace_diff_manual.patch` and convert to Markdown summary (e.g., pipe through `python scripts/validation/compare_scaling_traces.py --emit-markdown ...` if needed, otherwise wrap manual notes into summary.md).
- Provenance bundle: populate commands.txt (full command, git SHA, timestamp), env.json (`python -V`, torch info, pyrefly? env), cpu_info.txt (`lscpu | head -n 20`), sha256.txt (`(cd metrics_refresh && sha256sum * > sha256.txt)`).
- Hypothesis log: append a dated section to `reports/2025-10-cli-flags/phase_l/scaling_validation/lattice_hypotheses.md` summarizing first_divergence, F_latt deltas, and next investigative leads.
Pitfalls To Avoid:
- Do not overwrite the 20251008T172721Z trace; keep metrics in the new timestamp subdir.
- No production code edits; this is strictly evidence.
- Avoid CUDA runs this loop; CPU float64 remains the baseline.
- Don’t skip env.json/cpu_info.txt — parity audits require provenance.
- Ensure diff files are ASCII (no rich text) so reviewers can inspect them quickly.
- Keep summary.md concise but include first_divergence value and any residual tolerances.
- Verify compare_scaling_traces exit code; failures must be logged and escalated.
- Update docs/fix_plan.md Attempt immediately; stale ledgers cause double work.
- Re-run `pytest --collect-only -q` if you regenerate the venv mid-loop.
- Preserve existing lattice_hypotheses context; append rather than rewrite.
Pointers:
- plans/active/cli-noise-pix0/plan.md:28
- docs/fix_plan.md:461
- scripts/validation/compare_scaling_traces.py:1
- reports/2025-10-cli-flags/phase_l/carryover_probe/20251008T172721Z/README.md:33
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md:1
Next Up: 1) M2g.5 trace tooling patch (cache-aware taps). 2) Cache index audit once metrics confirm first_divergence cleared.
