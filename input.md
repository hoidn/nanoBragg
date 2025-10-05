Header: 2025-10-05 22:23:44Z | Commit 2324c15 | Author galph | Active Focus: [CLI-FLAGS-003] Phase B argparse and detector wiring for -nonoise / pix0 overrides
Context 1: Phase A logs exist under reports/2025-10-cli-flags/phase_a/; do not overwrite them while adding new artifacts.
Context 2: Long-term goal is to run the PyTorch CLI command matching the supervisor’s nanoBragg invocation; missing flags currently block execution outright.
Context 3: Detector currently calculates pix0 internally regardless of CLI overrides, preventing parity with CUSTOM inputs.
Context 4: Parser rejects unknown flags because allow_abbrev=False; any missing argument definitions cause hard exits.
Context 5: Noise writer unconditionally runs when noisefile is set; we must gate it to honor -nonoise while keeping SMV behavior intact.
Environment Baseline: Operate within /Users/ollie/Documents/nanoBragg3, approvals=never, sandbox=danger-full-access, shell=zsh.
Coordination: Record every major action (parser edit, detector override, pytest run) in docs/fix_plan.md Attempts with timestamps and artifact paths.
Reporting: Create phase-specific folders under reports/2025-10-cli-flags/phase_b/ (argparse/, detector/, pytest/, smoke/) to store logs and diffs.
Communication: If spec wording conflicts with observed C behavior, pause and document the discrepancy before coding detours.
Safety: Respect Protected Assets noted in docs/index.md (loop.sh, supervisor.sh, input.md) during any git operations.

Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — after implementing plan Phase B tasks B1–B3, run KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_entrypoint.py -q and archive the log.
Milestone A: Argparse recognizes both new flags without altering existing help strings.
Milestone B: parse_and_validate_args threads suppress_noise and pix0_override_m fields correctly.
Milestone C: Detector honors the override path and keeps caches coherent; smoke test proves CLI accepts the supervisor command.

If Blocked: capture failing command output to reports/2025-10-cli-flags/phase_b/attempt_fail/log.txt, include command + exit code, and reference it in docs/fix_plan.md before retrying.
Fallback 1: If argparse errors persist, isolate with `python -m nanobrag_torch -h` and store the trace in attempt_fail/parser_trace.log.
Fallback 2: If detector overrides break geometry tests, temporarily disable override usage, collect the failing pytest log, and mark fix_plan attempt as deferred with rationale.
Fallback 3: When pytest imports fail due to stale bytecode, remove __pycache__/ via `find src -name '__pycache__' -exec rm -rf {} +` and document the cleanup.
Fallback 4: If noise suppression logic touches missing plan tasks, revert the change, checkpoint the diff patch under attempt_fail/revert.patch, and alert supervisor via fix_plan entry.

Priorities & Rationale:
- Priority 1: specs/spec-a-cli.md:65 mandates -nonoise support; without it the PyTorch CLI cannot mirror the C baseline, halting the user’s parity test (see src/nanobrag_torch/__main__.py:334 for current gap).
  Detail: Add argparse flag, ensure config prevents noise image generation, and maintain compatibility with existing noisefile semantics.
- Priority 2: docs/architecture/detector.md:188 requires pix0 overrides to flow through detector caches; ignoring the override causes a geometry mismatch (src/nanobrag_torch/models/detector.py:326 currently recomputes pix0 regardless of CLI input).
  Detail: Introduce a canonical override tensor on DetectorConfig and short-circuit _calculate_pix0_vector when provided.
- Priority 3: docs/development/c_to_pytorch_config_map.md ensures CUSTOM convention when pix0 vectors are supplied; the new _mm alias must trigger the same pivot change (src/nanobrag_torch/__main__.py:451).
  Detail: Extend the CUSTOM detection block to include args.pix0_vector_mm and guard against mixed-unit usage.
- Priority 4: plans/active/cli-noise-pix0/plan.md Phase B lists tasks B1–B5; following the checklist prevents scope creep and keeps documentation aligned.
  Detail: After each task, capture evidence (e.g., help output, config dump, detector repr) in the reports folder.
- Priority 5: docs/fix_plan.md entry [CLI-FLAGS-003] currently points to Phase B execution; updating Attempts with concrete metrics proves progress to supervisor and unlocks Phase C.
  Detail: Summaries should include command names, success/failure status, and artifact locations.

