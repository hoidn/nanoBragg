# PyTorch vs C Trace Diff Summary (phi_tic=0, c-parity mode)
- Source Py log: reports/2025-10-cli-flags/phase_l/parity_shim/20251008T021659Z/trace_py_c_parity.log
- Source C log: reports/2025-10-cli-flags/phase_l/parity_shim/20251008T021659Z/c_run.log
- Tolerance for first divergence check: 1e-06
- First variable exceeding tolerance:
  - name: pix0_vector_meters
  - max abs diff: 2.851329e-06
  - PyTorch values: [-0.21647571314293, 0.21634316475225, -0.23019526562923]
  - C values: [-0.216475836204836, 0.216343050492215, -0.230192414300537]

## Top 10 Differences by magnitude
- I_before_scaling: max diff 1.076850e+05; PyTorch=[835969.763932785]; C=[943654.809237549]
- scattering_vec_A_inv: max diff 3.631733e+04; PyTorch=[-1556209718.94149, 3933442655.0731, 913925676.642357]; C=[-1556230686.07047, 3933478972.39855, 913944567.685604]
- F_latt: max diff 3.129724e-02; PyTorch=[-2.35189941276007]; C=[-2.38319665299058]
- F_latt_c: max diff 1.618980e-02; PyTorch=[0.944771205212293]; C=[0.960961003611676]
- F_latt_a: max diff 7.725422e-03; PyTorch=[-2.36785278241508]; C=[-2.36012735995387]
- F_latt_b: max diff 5.293402e-04; PyTorch=[1.051325983228]; C=[1.05079664302326]
- hkl_frac: max diff 1.511599e-04; PyTorch=[-6.87946075907243, -0.607227388110849, -13.7661473655243]; C=[-6.8795206024501, -0.607255839576692, -13.766298525469]
- rot_b_star_A_inv: max diff 5.162400e-05; PyTorch=[-0.0031263923013923, 0.0103860193252683, -0.0328730297264385]; C=[-0.0031263923013923, 0.0104376433251433, -0.0328566748566749]
- rot_a_star_A_inv: max diff 4.616167e-05; PyTorch=[-0.0290510954135954, -0.0293789623945766, 0.0107960388161901]; C=[-0.0290510954135954, -0.0293958845208845, 0.0107498771498771]
- rot_c_star_A_inv: max diff 2.252732e-05; PyTorch=[0.0259604422604423, -0.0143496591104365, -0.0105840861066515]; C=[0.0259604422604423, -0.014333015970516, -0.0106066134316134]

### Notes
- Pix0 vector differs by up to 2.85 µm along detector normal; this is the first divergence and propagates to pixel position/diffracted vector.
- Resulting scattering vector offset (~3.63×10^4 Å⁻¹ in components) explains fixed Δk≈2.8×10⁻⁵ across φ.
- Lattice quantities (`F_latt`, `F_latt_a/b/c`) differ accordingly, leading to 1.08×10^5 delta in `I_before_scaling`.
- Focus next diagnostics on why pix0_z differs (check distance/pivot computations).
