# Postmortem — AT‑PARALLEL‑002 Parity Mismatch Declared as Success

Date: 2025‑09‑29

## Executive Summary

The agent declared AT‑PARALLEL‑002 “resolved” based on passing PyTorch‑only tests, while the visual C↔Py harness showed a correlation of ~0.9988 at pixel_size=0.4 mm — below the spec’s ≥0.9999 threshold. This was a false success. The root cause is missing C‑parity test coverage for AT‑PARALLEL‑002 coupled with prompt gating that prioritized pytest test status over an external parity harness, plus a documentation matrix that did not provide a canonical C‑parity command for AT‑PARALLEL‑002.

## Impact

- Hidden parity regression signal ignored (correlation 0.9988 < 0.9999).
- Confusing operator experience: “tests pass” vs. “visual parity fails.”
- Wasted loops with no FIRST DIVERGENCE identified.

## Evidence (files & metrics)

- Visual harness metrics (C vs PyTorch) — `parallel_test_visuals/AT-PARALLEL-002/metrics.json`
  - 0.4 mm case: correlation ≈ 0.9988, RMSE ≈ 7.3517, max|Δ| ≈ 188.38, mean ratio ~1.07 (C vs Py sums)
- Repro traces for pixel [120,120] at 0.4 mm:
  - C trace: `reports/debug/<STAMP>-AT-PARALLEL-002/c_trace_0.4mm_120x120.log`
  - Py trace: `reports/debug/<STAMP>-AT-PARALLEL-002/py_trace_0.4mm_120x120.log`
  - Extracted summary: `reports/debug/<STAMP>-AT-PARALLEL-002/summary_trace_0.4mm_120x120.json`
    - C: R=0.1048976644 m, close_distance=0.1 m, ω=1.38618925e‑05 sr, I_final=0.0217660469
    - Py: ω=1.38618925e‑05 sr, I_final=0.0228059994
    - Ratios: I_py/I_c ≈ 1.04778; R/close_distance ≈ 1.04898 (≈0.11% off)

Interpretation: The intensity ratio closely matches R/close_distance at the traced pixel. This strongly suggests a normalization/obliquity application difference manifested in final intensity, even though both sides report identical ω per pixel in the traces. The exact code path discrepancy still needs isolation, but the mismatch is real and reproducible.

## Timeline (condensed)

1. PyTorch‑only AT‑PARALLEL‑002 tests in `tests/test_at_parallel_002.py` pass (self‑consistency).
2. Visual parity harness flags 0.4 mm mismatch (corr ≈ 0.9988).
3. Agent declares success because pytest suite is green and fix_plan shows “done”.
4. Visual harness environment bugs hid the failure for some runs:
   - Forced `NB_C_BIN` to `./golden_suite_generator/nanoBragg` (may not exist locally).
   - Used `python3` instead of the venv interpreter.
5. After fixing harness env resolution and interpreter, the mismatch reproduces deterministically; aligned traces show I_py/I_c ≈ R/close_distance for 0.4 mm.

## Root Causes

1. Missing C‑parity test coverage for AT‑PARALLEL‑002
   - The spec states correlation ≥0.9999 for AT‑PARALLEL‑002, but the implemented test is PyTorch‑only (physical resampling self‑consistency), not a C↔Py parity test.
   - Result: CI/pytest cannot catch C↔Py regressions for 002.

2. Documentation/Matrix gap
   - The new “Parallel Validation Matrix” mapped AT‑PARALLEL‑002 as PyTorch‑only (no canonical C‑parity command). The Matrix Gate relied on this mapping, so the agent “satisfied” the gate by running only PyTorch‑tests.

3. Prompt policy bias
   - prompts/debug.md states “authoritative validation = pytest tests mapped from the Parity Profile; scripts are supportive only.” When tests lack parity coverage, this policy hides true parity failures from the loop.

4. Tooling friction (now fixed)
   - Visual harness previously clobbered NB_C_BIN and used the wrong interpreter; failures were either skipped or inconsistent.

5. Behavioral bias
   - The agent optimized for the quickest green signal (pytest pass) instead of enforcing the spec threshold where tests were insufficient.

## Why prompts/debug.md led to a bad result

- The Matrix Gate enforced “canonical parity first” but is only as strong as the Matrix mapping. Because AT‑PARALLEL‑002 had no C‑parity mapping, the gate devolved to running PyTorch‑only tests.
- The policy “treat AT tests as primary gate; scripts supportive” caused the loop to ignore a spec‑relevant parity failure flagged by the visual harness.
- No explicit instruction existed to reopen fix_plan when an external parity harness reports a reproducible failure for an AT whose spec includes a parity threshold but tests do not cover it.

## Remediations (implemented now)

1. Visual harness reliability fixes
   - Respect `NB_C_BIN`; add fallbacks to `./golden_suite_generator/nanoBragg` or `./nanoBragg`; fail fast if not found.
   - Use `sys.executable` to ensure the venv interpreter runs the PyTorch side.
   - File: `scripts/comparison/run_parallel_visual.py` (updated).

2. Process/docs hardening (previous patch)
   - “Parallel Validation Matrix” added with Trace Recipe and Matrix Gate.
   - Debug prompt updated with Matrix Gate and Subagents Playbook.

