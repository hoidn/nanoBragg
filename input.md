Summary: Capture the nanoBragg.c seed pipeline so we can close Phase B3 of the determinism plan and unblock Sprint 1 remediation.
Mode: Parity
Focus: [DETERMINISM-001] PyTorch RNG determinism
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/determinism-callchain/phase_b3/<STAMP>/
Do Now: [DETERMINISM-001] PyTorch RNG determinism — document nanoBragg.c seed propagation (no pytest; evidence-only)
If Blocked: Record the obstacle in `reports/determinism-callchain/phase_b3/<STAMP>/blocked.md` with the attempted command and update Attempts History before proceeding elsewhere.

Priorities & Rationale:
- plans/active/determinism.md:30 keeps Phase B3 open until the C seed contract is captured.
- docs/fix_plan.md:100 pushes Sprint 1 to finish determinism triage before other remediation.
- specs/spec-a-core.md:520 defines canonical defaults for noise, mosaic, and misset seeds.
- arch.md:85 (ADR-05) mandates LCG parity across RNG domains.
- docs/architecture/c_function_reference.md:143 states the C RNG mutates seeds via `long *idum` side effects.

How-To Map:
1. `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`
2. `mkdir -p reports/determinism-callchain/phase_b3/$STAMP`
3. `rg -n "misset_seed" golden_suite_generator/nanoBragg.c | tee reports/determinism-callchain/phase_b3/$STAMP/grep_misset_seed.txt`
4. `rg -n "mosaic_seed" golden_suite_generator/nanoBragg.c | tee reports/determinism-callchain/phase_b3/$STAMP/grep_mosaic_seed.txt`
5. `sed -n '48650,49220p' golden_suite_generator/nanoBragg.c > reports/determinism-callchain/phase_b3/$STAMP/c_rng_excerpt.c` (captures `ran1`, seeding loops, and mosaic/misset usage)
6. Summarise the C callchain (entry → seed storage → RNG invocation → lattice loops) in `reports/determinism-callchain/phase_b3/$STAMP/c_seed_flow.md`, mirroring the structure used in `reports/determinism-callchain/callchain/static.md`.
7. List executed commands in `reports/determinism-callchain/phase_b3/$STAMP/commands.txt` and note any open questions (e.g., additional C instrumentation) at the end of `c_seed_flow.md`.

Pitfalls To Avoid:
- Do not edit production code or C sources; evidence only.
- Keep every artifact under `reports/determinism-callchain/phase_b3/$STAMP/` to preserve the bundle history.
- No full `pytest` run; stay within targeted evidence workflow.
- Maintain device/dtype neutrality in any exploratory Python snippets (avoid `.cpu()` / `.cuda()` guesses).
- Follow Protected Assets rule—never rename/delete files listed in docs/index.md.
- Reuse the existing callchain terminology; do not introduce new tap names without plan alignment.
- Record command outputs verbatim; avoid paraphrasing numerical data.
- If TorchDynamo must be disabled later, document it rather than changing tests now.
- Avoid generating large diffs from `nanoBragg.c`; rely on excerpts in artifacts.
- Update Attempts History immediately after capturing artifacts.

Pointers:
- plans/active/determinism.md:35
- docs/fix_plan.md:100
- specs/spec-a-core.md:520
- arch.md:85
- docs/architecture/c_function_reference.md:143
- reports/determinism-callchain/callchain/static.md

Next Up: Once the C callchain summary lands, scope a Dynamo mitigation plan so we can capture dynamic taps without the device_interface crash.
