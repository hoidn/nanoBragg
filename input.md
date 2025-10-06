Timestamp: 2025-10-06 04:39:01Z
Commit: 58b1412
Author: galph
Active Focus: [CLI-FLAGS-003] Phase G2 orientation ingestion before parity rerun
Summary: Preserve MOSFLM A* orientation through Crystal so the supervisor parity command can run end-to-end.
Phase: Implementation
Focus: [CLI-FLAGS-003] Phase G2 — Teach Crystal to ingest MOSFLM orientation
Branch: feature/spec-based-2
Mapped tests: env AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py tests/test_at_geo_003.py -v
Artifacts: reports/2025-10-cli-flags/phase_g/

Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm (Phase G2) — env AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py tests/test_at_geo_003.py -v

If Blocked: Capture C vs PyTorch lattice-vector traces for the supervisor command (pixel 1039,685) and write summary to reports/2025-10-cli-flags/phase_g/orientation_blocked.md; log the divergence in docs/fix_plan.md Attempts before exiting.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:84 — Phase G2 is the next blocker; without Crystal ingesting MOSFLM A* the parity command cannot succeed.
- docs/fix_plan.md:448 — Fix-plan attempts flag A* loss as the “PRIMARY BUG”; clearing Phase G2 is required before Phase F3 parity rerun.
- docs/architecture/pytorch_design.md:182 — Reciprocal vectors must be tensorized and reusable; orientation path must comply with vectorization rules.
- docs/development/c_to_pytorch_config_map.md:40 — Config map confirms MOSFLM matrices are authoritative for CUSTOM pivot; we must honor them verbatim.
- docs/debugging/debugging.md:32 — Trace-first debugging remains mandatory; Phase G3 validation will rely on these traces.
- reports/2025-10-cli-flags/phase_e/trace_summary.md — Existing evidence lists the wrong rot_a/rot_b/rot_c; Phase G2 must eliminate this delta.
- src/nanobrag_torch/config.py:128 — CrystalConfig already stores mosflm_*_star; Crystal must consume them without `.item()` detaches.

How-To Map:
- Export env vars before any commands:
- `export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md`
- `export KMP_DUPLICATE_LIB_OK=TRUE`
- `export NB_C_BIN=./golden_suite_generator/nanoBragg`
- Create Phase G artefact directory: `mkdir -p reports/2025-10-cli-flags/phase_g/{design,pytest,traces,parity}`
- Design prep:
- Summarize intended orientation flow in `reports/2025-10-cli-flags/phase_g/design/mosflm_orientation.md` (include Core Rules 12–13 checklist).
- Implementation steps:
- In `src/nanobrag_torch/models/crystal.py`, detect `config.mosflm_a_star`/`b_star`/`c_star` and convert to tensors on the active device/dtype (`torch.as_tensor(..., device=self.device, dtype=self.dtype)`); keep gradient expectations documented even if arrays start as numpy.
- Replace canonical reciprocal-vector bootstrap when MOSFLM data is present: use vectors as the starting point for Core Rule 12 misset pipeline, then recompute real vectors and re-derived reciprocal vectors per Core Rule 13 (metric duality with `V_actual`).
- Ensure caches (`_geometry_cache`) invalidate when orientation tensors injected; avoid mixing numpy arrays inside cache keys.
- Add lightweight helper (if needed) under `Crystal` to rebuild volume using `torch.dot(rot_a, torch.cross(rot_b, rot_c))` and assert `a·a* ≈ 1` etc.
- Maintain differentiability: no `.item()`, `.detach()`, `.numpy()` or device hard-coding; rely on `.to()` and dtype inherited from config.
- Validation sequence (record logs under `reports/2025-10-cli-flags/phase_g/pytest/`):
- `env AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py -v | tee reports/2025-10-cli-flags/phase_g/pytest/test_cli_flags.log`
- `env AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_geo_003.py -v | tee reports/2025-10-cli-flags/phase_g/pytest/test_at_geo_003.log`
- If CUDA is available, rerun the CLI suite with `--maxfail=1 -k pix0` under `device=cuda` and note availability in design log.
- Evidence capture:
- Generate PyTorch lattice vector dump via `python scripts/debug_pixel_trace.py --config configs/supervisor_phase_g.yaml > reports/2025-10-cli-flags/phase_g/traces/trace_py.log` (create temp config mirroring the parity command).
- Run equivalent C trace using instrumented binary, store as `trace_c.log`, and diff with `diff -u trace_c.log trace_py.log > trace_diff.log`.
- Once vectors align, queue Phase G3 parity (next loop) with `nb-compare --outdir reports/2025-10-cli-flags/phase_g/parity -- -mat A.mat ...` (full args in prompts/supervisor.md).
- Documentation tasks:
- Update `docs/fix_plan.md` Attempt history with Phase G2 summary (include metrics, artifact paths) once implementation validated.
- Mark plan task G2 as `[D]` with artifact references after commit.
- Note any remaining gaps (e.g., polarization) under “Next Actions” in fix_plan entry.

Pitfalls To Avoid:
- Recomputing canonical reciprocal axes when MOSFLM data exists; this erases orientation and reintroduces the regression.
- Leaving MOSFLM vectors as numpy arrays; convert once and keep tensors device/dtype aware.
- Forgetting to recalc real vectors after misset rotation — violates Core Rule 12 and breaks metric duality.
- Skipping reciprocal re-derivation (Core Rule 13); failing to recompute a*/b*/c* from real vectors will drift dot products.
- Introducing `.item()` on tensors like `close_distance` or volumes; this severs gradients and breaks long-term goal #1 guardrails.
- Allocating new CPU tensors inside CUDA runs; always use `.to(self.device)`.
- Neglecting to invalidate geometry caches after injecting orientation; stale cache entries will mask fixes.
- Ignoring trace comparison; without TRACE logs we cannot prove parity gains.
- Overwriting or deleting Protected Assets listed in docs/index.md (input.md, loop.sh, supervisor.sh, etc.).
- Leaving artefacts unstaged/unreferenced; Protected Assets policy requires clean documentation.

Pointers:
- plans/active/cli-noise-pix0/plan.md:80 — Phase G task table with exit criteria.
- docs/fix_plan.md:448 — Current attempts and next actions for `[CLI-FLAGS-003]`.
- docs/architecture/pytorch_design.md:186 — Reciprocal/real vector recalculation guidance.
- docs/development/c_to_pytorch_config_map.md:41 — MOSFLM orientation mapping details.
- docs/debugging/debugging.md:30 — Trace SOP to follow during parity triage.
- docs/architecture/detector.md:120 — Context for CUSTOM pivot handling impacting pix0/beam vector logic.
- specs/spec-a-cli.md:75 — CLI contract for `-mat`, `-pix0_vector_mm`, and related flags.
- src/nanobrag_torch/models/crystal.py:200 — Current reciprocal vector bootstrap that needs orientation branching.
- reports/2025-10-cli-flags/phase_e/trace_summary.md — Evidence of present orientation mismatch for reference.
- prompts/supervisor.md:18 — Authoritative parity command arguments.

Next Up:
- Phase G3 parity rerun once lattice vectors match C (same reports directory).
- [VECTOR-TRICUBIC-001] Phase A evidence capture after CLI parity unblocks (prepare reports/2025-10-vectorization/phase_a/ baseline logs).
