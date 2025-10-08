Summary: Finish removing φ-carryover from public/doc surfaces and tear out the remaining config/model plumbing so only spec-mode rotation remains.
Mode: none
Focus: CLI-FLAGS-003 / Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Context Recap:
- Phase A inventory and Phase B0 design review are archived (`reports/2025-10-cli-flags/phase_phi_removal/phase_a/`, `.../phase_b/20251008T185921Z/`).
- Commit 340683f removed the CLI flag but left documentation and internal plumbing intact; plan row B1 is [P] until docs sync lands.
- Plans/active/cli-noise-pix0/plan.md now expects B1 doc sync followed immediately by B2/B3 removals before any scaling retries.
- docs/fix_plan.md Next Actions explicitly require the doc refresh plus deletion of config/test shims; we must close those gaps today.
- Protected Assets guardrails still apply—confirm docs/index.md before touching documentation; vectorization/device neutrality remain mandatory.
Mapped tests:
- pytest --collect-only -q tests/test_cli_scaling_phi0.py (pre-edit import sanity and post-edit structural check).
- KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py (CPU regression after plumbing removal; add CUDA_VISIBLE_DEVICES=0 if GPU available without queueing).
- No full-suite run; additional selectors only if debugging a regression.
Artifacts:
- reports/2025-10-cli-flags/phase_phi_removal/phase_b/<ts>/commands.txt — chronological command log (include git status + diff hashes).
- reports/.../<ts>/collect_pre.log and collect_post.log — pytest collect-only outputs before/after edits.
- reports/.../<ts>/pytest_cpu.log — targeted CPU pytest run; add pytest_cuda.log if GPU executed.
- reports/.../<ts>/summary.md — narrative of edits, tests, open questions, follow-up gates.
- reports/.../<ts>/doc_diff.md — concatenated diff snippets for README_PYTORCH.md, prompts/supervisor.md, docs/bugs/verified_c_bugs.md.
- reports/.../<ts>/grep.log — `rg "phi_carryover_mode"` after edits to document residual references.
- reports/.../<ts>/env.json — Python/PyTorch/git/device metadata (reuse Phase B bundle schema).
- reports/.../<ts>/sha256.txt — checksums for every artifact in the directory.
Do Now: [CLI-FLAGS-003] Phase B2 (plans/active/phi-carryover-removal/plan.md) — run `pytest --collect-only -q tests/test_cli_scaling_phi0.py` before edits, then `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py` after removing config/model/test shims and finishing the documentation sync.
If Blocked:
- Document the blocker in summary.md (include owner, why, external dependencies).
- Log an Attempt in docs/fix_plan.md referencing the timestamped artifact folder.
- Capture the completed portion (e.g., doc sync) and stop code edits until supervisor guidance arrives; note open questions in the artifact bundle.
Priorities & Rationale:
- plans/active/phi-carryover-removal/plan.md:34-38 — Phase B1 remains [P] pending doc updates; B2 instructions enumerate the exact files to excise.
- docs/fix_plan.md:461-465 — Next Actions demand B1 doc sync followed by B2/B3 removal before regression sweeps.
- plans/active/cli-noise-pix0/plan.md:26-35 — Snapshot states that documentation must be refreshed and plumbing removed before parity/scaling work continues.
- docs/bugs/verified_c_bugs.md:166-186 — Current phrasing still advertises the PyTorch shim; must be updated as part of B1 completion.
- specs/spec-a-core.md:204-233 — Normative φ rotation pipeline; all code changes must preserve vectorized fresh-rotation semantics.
- docs/development/testing_strategy.md:118-155 — Codifies the collect-only + targeted pytest cadence we must follow.
- reports/2025-10-cli-flags/phase_phi_removal/phase_b/20251008T191302Z/summary.md — Record of what B1 already did; cite it when describing the follow-up bundle.
How-To Map:
1. `ts=$(date -u +%Y%m%dT%H%M%SZ)`; `base=reports/2025-10-cli-flags/phase_phi_removal/phase_b/$ts`; `mkdir -p "$base"`.
2. Start `$base/commands.txt`; log every command with timestamp (shell `printf` or add via `script -q`).
3. Baseline import check: `pytest --collect-only -q tests/test_cli_scaling_phi0.py | tee "$base/collect_pre.log"` (record exit code in commands.txt).
4. Finish B1 doc sync before touching code:
   - Update README_PYTORCH.md to remove `--phi-carryover-mode` mentions and clarify PyTorch is spec-only.
   - Update prompts/supervisor.md to drop all references to the shim and adjust guidance accordingly.
   - Update docs/bugs/verified_c_bugs.md:166-186 so the C-PARITY-001 entry states the shim existed historically but PyTorch no longer exposes it.
   - Capture doc diffs via `git diff` snippets into `$base/doc_diff.md` (group by file for clarity).
