Summary: Capture tricubic and detector absorption baselines so Phase A clears the runway for vectorization.
Mode: Perf
Focus: VECTOR-TRICUBIC-001 – Vectorize tricubic interpolation and detector absorption
Branch: feature/spec-based-2
Runtime Budget: Expect ~30 minutes including GPU runs; keep stopwatch notes for docs/fix_plan.md.
Context Notes: Phase A1 evidence landed (logs + env.json); Phase A2/A3 remain open with no reusable harnesses; fix_plan status now in_progress after latest supervisor audit.
Context Notes: Long-term Goal #2 demands this baseline before any tricubic refactor; no production code changes should occur until these metrics exist.
Context Notes: Repository currently clean aside from supervisor edits; ensure new artifacts stay under `reports/2025-10-vectorization/phase_a/` as per plan.
Context Notes: CUDA is available per env.json; baseline scripts must branch gracefully when GPU absent on other machines.
Context Notes: Protected Assets policy still in effect; do not touch docs/index.md listings.
Context Notes: Ralph’s last loop already ran AT-STR-002/ABS-001; reuse that pattern when validating new scripts.
Mapped tests: pytest --collect-only -q tests/test_at_str_002.py tests/test_at_abs_001.py
Metrics Expectation: Record per-size mean/median/stddev plus cold vs warm timings in JSON + Markdown.
Artifacts: reports/2025-10-vectorization/phase_a/tricubic_baseline.md, reports/2025-10-vectorization/phase_a/tricubic_baseline_results.json, reports/2025-10-vectorization/phase_a/absorption_baseline.md, reports/2025-10-vectorization/phase_a/absorption_baseline_results.json, reports/2025-10-vectorization/phase_a/env.json, reports/2025-10-vectorization/phase_a/run_log.txt, reports/2025-10-vectorization/phase_a/collection_blocker.log (only if needed)
Baseline Evidence Summary: Existing tricubic/absorption pytest logs confirmed green (Phase A1); new harnesses must extend that evidence with timing/perf data rather than duplicate tests.
Baseline Evidence Summary: Reports folder currently contains only test logs + env snapshot; keep naming consistent (`phase_a/<artifact>`).
Do Now: VECTOR-TRICUBIC-001 Phase A2/A3 — author `scripts/benchmarks/tricubic_baseline.py` and `scripts/benchmarks/absorption_baseline.py`, then run `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/tricubic_baseline.py --sizes 256 512 --repeats 5` and `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/absorption_baseline.py --sizes 256 512 --repeats 5`
If Blocked: Capture `pytest --collect-only -q tests/test_at_str_002.py tests/test_at_abs_001.py` output to `reports/2025-10-vectorization/phase_a/collection_blocker.log`, log the blocker in docs/fix_plan.md Attempt history, and stop before editing production code.
Priorities & Rationale:
- docs/fix_plan.md:1643 ties VECTOR-TRICUBIC-001 status to finishing Phase A2/A3 before design work resumes.
- plans/active/vectorization.md:1 spells out the Phase A deliverables and the expectation of reusable scripts under `scripts/benchmarks/`.
- specs/spec-a-core.md:200 anchors interpolation physics so benchmarks honour the 4×4×4 neighborhood semantics.
- specs/spec-a-core.md:247 mandates normalization rules that the timing harness must respect when comparing outputs.
- specs/spec-a-parallel.md:241 keeps parity tolerances visible, ensuring timing work never compromises acceptance criteria.
- specs/spec-a-parallel.md:282 reiterates auto-enable rules for tricubic interpolation; note if tests auto-enable during timings.
- docs/development/pytorch_runtime_checklist.md:1 enforces vectorization/device guardrails the new harnesses must obey.
- docs/development/testing_strategy.md:1 emphasises targeted tests before full suites; align harness validation with Tier 1 priorities.
- reports/2025-10-vectorization/phase_a/test_at_str_002.log captures the current acceptance baseline and sets the tone for follow-on artifacts.
- reports/2025-10-vectorization/phase_a/test_at_abs_001.log demonstrates detector absorption stability we must preserve.
- galph_memory.md: latest entries document supervisor expectation to close Phase A evidence immediately.
- CLAUDE.md: Protected Assets rule (lines 24-60) constrains where benchmark scripts live and forbids moving indexed files.
- prompts/supervisor.md: long-term goals section confirms vectorization remains the second highest priority after CLI parity.
How-To Map:
- Activate editable install if needed via `pip install -e .`; confirm `nanoBragg --help` succeeds so CLI entry remains valid.
- Export `KMP_DUPLICATE_LIB_OK=TRUE` in the shell (append to commands or set globally) to prevent MKL duplicate symbol crashes.
- Create `scripts/benchmarks/tricubic_baseline.py` with argparse hooks (`--sizes`, `--repeats`, `--device`, `--dtype`) and default to float32 with option for float64 if needed.
- Inside the tricubic script, construct a minimal simulator via existing config builders (avoid copy/paste from tests) to exercise tricubic interpolation for each requested detector size.
- Ensure the script supports CPU-only machines by catching `torch.cuda.is_available()` and skipping GPU timings with a logged note instead of crashing.
- For each device/size combo, capture cold-start timing (first invocation) and warm-start timing (subsequent invocation) separately; store raw samples in lists before aggregating.
- Emit structured data to JSON using keys like `{"device": "cpu", "size": 256, "samples": [...]}` along with summary statistics.
- Write human-readable commentary to `reports/2025-10-vectorization/phase_a/tricubic_baseline.md` describing command lines, device info, compile state, warnings, and interpretations.
- Repeat the pattern for `scripts/benchmarks/absorption_baseline.py`, tailoring the harness to iterate over detector thickness layers and record any broadcast inefficiencies observed.
- Capture stdout/stderr from each script invocation into `reports/2025-10-vectorization/phase_a/run_log.txt` (append mode) so cold and warm runs appear sequentially.
- After both scripts run, append or regenerate `reports/2025-10-vectorization/phase_a/env.json` to document git SHA, Python/PyTorch versions, CUDA availability, GPU name, and whether `torch.compile` was active.
- Re-run `pytest --collect-only -q tests/test_at_str_002.py tests/test_at_abs_001.py` once scripts are staged to confirm selectors still import successfully after adding new modules.
- If the scripts import helper modules, add lightweight unit tests or assertions within the script to fail fast when assumptions break.
- Consider adding a `--json` flag for explicit output path control; default should remain under `reports/2025-10-vectorization/phase_a/` to satisfy plan guidance.
- Re-execute `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_str_002.py tests/test_at_abs_001.py -v` if new imports risk impacting the tests; record outcomes in Markdown summaries.
- Update docs/fix_plan.md Attempt history (VECTOR-TRICUBIC-001) with metrics, command strings, device coverage, and links to the new artifacts.
- Update plans/active/vectorization.md Phase A checklist by flipping the `[ ]` markers for A2/A3 to `[D]` once artifacts and fix-plan updates land.
- Stage the new scripts and reports; leave commits for the next supervisor review unless this loop explicitly includes a commit step.
- Prepare brief notes summarising any surprises (e.g., unexpected warning, GPU unavailability) for the supervisor follow-up.
Verification Checklist:
- Cold timing recorded for each size/device.
- Warm timing recorded for each size/device.
- JSON + Markdown artifacts present and referenced in docs/fix_plan.md.
- env.json updated or annotated to indicate reuse.
- pytest collect-only command output archived.
- No unexpected diffs outside new scripts/reports and plan/fix_plan updates.
Pitfalls To Avoid:
- Do not skip CUDA runs if `torch.cuda.is_available()`; note explicitly when GPU timings are absent and why.
- Avoid hard-coded `.cuda()` or `.cpu()` calls inside benchmark helpers—pass the device through tensors and configs using `.to(device)` once per setup.
- Keep the new scripts aligned with repository CLI norms: include `if __name__ == "__main__":` entrypoints, argparse help strings, and docstring references to spec sections.
- Preserve Phase A1 logs; add new files or new sections rather than overwriting the original evidence bundle.
- Guard against warm-cache bias by flagging whether timings include compile overhead; consider toggling `torch._dynamo.reset()` between runs if you need clean cold data.
- Capture any warnings from the simulator (e.g., interpolation fallback, absorption disabling) and highlight them in the Markdown summary so Phase B design can address them.
- Respect Protected Assets: confirm no file referenced in docs/index.md is moved or deleted while organizing scripts or reports.
- Run only the mapped collect-only tests during this loop; full test sweeps can wait until code modifications land.
- Document any fixed RNG seeds, tolerance tweaks, or environment variables in the Markdown so reruns match today’s setup.
- Keep tensor allocations and script-level imports outside tight timing loops to ensure you profile the kernels, not Python overhead.
- Avoid writing large binary data to stdout; direct outputs into report files to prevent cluttering the loop log.
- Double-check that the scripts exit with non-zero status on failure so future automation can catch regressions.
- Ensure the scripts respect device/dtype neutrality by parameterising dtype and avoiding implicit float64 tensors.
- Avoid adding heavy dependencies; rely on stdlib + torch/numpy already present in environment.
- Watch for path issues when writing reports; use `Path` from pathlib to handle directories safely.
Pointers:
- docs/fix_plan.md:1643
- plans/active/vectorization.md:1
- specs/spec-a-core.md:200
- specs/spec-a-core.md:247
- specs/spec-a-parallel.md:241
- specs/spec-a-parallel.md:282
- docs/development/pytorch_runtime_checklist.md:1
- docs/development/testing_strategy.md:1
- reports/2025-10-vectorization/phase_a/test_at_str_002.log
- reports/2025-10-vectorization/phase_a/test_at_abs_001.log
- galph_memory.md: latest vectorization directive
- CLAUDE.md: Protected Assets rule (lines 24-60)
- prompts/supervisor.md: long-term goals section referencing vectorization work
- scripts/benchmarks/README.md (create/update if you add harness documentation)
Next Up: Draft Phase B design memo (`reports/2025-10-vectorization/phase_b/design_notes.md`) capturing tensor-shape strategy and gradient coverage once both baselines are logged.
Risk Log:
- GPU driver mismatch could invalidate timings; if detected, document driver/runtime versions and fall back to CPU-only measurements with justification.
- If tricubic warnings appear (out-of-range neighbourhood), note them verbatim and include counts so Phase B design knows the trigger frequency.
- Should the scripts expose torch.compile graph breaks, capture the warning text and include a TODO in docs/fix_plan.md for follow-up.
- Power-management throttling may skew timings on laptops; mention whether `nvidia-smi` shows P-state changes during runs.
- Large reports may bloat repo; gzip raw timing dumps if they exceed a few MB before committing or store aggregated values only.
- If `scaled.hkl` access is needed for the harness, ensure read-only usage to avoid overwriting golden data.
- Keep eyes on `NB_DISABLE_COMPILE` vs `NANOBRAGG_DISABLE_COMPILE`; benchmark scripts should not mutate global env vars inadvertently.
- Ensure repeated simulator construction does not leak GPU memory; monitor torch.cuda.memory_allocated() between runs if spikes occur and mention results.
- Record ambient hardware (CPU model, RAM, GPU type) in Markdown so future reruns can compare apples-to-apples.
- If new scripts suggest API seams that belong in reusable helpers, jot that insight in the Markdown for future refactor discussion (no refactor this loop).
