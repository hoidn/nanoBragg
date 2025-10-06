/home/ollie/Documents/tmp/nanoBragg/reports/2025-10-cli-flags/phase_k/f_latt_fix/mosflm_rescale.py:84: UserWarning: Using torch.cross without specifying the dim arg is deprecated.
Please either pass the dim explicitly or simply use torch.linalg.cross.
The default value of dim will change to agree with that of linalg.cross in a future release. (Triggered internally at /pytorch/aten/src/ATen/native/Cross.cpp:63.)
  b_cross_c = torch.cross(b_star_t, c_star_t)
================================================================================
MOSFLM Lattice Vector Rescaling Comparison
================================================================================

MOSFLM A.mat Reciprocal Vectors:
  a* = [-0.0290511  -0.02939588  0.01074988]
  b* = [-0.00312639  0.01043764 -0.03285667]
  c* = [ 0.02596044 -0.01433302 -0.01060661]

Derived Cell Parameters:
  a = 26.751388 Å
  b = 31.309964 Å
  c = 33.673354 Å
  α = 88.686974°
  β = 71.529482°
  γ = 68.137528°

--------------------------------------------------------------------------------
C-Style Calculation (user_cell=0, NO rescale)
--------------------------------------------------------------------------------
  V* = 0.000040514934067 Å⁻³
  V_cell = 24682.256630 Å³

Real space vectors (unrescaled):
  a = [-14.3562690335, -21.8717928454, -5.5820208350]
  b = [-11.4986968433, 0.7173200310, -29.1132147806]
  c = [21.0699500320, -24.3892962471, -9.7526516651]

  |a| = 26.7513876170 Å
  |b| = 31.3099641006 Å
  |c| = 33.6733541584 Å

If user_cell=1 (C would rescale):
  a = [-14.3562690335, -21.8717928454, -5.5820208350]
  b = [-11.4986968433, 0.7173200310, -29.1132147806]
  c = [21.0699500320, -24.3892962471, -9.7526516651]

  |a| = 26.7513876170 Å
  |b| = 31.3099641006 Å
  |c| = 33.6733541584 Å

--------------------------------------------------------------------------------
PyTorch Calculation (current implementation, WITH rescale)
--------------------------------------------------------------------------------
Real space vectors (rescaled to match cell params):
  a = [-14.3562690335, -21.8717928454, -5.5820208350]
  b = [-11.4986968433, 0.7173200310, -29.1132147806]
  c = [21.0699500320, -24.3892962471, -9.7526516651]

  |a| = 26.7513876170 Å
  |b| = 31.3099641006 Å
  |c| = 33.6733541584 Å

--------------------------------------------------------------------------------
Delta Analysis
--------------------------------------------------------------------------------

Case 1: PyTorch vs C with user_cell=0 (current supervisor command)

Vector differences (PyTorch - C_no_rescale):
  Δa = [0.0000000000, 0.0000000000, 0.0000000000]
  Δb = [0.0000000000, 0.0000000000, 0.0000000000]
  Δc = [0.0000000000, 0.0000000000, 0.0000000000]

  |Δa| = 0.0000000000 Å
  |Δb| = 0.0000000000 Å
  |Δc| = 0.0000000000 Å

Magnitude comparison (PyTorch vs C_no_rescale):
  a: C=26.7513876170 Å, PyTorch=26.7513876170 Å, Δ=0.0000000000 Å (0.0000%)
  b: C=31.3099641006 Å, PyTorch=31.3099641006 Å, Δ=-0.0000000000 Å (-0.0000%)
  c: C=33.6733541584 Å, PyTorch=33.6733541584 Å, Δ=0.0000000000 Å (0.0000%)

Case 2: PyTorch vs C with user_cell=1 (if -cell was provided)

Magnitude comparison (PyTorch vs C_rescaled):
  a: C=26.7513876170 Å, PyTorch=26.7513876170 Å, Δ=0.0000000000 Å (0.0000%)
  b: C=31.3099641006 Å, PyTorch=31.3099641006 Å, Δ=0.0000000000 Å (0.0000%)
  c: C=33.6733541584 Å, PyTorch=33.6733541584 Å, Δ=0.0000000000 Å (0.0000%)

--------------------------------------------------------------------------------
Detailed b-vector Component Analysis
--------------------------------------------------------------------------------
  b_x: C_no_rescale=-11.4986968433, PyTorch=-11.4986968433, Δ=0.0000000000
  b_y: C_no_rescale=0.7173200310, PyTorch=0.7173200310, Δ=0.0000000000
  b_z: C_no_rescale=-29.1132147806, PyTorch=-29.1132147806, Δ=0.0000000000

================================================================================
Summary
================================================================================

Expected cell parameters (from reciprocal_to_real_cell):
  a = 26.751388 Å
  b = 31.309964 Å
  c = 33.673354 Å

C-style magnitudes (NO rescale, user_cell=0 - current supervisor command):
  |a| = 26.7513876170 Å
  |b| = 31.3099641006 Å
  |c| = 33.6733541584 Å

C-style magnitudes (WITH rescale, user_cell=1 - if -cell provided):
  |a| = 26.7513876170 Å
  |b| = 31.3099641006 Å
  |c| = 33.6733541584 Å

PyTorch magnitudes (current implementation - always rescales):
  |a| = 26.7513876170 Å
  |b| = 31.3099641006 Å
  |c| = 33.6733541584 Å

Conclusion:
  PyTorch matches C with user_cell=1 (rescaled): Δb = 0.0000000000 Å
  PyTorch differs from C with user_cell=0 (not rescaled): Δb = 0.000000 Å

  The current supervisor command uses -matrix A.mat WITHOUT -cell, so C has
  user_cell=0 and does NOT rescale. PyTorch always rescales (as if user_cell=1),
  causing a mismatch in the real-space lattice vectors.

  Expected impact on F_latt_b:
  The magnitude match suggests rescaling is NOT the root cause of the
  F_latt_b discrepancy (21.6%). The issue must lie elsewhere (Miller
  index calculation, sincg evaluation, or orientation differences).

