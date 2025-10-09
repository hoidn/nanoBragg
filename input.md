Summary: Capture spec-backed evidence showing why source weights must be ignored so we can realign SOURCE-WEIGHT-001 before touching implementation.
Mode: Docs
Focus: SOURCE-WEIGHT-001 / Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2025-11-source-weights/phase_b/<STAMP>/{spec_alignment.md,pytorch_accumulation.md,analysis.md,commands.txt,env.json,metrics.json}
Do Now: SOURCE-WEIGHT-001 Phase B1-B3 — run `pytest --collect-only -q`
If Blocked: Record the blocking issue in `reports/2025-11-source-weights/phase_b/<STAMP>/attempts.md`, include command output, and notify in docs/fix_plan.md Attempts History.

Priorities & Rationale:
- specs/spec-a-core.md:150-190 – authoritative quote that the weight column “is read but ignored”.
- golden_suite_generator/nanoBragg.c:2570-2720 – confirm C ignores weights when building steps.
- src/nanobrag_torch/simulator.py:400-420;850-1125 – document where PyTorch still multiplies by `source_weights`.
- plans/active/source-weight-normalization.md – Phase B tasks define expected artifacts.
- docs/fix_plan.md:3953-4105 – refreshed Next Actions/Attempts reference the new evidence bundle.

How-To Map:
- C CLI: `"$NB_C_BIN" -mat A.mat -floatfile reports/2025-11-source-weights/phase_b/<STAMP>/c.bin -sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -nonoise -nointerpolate` (store stdout in commands.txt, metrics in metrics.json).
- PyTorch CLI: `KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -mat A.mat -floatfile reports/2025-11-source-weights/phase_b/<STAMP>/py.bin -sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 --nonoise --nointerpolate` (append metrics to metrics.json, compare to C).
- Document spec evidence in `spec_alignment.md` (quote spec + C code with line anchors) and PyTorch call-chain in `pytorch_accumulation.md` (show tensor shapes, line refs, explain weight multiplier).
- Summarize numeric deltas (correlation, sum_ratio) in `analysis.md`; stash CLI/binary hashes in metrics.json.
- Run `pytest --collect-only -q` for proof and log output under the same directory; capture environment via `python -m json.tool <<<'{...}'` or `scripts/validation/dump_env.py` if preferred.

Pitfalls To Avoid:
- Do not modify production code or tests this loop.
- Keep timestamps consistent in artifact paths; avoid overwriting Phase A bundles.
- Ensure metrics.json includes both C and PyTorch sums/max/correlation.
- Reference spec lines verbatim; avoid paraphrasing the normative language.
- Confirm commands.txt lists every command with exit codes; note NB_C_BIN path.
- Maintain device/dtype neutrality in analysis (call out CPU/CUDA assumptions explicitly).
- Do not delete or move protected assets (docs/index.md entries, existing reports).
- Skip NB_RUN_PARALLEL heavy tests; parity pytest will remain for implementation loop.
- Store env.json with python, torch, CUDA info for reproducibility.
- Update docs/fix_plan.md Attempts only after artifacts exist.

Pointers:
- specs/spec-a-core.md:150-170
- golden_suite_generator/nanoBragg.c:2570-2720
- src/nanobrag_torch/simulator.py:400-420
- src/nanobrag_torch/simulator.py:850-1125
- plans/active/source-weight-normalization.md
- docs/fix_plan.md:3953-4105

Next Up:
- Begin Phase C1-C3 implementation once Phase B evidence is logged.
- Prepare CUDA parity rerun commands for Phase D after implementation lands.
