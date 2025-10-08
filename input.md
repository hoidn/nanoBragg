Summary: Patch the trace harness so cache-aware parity taps work for the Option B batch pipeline and capture fresh CPU/CUDA evidence.
Mode: Parity
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — Phase M2g.5 trace tooling patch
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c
Artifacts: reports/2025-10-cli-flags/phase_l/trace_tooling_patch/<timestamp>/
Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — pytest --collect-only -q tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c
If Blocked: Capture the failing harness run under reports/2025-10-cli-flags/phase_l/trace_tooling_patch/<timestamp>_blocked/ with commands.txt, stdout, and env.json, then log the blocker in docs/fix_plan.md Attempts before stopping.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:115 keeps M2g.5 open until trace tooling handles the batched cache; without this the CUDA parity probe still crashes.
- docs/fix_plan.md:464 lists M2g.5 as the next actionable step after the refreshed metrics bundle we captured at 20251008T174753Z.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T174753Z/scaling_validation_summary.md:1 shows `I_before_scaling` still diverging; we need working taps to diagnose the cache rather than re-running metrics.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:1 must gains device/dtype-neutral cache indexing so parity evidence can exercise Option B on both CPU and CUDA.
- specs/spec-a-core.md:210 anchors the per-φ rotation contract we have to preserve while instrumenting the harness.
How-To Map:
- export AUTHORITATIVE_CMDS_DOC=docs/development/testing_strategy.md && pytest --collect-only -q tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c
- timestamp=$(date -u +%Y%m%dT%H%M%SZ) && outdir=reports/2025-10-cli-flags/phase_l/trace_tooling_patch/${timestamp} && mkdir -p "$outdir"
- KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --phi-mode c-parity --pixel 685 1039 --device cpu --dtype float64 --emit-rot-stars --out "$outdir/trace_cpu.log"
- KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --phi-mode c-parity --pixel 685 1039 --device cuda --dtype float64 --emit-rot-stars --out "$outdir/trace_cuda.log"
- tee "$outdir/commands.txt" <<'CMDS'
KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --phi-mode c-parity --pixel 685 1039 --device cpu --dtype float64 --emit-rot-stars --out trace_cpu.log
KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --phi-mode c-parity --pixel 685 1039 --device cuda --dtype float64 --emit-rot-stars --out trace_cuda.log
CMDS
- OUTDIR="$outdir" python - <<'PY'
import json, os, platform, subprocess, sys, time
outdir = os.environ['OUTDIR']
meta = {
  "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
  "git_sha": subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),
  "python": sys.version,
  "torch_version": __import__('torch').__version__,
  "device_cuda_available": __import__('torch').cuda.is_available(),
  "platform": platform.platform(),
}
with open(os.path.join(outdir, 'run_metadata.json'), 'w') as fh:
  json.dump(meta, fh, indent=2)
PY
- (cd "$outdir" && sha256sum commands.txt trace_cpu.log trace_cuda.log run_metadata.json > sha256.txt)
- Update docs/fix_plan.md Attempts with a new entry (Attempt #171) summarising the tooling patch evidence and reference "$outdir"; keep plan row M2g.5 open until CUDA harness passes without index errors.
Pitfalls To Avoid:
- No sequential Python fallbacks; maintain full vectorization when editing harness helpers.
- Preserve device/dtype neutrality—no implicit `.cpu()` or host-only tensors in trace taps.
- Keep Protected Assets intact; do not touch files listed in docs/index.md without plan updates.
- When adding logging, reuse existing tensor outputs rather than recomputing physics values (per instrumentation rule).
- Record every command in commands.txt and include SHA256 checksums before closing the loop.
- Respect the Parity mode gate: only run the targeted collect-only pytest plus the two harness commands.
- Do not downgrade existing evidence directories; create a fresh timestamped folder.
- Ensure CUDA runs use the same phi carryover mode and dtype as CPU to keep comparisons valid.
- Avoid editing simulator physics during this loop; focus solely on tooling and evidence capture.
- Run scripts under KMP_DUPLICATE_LIB_OK=TRUE to prevent MKL duplication crashes.
Pointers:
- docs/fix_plan.md:464
- plans/active/cli-noise-pix0/plan.md:115
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T174753Z/scaling_validation_summary.md:1
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:1
- specs/spec-a-core.md:210
- docs/bugs/verified_c_bugs.md:166
Next Up:
- 1. Complete M2g.6 documentation sync once the tooling patch evidence is green.
- 2. Start the cache index audit (Next Actions #4) to log per-pixel carryover behavior ahead of simulator fixes.
