Summary: Regenerate per-φ parity traces and log detector geometry so we can kill the residual Δk plateau before rerunning the supervisor command.
Mode: Parity
Focus: CLI-FLAGS-003 – Phase L3k.3c.4 parity shim diagnostics
Branch: feature/spec-based-2
Mapped tests: none — evidence-only (trace harness)
Artifacts: reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/; reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md
Do Now: CLI-FLAGS-003 L3k.3c.4 parity shim diagnostics — OUTDIR=reports/2025-10-cli-flags/phase_l/parity_shim/$(date -u +%Y%m%dT%H%M%SZ) && KMP_DUPLICATE_LIB_OK=TRUE python scripts/trace_per_phi.py --outdir "$OUTDIR" && python scripts/compare_per_phi_traces.py "$OUTDIR"/per_phi_pytorch.json reports/2025-10-cli-flags/phase_l/parity_shim/20251008T021659Z/c_trace_phi.log && pytest --collect-only -q tests/test_cli_scaling_phi0.py tests/test_phi_carryover_mode.py
If Blocked: Capture the failing command + stderr in reports/2025-10-cli-flags/phase_l/parity_shim/ATTEMPTS.md and ping Galph before retrying.
Priorities & Rationale:
- specs/spec-a-core.md:204 — spec mandates φ loop resets each step; diagnostics must confirm we stay spec-compliant.
- docs/bugs/verified_c_bugs.md:166 — C-PARITY-001 describes the carryover bug the shim emulates; use it to justify evidence expectations.
- plans/active/cli-phi-parity-shim/plan.md:70 — Follow the new C4 diagnostic checklist (rows C4b–C4d) so we finally eliminate the pix0_z drift.
- docs/fix_plan.md:455 — Current Next Actions require refreshed per-φ evidence and a detector geometry table before Phase L3k progresses.
How-To Map:
- Set OUTDIR as shown in Do Now; keep each iteration under reports/2025-10-cli-flags/phase_l/parity_shim/.
- First command emits per_phi_pytorch.json; second command regenerates delta_metrics.json & diff_summary.md in the same OUTDIR.
- After scripts finish, append the geometry comparison table to reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md (note exact C vs Py values).
- Store sha256 sums via `shasum -a 256 "$OUTDIR"/* > "$OUTDIR"/sha256.txt` once artifacts land.
Pitfalls To Avoid:
- Do not edit production code; this loop is evidence-only.
- Preserve existing traces; never overwrite reports/2025-10-cli-flags/phase_l/parity_shim/20251008T021659Z/.
- Keep tensors on their original device when running scripts (no `.cpu()` hacks).
- Respect Protected Assets in docs/index.md (no moves/deletes of loop.sh, supervisor.sh, input.md).
- Avoid rerunning full pytest; collect-only is sufficient this loop.
- Document any command failures immediately in attempts history before rerunning.
- Use UTC timestamps for new report directories.
- Ensure KMP_DUPLICATE_LIB_OK is set for every torch script.
Pointers:
- plans/active/cli-phi-parity-shim/plan.md:86
- docs/fix_plan.md:455
- reports/2025-10-cli-flags/phase_l/parity_shim/20251008T023956Z/diff_summary.md
- reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md
Next Up:
- CLI-FLAGS-003 L3k.3c.5 — update documentation/tests once Δk ≤ 1e-6 and traces are green.
