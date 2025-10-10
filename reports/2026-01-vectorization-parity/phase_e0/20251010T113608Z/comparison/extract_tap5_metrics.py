#!/usr/bin/env python3
"""Extract and compare Tap 5 intensity pre-normalization metrics.

Reads PyTorch JSON and C trace logs, computes ratios and deltas.
"""

import json
import sys

# PyTorch Tap 5 data
py_edge_file = "../../20251010T110735Z/py_taps/pixel_0_0_intensity_pre_norm.json"
py_centre_file = "../../20251010T110735Z/py_taps/pixel_2048_2048_intensity_pre_norm.json"

# C Tap 5 data (extract from logs)
c_edge_I = 141520.166457388
c_edge_steps = 4
c_edge_omega = 8.86109941671327e-09
c_edge_capture = 1.0
c_edge_polar = 0.961276939690433
c_edge_I_final = 0.000301366151806705

c_centre_I = 0.0
c_centre_steps = 4
c_centre_omega = 9.99999983125e-09
c_centre_capture = 1.0
c_centre_polar = 0.999999994375
c_centre_I_final = 0.0

# Load PyTorch data
with open(py_edge_file) as f:
    py_edge = json.load(f)

with open(py_centre_file) as f:
    py_centre = json.load(f)

py_edge_I = py_edge["values"]["accumulated_intensity"]
py_edge_steps = py_edge["values"]["steps"]
py_edge_omega = py_edge["values"]["last_omega_applied"]
py_edge_capture = py_edge["values"]["last_capture_fraction"]
py_edge_polar = py_edge["values"]["last_polar"]
py_edge_norm = py_edge["values"]["normalized_intensity"]

py_centre_I = py_centre["values"]["accumulated_intensity"]
py_centre_steps = py_centre["values"]["steps"]
py_centre_omega = py_centre["values"]["last_omega_applied"]
py_centre_capture = py_centre["values"]["last_capture_fraction"]
py_centre_polar = py_centre["values"]["last_polar"]
py_centre_norm = py_centre["values"]["normalized_intensity"]

# Compute ratios
def ratio_or_zero(c, py):
    """Return C/PyTorch ratio or 'N/A' if both near zero."""
    if abs(py) < 1e-10 and abs(c) < 1e-10:
        return "N/A (both zero)"
    if abs(py) < 1e-10:
        return "N/A (PyTorch zero)"
    return c / py

edge_I_ratio = ratio_or_zero(c_edge_I, py_edge_I)
edge_omega_ratio = ratio_or_zero(c_edge_omega, py_edge_omega)
edge_polar_ratio = ratio_or_zero(c_edge_polar, py_edge_polar)

centre_I_ratio = ratio_or_zero(c_centre_I, py_centre_I)
centre_omega_ratio = ratio_or_zero(c_centre_omega, py_centre_omega)
centre_polar_ratio = ratio_or_zero(c_centre_polar, py_centre_polar)

# Print table
print("=" * 80)
print("TAP 5 INTENSITY PRE-NORMALIZATION COMPARISON")
print("=" * 80)
print()
print("EDGE PIXEL (0,0):")
print("-" * 80)
print(f"{'Metric':<30} {'C Value':<20} {'PyTorch Value':<20} {'C/PyTorch Ratio':<15}")
print("-" * 80)
print(f"{'I_before_scaling':<30} {c_edge_I:<20.6e} {py_edge_I:<20.6e} {edge_I_ratio if isinstance(edge_I_ratio, str) else f'{edge_I_ratio:<15.6f}'}")
print(f"{'steps':<30} {c_edge_steps:<20} {py_edge_steps:<20} {c_edge_steps/py_edge_steps:<15.6f}")
print(f"{'omega_pixel (sr)':<30} {c_edge_omega:<20.6e} {py_edge_omega:<20.6e} {edge_omega_ratio if isinstance(edge_omega_ratio, str) else f'{edge_omega_ratio:<15.6f}'}")
print(f"{'capture_fraction':<30} {c_edge_capture:<20.6f} {py_edge_capture:<20.6f} {c_edge_capture/py_edge_capture:<15.6f}")
print(f"{'polar':<30} {c_edge_polar:<20.6f} {py_edge_polar:<20.6f} {edge_polar_ratio if isinstance(edge_polar_ratio, str) else f'{edge_polar_ratio:<15.6f}'}")
print(f"{'I_pixel_final':<30} {c_edge_I_final:<20.6e} {py_edge_norm:<20.6e} {c_edge_I_final/py_edge_norm:<15.6f}")
print()
print("CENTRE PIXEL (2048,2048):")
print("-" * 80)
print(f"{'Metric':<30} {'C Value':<20} {'PyTorch Value':<20} {'C/PyTorch Ratio':<15}")
print("-" * 80)
print(f"{'I_before_scaling':<30} {c_centre_I:<20.6e} {py_centre_I:<20.6e} {centre_I_ratio}")
print(f"{'steps':<30} {c_centre_steps:<20} {py_centre_steps:<20} {c_centre_steps/py_centre_steps:<15.6f}")
print(f"{'omega_pixel (sr)':<30} {c_centre_omega:<20.6e} {py_centre_omega:<20.6e} {centre_omega_ratio if isinstance(centre_omega_ratio, str) else f'{centre_omega_ratio:<15.6f}'}")
print(f"{'capture_fraction':<30} {c_centre_capture:<20.6f} {py_centre_capture:<20.6f} {c_centre_capture/py_centre_capture:<15.6f}")
print(f"{'polar':<30} {c_centre_polar:<20.6f} {py_centre_polar:<20.6f} {centre_polar_ratio if isinstance(centre_polar_ratio, str) else f'{centre_polar_ratio:<15.6f}'}")
print(f"{'I_pixel_final':<30} {c_centre_I_final:<20.6e} {py_centre_norm:<20.6e} {centre_I_ratio}")
print()
print("=" * 80)
print("KEY FINDINGS:")
print("=" * 80)
print(f"1. Edge pixel I_before_scaling ratio: {edge_I_ratio:.4f}× (C higher)")
print(f"2. Omega ratio (edge): {c_edge_omega/py_edge_omega:.6f}× (≈{abs(1 - c_edge_omega/py_edge_omega)*100:.4f}% difference)")
print(f"3. Polar ratio (edge): {c_edge_polar/py_edge_polar:.6f}× (≈{abs(1 - c_edge_polar/py_edge_polar)*100:.4f}% difference)")
print(f"4. Steps match exactly: {c_edge_steps} == {py_edge_steps}")
print(f"5. Centre pixel both implementations report zero intensity (F_cell=0)")
print()
print("CONCLUSION:")
print("-" * 80)
print("The ~4× discrepancy in I_before_scaling at the edge pixel is the primary")
print("divergence. Omega and polar variations are negligible (≤0.003%).")
print("This isolates the issue to the raw intensity accumulation loop:")
print("   I_term = (F_cell²) × (F_latt²)")
print("summed over all subpixels/sources/phi/mosaic.")
print("=" * 80)
