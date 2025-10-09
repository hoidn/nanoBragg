Summary: Produce the detector absorption vectorization design memo for Phase F1.
Mode: Docs
Focus: VECTOR-TRICUBIC-001 Vectorize tricubic interpolation and detector absorption
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2025-10-vectorization/phase_f/design_notes.md, reports/2025-10-vectorization/phase_f/commands.txt, reports/2025-10-vectorization/phase_f/env.json, reports/2025-10-vectorization/phase_f/sha256.txt
Do Now: VECTOR-TRICUBIC-001 Phase F1 design - pytest --collect-only -q
If Blocked: Capture the exact blocker in reports/2025-10-vectorization/phase_f/blockers.md and ping me via docs/fix_plan.md Attempt update.

Priorities & Rationale:
- Phase F is the remaining high-priority work on `docs/fix_plan.md:3364` and now that Phase E logged parity/perf we must keep momentum.
- `plans/active/vectorization.md` now marks E2/E3 [D]; F1 design notes are the gating deliverable before implementation tasks (F2-F4) can start.
- specs/spec-a-core.md section 4 requires detector absorption to respect batched tensor flows; design must quote the relevant equations so Phase F2 implementations stay aligned.
- `docs/architecture/pytorch_design.md` sections 2.2-2.4 outline the broadcast strategy; summarising the intended `(slow, fast, thicksteps)` shapes prevents regressions.
- `docs/development/pytorch_runtime_checklist.md` sets device/dtype guardrails; we need explicit callouts in the design to keep CPU/CUDA parity when Ralph vectorises absorption.
- `nanoBragg.c:3375-3450` is the authoritative C loop; copy the snippet into the memo per CLAUDE Rule #11 to anchor the implementation path.
- `reports/2025-10-vectorization/phase_a/absorption_baseline.md` holds current performance baselines; cite those numbers so Phase F benchmarks have a clear target.
- The design must document how to stage artifacts under `reports/2025-10-vectorization/phase_f/` so future attempts stay reproducible.
- Tight coupling exists with `tests/test_at_abs_001.py`; list the selectors that will need parametrisation so Phase F3 testers know the scope.
- Coordination note: PERF-PYTORCH-004 top-level benchmarks expect detector absorption speedups; your design should describe how batched layers unlock the promised 10-100x range.

How-To Map:
- Run `pytest --collect-only -q` (KMP_DUPLICATE_LIB_OK=TRUE) before writing to prove the tree imports cleanly.
- Create `reports/2025-10-vectorization/phase_f/` if it does not exist; include subfiles design_notes.md, commands.txt, env.json, and sha256.txt.
- In design_notes.md, start with context, goals, and prerequisites mirroring Phase E structure; outline tensor shapes for `(B, slow, fast, thicksteps)` and any reshaping helpers.
- Paste the exact C reference from `nanoBragg.c` lines 3375-3450 inside a fenced C block per CLAUDE Rule #11 before proposing PyTorch equivalents.
- Enumerate broadcast strategy for `detector_thicksteps`, oversample, and ROI handling; flag how to avoid reintroducing Python loops.
- Call out gradient considerations (no `.item()`, avoid `torch.linspace`, keep computations differentiable) referencing `docs/development/pytorch_runtime_checklist.md` and `docs/architecture/pytorch_design.md`.
- Document expected artifacts for future phases: F2 implementation commits, F3 benchmarks (`scripts/benchmarks/absorption_baseline.py` variants), F4 summaries, archive mirroring.
- Capture relevant commands in commands.txt (pytest collect, benchmark skeletons, nb-compare placeholder if parity runs are planned).
- Dump the current environment via `python -m json.tool` into env.json (include Python, torch, CUDA versions, device availability) so Phase F runs remain reproducible.
- Generate sha256.txt listing checksums for design_notes.md and commands.txt to comply with existing artifact conventions.
- After drafting, update docs/fix_plan.md Attempt history with a new entry that references the design bundle and records pytest collect output; include timestamps and SHA hashes.
- Note in the Attempt that plans/active/vectorization.md Phase F1 remains [ ] until implementation starts; the design memo is the completion signal.
- If you discover missing baseline data or ambiguous spec language, flag it in the memo under "Open Questions" with suggested owners or follow-ups.

Pitfalls To Avoid:
- Do not modify production code or tests in this loop; focus on documentation and evidence only.
- Keep Protected Assets intact (no edits to docs/index.md, loop.sh, supervisor.sh, input.md).
- Avoid introducing non-ASCII characters; stick to plain ASCII in the memo and commands.
- Do not run full pytest or long benchmarks; collect-only is the ceiling for this docs loop.
- Ensure every new document line cites authoritative sources (specs, arch docs, C references) so later phases have verifiable breadcrumbs.
- Maintain device/dtype neutrality in the design narrative; no `.cpu()` shortcuts or device-specific assumptions.
- Keep the memo aligned with vectorization principles-no proposals that resurrect scalar loops.
- Do not forget to set `KMP_DUPLICATE_LIB_OK=TRUE` in any command that imports torch.
- Make sure artifacts live under `reports/2025-10-vectorization/phase_f/` only; no scattered files in repo root.
- Double-check that CLAUDE Rule #11 is satisfied-the C snippet must precede any derived implementation guidance.

