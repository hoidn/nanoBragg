#!/usr/bin/env python3
"""
Debug Beam Pivot Trace Script

Replicates the C-code's mathematical steps for detector geometry calculation
and produces an identically formatted TRACE_PY: log for parallel debugging.
"""
import os
import math
import argparse
import numpy as np

# Determinism guardrails
os.environ["CUDA_VISIBLE_DEVICES"] = ""
np.set_printoptions(precision=17, floatmode="maxprec_equal", suppress=False)


def deg2rad(x):
    """Convert degrees to radians."""
    return x * math.pi / 180.0


def R_x(ax):
    """Rotation matrix around X axis."""
    c, s = math.cos(ax), math.sin(ax)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], dtype=np.float64)


def R_y(ay):
    """Rotation matrix around Y axis."""
    c, s = math.cos(ay), math.sin(ay)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]], dtype=np.float64)


def R_z(az):
    """Rotation matrix around Z axis."""
    c, s = math.cos(az), math.sin(az)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], dtype=np.float64)


def rotate_axis(v, axis, phi):
    """Rotate vector v around axis by angle phi using Rodrigues' formula."""
    axis = axis / np.linalg.norm(axis)
    v = v.astype(np.float64)
    c, s = math.cos(phi), math.sin(phi)
    cross = np.cross(axis, v)
    dot = np.dot(axis, v)
    return v * c + cross * s + axis * dot * (1.0 - c)


def p_vec(tag, v):
    """Print vector in trace format."""
    print(f"TRACE_PY:{tag}={v[0]:.15g} {v[1]:.15g} {v[2]:.15g}")


def p_mat(tag, M):
    """Print matrix in trace format."""
    a, b, c = M
    print(
        f"TRACE_PY:{tag}=[{a[0]:.15g} {a[1]:.15g} {a[2]:.15g}; "
        f"{b[0]:.15g} {b[1]:.15g} {b[2]:.15g}; "
        f"{c[0]:.15g} {c[1]:.15g} {c[2]:.15g}]"
    )


def main():
    ap = argparse.ArgumentParser(
        description="Generate Python trace for detector geometry debugging"
    )
    ap.add_argument("--pixel-mm", type=float, default=0.1)
    ap.add_argument("--distance-mm", type=float, default=100.0)
    ap.add_argument("--xbeam-mm", type=float, default=51.2)
    ap.add_argument("--ybeam-mm", type=float, default=51.2)
    ap.add_argument("--rotx-deg", type=float, default=1.0)
    ap.add_argument("--roty-deg", type=float, default=5.0)
    ap.add_argument("--rotz-deg", type=float, default=0.0)
    ap.add_argument("--twotheta-deg", type=float, default=3.0)
    args = ap.parse_args()

    # Convert angles to radians
    rotx = deg2rad(args.rotx_deg)
    roty = deg2rad(args.roty_deg)
    rotz = deg2rad(args.rotz_deg)
    tth = deg2rad(args.twotheta_deg)

    # Log convention and angles
    print("TRACE_PY:detector_convention=MOSFLM")
    print(
        f"TRACE_PY:angles_rad=rotx:{rotx:.15g} roty:{roty:.15g} rotz:{rotz:.15g} twotheta:{tth:.15g}"
    )
    print(
        f"TRACE_PY:beam_center_m=X:{args.xbeam_mm/1000.0/1000.0:.15g} Y:{args.ybeam_mm/1000.0/1000.0:.15g} pixel_mm:{args.pixel_mm:.15g}"
    )

    # Initial MOSFLM basis vectors
    fdet = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    sdet = np.array([0.0, -1.0, 0.0], dtype=np.float64)
    odet = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    p_vec("initial_fdet", fdet)
    p_vec("initial_sdet", sdet)
    p_vec("initial_odet", odet)

    # Rotation matrices (extrinsic XYZ -> R = Rz @ Ry @ Rx)
    Rx = R_x(rotx)
    Ry = R_y(roty)
    Rz = R_z(rotz)
    R = Rz @ Ry @ Rx
    p_mat("Rx", Rx)
    p_mat("Ry", Ry)
    p_mat("Rz", Rz)
    p_mat("R_total", R)

    # Stage-by-stage vector rotations
    f_rx = Rx @ fdet
    f_ry = Ry @ f_rx
    f_rz = Rz @ f_ry

    # Also rotate sdet and odet through all stages
    s_rx = Rx @ sdet
    s_ry = Ry @ s_rx
    s_rz = Rz @ s_ry

    o_rx = Rx @ odet
    o_ry = Ry @ o_rx
    o_rz = Rz @ o_ry

    # Two-theta axis for MOSFLM
    twotheta_axis = np.array([0.0, 0.0, -1.0], dtype=np.float64)

    # Apply twotheta rotation
    f_tt = rotate_axis(f_rz, twotheta_axis, tth)
    s_tt = rotate_axis(s_rz, twotheta_axis, tth)
    o_tt = rotate_axis(o_rz, twotheta_axis, tth)

    # Note: C code logs vectors AFTER all rotations including twotheta
    # So "fdet_after_rotz" actually includes twotheta rotation
    p_vec("fdet_after_rotz", f_tt)
    p_vec("sdet_after_rotz", s_tt)
    p_vec("odet_after_rotz", o_tt)

    p_vec("twotheta_axis", twotheta_axis)
    
    # These will be identical to the above since all rotations are already applied
    p_vec("fdet_after_twotheta", f_tt)
    p_vec("sdet_after_twotheta", s_tt)
    p_vec("odet_after_twotheta", o_tt)

    # MOSFLM convention mapping + 0.5 px adjustment
    print(
        "TRACE_PY:convention_mapping=Fbeam←Ybeam_mm(+0.5px),Sbeam←Xbeam_mm(+0.5px),beam_vec=[1 0 0]"
    )
    Fbeam_m = (args.ybeam_mm + 0.5 * args.pixel_mm) / 1000.0
    Sbeam_m = (args.xbeam_mm + 0.5 * args.pixel_mm) / 1000.0
    distance_m = args.distance_mm / 1000.0
    print(f"TRACE_PY:Fbeam_m={Fbeam_m:.15g}")
    print(f"TRACE_PY:Sbeam_m={Sbeam_m:.15g}")
    print(f"TRACE_PY:distance_m={distance_m:.15g}")

    # Calculate pix0 terms
    beam_vec = np.array([1.0, 0.0, 0.0], dtype=np.float64)  # MOSFLM beam vector
    term_fast = -Fbeam_m * f_tt
    p_vec("term_fast", term_fast)
    term_slow = -Sbeam_m * s_tt
    p_vec("term_slow", term_slow)
    term_beam = distance_m * beam_vec
    p_vec("term_beam", term_beam)

    # Final pix0_vector
    pix0 = term_fast + term_slow + term_beam
    p_vec("pix0_vector", pix0)


if __name__ == "__main__":
    main()