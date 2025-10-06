timestamp: 2025-10-06 06:22:50Z
commit: 15fdec5
author: galph
Active Focus: [CLI-FLAGS-003] Phase H3 lattice mismatch diagnosis

Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — run `env KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py > reports/2025-10-cli-flags/phase_h/trace_py_after_H3.log 2> reports/2025-10-cli-flags/phase_h/trace_py_after_H3.stderr`; finish with `pytest --collect-only -q`
If Blocked: Capture the failing stdout/stderr, append a short note to `reports/2025-10-cli-flags/phase_h/attempt_log.txt`, and diff against `trace_py_after_H2.log` to pinpoint where execution diverged before asking for guidance.

Priorities & Rationale:
- docs/fix_plan.md:448 — Next actions call for confirming the `(h-h0)` usage before any simulator edits.
- plans/active/cli-noise-pix0/plan.md:100 — Phase H3 checklist now requires a manual `sincg` reproduction and hypothesis log.
- reports/2025-10-cli-flags/phase_h/trace_comparison_after_H2.md:1 — Existing trace diff highlights the `F_latt` magnitude gap we must quantify.
- reports/2025-10-cli-flags/phase_h/implementation_notes.md:1 — Hypotheses already point at the `sincg` argument order; extend this with today’s evidence.
- golden_suite_generator/nanoBragg.c:3063 — Canonical formula uses absolute `h/k/l`; reproduce these numbers for our comparison.
- src/nanobrag_torch/simulator.py:218 — Current PyTorch path feeds `(h-h0)` into `sincg`; verify this is the culprit before touching code.

How-To Map:
- `env KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py > reports/2025-10-cli-flags/phase_h/trace_py_after_H3.log 2> reports/2025-10-cli-flags/phase_h/trace_py_after_H3.stderr` — regenerate the PyTorch trace with the post-H2 wiring; keep stderr for run metadata.
- `python - <<'PY'` (see below) → pipe output to `reports/2025-10-cli-flags/phase_h/manual_sincg.md` to compute `sincg` for the exact `h,k,l` tuples from the C trace and compare against PyTorch results:
  ```python
  import torch
  h = torch.tensor(2.001203, dtype=torch.float64)
  k = torch.tensor(1.992798, dtype=torch.float64)
  l = torch.tensor(-12.990767, dtype=torch.float64)
  Na, Nb, Nc = (36, 47, 29)
  from nanobrag_torch.utils.physics import sincg
  vals = {
      'C_expected': (35.889, 38.632, 25.702),
      'Py_current': (
          float(sincg(torch.pi * (h - torch.round(h)), torch.tensor(Na)).item()),
          float(sincg(torch.pi * (k - torch.round(k)), torch.tensor(Nb)).item()),
          float(sincg(torch.pi * (l - torch.round(l)), torch.tensor(Nc)).item()),
      ),
      'Py_with_absolute': (
          float(sincg(torch.pi * h, torch.tensor(Na)).item()),
          float(sincg(torch.pi * k, torch.tensor(Nb)).item()),
          float(sincg(torch.pi * l, torch.tensor(Nc)).item()),
      ),
  }
  for key, triplet in vals.items():
      print(key, ':', ', '.join(f'{x:.6f}' for x in triplet))
  PY
  ```
- Update `reports/2025-10-cli-flags/phase_h/implementation_notes.md` with a new “2025-10-06” block summarising the manual `sincg` findings, the confirmed root cause, and the proposed fix/test plan; note the filenames you produced and any follow-on questions.
- `pytest --collect-only -q` — ensure collection still passes after evidence gathering; stash the log under `reports/2025-10-cli-flags/phase_h/pytest_collect.log`.

Pitfalls To Avoid:
- Do not modify simulator code yet; today is evidence-only per Phase H3.
- Keep all new artifacts under `reports/2025-10-cli-flags/phase_h/` to preserve trace lineage.
- Avoid reintroducing manual beam overrides in the harness; rely on CLI wiring now that H2 landed.
- Maintain float64 tensors in scratch scripts so comparisons stay numerically stable.
- Do not delete or rename any files listed in `docs/index.md` (Protected Assets rule).
- Skip ad-hoc snippets outside `reports/…`; no temp files in repo root.
- Preserve device/dtype neutrality in any helper code (no `.cpu()`/`.item()` on critical tensors).
- If you need to re-run the harness, clean up old logs or suffix them clearly; no silent overwrites.
- Keep the loop evidence-only—no commits or merges until we agree on the fix plan.
- Continue logging attempts in `reports/2025-10-cli-flags/phase_h/attempt_log.txt` after each major action.

Pointers:
- docs/fix_plan.md:448 — Current status and next actions for `[CLI-FLAGS-003]`.
- plans/active/cli-noise-pix0/plan.md:91 — Phase H tasks and exit criteria.
- reports/2025-10-cli-flags/phase_h/trace_py_after_H2.log:1 — Last PyTorch trace for comparison.
- reports/2025-10-cli-flags/phase_h/trace_comparison_after_H2.md:1 — Prior diff to baseline your notes.
- reports/2025-10-cli-flags/phase_h/implementation_notes.md:1 — Append today’s findings here.
- src/nanobrag_torch/simulator.py:218 — Location of the current lattice factor calculation.
- golden_suite_generator/nanoBragg.c:3063 — Reference sincg usage (`sincg(M_PI*h, Na)`).

Next Up:
- Queue Phase H4 parity rerun after the lattice fix plan is agreed (still within `[CLI-FLAGS-003]`).
- Prep Phase A baselines for `[VECTOR-TRICUBIC-001]` once CLI parity evidence is captured.
