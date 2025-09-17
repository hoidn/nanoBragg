#!/usr/bin/env python3
"""Test script to debug detector pix0_vector calculation."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import torch
from nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models.detector import Detector

# Set environment variable
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Configuration matching the trace files
config = DetectorConfig(
    distance_mm=100.0,
    pixel_size_mm=0.1,
    spixels=1024,
    fpixels=1024,
    beam_center_s=51.2,  # Xbeam in C becomes Sbeam in MOSFLM
    beam_center_f=51.2,  # Ybeam in C becomes Fbeam in MOSFLM
    detector_convention=DetectorConvention.MOSFLM,
    detector_rotx_deg=1.0,
    detector_roty_deg=5.0,
    detector_rotz_deg=0.0,
    detector_twotheta_deg=3.0,
    detector_pivot=DetectorPivot.BEAM,
)

# Create detector
detector = Detector(config=config, device=torch.device("cpu"), dtype=torch.float64)

# Expected values from trace
expected_pix0 = torch.tensor([0.0983465378387818, 0.052294833982483, -0.0501561701251796])

# Print comparison
print("Detector pix0_vector:", detector.pix0_vector.numpy())
print("Expected from trace:", expected_pix0.numpy())
print("Difference:", (detector.pix0_vector - expected_pix0).numpy())
print("Max difference:", torch.max(torch.abs(detector.pix0_vector - expected_pix0)).item())

# Also print intermediate values for debugging
print("\nDetector basis vectors:")
print("  fdet:", detector.fdet_vec.numpy())
print("  sdet:", detector.sdet_vec.numpy())
print("  odet:", detector.odet_vec.numpy())

print("\nRotation angles (radians):")
print("  rotx:", config.detector_rotx_deg * 3.14159265359 / 180)
print("  roty:", config.detector_roty_deg * 3.14159265359 / 180)
print("  rotz:", config.detector_rotz_deg * 3.14159265359 / 180)
print("  twotheta:", config.detector_twotheta_deg * 3.14159265359 / 180)

print("\nBeam parameters:")
print("  beam_center_s (pixels):", detector.beam_center_s.item())
print("  beam_center_f (pixels):", detector.beam_center_f.item())
print("  Fbeam (meters):", (detector.beam_center_f.item() + 0.5) * detector.pixel_size)
print("  Sbeam (meters):", (detector.beam_center_s.item() + 0.5) * detector.pixel_size)
print("  distance (meters):", detector.distance)