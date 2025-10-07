Summary: Capture detailed Phase D1 blueprint so polynomial vectorization can proceed without surprises
Mode: Docs
Focus: VECTOR-TRICUBIC-001 / Phase D1
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_tricubic_vectorized.py
Artifacts: reports/2025-10-vectorization/phase_d/polynomial_validation.md; reports/2025-10-vectorization/phase_d/collect.log; reports/2025-10-vectorization/phase_d/tap_points.md (if tap inventory grows)
Do Now: VECTOR-TRICUBIC-001 Phase D1 — draft reports/2025-10-vectorization/phase_d/polynomial_validation.md with tensor-shape + C-reference plan; run `pytest --collect-only -q tests/test_tricubic_vectorized.py` and tee stdout to reports/2025-10-vectorization/phase_d/collect.log
If Blocked: Capture blockers + hypotheses in polynomial_validation.md, rerun the collect-only command to confirm selectors still resolve, and park raw stderr/stdout in collect.log for supervisor triage

Background Notes:
- Current gather path (Phase C) produces (B,4,4,4) neighbourhood tensors but still falls back to scalar polynomial helpers when B>1
- Vectorizing polynomials unblocks the long-term goal of running the supervisor command with PyTorch CLI parity without fallbacks
- Detector absorption work (Phase F) depends on the lessons from Phase D — thorough documentation now prevents duplicated effort later
- Prior perf studies (reports/benchmarks/20250930-165726-compile-cache/analysis.md) highlight polin3 as a hotspot once batching activates; note this in the worksheet

Context Reminders:
- Supervisor initiative currently prioritises CLI parity and vectorization; keep D1 scoped to enabling code work without actually modifying code
- Protected Assets rule applies; any new helper scripts must live beneath scripts/ and be referenced in docs/index.md if persistent
- The PyTorch runtime checklist mandates CPU + CUDA smoke for any new tensor path; plan for both devices even if CUDA unavailable locally
- Document how D1 interacts with future parity gating (nb-compare/Phase E) so we have a straight hand-off once implementation lands

Priorities & Rationale:
- plans/active/vectorization.md:1 — Context + dependency list; cite relevant docs inside worksheet to show full awareness
- plans/active/vectorization.md:48 — Phase D is labelled the active gate; D1 documentation is prerequisite for every subsequent task
- plans/active/vectorization.md:49 — Highlights need to avoid nearest-neighbour fallback by batching polynomials; reiterate the broadcast math
- plans/active/vectorization.md:54 — Table lists D4 test sweep requirements; note them in exit criteria
- docs/fix_plan.md:2194 — Fix-plan entry reiterates D1–D4 ordering and mandates artefact linkage
- docs/development/testing_strategy.md:70 — Supervisor loops require collect-only proof before running targeted tests; capture log once
- docs/development/pytorch_runtime_checklist.md:1 — Guardrails around vectorization + device neutrality must be called out in the new worksheet
- reports/2025-10-vectorization/phase_b/design_notes.md:12 — Contains the broadcast equations D1 must extend
- reports/2025-10-vectorization/phase_c/implementation_notes.md:14 — Documents gather output shapes and constraints that the polynomial layer must accept
- reports/2025-10-vectorization/phase_c/gradient_smoke.log — Shows existing regression harness to reuse post-implementation
- nanoBragg.c:4021 — Reference implementation for polin3 coefficients; D1 should quote this per CLAUDE Rule #11
- docs/architecture/pytorch_design.md:15 — Differentiability guidance to restate when planning gradcheck coverage
- docs/index.md — Protected asset list; ensure any new script references live under scripts/validation or scripts/benchmarks per policy

Diagnostic Questions To Answer:
- What tensor shapes enter each polynomial helper when batching B>1, and how do they reshape back to detector grids?
- How will out-of-range neighbourhoods propagate through batched polynomials, and what masking strategy will prevent NaNs?
- Which gradients must be preserved (w.r.t. Fhkl? lattice offsets?) and what gradcheck tolerances will we require in float64?
- Do we anticipate torch.compile graph breaks when swapping in batched helpers, and how will we detect/report them?
- What tap points are necessary to debug batched polynomial values if parity drifts (e.g., before/after each interpolation axis)?

Deliverable Checklist:
- [ ] Outline scalar vs batched input/output shapes for polint/polin2/polin3, including named axes and reshape rules
- [ ] Provide at least one worked example showing indices mapping from detector grid → flattened B → restored grid
- [ ] Identify tap points for instrumentation (pre/post polynomial evaluation, mask applications) and record them in tap_points.md if needed
- [ ] Cite exact C code ranges for each helper and mark intended docstring insertion points per CLAUDE Rule #11
- [ ] Define gradient validation strategy (float64 gradcheck + float32 smoke) and record target tolerances + command selectors
- [ ] Plan device coverage (cpu and cuda) noting fallback if CUDA unavailable; mention requirement to record `torch.cuda.is_available()` status
- [ ] Note performance measurement hooks (reuse scripts/benchmarks/tricubic_baseline.py with new flags) and expected metrics to compare
- [ ] Summarise expected failure modes (OOB neighbourhoods, NaN handling, dtype promotion) and mitigation strategies
- [ ] Enumerate configuration knobs (dtype overrides, torch.compile caching, environment flags) that need doc updates later
- [ ] Capture open questions for supervisor sign-off before D2 (e.g., handling complex HKL interpolation or caching of coefficients)

