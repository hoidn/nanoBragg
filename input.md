Summary: Publish Phase C determinism documentation so we can close the fix-plan before any new code work.
Mode: Docs
Focus: [DETERMINISM-001] PyTorch RNG determinism
Branch: feature/spec-based-2
Mapped tests: none — docs-only
Artifacts: reports/determinism-callchain/phase_c/<STAMP>/
Do Now: [DETERMINISM-001] PyTorch RNG determinism — capture the Phase C documentation bundle (remediation_summary/docs_updates/testing_strategy notes)
If Blocked: Record the obstacle in `reports/determinism-callchain/phase_c/<STAMP>/blocked.md`, note commands in `commands.txt`, and update `docs/fix_plan.md` Attempts before switching tasks.

Priorities & Rationale:
- plans/active/determinism.md:14-55 keeps Phase C open until we publish the doc/blueprint artifacts.
- docs/fix_plan.md:98-118 lists the new Next Actions that depend on the Phase C bundle.
- reports/determinism-callchain/phase_b3/20251011T051737Z/c_seed_flow.md captures the C seed contract we need to reference.
- reports/2026-01-test-suite-triage/phase_d/20251011T050024Z/determinism/phase_a_fix/logs/summary.txt shows the passing determinism tests to summarise.

How-To Map:
1. `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`
2. `mkdir -p reports/determinism-callchain/phase_c/$STAMP`
3. `tee reports/determinism-callchain/phase_c/$STAMP/commands.txt <<'CMDS'` and log the executed shell steps.
4. Draft `remediation_summary.md` describing the env guards (`TORCHDYNAMO_DISABLE`, `CUDA_VISIBLE_DEVICES=-1`), dtype propagation fixes, and how seeds reach `mosaic_rotation_umat` (cite Attempt #6 + c_seed_flow).
5. Draft `docs_updates.md` enumerating the concrete doc/comment edits needed (target `docs/architecture/c_function_reference.md` RNG section + `src/nanobrag_torch/utils/c_random.py` docstring).
6. Draft `testing_strategy_notes.md` capturing the determinism reproduction workflow (pytest selectors, env vars, artifact expectations) for updating `docs/development/testing_strategy.md`.
7. Save everything under the new stamp directory; no production files changed this loop.

Pitfalls To Avoid:
- Do not edit src/ code or tests—this loop is documentation only.
- Keep all new artifacts under the timestamped `reports/determinism-callchain/phase_c/` folder.
- Reference spec/arch citations when summarising seeds; avoid paraphrasing without citations.
- Maintain device/dtype neutrality in examples (no `.cpu()`/`.cuda()` shortcuts).
- Log every command in `commands.txt`; avoid opaque tooling.
- Leave TorchDynamo mitigation as documentation—no env tweaks in tests yet.
- Preserve Protected Assets from docs/index.md (input.md, loop.sh, supervisor.sh, etc.).
- Keep narratives concise; no speculative fixes.
- Update Attempts History only after artifacts exist.

Pointers:
- docs/fix_plan.md:98-118
- plans/active/determinism.md:14-55
- reports/determinism-callchain/phase_b3/20251011T051737Z/c_seed_flow.md
- reports/2026-01-test-suite-triage/phase_d/20251011T050024Z/determinism/phase_a_fix/logs/summary.txt

Next Up: Draft the actual doc edits (testing strategy + RNG references) once the Phase C bundle is reviewed.
