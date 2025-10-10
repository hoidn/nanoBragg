Summary: Fold Tap 5.2 bounds evidence into the hypothesis doc so Tap 5.3 planning starts from an updated decision record.
Mode: Docs
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2026-01-vectorization-parity/phase_e0/20251010T123132Z/comparison/tap5_hkl_bounds.md; reports/2026-01-vectorization-parity/phase_e0/20251010T113608Z/comparison/tap5_hypotheses.md
Do Now: VECTOR-PARITY-001 Tap 5.2 synthesis — pytest --collect-only -q
If Blocked: Capture the obstacle in docs/fix_plan.md Attempt log and note it in reports/.../tap5_hypotheses.md (Blocked) before exiting.

Priorities & Rationale:
- docs/fix_plan.md:70-76 — New Next Actions expect the Tap 5.2 semantics write-up and Tap 5.3 prep; keep ledger current.
- plans/active/vectorization-parity-regression.md:13-24 — Phase E status highlights Tap 5.3 instrumentation gating; hypotheses doc must reflect the updated queue.
- reports/2026-01-vectorization-parity/phase_e0/20251010T123132Z/comparison/tap5_hkl_bounds.md:1 — Source evidence describing per-pixel vs global HKL bounds semantics.
- reports/2026-01-vectorization-parity/phase_e0/20251010T113608Z/comparison/tap5_hypotheses.md:1 — Needs revision to retire H1 and reprioritise Tap 5.3.
- docs/development/testing_strategy.md:53 — Collect-only run remains the lightweight verification pass for doc-only loops.

How-To Map:
1. Review `tap5_hkl_bounds.md` and jot the per-pixel vs global bounds contrast; confirm default_F handling matches.
2. Update `tap5_hypotheses.md` (same directory) to: mark H1 closed with Tap 5.1/5.2 evidence, promote H2 as primary, and outline Tap 5.3 evidence needs (referencing plan rows E15–E18).
3. Append a short "Next Steps" block in the hypotheses doc calling out the instrumentation brief + PyTorch capture expectations.
4. Run `pytest --collect-only -q` from repo root; save output snippet in Attempt log if non-zero issues arise.
5. Log the Attempt in docs/fix_plan.md under `[VECTOR-PARITY-001]` with artifact path and elapsed time.

Pitfalls To Avoid:
- Don’t touch simulator or C sources during this evidence pass.
- Keep Tap numbering consistent with plan (E15–E18); no renumbering.
- Preserve existing table structure in `tap5_hypotheses.md` (update rows, don’t rebuild layout).
- No new environment variables or guards yet; instrumentation brief comes next loop.
- Ensure collect-only run uses `KMP_DUPLICATE_LIB_OK=TRUE` if shell profile requires it.
- Avoid editing docs outside the Tap 5 context this loop.
- Cite artifact timestamps exactly as recorded; no abbreviated paths.
- Keep notes factual—if confidence levels change, explain with Tap references.
- Do not mark plan tasks complete until evidence is committed and linked.
- Coordinate with supervisor before spawning subagents beyond prompts/main.md.

Pointers:
- docs/fix_plan.md:70-83
- plans/active/vectorization-parity-regression.md:13-110
- reports/2026-01-vectorization-parity/phase_e0/20251010T123132Z/comparison/tap5_hkl_bounds.md:1
- reports/2026-01-vectorization-parity/phase_e0/20251010T113608Z/comparison/tap5_hypotheses.md:1
- docs/development/testing_strategy.md:45-75

Next Up:
- Tap 5.3 instrumentation brief (`tap5_accum_plan.md`) once the hypotheses doc is refreshed.