5. Execute B2 plumbing removal:
   - `src/nanobrag_torch/config.py`: delete `phi_carryover_mode` fields (dataclass attributes, __post_init__, CLI mapping) while keeping tensor defaults intact.
   - `src/nanobrag_torch/models/crystal.py`: remove `_apply_phi_carryover` branches and associated cache usage; ensure docstring retains nanoBragg.c citation.
   - `src/nanobrag_torch/simulator.py`: eliminate carryover-mode conditionals so run() always follows spec rotation.
6. Begin B3 cleanup where needed:
   - Delete `tests/test_phi_carryover_mode.py` (or refactor residual spec assertions into `tests/test_cli_scaling_phi0.py`).
   - Remove shim-only switches from debug/tooling scripts if they live under scripts/ (note findings in summary even if left for next loop).
7. Run post-edit checks:
   - `pytest --collect-only -q tests/test_cli_scaling_phi0.py | tee "$base/collect_post.log"`.
   - `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py | tee "$base/pytest_cpu.log"` (add CUDA variant if executed).
8. Capture environment metadata: `python - <<'PY' > "$base/env.json"` to dump Python/PyTorch version, CUDA availability, git SHA, platform, env flags.
9. `rg "phi_carryover_mode" -n > "$base/grep.log"` after edits; annotate residual references (reports, archives) in summary.
10. `(cd "$base" && sha256sum * > sha256.txt)` to finalise artifact integrity.
11. Draft `$base/summary.md` — cover doc sync, code deletions, tests, residual items (e.g., tooling or plan updates), and cite relevant plan lines.
12. Update docs/fix_plan.md Attempts (include `$base` path, test results, follow-ups) and adjust plan row statuses (B1→[D] once docs synced, B2 maybe [P]/[D] depending on completion).
13. Stage changes with clear message once verified; if anything remains undone, leave notes in summary + fix_plan and stop.
Pitfalls To Avoid:
- Do not reintroduce scalar φ loops; preserve vectorized tensor math and gradient flow.
- Avoid `.cpu()`/`.cuda()` shims; keep tensors on caller device/dtype per PyTorch guardrails.
- No `.item()` on tensors that require gradients; maintain differentiability across rotations.
- Keep doc updates ASCII; touch only the files identified in plan B1 to respect Protected Assets.
- Don’t delete archival reports referencing the shim; only update active docs.
- Avoid broad search-and-replace that might clobber archival context—document residual references instead.
- Stick to mapped pytest selectors; no full-suite run unless instructed later.
- Ensure docstrings retain the C-code reference block (Rule #11) until Phase D closure.
- Record all commands in commands.txt; missing provenance will block acceptance of the bundle.
- If CUDA not available, state it explicitly in summary instead of leaving a gap.
Pointers:
- plans/active/phi-carryover-removal/plan.md:34-38 — Phase B status and tasks.
- docs/fix_plan.md:461-465 — Next Actions for CLI-FLAGS-003.
- plans/active/cli-noise-pix0/plan.md:26-35 — How CLI plan depends on B1/B2 progress.
- docs/bugs/verified_c_bugs.md:166-186 — Text to update during doc sync.
- docs/development/testing_strategy.md:118-155 — Test cadence requirements.
- specs/spec-a-core.md:204-233 — Normative φ rotation contract to honour.
Next Up: If the bundle lands early, catalog remaining shim references for Phase B3 (tests/tooling) in summary.md without modifying additional code yet.
