2025-10-05 23:26:58Z | 24fbeeb | galph | Active Focus: Close CLI-FLAGS-003 Phase C gaps so the supervisor command with -nonoise and -pix0_vector_mm succeeds under PyTorch CLI.
Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — implement Phase C1 regression tests | PyTest: KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src pytest tests/test_cli_flags.py -q
If Blocked: Capture a manual parser + detector smoke run (store under reports/2025-10-cli-flags/phase_c/manual/) and log the fallback in docs/fix_plan.md Attempts History before resuming implementation.

Priorities & Rationale:
- docs/fix_plan.md:664 now lists Phase C evidence as the First Divergence; addressing C1 tests is the enabling step for the parity smoke.
- plans/active/cli-noise-pix0/plan.md:36 defines the exact assertions the new tests must cover (meter/mm alias, noise suppression, override integrity).
- specs/spec-a-cli.md:109 keeps -noisefile/-nonoise normative, so automated coverage ensures we continue to satisfy the spec’s output contract.
- docs/architecture/detector.md:35 documents the pix0 override workflow; test coverage prevents regressions when detector internals change.
- src/nanobrag_torch/__main__.py:339 & 1170 contain the new flag handling; covering those lines via tests protects the CLI surface without manual smoke runs.
- docs/development/testing_strategy.md:166 reminds us to archive authoritative commands/logs; storing the pytest output is part of closing the fix-plan item.

How-To Map:
- Create `tests/test_cli_flags.py` if missing; add a module-level docstring referencing CLI-FLAGS-003 Phase C1.
- Import `pytest`, `torch`, `parse_and_validate_args`, `create_parser`, `DetectorConfig`, and `Detector` so tests touch the real CLI + detector stack.
- Define a helper `def run_parse(args):` that uses `parser = create_parser()` and returns `parse_and_validate_args(parser.parse_args(args))` to avoid shared state between tests.
- Test pix0 meters alias:
  - Call `config = run_parse(['-cell','100','100','100','90','90','90','-pixel','0.1','-pix0_vector','0.1','-0.2','0.3'])`.
  - Assert `config['pix0_override_m'] == pytest.approx((0.1, -0.2, 0.3), rel=0, abs=1e-12)`.
  - Assert `config['custom_pix0_vector'] == config['pix0_override_m']` to confirm CUSTOM override propagation.
- Test pix0 millimeter alias:
  - Call `config_mm = run_parse(['-cell','100','100','100','90','90','90','-pixel','0.1','-pix0_vector_mm','100','-200','300'])`.
  - Assert the override matches `(0.1, -0.2, 0.3)` and confirm meter conversion occurs with 1e-12 tolerance.
  - Compare to the meters result to enforce equality.
- Test dual-flag rejection:
  - Use `with pytest.raises(ValueError)` around `run_parse([...'-pix0_vector','0','0','0','-pix0_vector_mm','0','0','0'])` and assert the error message mentions mutual exclusivity.
- Cover detector override persistence on CPU:
  - Build `cfg = DetectorConfig(distance_mm=100, pixel_size_mm=0.1, spixels=4, fpixels=4, pix0_override_m=torch.tensor([0.01,-0.02,0.03], dtype=torch.float64))`.
  - Instantiate `det = Detector(cfg, device='cpu', dtype=torch.float64)`.
  - Assert `torch.allclose(det.pix0_vector, torch.tensor([0.01,-0.02,0.03], dtype=torch.float64))`.
  - Call `det.invalidate_cache()` and assert `pix0_vector` remains unchanged.
  - Check `det.close_distance == det.distance` and `det.r_factor == pytest.approx(1.0)`.
- Cover detector override persistence on CUDA:
  - Wrap in `pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")`.
  - Repeat the CPU assertions using `device='cuda'` and ensure the tensor stays on `cuda:0`.
- Test -nonoise suppresses runtime noise:
  - Parse `config = run_parse(['-floatfile','out.bin','-noisefile','noise.img','-nonoise'])`.
  - Assert `config['noisefile'] == 'noise.img'` and `config['suppress_noise'] is True`.
  - Assert `config['adc']` keeps default 40.0 to ensure we did not mutate unrelated fields.
- Test -noisefile without -nonoise:
  - Parse `config = run_parse(['-floatfile','out.bin','-noisefile','noise.img'])`.
  - Assert `config['suppress_noise'] is False` to show tests detect future regressions.
- Sanity test for seed handling:
  - Provide explicit `-seed 1234 -nonoise`; ensure `config['seed'] == 1234` (no forced reseeding when noise disabled).
