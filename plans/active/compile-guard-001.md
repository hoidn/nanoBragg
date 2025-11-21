## Implementation Plan — Dynamo-Safe Simulator Compile Guard

## Initiative
- ID: COMPILE-GUARD-001
- Title: Respect NANOBRAGG_DISABLE_COMPILE and harden HKL debug logging
- Owner: <TBD>
- Spec Owner: docs/development/pytorch_runtime_checklist.md
- Status: pending

## Goals
- Ensure `Simulator` fully respects `NANOBRAGG_DISABLE_COMPILE=1` (DBEX spelling) and never uses `torch.compile` in that mode.
- Make `compute_physics_for_position` Dynamo-safe so HKL debug logging cannot cause `torch._dynamo` failures when compilation is enabled.

## Phases Overview
- Phase A — Analysis & Design: Confirm failure mode and design guardrails.
- Phase B — Implementation: Update compile guards and HKL logging.
- Phase C — Validation & Docs: Reproduce DBEX scenario, validate behavior, and update runtime docs.

## Exit Criteria
1. With `NANOBRAGG_DISABLE_COMPILE=1` set, `Simulator` uses the eager `compute_physics_for_position` path (no `torch.compile` invocation) on both CPU and CUDA.
2. With compilation enabled, HKL stats logging cannot trigger Dynamo errors; either the print is skipped under compile or safely executed outside any compiled region.
3. The DBEX Stage-A mapping debug repro (TOOLING-VIS-001 phases 4–5) runs to completion without Dynamo errors when using the documented environment flags.
4. Runtime docs clearly describe the compile-disable behavior, supported env var names, and the behavior of debug instrumentation in compiled vs eager modes.

## Compliance Matrix (Mandatory)
- [ ] Spec Constraint: `docs/development/pytorch_runtime_checklist.md` — compile/gradcheck guardrails and debug runs.
- [ ] Spec Constraint: `docs/architecture/pytorch_design.md` — `torch.compile` usage and pure-function kernel expectations.
- [ ] Fix-Plan Link: `docs/fix_plan.md` — Row `[COMPILE-GUARD-001]` (this plan).
- [ ] Finding/Policy: PyTorch runtime guardrails (no per-iteration `.to()`, no hidden device transfers, debugger-safe instrumentation).
- [ ] Finding/Policy: TOOLING-VIS-001 expectations for disabling compile in DBEX debug flows.

## Spec Alignment
- Normative Spec: `docs/development/pytorch_runtime_checklist.md`
- Key Clauses:
  - Debugging/gradcheck flows MUST be able to disable `torch.compile` via env guard.
  - `torch.compile` usage MUST be opt-in and robust to instrumentation.
  - Instrumentation must not introduce new nondeterministic or non-vectorized behavior.

## Context Priming (read before edits)
- Primary docs/specs:
  - `docs/development/pytorch_runtime_checklist.md` (compile / debug / gradcheck sections).
  - `docs/architecture/pytorch_design.md` §performance/compile, kernel caching design.
  - `docs/development/testing_strategy.md` §1.4–1.5 (runtime/env knobs, grad tests).
- Required findings/case law:
  - `docs/fix_plan.md` entries that mention `NANOBRAGG_DISABLE_COMPILE=1` usage.
  - Any notes from `[PERF-PYTORCH-004]` and determinism fixes that already touched compile behavior.
- Related telemetry:
  - DBEX `TOOLING-VIS-001` Stage-A mapping debug scripts and their runtime checklist.
  - Any existing Dynamo/compile failures logged in `reports/` or `parallel_test_outputs`.

## Phase A — Analysis & Design

### Checklist
- [ ] A0: Reproduce the Dynamo error locally with a minimal harness:
  - Run `Simulator.run()` with `torch.compile` enabled and HKL stats logging active, confirm `Unknown format code 'f' for object of type 'str'` from the HKL print.
- [ ] A1: Confirm env-var mismatch:
  - Verify that `Simulator` currently checks `NANOBRAGG_DISABLE_COMPILE` (double “G”) while DBEX uses `NANOBRAG_DISABLE_COMPILE` (single “G”).
  - Decide on backward-compatible behavior: accept both spellings, prefer the DBEX spelling in docs.
- [ ] A2: Design compile guard behavior:
  - Define a single helper to compute `disable_compile` that:
    - Accepts both `NANOBRAGG_DISABLE_COMPILE` and `NANOBRAG_DISABLE_COMPILE`,
    - Is evaluated once per `Simulator` instance, and
    - Applies to both CPU and CUDA devices uniformly.
