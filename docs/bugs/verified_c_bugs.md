# Verified `nanoBragg.c` Bugs (2025-10)

## Severity Overview
- **High:** C-IMPL-BUG-002, C-DESIGN-FLAW-001, C-DESIGN-FLAW-003, NANO-C-BUG-001, NANO-C-BUG-002
- **Medium:** C-DESIGN-FLAW-002, C-DESIGN-FLAW-005, C-PARITY-001
- **Low:** C-LOGGING-BUG-001

Artifact logs for the reproductions below live under `docs/bugs/artifacts/`.

---

### C-IMPL-BUG-002 — Incorrect Angle Units in `mosaic_rotation_umat` (High)
**Summary:** The random misset path feeds `90.0` (degrees) into `mosaic_rotation_umat`, but the helper interprets angles in radians. The code therefore constructs rotation matrices using a 90-radian cap (≈5156°), which produces non-physical orientations.

**Reproduction:**
```bash
./golden_suite_generator/nanoBragg \
  -cell 50 60 70 80 90 100 \
  -misset random \
  -default_F 1 -N 0 \
  -distance 100 -detpixels 4 -pixel 0.1 \
  -floatfile /tmp/bug_float.bin -intfile /tmp/bug_int.img -noisefile /tmp/bug_noise.img \
  -nopgm -nonoise -noprogress > docs/bugs/artifacts/c-impl-bug-002.txt
```
The log (`docs/bugs/artifacts/c-impl-bug-002.txt`) shows `random orientation misset angles` emitted immediately after the `-misset random` option is processed.

**Relevant code:**
- `golden_suite_generator/nanoBragg.c:2083` — calls `mosaic_rotation_umat(90.0, …)` with degrees.
- `golden_suite_generator/nanoBragg.c:3795` – `rot = mosaicity * powf(...)` is consumed by `sin`/`cos` as radians.

---

### C-DESIGN-FLAW-001 — Convention Switches to CUSTOM on Vector Overrides (High)
**Summary:** Supplying any detector-direction override (e.g., `-fdet_vector`, `-twotheta_axis`) forces `beam_convention = CUSTOM`. This bypasses MOSFLM’s `+0.5` pixel beam-centre adjustment and shifts `Fbeam/Sbeam` by half a pixel.

**Reproduction:**
```bash
# MOSFLM defaults
./golden_suite_generator/nanoBragg -cell 70 80 90 90 90 90 -default_F 1 -N 0 \
  -distance 100 -detpixels 4 -pixel 0.1 \
  -floatfile /tmp/d1_float.bin -intfile /tmp/d1_int.img -noisefile /tmp/d1_noise.img \
  -nopgm -nonoise -noprogress > docs/bugs/artifacts/design-flaw-001-base.txt

# Same geometry but explicit vectors
./golden_suite_generator/nanoBragg -cell 70 80 90 90 90 90 -default_F 1 -N 0 \
  -distance 100 -detpixels 4 -pixel 0.1 \
  -fdet_vector 0 0 1 -sdet_vector 0 -1 0 -odet_vector 1 0 0 \
  -floatfile /tmp/d2_float.bin -intfile /tmp/d2_int.img -noisefile /tmp/d2_noise.img \
  -nopgm -nonoise -noprogress > docs/bugs/artifacts/design-flaw-001-custom.txt
```
`docs/bugs/artifacts/design-flaw-001-base.txt` reports `Fbeam=0.0003`, while the custom-vector run drops to `Fbeam=0.0002`, confirming the implicit convention switch.

**Relevant code:**
- `golden_suite_generator/nanoBragg.c:691-739` — any detector-vector flag forces `beam_convention = CUSTOM`.
- `golden_suite_generator/nanoBragg.c:1210-1222` — MOSFLM adds `+0.5*pixel_size` to `Fbeam/Sbeam`, behaviour lost once the convention flips.

---

### C-DESIGN-FLAW-003 — `-pix0_vector(_mm)` Rewrites Beam Centre (High)
**Summary:** Providing a `pix0_vector` causes the geometry stage to recompute `Fbeam/Sbeam` from that vector, silently overriding `-Xbeam/-Ybeam`. This occurs even when other detector vectors are customised.

**Reproduction:**
```bash
# Beam centre set via -Xbeam/-Ybeam only
./golden_suite_generator/nanoBragg -cell 70 80 90 90 90 90 -default_F 1 -N 0 \
  -distance 100 -detpixels 4 -pixel 0.1 \
  -Xbeam 0.12 -Ybeam 0.13 \
  -floatfile /tmp/pre_a_float.bin -intfile /tmp/pre_a_int.img -noisefile /tmp/pre_a_noise.img \
  -nopgm -nonoise -noprogress > docs/bugs/artifacts/nano-c-bug-002-base.txt

# Same command with pix0 override
./golden_suite_generator/nanoBragg -cell 70 80 90 90 90 90 -default_F 1 -N 0 \
  -distance 100 -detpixels 4 -pixel 0.1 \
  -Xbeam 0.12 -Ybeam 0.13 -pix0_vector_mm 0.5 0.1 120 \
  -floatfile /tmp/pre_b_float.bin -intfile /tmp/pre_b_int.img -noisefile /tmp/pre_b_noise.img \
  -nopgm -nonoise -noprogress > docs/bugs/artifacts/nano-c-bug-002-override.txt
```
`docs/bugs/artifacts/nano-c-bug-002-base.txt` shows `Fbeam=0.00018`, whereas the override run drops to `Fbeam=0.00012`, demonstrating the precedence of `pix0_vector`.

