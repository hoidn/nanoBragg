Summary: Categorize the recorded loop inventory so we know which simulator surfaces still require vectorization follow-up.
Mode: Docs
Focus: [VECTOR-GAPS-002] Vectorization gap audit
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q (collect-only proof)
Artifacts: reports/2026-01-vectorization-gap/phase_a/<STAMP>/summary.md
Artifacts: reports/2026-01-vectorization-gap/phase_a/<STAMP>/analysis.md
Artifacts: reports/2026-01-vectorization-gap/phase_a/<STAMP>/commands.txt
Artifacts: reports/2026-01-vectorization-gap/phase_a/<STAMP>/pytest_collect.log

Do Now: [VECTOR-GAPS-002] Vectorization gap audit — Phase A3. Reuse the 20251009 loop inventory JSON to label each loop as vectorized, safe, or todo; capture the classification in `analysis.md`, update `summary.md` with an annotated appendix, and run `pytest --collect-only -q` (log output alongside `commands.txt`).
If Blocked: If classification is ambiguous for a loop, note the reasoning in analysis.md, tag it “needs follow-up (uncertain)”, and pause before altering production code.

Priorities & Rationale:
plans/active/vectorization-gap-audit.md:20 — Phase A3 is the final gate before profiling work in Phase B can proceed.
docs/fix_plan.md:3738 — Updated Next Actions demand annotated inventory evidence before any profiler runs.
reports/2026-01-vectorization-gap/phase_a/20251009T064345Z/summary.md — Baseline loop list that now requires status labels.
docs/architecture/pytorch_design.md:1 — Vectorization guardrails to cite when marking loops safe or todo.
docs/development/testing_strategy.md:33 — Collect-only proof is required even for documentation-focused loops.
reports/2025-10-vectorization/gaps/20251009T061928Z/analysis.md — Example reporting style for actionable vectorization investigations.

