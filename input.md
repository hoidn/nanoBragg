Summary: Audit the CLI HKL ingestion path so it mirrors the harness pattern before resuming scaling fixes.
Mode: Parity
Focus: CLI-FLAGS-003 – Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_cli_scaling.py
Artifacts: reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_audit.md, reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_audit_raw.txt, reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_env.json
Do Now: CLI-FLAGS-003 Phase L3c CLI ingestion audit — KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python - <<'PY' > reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_audit_raw.txt
import json
from pathlib import Path
from nanobrag_torch.__main__ import create_parser, parse_and_validate_args

def build_args():
    return [
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
args = parser.parse_args(build_args())
config = parse_and_validate_args(args)
meta = config["hkl_data"][1]
out = {
    "dtype": str(config["hkl_data"][0].dtype),
    "device": str(config["hkl_data"][0].device),
    "shape": list(config["hkl_data"][0].shape),
    "metadata": meta,
    "has_metadata_keys": sorted(meta.keys()),
}
print(json.dumps(out, indent=2, default=str))
PY
If Blocked: Capture stderr/stdout to reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_audit_failure.log and summarize the exception plus reproduction steps in docs/fix_plan.md Attempt history before stopping.
Priorities & Rationale:
- docs/fix_plan.md:452-468 now points Phase L3 toward the CLI ingestion audit, so today’s work must produce that evidence bundle.
- plans/active/cli-noise-pix0/plan.md:270-283 lists L3c as the current open task, requiring documentation before code edits.
- reports/2025-10-cli-flags/phase_l/structure_factor/analysis_20251117.md:1-120 confirms the harness delivers F_cell=190.27; CLI must match this behavior next.
- specs/spec-a-cli.md:60-140 defines -hkl / -floatfile precedence and forbids silent dtype/device coercion at the CLI boundary.
- docs/development/c_to_pytorch_config_map.md:1-80 reiterates that HKL tensors must stay on the caller’s device/dtype, which the audit should verify.
How-To Map:
- mkdir -p reports/2025-10-cli-flags/phase_l/structure_factor
- Run the Python audit command above; it dumps the parsed HKL tensor meta directly to cli_hkl_audit_raw.txt.
- jq '.' reports/.../cli_hkl_audit_raw.txt > reports/.../cli_hkl_audit.json (optional pretty copy). Extract key findings into cli_hkl_audit.md (dtype/device, min/max h/k/l, any gaps).
- Record env metadata: KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python - <<'PY' > reports/.../cli_hkl_env.json
import json, torch, platform, subprocess
env = {
    "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip(),
    "python": platform.python_version(),
    "torch": torch.__version__,
    "cuda_available": torch.cuda.is_available()
}
print(json.dumps(env, indent=2))
PY
- Validate selector: KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py | tee reports/2025-10-cli-flags/phase_l/structure_factor/collect_cli_scaling_post_audit.log
- Summarize findings (bullet list) in cli_hkl_audit.md citing the raw log, env snapshot, and any discrepancies; flag whether metadata keys (`h_min`, etc.) are present and if dtype/device align with expectations.
Pitfalls To Avoid:
- Do not modify src/nanobrag_torch code yet; today is evidence-only.
- Keep reports timestamped; never overwrite prior artifacts without copying first.
- Avoid using `.item()` or `.numpy()` inside audit scripts when tensors may require grad; stick to `.detach().cpu()` if needed.
- Maintain device neutrality in scripts (no hard-coded `.cpu()` conversions unless copying for logging outside simulator paths).
- Respect Protected Assets listed in docs/index.md; do not move/delete them.
- Stay on feature/spec-based-2; no rebases or merges mid-loop.
- Do not run nb-compare or the full parity suite until plan marks L3 complete.
- Capture env var `KMP_DUPLICATE_LIB_OK=TRUE` for every PyTorch invocation to avoid MKL crashes.
- Avoid ad-hoc scripts outside reports/…; keep analysis local to plan directories.
- Document any anomalies in docs/fix_plan.md Attempts immediately.
Pointers:
- docs/fix_plan.md:448
- plans/active/cli-noise-pix0/plan.md:260
- reports/2025-10-cli-flags/phase_l/structure_factor/analysis_20251117.md:1
- specs/spec-a-cli.md:80
- docs/development/c_to_pytorch_config_map.md:20
- src/nanobrag_torch/__main__.py:360
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:200
Subproject Guidance: none
Attempts History: Continue numbering from Attempt #78 in docs/fix_plan.md.
Next Up: 1. Extend tests/test_cli_scaling.py with the structure-factor assertion; 2. Build the scaling validation helper once CLI ingestion is confirmed.