How-To Map:
Step 1: Modify create_parser() to include `parser.add_argument('-nonoise', action='store_true', help='Suppress noise image generation')`; mirror C help text exactly.
Command: edit src/nanobrag_torch/__main__.py near line 334 and verify `nanoBragg --help | grep nonoise` shows the new flag (capture output to reports/2025-10-cli-flags/phase_b/argparse/help.txt).
Verification: Confirm the --help invocation exits with status 0.
Step 2: Add `parser.add_argument('-pix0_vector_mm', nargs=3, type=float, metavar=('X','Y','Z'), help='Detector origin override in millimeters')` adjacent to -pix0_vector.
Command: `nanoBragg --help | sed -n '170,210p' > reports/2025-10-cli-flags/phase_b/argparse/pix0_help.txt` to document the updated usage text.
Verification: Ensure both pix0 flags appear under Custom vectors section without duplication.
Step 3: Extend parse_and_validate_args() to record args.nonoise into config['suppress_noise'] and to normalize pix0 inputs (convert mm to meters) into config['pix0_override_m'].
Command: insert unit conversion helper (mm -> m) and test by running `python - <<'PY'
from nanobrag_torch.__main__ import create_parser, parse_and_validate_args
parser = create_parser()
ns = parser.parse_args('-pix0_vector_mm 1 2 3 -nonoise'.split())
print(parse_and_validate_args(ns)['pix0_override_m'])
PY` storing stdout in reports/2025-10-cli-flags/phase_b/argparse/parse_smoke.txt.
Verification: Output should be a tuple/list scaled to 0.001,0.002,0.003 and suppress_noise truthy.
Step 4: Update the CUSTOM convention detection block so any pix0 override (meter or millimeter) forces config['convention']='CUSTOM'; add validation to reject simultaneous use of both flags.
Command: run `python - <<'PY'
from nanobrag_torch.__main__ import create_parser, parse_and_validate_args
parser = create_parser()
ns = parser.parse_args('-pix0_vector 0.1 0.2 0.3'.split())
print(parse_and_validate_args(ns)['convention'])
PY` and store under reports/2025-10-cli-flags/phase_b/argparse/custom_guard.txt.
Verification: Expect 'CUSTOM'; ensure exception is raised when both flags are used (capture message in parse_error.txt).
Step 5: Add `pix0_override_m: Optional[torch.Tensor] = None` to DetectorConfig (src/nanobrag_torch/config.py:202) and thread the provided override into Detector.__init__.
Command: run `python - <<'PY'
from nanobrag_torch.config import DetectorConfig
cfg = DetectorConfig(distance_mm=100.0, pixel_size_mm=0.1, pix0_override_m=(0.1,0.2,0.3))
print(cfg.pix0_override_m)
PY` verifying the attribute exists; log output to reports/2025-10-cli-flags/phase_b/detector/config_print.txt.
Verification: Ensure __post_init__ keeps beam centers consistent when override is present.
Step 6: Modify Detector._calculate_pix0_vector to short-circuit when pix0_override_m is provided, converting to the correct device/dtype and caching copies.
Command: run `python - <<'PY'
import torch
from nanobrag_torch.config import DetectorConfig, DetectorConvention
from nanobrag_torch.models.detector import Detector
cfg = DetectorConfig(distance_mm=100.0, pixel_size_mm=0.1, pix0_override_m=torch.tensor([0.1,0.2,0.3]))
cfg.detector_convention = DetectorConvention.CUSTOM
det = Detector(cfg)
print(det.pix0_vector)
PY` storing tensor output in reports/2025-10-cli-flags/phase_b/detector/override_smoke.txt.
Verification: pix0_vector should match override (within dtype tolerance) and cache version increments correctly.
Step 7: Ensure invalidate_cache() respects overrides by changing pix0_override_m and confirming recalculation resets caches.
Command: extend prior snippet to mutate cfg.pix0_override_m and call det.invalidate_cache(); capture results in override_cache.txt.
Verification: `_geometry_version` should increment and pix0_vector should update.
Step 8: Run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_entrypoint.py -q` after edits; redirect output to reports/2025-10-cli-flags/phase_b/pytest/cli_entrypoint.log.
Verification: Tests must pass; if new tests were added, confirm they appear in the log.
Step 9: Execute the full supervisor PyTorch command to confirm CLI parsing via Python: `KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -mat A.mat ... -pix0_vector_mm ... -nonoise` (fill in entire parameter list from prompts).
Command: Save stdout/stderr to reports/2025-10-cli-flags/phase_b/smoke/pytorch_cli.log.
Verification: Command should run to completion, emitting floatfile write and skipping noise writer; inspect log for absence of noiseimage lines.
Step 10: Document outcomes in docs/fix_plan.md `[CLI-FLAGS-003]` Attempts, referencing artifact files created above.
Command: open docs/fix_plan.md, append Attempt entry, and stage the change once details are finalized.
Verification: Ensure attempt entry lists success/failure, metrics (e.g., tests passing), and artifact paths.

Pitfalls To Avoid:
- Do not leave config['noisefile'] populated when suppress_noise is True; otherwise noiseimage.img may still be written.
  Explanation: C code drops the noise write entirely; we must mimic this to satisfy spec acceptance tests.
- Avoid storing pix0 overrides as tuples without dtype/device normalization; convert to detector dtype to keep gradients valid.
  Explanation: Mixing Python floats with tensors can break autograd and device neutrality rules.
- Refrain from using `.item()` on override tensors; maintain differentiability for potential future refinement workflows.
  Explanation: Items detach tensors and violate differentiability guidelines in docs/architecture/pytorch_design.md.
- Do not bypass Detector.invalidate_cache(); ensure overrides trigger recalculation of dependent tensors.
  Explanation: Cached pixel coordinates rely on pix0_vector; stale caches corrupt physics results.
- Skip enabling argparse abbreviation; maintain allow_abbrev=False so short forms do not conflict with existing flags.
  Explanation: Abbreviations can introduce hard-to-debug parsing differences vs C.
- Do not suppress warnings silently when both pix0 flags are provided; raise a clear argparse error instead.
  Explanation: Ambiguous overrides lead to undefined behavior; fail fast.
- Avoid editing docs/index.md or other Protected Assets; any doc updates must respect the protected list.
  Explanation: Protected Assets Rule in CLAUDE.md forbids deleting or renaming indexed files.
- Keep NB_C_BIN unset for PyTorch tests; only export when intentionally running the C binary for parity evidence.
  Explanation: Environment leaks can confuse wrapper scripts and mask CLI bugs.
- Do not forget to rerun pytest after editing tests; commit messages must state whether tests ran.
  Explanation: Supervisor requires explicit test status in final summary.
- Avoid merging code without updating docs/fix_plan.md; the ledger tracks supervisory coordination.
  Explanation: Missing updates break galph’s oversight loop.

Pointers:
- docs/fix_plan.md:664 — current status, Next Actions, and artifacts list for [CLI-FLAGS-003]; update Attempts after each milestone.
- plans/active/cli-noise-pix0/plan.md:31 — Phase B table (B1–B5) detailing argparse and detector tasks plus hygiene notes.
- specs/spec-a-cli.md:60 — authoritative flag definitions for -nonoise and the pix0 vector aliases; ensure help strings match this text.
- docs/architecture/detector.md:188 — describes pix0 Vector handling, cache invalidation, and CUSTOM convention details.
- docs/development/c_to_pytorch_config_map.md:22 — C↔Py parity list; shows CUSTOM pivot requirement for pix0 overrides.
- src/nanobrag_torch/__main__.py:334 — output flag parsing section requiring new arguments and config wiring.
- src/nanobrag_torch/__main__.py:541 — existing custom_pix0_vector assignment earmarked for replacement.
- src/nanobrag_torch/models/detector.py:326 — pix0 calculation routine that must accept override tensors.
- src/nanobrag_torch/config.py:202 — DetectorConfig dataclass to extend with pix0_override_m and suppress_noise wiring.
- tests/test_cli_entrypoint.py — location for CLI regression tests covering new flags; add cases ensuring normalized override tensors.

Next Up: If time remains after Phase B, begin drafting Phase C regression tests under tests/test_cli_flags.py and prepare nb-compare smoke instructions, but record the new focus in docs/fix_plan.md before implementation.
Next Up Alt: Alternatively, queue Detector cache profiling (PERF-PYTORCH-004 tasks C8/C9) once CLI work is stable; note the deferment reason in fix_plan if chosen.
