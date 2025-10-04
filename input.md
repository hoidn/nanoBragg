# Supervisor Steering Memo (input.md)

Author: galph (supervisor)
Ownership: single-writer (galph only). Ralph MUST NOT edit this file.
Lifecycle: rewritten every supervisor invocation and committed when content changes.
Purpose: steer Ralph’s single-loop focus, provide precise commands, and list pitfalls to avoid.

---

Header
- Timestamp: <set by supervisor>
- Commit: <short SHA set by supervisor>
- Active Focus (from docs/fix_plan.md): <concise summary by supervisor>

Do Now
- delegate
  Guidance: Choose the highest-value `pending` item in `docs/fix_plan.md` OR continue the most consequential `in_progress` track. Favor items that unblock the PyTorch runtime guardrails (vectorization, device/dtype neutrality) and Tier-1 acceptance tests. Record your choice in the item’s Attempts History with reproduction commands.

If Blocked
- If mapped tests are unavailable or flaky, run `pytest --collect-only -q` to verify collection and capture logs under `reports/<date>/collect/`.
- If a C parity binary is missing, skip live parity and run golden-data ATs; record the limitation explicitly in Attempts History.

Priorities & Rationale
- Prefer work that closes open acceptance tests or removes critical runtime violations (vectorization, device/dtype).
- Confirm configuration parity via `docs/development/c_to_pytorch_config_map.md` before any C↔Py comparisons.
- For detector geometry tasks, follow `docs/debugging/detector_geometry_checklist.md` to avoid unit/convention pitfalls (meters vs mm, MOSFLM +0.5, pivot modes).
- For differentiability, avoid `.item()`, `.detach()`, `.numpy()` on gradients; use explicit dtype overrides only where precision-critical.
- Keep the loop scope to one item; defer adjacent refactors as TODOs in `docs/fix_plan.md`.

How-To Map
- Test mapping: read `docs/development/testing_strategy.md` for authoritative AT→pytest mapping and required env.
- Environment:
  - `KMP_DUPLICATE_LIB_OK=TRUE` for all PyTorch runs
  - `NB_C_BIN` resolution order: `--c-bin` arg > env > `./golden_suite_generator/nanoBragg` > `./nanoBragg`
- Commands (examples):
  - Collect-only: `env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q`
  - Tier-1 AT: `env KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_*.py`
  - Parallel validation: `env KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_*.py`
- Artifacts: save logs/metrics under `reports/<date>/<task-id>/`; do NOT commit binaries or images.

Pitfalls To Avoid
- Do not validate against ad‑hoc scripts; only use `pytest` under `./tests`.
- Do not break vectorization with Python loops when batched helpers exist.
- Do not insert `.cpu()`/`.cuda()` or per-call `.to()` shims in compiled paths; ensure tensors are on the correct device up front.
- Do not modify or remove files listed in `docs/index.md` (Protected Assets).
- Do not exceed two messages per loop: brief preamble + final checklist.
- Do not change tests or thresholds for equivalence work; fix the implementation or document the gap.
- Do not commit runtime artifacts; commit code/docs/prompt/plan changes only.

Pointers
- Plan ledger: `docs/fix_plan.md`
- Spec: `specs/spec-a.md`
- Architecture hub: `docs/architecture/README.md`
- Testing strategy: `docs/development/testing_strategy.md`
- C↔Py config map: `docs/development/c_to_pytorch_config_map.md`
- Detector geometry checklist: `docs/debugging/detector_geometry_checklist.md`
- CLAUDE agent rules: `CLAUDE.md`
- Loop prompt (Ralph): `prompts/main.md`
- Supervisor prompt (Galph): `prompts/supervisor.md`

Exit Gates (for this loop)
- Re-run mapped authoritative tests; pass thresholds with zero collection errors.
- Append Attempts History entry in `docs/fix_plan.md` with: Metrics, Artifacts (real paths), and First Divergence when traces are used.
- If work is doc/prompt-only, ensure `pytest --collect-only -q` passes.

Next Up (for next loop)
- If you finish early, pick exactly one candidate from the highest-priority `pending` items and declare it at loop start. Do not split focus across items.

Notes
- This file is a steering memo, not a status ledger. Status, history, and decisions live in `docs/fix_plan.md` and plan files under `plans/`.

