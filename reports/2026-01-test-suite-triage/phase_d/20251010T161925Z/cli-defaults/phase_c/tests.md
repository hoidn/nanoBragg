# Phase C Test & Validation Map — CLI-DEFAULTS-001

**Timestamp:** 2025-10-10T16:19:25Z

## Targeted PyTest Selectors

| Priority | Selector | Purpose | Notes |
| --- | --- | --- | --- |
| P0 | `pytest -v tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F` | Canonical acceptance for spec §AT-CLI-002 | Run after code change; capture `float_stats.txt` from generated floatfile. |
| P0 | `pytest -v tests/test_at_cli_002.py::TestAT_CLI_002::test_cli_matches_debug_default_script` *(new, TBD)* | Regression ensuring CLI emits same intensities as control API script | Add in same patch as fix; use fixtures to call `debug_default_f.py` or embed API call. |
| P1 | `pytest -v tests/test_hkl_cache.py::TestHKLCache::test_fdump_roundtrip` (or closest equivalent) | Guard HKL cache path after adjusting return semantics | If such test is missing, author targeted unit test covering `try_load_hkl_or_fdump`. |
| P1 | `pytest -v tests/test_cli_end_to_end.py::TestCLI::test_default_f_only_render` *(new, optional)* | Smoke test for CLI-run binary with ROI to ensure non-zero intensities | Convert to quick-run format (32×32 detector) to keep runtime <2s. |
| P2 | `pytest -v tests/test_cli_help.py` | Sanity check CLI wiring still imports | Quick guard, already part of acceptance pack. |

## Auxiliary Scripts / Commands
- `KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_default_f.py --device cpu --dtype float32 --out reports/.../api_control/` — baseline control output; reuse pre-existing script but update instructions to record when default_F fallback works.
- `nb-compare --roi 0 31 0 31 --resample --outdir reports/.../cli-defaults/phase_c/compare_cli_vs_api -- floatbin_cli floatbin_api` — optional parity comparison; record correlation metric.

## Artifact Expectations
- `phase_c/commands.txt` — chronological list of commands executed during verification (pytest selectors, nb-compare, script runs).
- `phase_c/float_stats_cli.txt` & `phase_c/float_stats_api.txt` — summary statistics for CLI vs API float images.
- `phase_c/nb_compare_summary.md` — correlation metrics if nb-compare is executed.
- `phase_c/test_results.json` — pytest JSON report (use `--json-report` if available) capturing pass/fail state.

## Environment Requirements
- Set `KMP_DUPLICATE_LIB_OK=TRUE` for every Python/pytest invocation touching torch.
- Use CPU device for baseline; rerun primary acceptance on CUDA (if available) to ensure no device/dtype regressions.

## Exit Criteria Recap
- All selectors above at priority P0/P1 must pass on both CPU (required) and CUDA (when available).
- Capture artifacts under the same timestamped directory for Attempt #5.
- Update `docs/fix_plan.md` Attempts History with results + artifact pointers.
