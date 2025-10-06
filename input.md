timestamp: 2025-10-06 06:37:45Z
commit: ae4ac7f
author: galph
Active Focus: [CLI-FLAGS-003] Phase H3 lattice mismatch diagnosis
Summary: Prove the pix0-driven lattice divergence and log an evidence-backed fix plan before touching detector code.
Phase: Evidence
Focus: CLI-FLAGS-003
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2025-10-cli-flags/phase_h/trace_py_after_H3_refresh.log; reports/2025-10-cli-flags/phase_h/pix0_reproduction.md; reports/2025-10-cli-flags/phase_h/attempt_log.txt

Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — evidence: execute the trace harness + pix0 reproduction per How-To Map, then run `pytest --collect-only -q`.
If Blocked: Capture stdout/stderr for any failing command under `reports/2025-10-cli-flags/phase_h/blocked/` and diff against the prior attempt before escalating.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:105 — Phase H3 now requires a C-style pix0 reconstruction plus restored attempt log before implementation.
- docs/fix_plan.md:472 — Next Actions call for demonstrating the ~1.14 mm pix0 delta and propagating it through to h/k/l.
- reports/2025-10-cli-flags/phase_h/implementation_notes.md:54 — Latest entry flags Miller index divergence but leaves the detector fix plan blank.
- reports/2025-10-cli-flags/phase_h/trace_py_after_H3.log:1 — Current trace still reflects the mismatched pix0; we need a refreshed run tied to today’s evidence.
- docs/development/testing_strategy.md:1 — Authoritative commands doc; keep `pytest --collect-only -q` as the validation touchpoint for evidence loops.

How-To Map:
- Export the authoritative commands doc before running anything: `export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md`.
- Trace refresh (store stderr for provenance):
  `env KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py > reports/2025-10-cli-flags/phase_h/trace_py_after_H3_refresh.log 2> reports/2025-10-cli-flags/phase_h/trace_py_after_H3_refresh.stderr`
- Pix0 + lattice reproduction (captures both raw override and C formula) — pipe output to the Markdown evidence file:
  ```bash
  python - <<'PY' > reports/2025-10-cli-flags/phase_h/pix0_reproduction.md
  import torch, math

  mm_to_m = 1e-3
  pixel_size_mm = 0.172
  distance_mm = 231.274660
  xbeam_mm = 217.742295
  ybeam_mm = 213.907080
  target_fast = 685
  target_slow = 1039
  wavelength_A = 0.9768

  fdet = torch.tensor([0.999982004873912, -0.00599800002923425, -0.000118000000575132], dtype=torch.float64)
  sdet = torch.tensor([-0.0059979996566955, -0.999969942765222, -0.0049129997187971], dtype=torch.float64)
  beam = torch.tensor([0.000513879494092498, 0.0, -0.999999867963924], dtype=torch.float64)

  pix0_override_m = torch.tensor([-216.336293, 215.205512, -230.200866], dtype=torch.float64) * mm_to_m
  Fbeam_m = xbeam_mm * mm_to_m
  Sbeam_m = ybeam_mm * mm_to_m
  distance_m = distance_mm * mm_to_m
  pix0_c_m = -Fbeam_m * fdet - Sbeam_m * sdet + distance_m * beam

  pixel_size_m = pixel_size_mm * mm_to_m
  center_fast = (target_fast + 0.5) * pixel_size_m
  center_slow = (target_slow + 0.5) * pixel_size_m
  pixel_py = pix0_override_m + center_slow * sdet + center_fast * fdet
  pixel_c = pix0_c_m + center_slow * sdet + center_fast * fdet

  def scattering_and_hkl(pixel_vec, label):
      coords_ang = pixel_vec * 1e10
      diffracted_unit = coords_ang / coords_ang.norm()
      scattering = (diffracted_unit - beam) / wavelength_A
      a_vec = torch.tensor([-14.3562690335399, -21.8805340763623, -5.5476578307123], dtype=torch.float64)
      b_vec = torch.tensor([-11.4986968432508, 0.671588233999813, -29.1143056268565], dtype=torch.float64)
      c_vec = torch.tensor([21.0699500320179, -24.4045855811067, -9.7143290320006], dtype=torch.float64)
      h = torch.dot(scattering, a_vec).item()
      k = torch.dot(scattering, b_vec).item()
      l = torch.dot(scattering, c_vec).item()
      return scattering, (h, k, l)

  scattering_py, hkl_py = scattering_and_hkl(pixel_py, "Py override")
  scattering_c, hkl_c = scattering_and_hkl(pixel_c, "C formula")

  def fmt(vec):
      return ', '.join(f"{v:.12f}" for v in vec)

  print("# Pix0 + Lattice Reproduction")
  print("pix0_override_m:", fmt(pix0_override_m))
  print("pix0_c_formula_m:", fmt(pix0_c_m))
  diff = pix0_c_m - pix0_override_m
  print("pix0_delta_m:", fmt(diff))
  print("\n## Pixel positions (meters)")
  print("pixel_py:", fmt(pixel_py))
  print("pixel_c:", fmt(pixel_c))
  print("pixel_delta:", fmt(pixel_c - pixel_py))
  print("\n## Scattering vectors (1/Å)")
  print("scattering_py:", fmt(scattering_py))
  print("scattering_c:", fmt(scattering_c))
  print("scattering_delta:", fmt(scattering_c - scattering_py))
  print("\n## Miller indices (fractional)")
  print("hkl_py:", ', '.join(f"{v:.12f}" for v in hkl_py))
  print("hkl_c:", ', '.join(f"{v:.12f}" for v in hkl_c))
  print("hkl_delta:", ', '.join(f"{(c - p):.12f}" for p, c in zip(hkl_py, hkl_c)))

  # Quick sincg check for completeness
  def sincg(arg, n):
      arg = torch.tensor(arg, dtype=torch.float64)
      n = torch.tensor(float(n), dtype=torch.float64)
      return torch.where(arg == 0, n, torch.sin(arg * n) / torch.sin(arg))

  Na, Nb, Nc = 36, 47, 29
  import math
  pi = math.pi
  for label, hkl in ("py", hkl_py), ("c", hkl_c):
      ha, ka, la = hkl
      Fa = sincg(pi * (ha - round(ha)), Na)
      Fb = sincg(pi * (ka - round(ka)), Nb)
      Fc = sincg(pi * (la - round(la)), Nc)
      print(f"\nF_latt components ({label}): {Fa.item():.6f}, {Fb.item():.6f}, {Fc.item():.6f}")
  PY
  ```
