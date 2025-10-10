Summary: Fix the CLI default_F-only run so it emits non-zero intensities and passes AT-CLI-002.
Mode: Parity
Focus: [CLI-DEFAULTS-001] Minimal -default_F CLI invocation
Branch: feature/spec-based-2
Mapped tests: tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F
Artifacts: reports/2026-01-test-suite-triage/phase_d/<STAMP>/cli-defaults/attempt_fix/
Do Now: [CLI-DEFAULTS-001] Minimal -default_F CLI invocation — implement the Phase C guard fix, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F`
If Blocked: If the CLI still yields zeros, add the Tap 4 probe from Phase B (see summary at reports/2026-01-test-suite-triage/phase_d/20251010T160902Z/cli-defaults/phase_b/summary.md) and capture the logs under `.../attempt_fix/debug_tap4/` before pausing.

Priorities & Rationale:
- spec compliance — spec-a-cli.md:163 requires the default_F-only CLI path to render non-zero intensity; we are currently violating AT-CLI-002.
- orchestration bug — src/nanobrag_torch/__main__.py:443 and src/nanobrag_torch/__main__.py:1090 show the sentinel `hkl_data=None` plus loose guard that Phase C flagged as the root cause.
- remediation blueprint — plans/active/cli-defaults/plan.md:48 documents the approved implementation steps and artifact policy for this attempt.
- validation coverage — reports/2026-01-test-suite-triage/phase_d/20251010T161925Z/cli-defaults/phase_c/tests.md:1 lists the selectors and auxiliary checks you must run post-fix.

How-To Map:
- Fix the config handling: remove the unconditional `config['hkl_data'] = None` assignment and tighten the guard as outlined in reports/2026-01-test-suite-triage/phase_d/20251010T161925Z/cli-defaults/phase_c/remediation_plan.md:1; ensure `try_load_hkl_or_fdump` only returns meaningful tuples.
- Reproduce AT-CLI-002: parameters lifted from tests/test_at_cli_002.py:31-48 — 32×32 detector, `-default_F 100`, `-lambda 6.2`, `-distance 100`, `-pixel 0.1`; run the test via `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F` from repo root.
- After the fix passes, run the control script for parity: `KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_default_f.py --out reports/.../attempt_fix/api_control/` and compare stats against the CLI floatfile (store `float_stats_cli.txt` and `float_stats_api.txt`).
- Optional but recommended: `nb-compare --roi 0 31 0 31 --outdir reports/.../attempt_fix/nb_compare -- float_cli.bin float_api.bin` to confirm numerical alignment; capture summary in `nb_compare_summary.md`.
- Maintain an updated `commands.txt` in the attempt directory listing every command executed (pytest, scripts, nb-compare) in chronological order.

Pitfalls To Avoid:
- Do not leave the sentinel `config['hkl_data'] = None`; the guard must rely on `config.get` semantics only when real data exists.
- Preserve device/dtype neutrality — no hard-coded `.cpu()`/`.cuda()`; reuse incoming `device`/`dtype` (testing strategy §1.4).
- Keep vectorization intact; avoid adding loops inside the simulator when touching HKL handling.
- Guard against stale `Fdump.bin`; note in artifacts whether one existed and how you handled it.
- Update or add tests before running the full suite; keep runtime under control (no full pytest).
- Follow artifact policy in plans/active/cli-defaults/plan.md:1 — commands, env snapshot, stats, and summaries all live under the timestamped attempt folder.
- Respect Protected Assets — do not move files referenced in docs/index.md.
- Ensure any new asserts log helpful context; do not leave debug prints enabled.

Pointers:
- specs/spec-a-cli.md:163 — AT-CLI-002 acceptance criteria.
- src/nanobrag_torch/__main__.py:443 — sentinel assignment that must be removed.
- src/nanobrag_torch/__main__.py:1090 — HKL guard to tighten.
- plans/active/cli-defaults/plan.md:14 — status snapshot and Phase C/D expectations.
- reports/2026-01-test-suite-triage/phase_d/20251010T161925Z/cli-defaults/phase_c/remediation_plan.md:1 — detailed remediation steps.
- tests/test_at_cli_002.py:28 — failing test harness for reproduction.

Next Up:
- [DETERMINISM-001] PyTorch RNG determinism — prep plan once CLI defaults pass.
