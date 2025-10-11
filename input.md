Summary: Ship Phase C Option A fixes for source weighting (dtype-neutral parser + targeted tests) so cluster C3 can start clearing.
Mode: Parity
Focus: [SOURCE-WEIGHT-002] Simulator source weighting
Branch: main
Mapped tests: tests/test_at_src_001.py; tests/test_at_src_001_simple.py
Artifacts: reports/2026-01-test-suite-triage/phase_j/<STAMP>/source_weighting/phase_c/
Do Now: [SOURCE-WEIGHT-002] Simulator source weighting — implement Phase C1–C3, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py` (CPU first, GPU after pass) and archive under the new Phase C stamp.
If Blocked: Log the roadblock plus current pytest output in Attempt #17 (docs/fix_plan.md) and capture failing run + dtype diagnostics under the same stamp before stopping.
Priorities & Rationale:
- docs/fix_plan.md:166 — Next Actions explicitly call for Phase C1–C3, including new regression test + report delta back to the tracker.
- plans/active/source-weighting.md:55 — Phase C tasks are now active with Option A guardrails; we need Attempt #17 artifacts to progress Sprint 1.2.
- reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/summary.md:31 — Phase K summary flags Sprint 1.2 (source weighting) as the immediate remediation focus after tracker refresh.
- specs/spec-a-core.md:142 — AT-SRC-001 acceptance criteria remain authoritative for semantics; Option A keeps equal-weight behavior but still must honor dtype neutrality.
How-To Map:
- Set `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and create `reports/2026-01-test-suite-triage/phase_j/${STAMP}/source_weighting/phase_c/` before edits; drop commands, env, and before/after dtype notes there.
- Implement parser dtype change + regression test per `implementation_map.md`, then run `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py > reports/.../pytest_cpu.log`.
- If CPU passes, re-run on GPU (`KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py --device=cuda` or equivalent) and save as `pytest_gpu.log`; update Attempt #17 in docs/fix_plan.md with counts + artifact paths and refresh plans/active/source-weighting.md checkboxes.
Pitfalls To Avoid:
- Do not drop vectorization — keep source parsing batched and device/dtype neutral (docs/architecture/pytorch_design.md §1.1.5).
- No `.item()` / `.detach()` on tensors that require gradients (arch.md §15).
- Preserve Option A semantics: still respect CLI wavelength override; do not wire per-source λ changes.
- Maintain Protected Assets (docs/index.md) — do not relocate loop.sh/input.md.
- Keep new tests CPU/GPU aware without forcing device transfers.
- Record env + commands in the artifact bundle; missing provenance breaks triage audit.
- Update docs only after code/tests succeed; avoid speculative spec edits mid-loop.
- Follow `KMP_DUPLICATE_LIB_OK=TRUE` requirement before importing torch (CLAUDE.md rule #6).
- Don’t run full pytest suite this loop; stay on the two targeted selectors unless instructed otherwise.
Pointers:
- docs/fix_plan.md:166
- plans/active/source-weighting.md:55
- reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/summary.md:31
- specs/spec-a-core.md:142
- docs/development/testing_strategy.md:90
Next Up: [TEST-SUITE-TRIAGE-001] — after Phase C passes, prep Sprint 1 tracker update + consider scheduling the next partial suite rerun.
