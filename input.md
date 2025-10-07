Summary: Refresh the CLI HKL ingestion audit (Phase L3c) so the device/dtype gap is documented before simulator fixes start.
Mode: Parity
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests:
- env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py --collect-only -q
Artifacts:
- reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_audit.md
- reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_device_probe.json
- reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_env.json
Do Now: CLI-FLAGS-003 Phase L3c — refresh the CLI HKL ingestion audit, then run env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py --collect-only -q
If Blocked: Capture the failing command output to reports/2025-10-cli-flags/phase_l/structure_factor/attempt_log.txt and log the issue under CLI-FLAGS-003 in docs/fix_plan.md.
Priorities & Rationale:
- docs/fix_plan.md:450 — L3c demands a fresh CLI HKL audit before touching simulator code.
- plans/active/cli-noise-pix0/plan.md:141 — Phase L3c exit criteria require documenting device/dtype gaps in cli_hkl_audit.md.
- reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_audit.md:12 — Existing audit still flags CPU-only HKL tensors; confirm this remains true on current commit.
- specs/spec-a-cli.md:25 — CLI must honor -device for structure-factor ingestion per reference binding.
- docs/development/c_to_pytorch_config_map.md:59 — HKL tensors must respect caller device/dtype to preserve parity.
How-To Map:
- Inspect src/nanobrag_torch/__main__.py around parse_and_validate_args() and main() to confirm how hkl_data / metadata propagate to Crystal (note exact line numbers for the audit).
- Re-run the CLI HKL device probe (python reports/2025-10-cli-flags/phase_l/structure_factor/probe.py --device cuda) and update cli_hkl_device_probe.json + cli_hkl_env.json with today’s run.
- Append a 2025-11-18 section to cli_hkl_audit.md summarizing findings, referencing the exact code locations and probe outputs.
- After updating artifacts, execute env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py --collect-only -q and stash the log beside the audit if errors appear.
Pitfalls To Avoid:
- Do not edit simulator or config code during this audit loop.
- Keep HKL tensors on caller-requested device; no silent .cpu() helpers.
- Avoid creating new ad-hoc scripts outside reports/…/structure_factor/.
- Preserve Protected Assets from docs/index.md (input.md, loop.sh, supervisor.sh, etc.).
- Don’t run the full pytest suite; stick to the mapped selector.
- Maintain KMP_DUPLICATE_LIB_OK=TRUE for every torch invocation.
- Document probe commands and hashes directly in cli_hkl_audit.md.
- Ensure all new files remain ASCII and reuse existing report folders.
Pointers:
- src/nanobrag_torch/__main__.py:438 — HKL tuple collection.
- src/nanobrag_torch/__main__.py:872 — Crystal instantiation without device/dtype.
- src/nanobrag_torch/__main__.py:1068 — HKL tensor attachment lacking device transfer.
- reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_audit.md:1 — Audit doc to extend.
- docs/fix_plan.md:465 — CLI-FLAGS-003 next actions list.
Next Up: Phase L3d regression tests once the audit confirms the device fix requirements.