Pointers:
- docs/fix_plan.md:3364 (VECTOR-TRICUBIC-001 entry - confirms Phase F scope)
- plans/active/vectorization.md:60 (Phase F table - tasks F1-F4 definitions)
- reports/2025-10-vectorization/phase_e/summary.md (Phase E precedent for structure and content)
- docs/architecture/pytorch_design.md:120-220 (vectorization broadcast rules)
- docs/development/pytorch_runtime_checklist.md (device/dtype requirements to cite)
- specs/spec-a-core.md:400-460 (detector absorption equations and sampling weights)
- nanoBragg.c:3375-3450 (C absorption loop for CLAUDE Rule #11 reference)
- scripts/benchmarks/absorption_baseline.py (baseline harness to mention in the design)
- docs/bugs/verified_c_bugs.md:120-170 (absorption-related quirks to note if relevant)
- reports/2025-10-vectorization/phase_a/absorption_baseline.md (baseline metrics to cite in goals)
- tests/test_at_abs_001.py (selectors to mention for future parameterisation)
- docs/development/testing_strategy.md:70-150 (testing cadence and device expectations)

Next Up:
- If Phase F1 finishes early, queue F2 implementation planning - outline helper APIs before coding.
- Alternatively, prep an nb-compare ROI plan for Phase F3 parity once the absorption code is vectorized.

Design Outline Checklist:
- Start the memo with a recap of Phase A baselines and Phase E validation so readers know what changed.
- Include a dedicated section clarifying tensor dimensions for each stage (gather, polynomial eval, absorption) and how detector_thicksteps expands them.
- Spell out the broadcast order for oversample, phi, mosaic, sources, and thickness to avoid off-by-one bugs later.
- Provide a subsection on memory considerations (detector size versus VRAM) and propose fallback tiling for 4096x4096 detectors.
- Describe how ROI or stripe execution should reuse cached coordinates without degrading vectorization.
- Call out how to integrate with existing caching in `Detector.invalidate_cache()` when new tensors are introduced.
- Document planned helper functions or class methods so the implementation phase has a concrete API sketch.
- Highlight gradient taps that should be verified post-implementation (for example, detector_thicksteps and detector_abs_um).
- Note potential logging hooks for debug mode (tap points for per-layer absorption factors) that stay reusable in callchain traces.
- End the memo with explicit exit criteria mirroring Phase F table so status tracking stays consistent.

Evidence Logging Steps:
- Record every command you run in commands.txt with UTC timestamps and environment prerequisites.
- Add the pytest collect output to commands.txt and attach the console transcript under reports if it contains warnings.
- When saving env.json, include both torch.__version__ and torch.version.cuda plus torch.cuda.is_available() results.
- Capture checksum lines in sha256.txt for design_notes.md, commands.txt, and env.json to maintain artifact integrity.
- Reference the new design bundle in docs/fix_plan.md Attempt description with the exact directory path.
- Mention in docs/fix_plan.md that plans/active/vectorization.md already carries the Phase F checklist so the engineer loop knows where to look.
- Encourage future loops to extend the bundle with benchmark scripts; leave TODO placeholders if appropriate.
- If you spot doc drift elsewhere (for example, runtime checklist missing absorption notes), log it in the Attempt as follow-up work.
- Keep a short Open Questions section in design_notes.md for unresolved issues so later loops can pick them up systematically.
- Close commands.txt with a reminder to set KMP_DUPLICATE_LIB_OK=TRUE on every Python invocation touching torch.

Reference Excerpts To Cite:
- specs/spec-a-parallel.md section 2.3.4 (tricubic acceptance metrics) even though Phase F targets absorption; note parity expectations.
- docs/architecture/detector.md section 5.3 (absorption pipeline) for detailed geometry interplay.
- docs/debugging/detector_geometry_checklist.md items on absorption to reiterate mandatory trace steps.
- reports/2025-10-vectorization/phase_a/absorption_baseline_results.json average timings for CPU and CUDA.
- reports/benchmarks/20250930-165726-compile-cache/analysis.md if you need to justify hotspot prioritisation.
- prompts/callchain.md to align any proposed logging hooks with existing instrumentation practices.
- docs/development/implementation_plan.md Phase 3 notes on detector work to contextualise deliverables.
- docs/development/testing_strategy.md section 4.2 (unit versus integration gradients) for the absorber parameter checks.
- tests/test_tricubic_vectorized.py for structure on how device parametrisation is done today.
- reports/archive/cli-flags-003/watch.md for cadence language when you define future monitoring hooks.
