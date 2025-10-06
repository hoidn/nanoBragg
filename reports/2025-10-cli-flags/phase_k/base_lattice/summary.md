======================================================================
Phase K3f3: Base Lattice Trace Comparison
======================================================================
C trace:  /home/ollie/Documents/tmp/nanoBragg/reports/2025-10-cli-flags/phase_k/base_lattice/c_stdout.txt
Py trace: /home/ollie/Documents/tmp/nanoBragg/reports/2025-10-cli-flags/phase_k/base_lattice/trace_py.log

======================================================================
RECIPROCAL VECTORS (Å⁻¹, λ-scaled)
======================================================================
  a_star: DIVERGE
    C:      [-0.0290511, -0.0293959, 0.0107499]
    Py:     [-1.177003215, -1.190972323, 0.435530564]
    Delta:  [1.147952115, 1.161576423, 0.424780664] (max=1.161576423)
    Ratio:  [40.51492766, 40.51491273, 40.51484795]

  b_star: DIVERGE
    C:      [-0.00312639, 0.0104376, -0.0328567]
    Py:     [-0.126665578, 0.4228804311, -1.331186015]
    Delta:  [0.123539188, 0.4124428311, 1.298329315] (max=1.298329315)
    Ratio:  [40.5149639, 40.51510224, 40.51490305]

  c_star: DIVERGE
    C:      [0.0259604, -0.014333, -0.0106066]
    Py:     [1.051785607, -0.580701197, -0.4297262439]
    Delta:  [1.025825207, 0.566368197, 0.4191196439] (max=1.025825207)
    Ratio:  [40.51500004, 40.51497921, 40.51498538]


======================================================================
REAL-SPACE VECTORS (meters)
======================================================================
  a (real): DIVERGE
    C:      [-1.43563e-09, -2.18718e-09, -5.58202e-10]
    Py:     [-0.0005816432933, -0.0008861342451, -0.0002261552061]
    Delta:  [0.0005816418577, 0.0008861320579, 0.0002261546479] (max=0.0008861320579)
    Ratio:  [405148.4667, 405149.2082, 405149.4013]

  b (real): DIVERGE
    C:      [-1.14987e-09, 7.1732e-11, -2.91132e-09]
    Py:     [-0.0004658689445, 2.906217376e-05, -0.001179519977]
    Delta:  [0.0004658677946, 2.906210203e-05, 0.001179517066] (max=0.001179517066)
    Ratio:  [405149.2295, 405149.3582, 405149.5463]

  c (real): DIVERGE
    C:      [2.107e-09, -2.43893e-09, -9.75265e-10]
    Py:     [0.0008536476363, -0.0009881307294, -0.0003951280392]
    Delta:  [0.0008536455293, 0.0009881282905, 0.0003951270639] (max=0.0009881282905)
    Ratio:  [405148.3798, 405149.2783, 405149.4099]


======================================================================
CELL VOLUMES
======================================================================
  V_cell:
    C:      24682.3 m³
    Py:     1.641459882e-09 m³
    Delta:  24682.3
    Ratio:  6.650352204e-14

======================================================================
FIRST DIVERGENCE
======================================================================
First component exceeding 5e-4 tolerance: a_star

======================================================================
DIAGNOSIS
======================================================================
The first divergence is in a_star.

Key observations:
  - a_star magnitude ratio (Py/C): 40.514916
  - PyTorch reciprocal vectors are much larger than C (~40×)
  - This suggests λ-scaling is being applied incorrectly or twice
  - Check MOSFLM matrix reader and Crystal.compute_cell_tensors()
  - a (real) magnitude ratio (Py/C): 405149.003038
  - PyTorch real vectors are ~405149× larger than C
  - This cascades from the reciprocal vector error
======================================================================

-----------------------------------------------------------------------
2025-11-08 Update — MOSFLM rescale implementation check (Commit 46ba36b)
-----------------------------------------------------------------------
- Command: Inline `KMP_DUPLICATE_LIB_OK=TRUE python - <<'PY'` snippet (see `post_fix/cell_tensors_py.txt` for exact code and output).
- Results confirm PyTorch now matches C trace magnitudes pre-φ rotation:
  * Root cause (from 2025-10-06 analysis): `Crystal.compute_cell_tensors` kept V=1 Å³ when MOSFLM matrices were provided, inflating reciprocal vectors by 40×. Commit 46ba36b now recomputes V_star, V_cell, and real vectors from MOSFLM inputs before rebuilding duals.
  * V_cell = 24682.256630 Å³ (C trace 24682.3 Å³ → Δ=4.3e-5, 1.7e-6 relative)
  * |a| = 26.751388 Å, |b| = 31.309964 Å, |c| = 33.673354 Å (all within 5e-6 relative to C values)
  * |a*| = 0.042704 Å⁻¹ (reciprocal magnitudes align with C after recomputation)
- Evidence stored under `reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/cell_tensors_py.txt`.
- Next Step: Regenerate `trace_py.log` after rerunning the harness so the diff reflects the fixed vectors (Plan K3f4 exit criteria), then proceed to K3g3 normalization parity.