Quality Gates To Record:
- Explicit exit criteria for D1 completion (worksheet reviewed, tap list agreed, collect-only log captured)
- Blocking conditions that would prevent D2 start (missing C references, incomplete gradient plan, device ambiguity)
- Artefact directory hygiene expectations (only phase_d/ contains new files for this loop)
- Confirmation that future D2 commits must bundle docstring updates alongside code edits

How-To Map:
- export KMP_DUPLICATE_LIB_OK=TRUE before invoking pytest or scripts (avoid MKL duplicate-lib crash)
- mkdir -p reports/2025-10-vectorization/phase_d to keep artefacts organised alongside earlier phases
- pytest --collect-only -q tests/test_tricubic_vectorized.py | tee reports/2025-10-vectorization/phase_d/collect.log (aggregate proof for supervisor log)
- After collect-only, open reports/2025-10-vectorization/phase_b/design_notes.md and copy relevant equations into the new worksheet with updated batching commentary
- Structure polynomial_validation.md sections as: Context, C references, Tensor shapes, Broadcast diagrams, Masking & OOB plan, Gradient plan, Device plan, Tap points, Performance hooks, Open questions, Exit criteria
- If tap points become numerous, create reports/2025-10-vectorization/phase_d/tap_points.md summarising desired traces for future debugging scripts
- Reference docs/development/testing_strategy.md:70 within the worksheet to show compliance with testing SOPs
- Close the worksheet with clear exit criteria mapping directly to plan tasks D2–D4 so future loops know when D1 is satisfied
- Mention in the worksheet that Phase E will rerun benchmarks under scripts/benchmarks/tricubic_baseline.py and compare before/after metrics
- Annotate any assumptions about HKL tensor layout (contiguous/Fortran order) so implementation can validate them later

Pitfalls To Avoid:
- Do not edit production code or tests during this documentation loop; leave implementation for D2+
- Avoid vague shape descriptions — specify exact tensor dimensions with named axes and flattening order
- Do not forget CLAUDE Rule #11: the worksheet must note the exact C snippet to paste into docstrings before implementation
- Keep device/dtype neutrality explicit; note how tensors stay on caller device without `.to()` churn
- Do not schedule benchmarks yet; Phase E will own quantitative comparisons
- Guard against slipping into implementation details without documenting validation strategy first
- Remember Protected Assets: no deletions or renames of docs/index.md entries or scripts referenced there
- Do not expand the plan into multiple files; all design notes stay under reports/2025-10-vectorization/phase_d/
- Avoid promising timelines; focus on requirements and exit criteria only
- Refrain from editing docs outside the scoped artefacts unless absolutely necessary; changes to specs/arch docs come in Phase G
- Do not assume CUDA availability; explicitly document fallback steps if only CPU is reachable
- Avoid mixing float32/float64 inadvertently in examples—call out dtype expectations clearly

Pointers:
- plans/active/vectorization.md:1 — Context + dependency list; cite relevant docs inside worksheet
- plans/active/vectorization.md:48 — Phase D table for task sequencing and required artefacts
- docs/fix_plan.md:2194 — Active fix-plan entry providing supervisor expectations and reproduction commands
- docs/development/testing_strategy.md:70 — Collect-only guidance for documentation loops
- docs/development/pytorch_runtime_checklist.md:1 — Runtime guardrails to quote in validation plan
- reports/2025-10-vectorization/phase_b/design_notes.md — Prior broadcast design to extend
- reports/2025-10-vectorization/phase_c/gradient_smoke.log — Evidence of current regression harness to reuse
- reports/2025-10-vectorization/phase_c/implementation_notes.md — Gather implementation summary for reference
- docs/architecture/pytorch_design.md:1 — Differentiability + performance trade-offs to restate

Coordination Notes:
- Flag any discovered doc drift (spec vs arch) within polynomial_validation.md so Phase G can schedule updates
- If new scripts are required later, list them as TODOs rather than creating them now; supervisor will author follow-up plan entries
- Record any open questions for performance initiative owners (PERF-PYTORCH-004) regarding benchmark thresholds

Next Up: Phase D2 — implement batched polint/polin2/polin3 once the worksheet (D1) is reviewed and accepted; ensure docstrings include the quoted C code before coding