- [ ] A3: Design Dynamo-safe HKL logging:
  - Choose a strategy:
    - Prefer: guard the logging with `if not torch._dynamo.is_compiling(): ...`.
    - Fallback: move HKL logging to the uncompiled `_compute_physics_for_position` wrapper.
  - Ensure logging remains available in eager/debug runs and is bounded (no log storms).

### Dependency Analysis
- Touched Modules:
  - `src/nanobrag_torch/simulator.py` (`compute_physics_for_position`, compile guard in `Simulator.__init__`).
  - Potential runtime docs: `docs/development/pytorch_runtime_checklist.md`.
- Circular Import Risks:
  - Avoid introducing new imports at module top level that depend on `torch._dynamo` in ways that affect import order; if needed, import inside functions.
- State Migration:
  - No user-visible state change; only how `_compiled_compute_physics` is chosen and when logging fires.
  - Ensure existing cached compiled function behavior is preserved when `disable_compile` is false.

### Notes & Risks
- Risk: mis-wiring env guards could inadvertently disable compile in production flows; must keep default behavior unchanged when neither env var is set.
- Risk: using `torch._dynamo.is_compiling()` incorrectly (e.g., at import time) could itself cause issues; keep checks strictly inside the function.

## Phase B — Implementation

### Checklist
- [ ] B1: Implement robust compile-disable guard:
  - Add logic in `Simulator.__init__`:
    ```python
    disable_compile = (
        os.environ.get("NANOBRAGG_DISABLE_COMPILE", "0") == "1"
        or os.environ.get("NANOBRAG_DISABLE_COMPILE", "0") == "1"
    )
    ```
  - Use this flag to decide whether `_compiled_compute_physics` is the raw function or a compiled variant.
- [ ] B2: Harden HKL debug logging:
  - Add a Dynamo guard around the HKL stats print in `compute_physics_for_position`, e.g.:
    ```python
    import torch._dynamo as _dynamo
    if apply_polarization and not _dynamo.is_compiling():
        ...
        print(...)
    ```
  - Ensure use of `.item()` remains restricted to non-grad-bearing quantities (indices, counts) and does not affect differentiability.
- [ ] B3: Fallback behavior:
  - Keep the existing try/except around `torch.compile` so that if compilation fails for any other reason, `_compiled_compute_physics` still falls back to eager.
- [ ] B4: Minimal unit tests:
  - Add or extend tests to:
    - Force `NANOBRAGG_DISABLE_COMPILE=1` and `NANOBRAG_DISABLE_COMPILE=1` and assert that `_compiled_compute_physics` is the plain function (no Dynamo involvement).
    - Optionally (if feasible in CI), run a tiny `torch.compile` path to ensure HKL logging does not throw when compile is enabled.

### Notes & Risks
- Keep any `torch._dynamo` imports local to avoid hard dependency issues in environments without Dynamo; wrap in try/except if necessary.

## Phase C — Validation & Documentation

### Checklist
- [ ] C1: DBEX integration validation:
  - From the DBEX repo, rerun:
    - `python plans/active/TOOLING-VIS-001/bin/stage_a_mapping_adam_debug.py --phases 1,2`
    - `python plans/active/TOOLING-VIS-001/bin/stage_a_mapping_adam_debug.py --phases 4,5`
  - Confirm that:
    - With `NANOBRAG_DISABLE_COMPILE=1`, no Dynamo or `torch.compile` errors occur.
    - Stage-A mapping diagnostics still match prior behavior (no changes to physics).
- [ ] C2: Local nanoBragg validation:
  - Run a small ROI simulation with and without the env flags to ensure:
    - Compile is used when allowed and disabled when requested.
    - HKL stats logs appear only in eager mode and are bounded.
- [ ] C3: Documentation updates:
  - Update `docs/development/pytorch_runtime_checklist.md` to:
    - Document accepted env vars (`NANOBRAG_DISABLE_COMPILE` and `NANOBRAGG_DISABLE_COMPILE`), with a note that DBEX uses the single-G spelling.
    - Clarify expected behavior: debug / gradcheck flows should set this flag to avoid `torch.compile`.
    - Mention that HKL stats logging is eager-only and intentionally skipped in compiled runs.
- [ ] C4: Fix-plan ledger:
  - Add `[COMPILE-GUARD-001]` entry to `docs/fix_plan.md` with:
    - Plan reference path.
    - Reproduction commands (DBEX script + any local nanoBragg commands).
    - Attempts history for implementation and validation.

### Notes & Risks
- Ensure any behavior changes are narrowly scoped to compile behavior and logging; no golden-suite parity changes should be introduced.

## Artifacts Index
- Reports root: `plans/active/COMPILE-GUARD-001/reports/`
- Latest run: `<YYYY-MM-DDTHHMMSSZ>/`