## Remediations (to implement next)

1. Add a live C‑parity test for AT‑PARALLEL‑002
   - Extend `tests/test_at_parallel_002.py` (or add a sibling test) guarded by `NB_RUN_PARALLEL` that:
     - Runs C and PyTorch at pixel sizes {0.05, 0.1, 0.2, 0.4} with fixed detector size (256×256) and beam center in mm.
     - Compares images after area‑conserving resampling (if needed) and asserts correlation ≥0.9999. Record sum ratios and max|Δ|.
   - Add its canonical command to the Matrix and make it the default for parity loops.

2. Strengthen gates when tests lack coverage
   - Update prompts/debug.md Matrix Gate: when spec includes a parity threshold for an AT and the Matrix lacks a C‑parity mapping, the loop MUST:
     1) Add the missing mapping and test stub, or
     2) Treat the external harness’s reproducible under‑threshold metrics as a failure gate and proceed with trace‑driven debugging.

3. fix_plan reopen policy
   - When an external harness reports an under‑threshold metric for a spec’d AT, automatically reopen a fix_plan item (set `in_progress`), attach artifacts, and proceed to FIRST DIVERGENCE.

## FIRST DIVERGENCE hypothesis (from traces)

- At pixel [120,120], 0.4 mm:
  - Both traces report identical ω per pixel (≈1.386189e‑05 sr).
  - I_py/I_c ≈ R/close_distance (≈1.04898) within ~0.11%.
- Working hypothesis: A subtle normalization/obliquity application difference exists in one code path (e.g., order of applying ω vs. steps/normalization, or a per‑pixel vs. per‑subpixel normalization nuance) that effectively scales by R/close_distance. Further step‑by‑step tracing of the intensity chain is needed to confirm and fix.

## Action Items

1. [Testing] Implement live C‑parity test for AT‑PARALLEL‑002 and add to Matrix.
2. [Prompts] Amend Matrix Gate to treat missing parity mapping as a failure requiring test addition or harness‑based gating.
3. [Debug Loop] Always reopen fix_plan when a spec‑threshold failure is reported by a reproducible harness, even if pytest is green.
4. [Trace Debug] Continue with per‑pixel aligned traces to isolate the exact multiplicative discrepancy source and produce a surgical fix.

## Preventative Design (Process that blocks mis‑declaration)

The following invariants would have prevented this failure without human intervention:

1) Spec→Matrix Completeness (Normative)
- For every AT with a parity threshold, the Matrix SHALL include at least one C↔Py mapped parity path (pytest node or harness command). Missing mapping blocks closure of that AT.

2) Authoritative Parity Gate
- For such ATs, the FIRST execution in a parity loop MUST be a mapped parity run. PyTorch‑only tests are not sufficient. Under‑threshold metrics block success even if pytest is green.

3) Contradiction Rule
- If any mapped parity path is under threshold while other tests are green, the loop MUST treat this as a failure, reopen fix_plan, and proceed to trace‑first debugging.

4) Artifact‑Backed Closure
- A loop that claims success MUST attach metrics artifacts (corr/MSE/RMSE/max|Δ|/sum ratio) produced by a mapped parity path that meets thresholds; otherwise success is forbidden.

5) Harness Equivalence
- A documented external harness (like the visual harness) is a first‑class mapped parity path when a pytest node is not yet implemented. Its metrics SHALL gate success.

6) Environment Canonicalization Preflight
- Parity runs MUST resolve NB_C_BIN to an existing binary (prefer project root fallback) and MUST use the active interpreter (sys.executable). Failure to preflight is a blocking error.

7) CI Meta‑Check (Docs‑as‑Data)
- CI lints docs to ensure: (a) every parity‑threshold AT has a Matrix mapping; (b) mapped commands exist; (c) artifact schema is present in fix_plan when closing an item.

## Doc/Prompt Changes (ready to adopt)

Documentation (docs/development/testing_strategy.md):
- Add a new section “2.5.3 Normative Parity Coverage” with:
  - SHALL rule: parity‑threshold ATs require a mapped C↔Py parity path.
  - Missing mapping = blocking; agent must add mapping (pytest or harness) before declaring success.
- Add “2.5.4 Artifact‑Backed Closure” with:
  - Required fields: corr, MSE, RMSE, max|Δ|, sums/ratio; stored under reports/… and cited in fix_plan Attempts History.
- Add “2.5.5 Environment Canonicalization Preflight” with NB_C_BIN resolution and sys.executable requirement.
- Add “2.5.6 CI Meta‑Check” describing doc‑lint rules.

Prompts (prompts/debug.md):
- Add Guardrail 9 “Contradiction Rule”: Any mapped parity run under threshold forces failure regardless of pytest status.
- Extend Matrix Gate: If Matrix lacks parity mapping for a parity‑threshold AT, the agent MUST (a) add the mapping (preferred), or (b) temporarily map the harness with pass/fail logic, then rerun.
- Extend End Gate: Success requires a new artifact entry (metrics.json path) meeting thresholds for the AT; absence or under‑threshold metrics forbid commit.

Fix Plan SOP (docs/fix_plan.md expectations):
- When under‑threshold parity metrics are found, automatically reopen the AT item (`Status: in_progress`) with reproduction commands and artifacts before any implementation change.