How-To Map:
Step 1: Export `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and create `reports/2026-01-vectorization-gap/phase_a/$STAMP` for the documentation drop.
Step 1 detail: `mkdir -p reports/2026-01-vectorization-gap/phase_a/$STAMP` keeps historical artifacts separated.
Step 2: Copy `loop_inventory.json` from `20251009T064345Z` into the new stamp or read it in-place for the annotation work.
Step 2 detail: `cp reports/2026-01-vectorization-gap/phase_a/20251009T064345Z/loop_inventory.json reports/2026-01-vectorization-gap/phase_a/$STAMP/` if you want the JSON co-located.
Step 3: Draft `analysis.md` with an ASCII table using columns `Module`, `Line`, `Status`, and `Notes` so future design packets know where to focus.
Step 3 detail: Include counts at the top (e.g., “Vectorized: X, Safe: Y, Todo: Z, Uncertain: W”) for quick scanning.
Step 4: Update `summary.md` overview to cite the previous scan and append a “Classification Appendix” enumerating each loop with status plus rationale.
Step 4 detail: Reference spec or arch citations whenever you justify leaving a loop scalar (e.g., cite `arch.md §8` about broadcast responsibilities).
Step 5: Mention any dependency on device/dtype nuances; note GPU-specific considerations for loops that remain todo.
Step 5 detail: If a loop is currently CPU-only but may hurt CUDA, call that out explicitly in notes.
Step 6: Capture every command in `commands.txt`, including copy operations, editors used, `pytest --collect-only -q`, and checksum commands if helpful.
Step 6 detail: Use ISO timestamps (`date -u`) before each command entry for traceability.
Step 7: Run `pytest --collect-only -q` once documentation edits stage; redirect stdout/stderr to `pytest_collect.log` inside the same folder.
Step 7 detail: e.g., `pytest --collect-only -q | tee reports/.../pytest_collect.log` ensures command output is archived.
Step 8: Record the pytest command, exit code, and environment summary in `commands.txt`; note Python and torch versions if they differ from previous runs.
Step 8 detail: Use `python -c "import torch, sys; print(sys.version); print(torch.__version__)"` and capture output if versions changed.
Step 9: Update docs/fix_plan.md Attempt for [VECTOR-GAPS-002] with the new classification counts and artifact paths.
Step 9 detail: Under the attempt, add bullet points listing `Vectorized`, `Safe (documentation)`, `Todo (requires vectorization)`, and `Uncertain`, then cite analysis.md.
Step 10: Flag loops needing design packets (future Phase C) inside docs/fix_plan.md Next Actions so the backlog is ready for delegation.
Step 10 detail: Reference the specific module + line numbers when you queue those follow-ups.

Pitfalls To Avoid:
Do not overwrite the original 20251009 summary; keep the annotation in a fresh stamp so raw inventory data remains intact.
Maintain ASCII-only output; avoid smart quotes, emojis, or Unicode box drawings in tables.
Avoid making production code edits during this loop; Phase A3 is documentation only.
Respect Protected Assets such as `docs/index.md`, `loop.sh`, and `supervisor.sh`.
Skip re-running the AST scanner unless you document the delta; Phase A3 should reference the existing inventory output.
Provide a rationale for every “safe” or “todo” tag; blank notes will be rejected during review.
Highlight device/dtype expectations for todo loops so later implementations know the constraints.
Ensure the new folder contains `commands.txt`; missing command logs will block sign-off.
Keep `summary.md` concise yet explicit—link back to source artifacts when referencing evidence.
Stage new files and review diff outputs before committing; avoid leaving stray files.
Capture environment differences (Python, torch, CUDA availability) if they differ from Attempt #1; note them in analysis.md footnotes.
If you discover a loop already vectorized in HEAD, document the commit or module that now handles it vectorially.
When classifying I/O loops as safe, note that they operate on finite file lines and sit outside the simulator hot path.

Pointers:
plans/active/vectorization-gap-audit.md:29 — Detailed guidance for A3 artifact expectations.
docs/fix_plan.md:3744 — Attempt #1 notes on suspected hotspots to classify carefully.
docs/development/pytorch_runtime_checklist.md:1 — Cite when marking loops that must remain vectorized.
docs/index.md — Quick path map if additional documentation references become necessary.
docs/development/testing_strategy.md:15 — Device/dtype discipline paragraph to quote where relevant.
reports/2025-10-vectorization/gaps/20251009T061928Z/analysis.md — Example narrative for summarising hot loops.
scripts/benchmarks/benchmark_detailed.py — Mentioned for future profiling; no changes this loop.
src/nanobrag_torch/simulator.py:1469 — Examine loops flagged “likely hot” for classification notes.
src/nanobrag_torch/utils/c_random.py:100 — RNG loop likely todo; cite spec if deferring.
src/nanobrag_torch/utils/auto_selection.py — Already vectorized; mark accordingly.

Next Up Option 1: Phase B1 profiler capture once classifications land so hot loops gain runtime context.
Next Up Option 2: Draft backlog.md for Phase B3 after profiling results exist and priorities are clear.

Classification Notes:
Vectorized status: Use when code path already operates purely in batched tensor form; cite commit or module implementing the vectorized flow.
Vectorized note: Mention tests that cover this vectorization (e.g., `tests/test_tricubic_vectorized.py`).
Safe status: Use for scalar loops outside hot paths (I/O parsing, configuration lists); explain why vectorization offers no practical gain.
Safe note: Reference spec clauses that limit scope (e.g., spec-a-cli parsing requirements).
Todo status: Reserve for loops still impacting runtime; provide hypotheses about expected speedup and affected modules.
Todo note: Identify acceptance tests or profilers that should be rerun after the fix.
Uncertain status: Use when additional evidence is required; define what proof would resolve the uncertainty (trace, profiler, parity check).
Uncertain note: Flag these for supervisor review before implementation is queued.

Reporting Expectations:
Include a short executive summary in analysis.md highlighting the most urgent todo loops.
List any prerequisites for profiling (e.g., device-placement fixes) so future loops reference blockers.
Document whether each todo loop is CPU-only, GPU-only, or both; state how that affects benchmark planning.
Record any open questions that should be answered before Phase C design packets are drafted.
If additional tooling is needed (e.g., callchain traces), note it explicitly with owner suggestions.
Ensure commands.txt references the timestamped directory names exactly as created to avoid ambiguity.
Capture git commit hash (`git rev-parse HEAD`) in commands.txt for reproducibility.
If you review code without changes, still note the files inspected to aid future auditors.
Attach checksum outputs (`shasum -a 256` or `sha256sum`) for the key artifacts if feasible.
Call out any loops that already have partial design notes elsewhere to avoid duplicate work.

Archive Guidance:
Once annotations are complete and accepted, plan to move the entire stamp under `reports/archive/vectorization-gap/` when the plan closes; note this future action in analysis.md so we remember.
Mention in analysis.md whether the original 20251009 stamp should remain untouched as baseline evidence.
Remind yourself to compare future inventories against the 20251009 JSON to catch newly introduced loops.
Archive note: log any future comparisons against this stamp in docs/fix_plan.md to keep provenance clear.
