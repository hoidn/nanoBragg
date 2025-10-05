Header: 2025-10-05 23:08:58Z | Commit f69007c | Author galph | Active Focus: [CLI-FLAGS-003] Phase B4/B5 – prove pix0 alias parity and detector cache stability before Phase C
Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — capture Phase B4/B5 evidence logs | PyTest: KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src pytest tests/test_at_cli_001.py -q
If Blocked: Dump failing argv/trace to reports/2025-10-cli-flags/phase_b/attempt_fail/<stamp>.txt, note exit codes, and log the attempt under docs/fix_plan.md#CLI-FLAGS-003 before retrying commands.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:23-41 — Phase B table tags B4/B5 as [P]; without the parser parity log and cache harness we cannot advance to C1 regression testing.
- docs/fix_plan.md:667-674 — First Divergence explicitly calls out missing artifacts for meter vs mm parity and cache hygiene; closing them is mandatory to unblock the long-term parity command.
- src/nanobrag_torch/__main__.py:546-557 — CLI parses both pix0 flags and applies mm→m conversion; we must demonstrate equivalence and SystemExit when both flags appear.
- src/nanobrag_torch/models/detector.py:391-407 and 661-684 — Override branch and cache refresh; evidence must show override tensors survive invalidate_cache() and device transfers.
- docs/development/testing_strategy.md:18-26 — Device/dtype discipline requires logs documenting CPU and CUDA behaviour (or explicit note when CUDA unavailable).
- docs/development/c_to_pytorch_config_map.md:60-68 — Config map ties CLI flags to DetectorConfig fields; artefacts should cite this mapping to confirm parity with C semantics.
- reports/2025-10-cli-flags/phase_b/ currently contains argparse/pytest folders only; new detector/ parity logs keep plan reporting consistent with Phase A layout.
- prompts/supervisor.md long-term goal command includes -pix0_vector_mm and -nonoise; today’s work is the prerequisite to even attempt a PyTorch dry run of that command.
- docs/architecture/detector.md (pix0 discussion) — reiterates the hybrid unit system; referencing it in logs clarifies why mm inputs convert to meters internally.
- docs/debugging/detector_geometry_checklist.md Section 1 — mandates verifying pix0 vector orientation before comparing traces; parity logs should mention alignment with that checklist.
- arch.md §2 — documents detector module responsibilities; cite it in cache_handoff.txt when describing invalidate_cache ergonomics.
- reports/2025-10-cli-flags/phase_a/c_with_noise.log — use as reference when confirming C writes noiseimage.img; include contrast statement in new logs.
How-To Map:
- Prep step: mkdir -p reports/2025-10-cli-flags/phase_b/detector to keep artefacts grouped with Phase B evidence.
- Step 1 (parser alias check):
PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python - <<'PY' > reports/2025-10-cli-flags/phase_b/detector/pix0_override_equivalence.txt
from nanobrag_torch.__main__ import create_parser, parse_and_validate_args
import itertools
parser = create_parser()
inputs = [
    ['-cell','100','100','100','90','90','90','-default_F','1','-lambda','0.5','-pixel','0.1','-pix0_vector','-0.2','0.3','0.4'],
    ['-cell','100','100','100','90','90','90','-default_F','1','-lambda','0.5','-pixel','0.1','-pix0_vector_mm','-200','300','400'],
]
for argv in inputs:
    args = parser.parse_args(argv)
    cfg = parse_and_validate_args(args)
    print('argv', argv)
    print('pix0_override_m', cfg.get('pix0_override_m'))
try:
    parser.parse_args(inputs[0] + ['-pix0_vector_mm','1','2','3'])
except SystemExit as exc:
    print('dual_flag_exit_code', exc.code)
PY
- Step 2 (detector cache harness with device sweep):
PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python - <<'PY' > reports/2025-10-cli-flags/phase_b/detector/cache_handoff.txt
import torch
from nanobrag_torch.config import DetectorConfig, DetectorConvention
from nanobrag_torch.models.detector import Detector
cfg = DetectorConfig(distance_mm=150.0, pixel_size_mm=0.12, spixels=16, fpixels=20,
                     detector_convention=DetectorConvention.CUSTOM,
                     pix0_override_m=(0.12, -0.34, 0.56))
det = Detector(config=cfg, device=torch.device('cpu'), dtype=torch.float64)
print('cpu_pix0', det.pix0_vector, det.pix0_vector.device, det.pix0_vector.dtype)
det.invalidate_cache()
print('cpu_after_invalidate', det.pix0_vector)
if torch.cuda.is_available():
    det = det.to(torch.device('cuda'))
    print('cuda_pix0', det.pix0_vector, det.pix0_vector.device, det.pix0_vector.dtype)
    det.invalidate_cache()
    print('cuda_after_invalidate', det.pix0_vector)
else:
    print('cuda_unavailable')
