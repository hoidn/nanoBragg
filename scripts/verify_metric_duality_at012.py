"""
Verify metric duality for AT-PARALLEL-012 triclinic case.
Tests a·a* = 1, b·b* = 1, c·c* = 1 for the triclinic cell with misset.
"""
import os
import torch

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.config import CrystalConfig
from nanobrag_torch.models.crystal import Crystal


def main():
    print("=== Metric Duality Test for AT-PARALLEL-012 ===")
    print()

    # Triclinic cell parameters
    crystal_config = CrystalConfig(
        cell_a=70.0, cell_b=80.0, cell_c=90.0,
        cell_alpha=75.0, cell_beta=85.0, cell_gamma=95.0,
        N_cells=(5, 5, 5),
        misset_deg=(-89.968546, -31.328953, 177.753396),
        default_F=100.0
    )

    crystal = Crystal(crystal_config, dtype=torch.float64)

    # Get vectors
    a = crystal.a
    b = crystal.b
    c = crystal.c
    a_star = crystal.a_star
    b_star = crystal.b_star
    c_star = crystal.c_star
    V = crystal.V

    print(f"Cell parameters: a={crystal_config.cell_a}, b={crystal_config.cell_b}, c={crystal_config.cell_c}")
    print(f"Cell angles: α={crystal_config.cell_alpha}, β={crystal_config.cell_beta}, γ={crystal_config.cell_gamma}")
    print(f"Misset: rotx={crystal_config.misset_deg[0]:.6f}, roty={crystal_config.misset_deg[1]:.6f}, rotz={crystal_config.misset_deg[2]:.6f}")
    print()

    print(f"Volume: {V:.6f} Å³")
    print()

    print("Real-space vectors:")
    print(f"  a = {a.cpu().numpy()}")
    print(f"  b = {b.cpu().numpy()}")
    print(f"  c = {c.cpu().numpy()}")
    print()

    print("Reciprocal-space vectors:")
    print(f"  a* = {a_star.cpu().numpy()}")
    print(f"  b* = {b_star.cpu().numpy()}")
    print(f"  c* = {c_star.cpu().numpy()}")
    print()

    # Test metric duality: a·a* = 1, etc.
    aa_star = torch.dot(a, a_star).item()
    bb_star = torch.dot(b, b_star).item()
    cc_star = torch.dot(c, c_star).item()

    print("=== Metric Duality Tests ===")
    print(f"a·a* = {aa_star:.15f} (should be 1.0)")
    print(f"b·b* = {bb_star:.15f} (should be 1.0)")
    print(f"c·c* = {cc_star:.15f} (should be 1.0)")
    print()

    # Test orthogonality: a·b* = 0, etc.
    ab_star = torch.dot(a, b_star).item()
    ac_star = torch.dot(a, c_star).item()
    ba_star = torch.dot(b, a_star).item()
    bc_star = torch.dot(b, c_star).item()
    ca_star = torch.dot(c, a_star).item()
    cb_star = torch.dot(c, b_star).item()

    print("=== Orthogonality Tests ===")
    print(f"a·b* = {ab_star:.15e} (should be 0.0)")
    print(f"a·c* = {ac_star:.15e} (should be 0.0)")
    print(f"b·a* = {ba_star:.15e} (should be 0.0)")
    print(f"b·c* = {bc_star:.15e} (should be 0.0)")
    print(f"c·a* = {ca_star:.15e} (should be 0.0)")
    print(f"c·b* = {cb_star:.15e} (should be 0.0)")
    print()

    # Calculate errors
    aa_star_error = abs(aa_star - 1.0)
    bb_star_error = abs(bb_star - 1.0)
    cc_star_error = abs(cc_star - 1.0)

    max_duality_error = max(aa_star_error, bb_star_error, cc_star_error)
    max_orthog_error = max(abs(ab_star), abs(ac_star), abs(ba_star), abs(bc_star), abs(ca_star), abs(cb_star))

    print("=== Error Summary ===")
    print(f"Max metric duality error: {max_duality_error:.2e}")
    print(f"Max orthogonality error: {max_orthog_error:.2e}")
    print()

    # Tolerance check (from test_metric_duality)
    rtol = 1e-12
    if max_duality_error < rtol:
        print(f"✅ PASS: Metric duality within tolerance ({rtol:.2e})")
    else:
        print(f"❌ FAIL: Metric duality error {max_duality_error:.2e} exceeds tolerance ({rtol:.2e})")

    # Also test volume consistency
    V_from_cross = torch.dot(a, torch.cross(b, c, dim=0)).item()
    V_error = abs(V.item() - V_from_cross)

    print()
    print(f"Volume from property: {V.item():.6f}")
    print(f"Volume from a·(b×c): {V_from_cross:.6f}")
    print(f"Volume error: {V_error:.2e}")

    if V_error < 1e-9:
        print("✅ PASS: Volume consistent")
    else:
        print("❌ FAIL: Volume inconsistent")


if __name__ == "__main__":
    main()