- Add docstrings/comment blocks referencing Phase A evidence (`reports/2025-10-cli-flags/phase_a/README.md`) so future maintainers know the expected values.
- Parameterize pix0 tests over several signed combinations (e.g., `[('0.1','-0.2','0.3'), ('-0.1','0.0','0.0')]`) to catch sign bugs; convert mm by multiplying by 1000 using list comprehension.
- Default dtype in tests should follow runtime default (float32) unless checking precision; when necessary, set `dtype=torch.float64` explicitly to match detector override code.
- After writing tests, run the authoritative command `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src pytest tests/test_cli_flags.py -q | tee reports/2025-10-cli-flags/phase_c/pytest/test_cli_flags.log`.
- Inspect the log: ensure 0 failures, desired skips, and recorded run duration.
- If pytest fails, triage by verifying CLI parsing logic or detector override path; adjust implementation only if spec alignment demands it.
- Upon success, update docs/fix_plan.md Attempts History (append Phase C1 entry) referencing the new log and summarizing metrics (pass count, skips, runtime).
- Optionally, add TODO comments in plan Phase C2 referencing upcoming parity smoke to keep momentum.
- Stage new test file and report artifacts before ending the engineer loop (document expectation in input to maintain transparency).
- Keep commands reproducible: note any temporary environment variables (NB_C_BIN not needed yet) in the log header.
- If manual smoke fallback triggered, save stdout/stderr under `reports/2025-10-cli-flags/phase_c/manual/parser_noise_diff.log` and cite it in fix_plan Attempts History.
- Prepare to reuse helper functions from Phase B logs if needed (e.g., conversion check) but prefer pytest assertions over print statements.
- Ensure the test file imports only necessary modules; avoid heavy simulator imports to keep runtime low.
- When comparing floats, rely on `pytest.approx` rather than direct equality to avoid spurious failures from float formatting.
- Verify ROI defaults remain unchanged by the new flags by asserting `config.get('roi') is None` in relevant tests.
- Document expected behavior for future reference: `-pix0_vector_mm` accepts millimeter inputs, PyTorch converts to meters (improvement over C), tests should assert this conversion explicitly.
 - After pytest succeeds, run `git status --short tests/test_cli_flags.py` to confirm only the intended files changed before logging the attempt.
 - Note skip counts in the pytest log (e.g., CUDA skip) so future loops can verify coverage remained consistent.
 - Consider adding `pytest.register_assert_rewrite` in the test module if helper functions are factored out for clearer assertion messages.
 - If you add helper functions, place them above tests and prefix with `_` to reduce pytest collection noise.
 - Keep test names descriptive (`test_pix0_alias_mm_matches_meters`) so failures immediately indicate which flag regressed.
 - Capture expected `DetectorConfig.detector_convention` value when overrides are provided (should remain MOSFLM unless CUSTOM triggered) to document behavior.
 - Verify `config['convention']` transitions to `CUSTOM` when pix0 vectors supplied, mirroring C behavior, and assert this inside tests.
 - Double-check that enabling `-pix0_vector_mm` does not alter `beam_vector`; include asserts on `config.get('custom_beam_vector') is None` unless explicitly set.
 - For future reuse, comment the fixture structure so Phase C2 can import the same helpers rather than duplicating parsing logic.
- Before leaving the loop, ensure `reports/2025-10-cli-flags/phase_c/` has an updated README or index summarizing new artifacts (even a short note suffices).
 - Plan to tag the pytest log with commit hash 24fbeeb in its header for traceability; include the exact command used.
 - If you rely on helper constants (e.g., expected pix0 tuples), define them at top-level so multiple tests reuse the same canonical values.
 - Record the wall-clock runtime of the pytest invocation in the log; it helps spot future slowdowns in CLI parsing.
 - After writing tests, run `python -m compileall tests/test_cli_flags.py` to ensure there are no syntax errors before handing control back.

Pitfalls To Avoid:
- Do not construct Namespace objects manually; always run through `create_parser()` so argparse-level defaults are honored.
- Avoid mutating global state between tests (e.g., env vars, working directory); isolate each scenario to prevent cross contamination.
- Refrain from calling `torch.cuda.manual_seed` inside tests—letting CLI set seeds keeps parity with runtime behavior.
- Do not refactor CLI code during this loop; focus on tests unless failures expose a clear implementation bug tied to spec compliance.
- Skip adding sleeps or long-running simulations; tests must finish quickly to keep supervisor loops tight.
- Avoid storing large binary fixtures in git; rely on existing golden data and new textual logs under `reports/`.
- Do not downgrade assertions to loose tolerances; keep unit conversion checks strict so they catch regressions.
- Resist the urge to run the full supervisor command yet; defer to Phase C2 once tests pass.
- Ensure any conditional CUDA coverage falls back gracefully; never mark tests xfail for missing GPU support.
- Do not forget to mention new artifacts in docs/fix_plan.md; missing logs make future audits painful.

Pointers:
- docs/fix_plan.md:664
- plans/active/cli-noise-pix0/plan.md:36
- specs/spec-a-cli.md:109
- docs/architecture/detector.md:35
- src/nanobrag_torch/__main__.py:339
- src/nanobrag_torch/__main__.py:1170
- src/nanobrag_torch/models/detector.py:391
- docs/development/testing_strategy.md:166
- reports/2025-10-cli-flags/phase_a/README.md:10
- prompts/supervisor.md:7

Next Up: After Phase C1 passes, move directly to Phase C2 parity smoke (PyTorch CLI vs NB_C_BIN command capture) or Phase C3 documentation updates (specs/spec-a-cli.md, README_PYTORCH.md) depending on time remaining.
