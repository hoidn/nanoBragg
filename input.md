Summary: Capture fresh CLI HKL ingestion evidence (incl. CUDA probe) and document the device-handling gap before L3 structure-factor fixes.
Mode: Parity
Focus: CLI-FLAGS-003 – Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_cli_scaling.py
Artifacts: reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_device_probe.json, reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_env.json, reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_audit.md
Do Now: CLI-FLAGS-003 Phase L3c device audit — KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python - <<'PY' > reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_device_probe.json
import json
import torch
from nanobrag_torch.__main__ import create_parser, parse_and_validate_args

base_args = [
    "-mat", "A.mat",
    "-floatfile", "img.bin",
    "-hkl", "scaled.hkl",
    "-nonoise",
    "-nointerpolate",
    "-oversample", "1",
    "-exposure", "1",
    "-flux", "1e18",
    "-beamsize", "1.0",
    "-spindle_axis", "-1", "0", "0",
    "-Xbeam", "217.742295",
    "-Ybeam", "213.907080",
    "-distance", "231.274660",
    "-lambda", "0.976800",
    "-pixel", "0.172",
    "-detpixels_x", "2463",
    "-detpixels_y", "2527",
    "-odet_vector", "-0.000088", "0.004914", "-0.999988",
    "-sdet_vector", "-0.005998", "-0.999970", "-0.004913",
    "-fdet_vector", "0.999982", "-0.005998", "-0.000118",
    "-pix0_vector_mm", "-216.336293", "215.205512", "-230.200866",
    "-beam_vector", "0.00051387949", "0.0", "-0.99999986",
    "-Na", "36",
    "-Nb", "47",
    "-Nc", "29",
    "-osc", "0.1",
    "-phi", "0",
    "-phisteps", "10",
    "-detector_rotx", "0",
    "-detector_roty", "0",
    "-detector_rotz", "0",
    "-twotheta", "0"
]

parser = create_parser()

results = {}
args_cpu = parser.parse_args(base_args)
config_cpu = parse_and_validate_args(args_cpu)
hkl_cpu, meta_cpu = config_cpu["hkl_data"]
results["cpu"] = {
    "dtype": str(hkl_cpu.dtype),
    "device": str(hkl_cpu.device),
    "shape": list(hkl_cpu.shape),
    "metadata": meta_cpu,
}

if torch.cuda.is_available():
    args_cuda = parser.parse_args(base_args + ["-device", "cuda"])
    config_cuda = parse_and_validate_args(args_cuda)
    hkl_cuda, meta_cuda = config_cuda["hkl_data"]
    results["cuda"] = {
        "dtype": str(hkl_cuda.dtype),
        "device": str(hkl_cuda.device),
        "shape": list(hkl_cuda.shape),
        "metadata_match": meta_cuda == meta_cpu,
    }
else:
    results["cuda"] = "cuda_unavailable"

print(json.dumps(results, indent=2, default=str))
PY
If Blocked: Capture stdout/stderr to reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_device_probe_failure.log, note the exact traceback plus shell/command in docs/fix_plan.md Attempt history, and halt.
Priorities & Rationale:
- docs/fix_plan.md:452-468 keeps L3c front-and-center; today’s probe verifies the outstanding device gap before edits.
- plans/active/cli-noise-pix0/plan.md:270-283 requires CLI audit artifacts ahead of normalization fixes.
- reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_audit.md already logs dtype handling; extend it with this CUDA finding so future attempts see the blocker.
- specs/spec-a-cli.md:60-140 forbids silent dtype/device drift at the CLI boundary—evidence must show where we violate this.
- docs/development/c_to_pytorch_config_map.md:20-84 reiterates that CLI inputs must honour caller device/dtype, guiding the upcoming fix.
How-To Map:
- mkdir -p reports/2025-10-cli-flags/phase_l/structure_factor
- Run the Python probe above; it emits cpu/cuda HKL tensor metadata to cli_hkl_device_probe.json.
- Record env snapshot: KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python - <<'PY' > reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_env.json
import json, platform, subprocess, torch
env = {
    "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip(),
    "python": platform.python_version(),
    "torch": torch.__version__,
    "cuda_available": torch.cuda.is_available()
}
print(json.dumps(env, indent=2))
PY
- Update reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_audit.md with a short bullet citing the new JSON artifact and noting that the CLI keeps HKL on cpu even when -device cuda is requested.
- Validate the mapped selector: KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py | tee reports/2025-10-cli-flags/phase_l/structure_factor/collect_cli_scaling_post_audit.log
- Log Attempt #79 under CLI-FLAGS-003 in docs/fix_plan.md summarizing the device gap and attaching the probe path.
Pitfalls To Avoid:
- Evidence only: no edits to src/ modules yet.
- Keep all artifacts under reports/2025-10-cli-flags/phase_l/structure_factor/ with timestamps when adding variants.
- Set KMP_DUPLICATE_LIB_OK=TRUE for every Python/PyTorch invocation.
- Do not guess at pytest selectors beyond the mapped command; rely on docs/development/testing_strategy.md guidance.
- Leave Protected Assets untouched (docs/index.md guard).
- Avoid hard-coding `.cpu()` in scripts; use `.to()` only outside simulator codepaths when logging.
- Stay on feature/spec-based-2; don’t rebase/merge mid-loop.
- No nb-compare or full parity suite until CLI ingestion fix is implemented.
- Document any deviations immediately in docs/fix_plan.md Attempts.
Pointers:
- docs/fix_plan.md:452
- plans/active/cli-noise-pix0/plan.md:270
- reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_audit.md#2025-11-17-re-audit-galph
- specs/spec-a-cli.md:60
- docs/development/c_to_pytorch_config_map.md:1
- src/nanobrag_torch/__main__.py:442
- src/nanobrag_torch/__main__.py:1068
- src/nanobrag_torch/simulator.py:204
Next Up: 1) Extend tests/test_cli_scaling.py with structure-factor coverage once device fix lands; 2) Re-run Phase L scaling trace after HKL ingestion is corrected.