- Restore the attempt log by overwriting `reports/2025-10-cli-flags/phase_h/attempt_log.txt` with a concise Attempt #21 entry summarising today’s evidence (remove the stray pytest output before committing anything).
- Append a 2025-10-06 section to `reports/2025-10-cli-flags/phase_h/implementation_notes.md` capturing the quantified pix0/pixel/scattering deltas and outlining the detector override fix you plan to implement next loop.
- Validation touchpoint: `pytest --collect-only -q > reports/2025-10-cli-flags/phase_h/pytest_collect_refresh.log`

Pitfalls To Avoid:
- Stay evidence-only; no code or config edits while Phase H3 remains open.
- Do not overwrite prior trace artifacts—use the `_refresh` suffixes above.
- Keep all scratch outputs under `reports/2025-10-cli-flags/phase_h/`; no repo-root temp files.
- Maintain float64 throughout the reproduction script (no `.float()` shortcuts).
- Set `AUTHORITATIVE_CMDS_DOC` before running commands to comply with testing SOP.
- Ensure attempt_log.txt is human-readable (summary + metrics); never paste raw pytest output again.
- Avoid running broader pytest suites; `--collect-only -q` is the sole test this loop.
- No manual beam overrides in the harness—rely on CLI wiring now that H2 landed.
- Preserve Protected Assets listed in docs/index.md (do not rename/remove input.md, loop.sh, etc.).
- Keep git tree clean at end; evidence artifacts must be committed with this memo.

Pointers:
- docs/development/testing_strategy.md:1 — Authoritative commands + evidence-only loop guidance.
- docs/debugging/debugging.md:18 — Parallel trace SOP to contextualise today’s trace refresh.
- plans/active/cli-noise-pix0/plan.md:95 — Phase H checklist with the new pix0 reproduction requirement.
- docs/fix_plan.md:448 — `[CLI-FLAGS-003]` entry housing Next Actions and attempt history.
- reports/2025-10-cli-flags/phase_h/trace_comparison_after_H2.md:1 — Prior diff highlighting pix0 as the first divergence (use as baseline).

Next Up:
- After the detector pix0 fix plan is locked, schedule Phase H4 parity rerun (still `[CLI-FLAGS-003]`).
