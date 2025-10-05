timestamp: 2025-10-05T23:53:52Z
commit: e7a7505
author: galph
focus: CLI-FLAGS-003 Phase C2 parity run
Summary: Capture PyTorch vs C CLI parity evidence for -nonoise/-pix0 overrides and prep docs follow-up.
Phase: Implementation
Focus: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest -q tests/test_cli_flags.py
Artifacts: reports/2025-10-cli-flags/phase_c/parity/

Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md; run NB_C_BIN=./golden_suite_generator/nanoBragg timeout 900 ./golden_suite_generator/nanoBragg -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0; then KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src timeout 900 python -m nanobrag_torch -mat A.mat -floatfile reports/2025-10-cli-flags/phase_c/parity/torch_img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 -floatlog reports/2025-10-cli-flags/phase_c/parity/torch_cli.log; finish with env AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md KMP_DUPLICATE_LIB_OK=TRUE pytest -q tests/test_cli_flags.py
If Blocked: If either run fails, capture stdout/stderr to reports/2025-10-cli-flags/phase_c/parity/attempt_FAIL.log, note the failing command, and log the outcome under docs/fix_plan.md Attempts before looping back through the error (do not patch code without new supervisor guidance).

Priorities & Rationale:
- docs/fix_plan.md:664 — Phase C2 demands parity evidence; without logs we cannot certify CLI support before documentation updates.
- plans/active/cli-noise-pix0/plan.md:33 — Phase C exit criteria require C vs PyTorch command execution with artifacts; parcels next phases.
- docs/development/c_to_pytorch_config_map.md:25 — Confirms unit expectations for pix0 overrides to cross-check against trace output.
- docs/architecture/detector.md:210 — Details pix0 handling and pivot interactions; align logs to spec to avoid silent geometry regressions.
- reports/2025-10-cli-flags/phase_a/README.md — Contains baseline observations from C runs; compare new parity artifacts for drift detection.

How-To Map:
- mkdir -p reports/2025-10-cli-flags/phase_c/parity before running commands; keep raw stdout with tee for traceability.
- Before PyTorch CLI run, set AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md to satisfy harness requirements and note value in attempt log.
- For C run: NB_C_BIN=./golden_suite_generator/nanoBragg timeout 900 ./golden_suite_generator/nanoBragg ... > reports/2025-10-cli-flags/phase_c/parity/c_cli.log 2>&1; archive generated img.bin alongside log (copy to parity directory without deleting root artifact).
- For PyTorch run: use PYTHONPATH=src and ensure output floatfile points into parity dir; pipe stdout/stderr to torch_cli.log via tee.
- After each command, verify reports/2025-10-cli-flags/phase_c/parity/ contains img.bin, torch_img.bin, c_cli.log, torch_cli.log; record file sizes in attempt note.
- Immediately rerun `env AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md KMP_DUPLICATE_LIB_OK=TRUE pytest -q tests/test_cli_flags.py > reports/2025-10-cli-flags/phase_c/parity/test_cli_flags.log 2>&1` to confirm regression suite stays green.
- Compare pix0 vector traces by grepping `DETECTOR_PIX0_VECTOR` (C) and adding `--dump-detector` flag equivalent (if available) or capturing Detector repr via `python - <<'PY'` snippet; if absent, note gap in attempt.
- Log total runtime and any warnings in docs/fix_plan.md under `[CLI-FLAGS-003]` Attempts History (timestamp + command + artefact path).
- If output directories already exist, append new timestamped suffix (e.g., parity_v2) to avoid overwriting Phase A evidence.
- After completion, update reports/2025-10-cli-flags/phase_c/README.md summarising parity outcome (corr metrics if computed) before leaving loop.

Pitfalls To Avoid:
- Do not delete or rename scaled.hkl or any file referenced by docs/index.md; treat them as protected assets.
- Avoid rerunning commands without tee; missing logs invalidate evidence and block plan closure.
- Keep device/dtype neutrality: ensure PyTorch CLI run inherits default float32 and respects config dtype (no manual `.cpu()` conversions).
- Do not modify code; this loop is evidence-only implementation — record failures instead of patching.
- Ensure NB_C_BIN points to golden_suite_generator/nanoBragg, not root nanoBragg binary, to keep instrumentation consistent.
- Watch for accidental double mm→m conversion; if PyTorch output deviates notably, capture pix0 tensors rather than editing code.
- Respect two-message loop policy: log Attempt entry before requesting new supervisor guidance.
- Avoid generating new Fdump.bin or other caches outside workspace; keep outputs within reports/.
- Maintain env var hygiene: reset/confirm AUTHORITATIVE_CMDS_DOC and KMP_DUPLICATE_LIB_OK before each command.
- Keep pytest runs constrained to the mapped suite; do not launch full test battery without instruction.

Pointers:
- docs/fix_plan.md:664 — `[CLI-FLAGS-003]` item details next actions and attempts log requirements.
- plans/active/cli-noise-pix0/plan.md:60 — Phase C2/C3 task definitions and guidance on parity artefacts.
- docs/development/testing_strategy.md:18 — Device/dtype discipline expectations; cite in attempt summary.
- docs/architecture/detector.md:214 — Pix0 override semantics; cross-check with captured tensors.
- prompts/supervisor.md:7 — Canonical parity command; ensure executed verbatim for both C and PyTorch runs.

Next Up:
- Phase C3 documentation updates for CLI flags (specs/spec-a-cli.md, README_PYTORCH.md) once parity evidence is archived and reviewed.
