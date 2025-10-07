Summary: Implement Phase L3d HKL device transfer + regression coverage so CLI HKL ingestion matches CUDA parity
Mode: Parity
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling.py::TestHKLDevice::test_hkl_tensor_respects_device (to be authored)
Artifacts: reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_device_probe_20251118.json, reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_audit.md, reports/2025-10-cli-flags/phase_l/structure_factor/test_cli_scaling_l3d.log
Do Now: CLI-FLAGS-003 Phase L3d implementation — add the targeted regression then run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestHKLDevice::test_hkl_tensor_respects_device -vv`
If Blocked: Re-run `env KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/cli_hkl_probe.py --device cuda --out reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_device_probe_retry.json` and document findings in Attempts History
- Priorities & Rationale:
  - plans/active/cli-noise-pix0/plan.md:258 — Phase L3d is the next open task and unblocks scaling closure
  - docs/fix_plan.md:452 — Next Actions now call for the `.to(device=device)` patch plus regression coverage
  - specs/spec-a-cli.md:1 — Normative contract for CLI flags and device behavior; CUDA parity is required
  - docs/development/c_to_pytorch_config_map.md:1 — Confirms HKL tensors must observe CLI `-device`
  - reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_audit.md:3 — Evidence from Attempt #80 pinpointing the device gap
- How-To Map:
  - `env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only tests/test_cli_scaling.py -q` after authoring the new test to confirm selector
  - `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestHKLDevice::test_hkl_tensor_respects_device -vv` (expect fail before patch, pass after)
  - `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py -vv` once fix + tests land, CPU first then CUDA if available
  - `env KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/cli_hkl_probe.py --device cuda --out reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_device_probe_20251118.json`
  - Update `reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_audit.md` with probe results + code refs
- Pitfalls To Avoid:
  - Do not alter simulator scaling during this loop; stay inside CLI/config scope until L3d passes
  - No `.cpu()` or implicit device transfers; rely on `.to(device=device, dtype=dtype)` with cloned tensors
  - Preserve HKL metadata tuple exactly as returned from `read_hkl_file`
  - Keep Protected Assets untouched (docs/index.md, loop.sh, supervisor.sh, input.md)
  - Write artifacts under the timestamped Phase L folder; avoid ad-hoc directories
  - Maintain KMP_DUPLICATE_LIB_OK=TRUE for every Python/PyTest invocation
  - Add tests before the fix and capture the expected failure message in Attempts History
  - Respect vectorization guardrails; no Python loops when touching tensor prep code
- Pointers:
  - plans/active/cli-noise-pix0/plan.md:19
  - docs/fix_plan.md:452
  - specs/spec-a-cli.md:1
  - docs/development/c_to_pytorch_config_map.md:1
  - reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_audit.md:3
- Next Up: After L3d passes, move to Phase L3e scaling validation per plan
