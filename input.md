Summary: Implement the Option B lambda override and steps fix so weighted-source parity can unblock vectorization follow-ups.
Mode: Parity
Focus: SOURCE-WEIGHT-001 / Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_src_003.py -v
Artifacts: reports/2025-11-source-weights/phase_e/<STAMP>/{commands.txt,collect.log,pytest.log,metrics.json,simulator_diagnostics.txt}
Do Now: [SOURCE-WEIGHT-001] Implement Option B override, add TC-E1/E2/E3, then run KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_src_003.py -v
If Blocked: Capture the partial command/test output under reports/2025-11-source-weights/phase_e/<STAMP>/attempts/ and log the blocker in docs/fix_plan.md attempts.
Priorities & Rationale:
- docs/fix_plan.md:4046 enumerates Option B implementation, regression, parity, and doc updates that unblock dependent plans.
- plans/active/vectorization.md:23 marks Phase A as blocked until SOURCE-WEIGHT-001 Phase E parity evidence lands.
- plans/active/source-weight-normalization.md:65 keeps Phase E3 blocked pending the CLI lambda override and steps reconciliation.
- reports/2025-11-source-weights/phase_e/20251009T131709Z/lambda_semantics.md documents the agreed code/test/doc touchpoints to follow.
- specs/spec-a-core.md Section 4 reaffirms source weights (and wavelengths) are ignored in accumulation, guiding the override.
How-To Map:
- Implement override: edit src/nanobrag_torch/io/source.py, __main__.py, and simulator.py per lambda_semantics.md; emit warnings.warn(..., stacklevel=2).
- Tests: KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_src_003.py -v (author TC-E1/E2/E3 first); store collect-only output in collect.log.
- Parity bundle: NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE python scripts/cli/run_weighted_source_parity.py --oversample 1 --outdir reports/2025-11-source-weights/phase_e/<STAMP>/; compute correlation.txt and sum_ratio.txt.
- Diagnostics: capture simulator diagnostics (n_sources, steps, fluence) via helper script and save to simulator_diagnostics.txt alongside env.json.
- Docs: after parity passes, update specs/spec-a-core.md (Sources) and docs/development/c_to_pytorch_config_map.md, noting CLI lambda precedence.
Pitfalls To Avoid:
- Do not reintroduce source_weight multipliers; equal weighting must remain vectorized.
- Preserve device/dtype neutrality (no hardcoded .cpu()/.cuda()); respect existing tensor broadcast shapes.
- Keep protected assets intact (docs/index.md references loop.sh, supervisor.sh, input.md).
- Use warnings.warn with stacklevel=2; avoid print statements for user warnings.
- Ensure new tests guard warm/cold devices with torch.cuda.is_available().
- Record exact commands/exit codes in commands.txt for reproducibility.
- Maintain differentiability: no .item()/.detach() on gradient-bearing tensors in simulator paths.
- Remove any temporary scripts or debug prints before finishing.
Pointers:
- docs/fix_plan.md:4046
- docs/fix_plan.md:4052
- plans/active/vectorization.md:23
- plans/active/source-weight-normalization.md:65
- reports/2025-11-source-weights/phase_e/20251009T131709Z/lambda_semantics.md:1
- specs/spec-a-core.md:150
Next Up: If parity succeeds early, start drafting docs updates (specs/spec-a-core.md Sources paragraph, config_map beam table).