**Relevant code:**
- `golden_suite_generator/nanoBragg.c:740-746` — CLI parser stores the raw vector.
- `golden_suite_generator/nanoBragg.c:1901-1927` — geometry re-derives `pix0_vector` from `Fbeam/Sbeam`, effectively re-basing the direct beam.

---

### NANO-C-BUG-001 — `_mm` Suffix Ignores Unit Conversion (High)
**Summary:** The `_mm` variant is parsed by the same branch as `-pix0_vector`, so values are treated as metres. Users expecting millimetre input must still convert manually.

**Reproduction:**
```bash
./golden_suite_generator/nanoBragg -cell 70 70 70 90 90 90 -default_F 1 -N 0 \
  -distance 100 -detpixels 2 -pixel 0.1 \
  -pix0_vector_mm 0 0 200 \
  -floatfile /tmp/pix0_float.bin -intfile /tmp/pix0_int.img -noisefile /tmp/pix0_noise.img \
  -nopgm -nonoise -noprogress > docs/bugs/artifacts/nano-c-bug-001b.txt
```
Despite the `_mm` suffix, `docs/bugs/artifacts/nano-c-bug-001b.txt` reports `DETECTOR_PIX0_VECTOR 0.1 0.0001 -0.0001`, matching a 0.1 m placement—the supplied value was treated as metres.

**Relevant code:**
- `golden_suite_generator/nanoBragg.c:740-746` — no `_mm` detection or scaling before storing the coordinates.

---

### NANO-C-BUG-002 — Undocumented Beam-Centre Override (High)
**Summary:** The `pix0_vector` override recalculates `Fbeam/Sbeam`, so any beam-centre determined via `-Xbeam/-Ybeam` or detector conventions is superseded silently.

**Reproduction:** See the paired commands in the C-DESIGN-FLAW-003 section. The same artefacts (`nano-c-bug-002-base.txt` / `nano-c-bug-002-override.txt`) show the shift from `Fbeam=0.00018` to `0.00012`.

**Relevant code:**
- `golden_suite_generator/nanoBragg.c:1901-1927` — `pix0_vector` recomputed from `Fbeam/Sbeam`, affecting subsequent geometry.
- `golden_suite_generator/nanoBragg.c:1930-1939` — derived origins (XDS/DIALS) now align with the recomputed values, not the original inputs.

---

### C-DESIGN-FLAW-002 — Implicit Detector Pivot Selection (Medium)
**Summary:** CLI arguments such as `-xds`, `-Xclose`, or `-twotheta` overwrite `detector_pivot`, switching between BEAM and SAMPLE without notice. Slight command changes therefore alter the geometry pathway.

**Reproduction:**
```bash
# Default: BEAM pivot
./golden_suite_generator/nanoBragg -cell 70 80 90 90 90 90 -default_F 1 -N 0 \
  -distance 100 -detpixels 4 -pixel 0.1 \
  -floatfile /tmp/pivot_default.bin -intfile /tmp/pivot_default.img -noisefile /tmp/pivot_default_noise.img \
  -nopgm -nonoise -noprogress > docs/bugs/artifacts/design-flaw-001-base.txt

# Switching to XDS toggles SAMPLE pivot
./golden_suite_generator/nanoBragg -cell 70 80 90 90 90 90 -default_F 1 -N 0 \
  -distance 100 -detpixels 4 -pixel 0.1 -xds \
  -floatfile /tmp/pivot_xds.bin -intfile /tmp/pivot_xds.img -noisefile /tmp/pivot_xds_noise.img \
  -nopgm -nonoise -noprogress > docs/bugs/artifacts/design-flaw-002-xds.txt
```
The second log begins with `pivoting detector around sample`, confirming the hidden mode flip.

**Relevant code:**
- `golden_suite_generator/nanoBragg.c:631-789` — individual flags mutate `detector_pivot` in different directions.
- `golden_suite_generator/nanoBragg.c:1736-1907` — pivot choice determines which geometry branch runs.

---

### C-DESIGN-FLAW-005 — Silent HKL Cache (`Fdump.bin`) Reuse (Medium)
**Summary:** When `-hkl` is omitted, the simulator silently loads `Fdump.bin` from the working directory, reusing cached structure factors without informing the user.

