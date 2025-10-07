Summary: Capture φ=0 carryover evidence and prep the remediation plan for CLI-FLAGS-003 before simulator edits.
Mode: Parity
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/diagnosis.md; reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/delta_metrics.json; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/compare_latest.txt; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/delta_by.txt
Do Now: CLI-FLAGS-003 (Handle -nonoise and -pix0_vector_mm) — execute Phase L3k.3c.2 by running `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/compare_per_phi_traces.py reports/2025-10-cli-flags/phase_l/per_phi/reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/trace_py_rot_vector_20251123_per_phi.json reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/c_trace_phi_20251123.log`, compute Δb_y with the helper snippet below, then record both deltas in `diagnosis.md` and `fix_checklist.md` before touching simulator code.
If Blocked: Re-run the supervisor harness from `commands.txt` to regenerate traces, capture stdout/stderr, and log the failure plus partial artifacts in Attempts History; rerun `compare_per_phi_traces.py` once files exist.

Priorities & Rationale:
- docs/fix_plan.md:460 — Next Actions explicitly require Δk and Δb_y documentation ahead of Phase L3k.3c.3.
- plans/active/cli-noise-pix0/plan.md:295 — Phase L3k.3b marked [D]; current row gates VG-1 evidence before implementation work.
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/comparison_stdout_20251123.txt:1 — Source of the Δk=1.8116×10⁻² measurement that must be cited verbatim.
- scripts/compare_per_phi_traces.py:1 — Tool handles both trace schemas; reuse it instead of crafting ad-hoc diffs.
- reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md:82 — Section awaiting concrete Δb_y/Δk entries and remediation outline.
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/phi0_state_analysis.md:1 — Prior φ₀ analysis needs refresh with coeval C trace.
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/commands.txt:1 — Canonical repro steps; reuse rather than inventing new invocation syntax.
- docs/development/testing_strategy.md:132 — VG-1 tolerances (≤1e-6) referenced when framing the remediation target.
- docs/architecture/pytorch_design.md:215 — Vectorization strategy section guides the carryover design notes.
- docs/debugging/debugging.md:40 — Parallel trace workflow to cite in diagnosis when summarizing evidence.

How-To Map:
- Ensure working dir is repo root; set `export KMP_DUPLICATE_LIB_OK=TRUE` for shell session handling torch.
- `ls reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123` (sanity check that expected files are present before adding new ones).
- PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/compare_per_phi_traces.py   reports/2025-10-cli-flags/phase_l/per_phi/reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/trace_py_rot_vector_20251123_per_phi.json   reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/c_trace_phi_20251123.log   | tee reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/compare_latest.txt
- `tail -n +1 reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/compare_latest.txt` (quickly confirm φ₀ DIVERGE and recorded Δk).
- python - <<'PY_SNIPPET'
from pathlib import Path
import re
c_log = Path('reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/c_trace_phi_20251123.log')
py_probe = Path('reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/rot_vector_state_probe.log')
py_val = None
for line in py_probe.read_text().splitlines():
    if line.startswith('rot_b_phi0_y'):
        py_val = float(line.split()[1])
        break
if py_val is None:
    raise SystemExit('rot_b_phi0_y missing in rot_vector_state_probe.log')
pattern = re.compile(r'TRACE_C: rot_b_angstroms [^ ]+ ([^ ]+) [^ ]+')
for line in c_log.read_text().splitlines():
    if 'TRACE_C: rot_b_angstroms' in line:
        match = pattern.search(line)
        if match:
            c_val = float(match.group(1))
            break
else:
    raise SystemExit('TRACE_C rot_b_angstroms missing for φ₀ in C log')