PY
- Step 2b (optional dtype downshift): rerun the harness with dtype=torch.float32 once the float64 run succeeds and append results to cache_handoff.txt for completeness.
- Step 3 (optional warning check): ensure `-nonoise` still suppresses noise output by grepping CLI config echo once parser parity is logged (record result in pix0_override_equivalence.txt).
- Step 4 (pytest smoke for CLI help baseline):
KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src pytest tests/test_at_cli_001.py -q | tee reports/2025-10-cli-flags/phase_b/pytest/cli_help_smoke.log
- Step 5 (documentation bookkeeping): append Attempt entry in docs/fix_plan.md:664-706 citing both detector logs, and mark plan tasks B4/B5 as ready for closure once reviewers confirm.
- Step 6 (git sanity check): git status --short should show only input.md, docs/fix_plan.md, plans/active/cli-noise-pix0/plan.md after edits; if additional files appear, document why in the Attempt entry.
- Step 7 (context reminder): copy summary snippets from reports/2025-10-cli-flags/phase_b/detector/*.txt into docs/fix_plan.md attempts so auditors can spot-check without opening raw logs.
Pitfalls To Avoid:
- Do not remove or rename reports/2025-10-cli-flags artifacts; Phase A audit relies on consistent paths.
- Avoid editing loop.sh or supervisor.sh; supervisor guard plan is still active elsewhere.
- Keep override tensors as torch.Tensor; never convert to float via .item()/.tolist() when logging.
- Respect CUSTOM convention side effects; do not reset config['convention']='MOSFLM' after overrides.
- Remember parser.parse_args exits with SystemExit; capture exit codes rather than swallowing exceptions and continue logging them.
- When CUDA is unavailable, explicitly log that fact to satisfy device/dtype documentation requirements.
- Ensure stdout redirection overwrites (not appends) the detector logs to avoid stale content.
- No new helper scripts outside the repo tree; use inline python - <<'PY' blocks as outlined.
- After pytest, clear temporary __pycache__ only if failures reference stale bytecode; otherwise leave tree untouched.
- Maintain ASCII in logs and doc updates; avoid smart quotes or non-breaking spaces when editing fix_plan.md.
- Record manual command invocations in docs/fix_plan.md Attempts with timestamps; missing provenance will block supervisor sign-off.
- Avoid running the full 2463×2527 simulation until Phase C artifacts say so; today’s focus is lightweight parity, not end-to-end execution.
- Keep the detector harness free of torch.compile wrappers; the plan expects eager mode evidence for cache behaviour.
- When using tee, verify the resulting file ends with a newline to satisfy lint tools that parse logs.
- After completing commands, re-run the alias script with reversed argv order if needed to prove determinism; include note if outputs differ.
- Keep environment variables explicit in every command you log; implicit inheritance causes audit drift.
Pointers:
- plans/active/cli-noise-pix0/plan.md:23-41 — Phase B + C guidance.
- docs/fix_plan.md:664-708 — Current status and attempts history for [CLI-FLAGS-003].
- src/nanobrag_torch/__main__.py:546-557 — pix0 flag parsing logic to compare with logs.
- src/nanobrag_torch/models/detector.py:391-407, 661-684 — override path and cache refresh checks relative to harness output.
- docs/development/testing_strategy.md:18-26 — device/dtype logging expectations.
- docs/architecture/detector.md (pix0 section) — use for interpreting logged vectors, especially MOSFLM vs CUSTOM discussion.
- specs/spec-a-cli.md (pix0 flag shard) — reference for documentation updates after tests.
- reports/2025-10-cli-flags/phase_a/README.md — baseline findings to echo when describing mm conversion rationale.
- docs/debugging/detector_geometry_checklist.md:12-38 — checklist items to cite if parity logs uncover orientation mismatches.
- docs/architecture/pytorch_design.md §2.4 — reminds why detector caches are hoisted; mention in cache_handoff.txt when commenting on invalidate_cache behaviour.
- arch.md §2 — documents detector module responsibilities; cite in cache_handoff.txt when describing invalidate_cache ergonomics.
- reports/2025-10-cli-flags/phase_a/c_with_noise.log — reference for expected noisefile behaviour; contrast with PyTorch logs showing suppression.
- reports/2025-10-cli-flags/phase_b/argparse/help.txt — prior Phase B output ensuring help text already listed the new flags; confirm parity after modifications.
Next Up:
- Phase C1 regression: add pytest covering meter/mm alias plus -nonoise once B4/B5 artefacts land.
- Supervisor command dry-run under PyTorch CLI with -nonoise and pix0 override after parity proof is committed.
- Phase C2 golden comparison: plan the NB_C_BIN vs PyTorch execution using the supervisor command, noting ROI and expected output paths for reports/2025-10-cli-flags/phase_c.
- Phase C3 documentation sweep: refresh specs/spec-a-cli.md and README_PYTORCH.md tables with the new flags once tests land.
- Coordinate with docs/index.md update (Phase B5 reminder) to list supervisor.sh as protected asset after guard work resumes; note dependency in fix_plan once guard plan moves forward.