**Reproduction:**
```bash
# First run: generates Fdump.bin
./golden_suite_generator/nanoBragg -cell 70 70 70 90 90 90 \
  -hkl docs/bugs/artifacts/test_small.hkl -N 0 \
  -distance 100 -detpixels 2 -pixel 0.1 \
  -floatfile /tmp/cache_float.bin -intfile /tmp/cache_int.img -noisefile /tmp/cache_noise.img \
  -nopgm -nonoise -noprogress > docs/bugs/artifacts/design-flaw-005-with-hkl.txt

# Second run: no -hkl, automatically reads the cache
./golden_suite_generator/nanoBragg -cell 70 70 70 90 90 90 -N 0 \
  -distance 100 -detpixels 2 -pixel 0.1 \
  -floatfile /tmp/cache2_float.bin -intfile /tmp/cache2_int.img -noisefile /tmp/cache2_noise.img \
  -nopgm -nonoise -noprogress > docs/bugs/artifacts/design-flaw-005-no-hkl.txt
```
The follow-up log contains `reading Fs from Fdump.bin`, demonstrating the implicit dependency.

**Relevant code:**
- `golden_suite_generator/nanoBragg.c:1297-1304` — attempts to open `Fdump.bin` whenever `-hkl` is absent.
- `golden_suite_generator/nanoBragg.c:2355-2368` — rehydrates the cached structure factors silently.

---

### C-PARITY-001 — φ=0 Uses Stale Crystal Vectors (Medium)
**Summary:** Inside the φ loop, the rotated vectors `ap/bp/cp` are only updated when `phi != 0.0`; otherwise, they retain the previous state (often from the prior pixel's final φ step). This produces step-0 Miller fractions that mirror the previous pixel rather than the unrotated lattice.

**Reproduction:**
```bash
./golden_suite_generator/nanoBragg -cell 70 70 70 90 90 90 -default_F 1 -N 2 \
  -distance 100 -detpixels 4 -pixel 0.1 \
  -phi 0 -osc 0.09 -phisteps 10 -trace_pixel 0 0 \
  -floatfile /tmp/phi_float.bin -intfile /tmp/phi_int.img -noisefile /tmp/phi_noise.img \
  -nopgm -nonoise -noprogress > docs/bugs/artifacts/c-parity-001.txt
```
The trace (`docs/bugs/artifacts/c-parity-001.txt`) includes a single `TRACE_C: hkl_frac …` entry, regardless of φ step, confirming that the φ=0 pass reused the rotated vectors. Comparing successive pixels reveals identical `k_frac` values at φ=0 and the terminal φ step.

**PyTorch Parity Shim (Historical):**
- The PyTorch implementation **previously** provided an opt-in emulation of this C bug via `--phi-carryover-mode c-parity` (removed in commit 340683f, October 2025)
- **Current behavior**: PyTorch uses spec-compliant fresh rotations exclusively (no carryover mode available)
- **Historical c-parity mode tolerance**: |Δk_frac| ≤ 5e-5, |Δb_y| ≤ 1e-4 (relaxed to document C bug behavior)
- **Current spec mode tolerance**: |Δk_frac| ≤ 1e-6, |Δb_y| ≤ 1e-6 (strict, normative)
- Dtype sensitivity analysis (2025-12-01) confirmed the ~2.8e-05 plateau was intrinsic to the carryover logic, not precision-limited
- Evidence: `reports/2025-10-cli-flags/phase_l/parity_shim/20251201_dtype_probe/analysis_summary.md`
- **Removal Status (2025-10-08)**: CLI flag removed (commit 340683f); config/model plumbing removal in progress per `plans/active/phi-carryover-removal/plan.md`. Documentation sync: `reports/2025-10-cli-flags/phase_phi_removal/phase_b/`

**Relevant code:**
- `golden_suite_generator/nanoBragg.c:3042-3059` — rotation only applied when `phi != 0.0`; no reset path exists.
- `golden_suite_generator/nanoBragg.c:2793-2807` — `ap/bp/cp` are captured by `firstprivate`, so stale state flows into the next pixel.
- `src/nanobrag_torch/models/crystal.py:1084-1128` — PyTorch opt-in carryover shim (batched implementation)

---

### C-LOGGING-BUG-001 — Beam-Centre Trace Reports Wrong Units (Low)
**Summary:** The debug trace divides metre-valued beam centres by 1000 but labels the output as metres, yielding misleading logs.

**Reproduction:** Any of the preceding commands will show the issue; for example `docs/bugs/artifacts/design-flaw-001-base.txt` contains:
```
TRACE_C:beam_center_m=X:2.5e-07 Y:2.5e-07 pixel_mm:0.1
```
Here `Xbeam`/`Ybeam` were already metres (2.5 × 10⁻⁴), but the trace prints values divided by 1000.

**Relevant code:**
- `golden_suite_generator/nanoBragg.c:1845-1846` — divides by `1000.0` while labelling the output in metres.

---

## Suggested Next Steps
1. Convert `mosaic_rotation_umat` to accept degrees explicitly (or convert at the call sites) and add a regression test for random misset coverage.
2. Emit CLI warnings whenever convention, pivot, or beam centre is changed implicitly; consider requiring explicit overrides for conflicting parameters.
3. Honour the `_mm` suffix by applying millimetre-to-metre scaling and document the precedence hierarchy for beam-centre configuration.
4. Reset `ap/bp/cp` when `phi == 0.0` so the first φ slice uses the unrotated lattice.
5. Fix trace logging units to avoid future debugging confusion.