delta = py_val - c_val
print(f'Delta_b_y = {delta:.12f}')
with open('reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/delta_by.txt', 'w') as f:
    f.write(f'Delta_b_y = {delta:.12f}
')
PY_SNIPPET
- `cat reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/delta_by.txt` (verify sign and magnitude before documenting).
- Append Δk and Δb_y values with context (units, tolerance gap, tracing reference) to reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/diagnosis.md under the L3k.3c.2 subsection.
- Update reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md VG-1.4 row: mark evidence captured, cite compare_latest.txt and delta_by.txt, include remediation outline (carryover via cached φ_{last}).
- `shasum -a 256 reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/*.txt >> reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/sha256.txt` (append new hashes; keep chronological).
- env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q > reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/pytest_collect.log
- Append Attempt entry in docs/fix_plan.md (L3k.3c.2) summarising measurements, artifacts, and remediation plan pointer.
- `git status --short reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123` (ensure only intended files changed before commit later).

Pitfalls To Avoid:
- Do not edit simulator or crystal code paths during this evidence loop.
- Keep all newly generated files inside `base_vector_debug/20251123/`; do not scatter outputs elsewhere.
- Maintain JSON/Markdown structure when editing diagnosis.md and fix_checklist.md; tooling expects specific headings.
- No `.cpu()` / `.cuda()` shims in helper snippets—stick to pure Python math for analysis.
- Do not overwrite delta_metrics.json; if commentary required, place it in diagnosis.md instead.
- Avoid deleting or renaming anything referenced in docs/index.md (Protected Assets rule).
- Skip running nb-compare until VG-1 is green; Phase L3k.3d depends on carryover fix first.
- Preserve vectorization guidance (docs/architecture/pytorch_design.md) when describing remediation; no endorsement of Python loops.
- When logging Attempt updates, follow numbering and include Δk/Δb_y metrics plus artifact paths.
- Retain KMP_DUPLICATE_LIB_OK=TRUE for every torch-based command to avoid MKL crashes.
- Do not commit partial documentation edits; batch updates after all deltas captured.
- Append to commands.txt rather than rewriting previous history to preserve provenance.
- Validate delta_by.txt before citing values; rerun snippet if sign looks wrong.
- Make sure compare_latest.txt is referenced in fix_checklist.md so reviewers can reproduce.
- Confirm pytest collect output is archived; guards against hidden import regressions.
- Keep sha256.txt entries sorted chronologically to avoid confusion for future diffs.
- Avoid mixing CRLF endings in updated text files; stick to LF for repo consistency.
- Refrain from editing plan tables outside the scoped rows; maintain formatting to avoid merge pain.
- Note units explicitly (Å) when recording Δb_y to prevent ambiguity.

Pointers:
- specs/spec-a-cli.md:1 — Canonical CLI flag semantics and precedence.
- docs/architecture/pytorch_design.md:200 — Vectorization requirements for φ rotation and carryover handling.
- docs/development/testing_strategy.md:132 — VG-1 thresholds and evidence expectations.
- docs/fix_plan.md:460 — Current Next Actions for CLI-FLAGS-003.
- plans/active/cli-noise-pix0/plan.md:295 — Phase L3k status table with exit criteria.
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/comparison_stdout_20251123.txt:1 — Latest Δk printout for citation.
- scripts/compare_per_phi_traces.py:1 — Implementation reference for the comparison tool.
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/c_trace_phi_20251123.log:1 — Ground-truth source for C rot_b values.
- docs/debugging/debugging.md:38 — Parallel trace comparison SOP to reference when summarising evidence.
- docs/index.md:1 — Protected assets list to consult before touching shared files.

Next Up:
- 1. Phase L3k.3c.3 — Implement φ==0 carryover in `Crystal.get_rotated_real_vectors`, regenerate traces, and drive VG-1 to green.
- 2. Phase L3k.3d — Re-run nb-compare ROI analysis once φ carryover fix lands and documentation is closed.
- 3. Phase L3k.4 — Log full attempt metrics and prep Phase L4 supervisor command rerun after parity holds.
- 4. Phase L4 — Re-execute the supervisor command end-to-end once VG-1/VG-3/VG-4 checklists are satisfied.

Support Notes:
- Keep galph_memory.md updated after each loop with artifact paths and open questions.
- Mention any anomalies (e.g., script schema mismatches) in Attempts History so future loops know context.
- Reserve commits for bundled documentation updates; avoid piecemeal git noise while evidence is in flux.
- Confirm timestamps on new artifacts follow YYYYMMDD format to stay aligned with existing structure.
- If CUDA smoke becomes necessary later, remember to capture `nvidia-smi` snapshot alongside logs.
