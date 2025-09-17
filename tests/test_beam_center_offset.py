#!/usr/bin/env python3
"""Test if beam center offset is the issue."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import numpy as np
import torch
from src.nanobrag_torch.config import DetectorConfig
from src.nanobrag_torch.models.detector import Detector

# Test the beam center calculation
config = DetectorConfig(
    distance_mm=100.0,
    pixel_size_mm=0.1,
    spixels=1024,
    fpixels=1024,
    beam_center_s=51.2,
    beam_center_f=51.2,
)

detector = Detector(config)

print("Configuration:")
print(f"  beam_center_s: {config.beam_center_s} mm")
print(f"  beam_center_f: {config.beam_center_f} mm")
print(f"  pixel_size: {config.pixel_size_mm} mm")

print("\nDetector internal values:")
print(f"  beam_center_s: {detector.beam_center_s} pixels")
print(f"  beam_center_f: {detector.beam_center_f} pixels")

print("\nExpected for MOSFLM convention:")
print(f"  beam_center_s should be: {config.beam_center_s / config.pixel_size_mm} = {51.2 / 0.1} pixels")
print(f"  beam_center_f should be: {config.beam_center_f / config.pixel_size_mm} = {51.2 / 0.1} pixels")

print("\nC code expectation:")
print("  In MOSFLM convention, C adds 0.5 pixel offset")
print("  Xbeam = Ybeam = 51.25 mm (from default calculation)")
print("  Then adds 0.5 pixel: Fbeam = Sbeam = 51.25 + 0.5*0.1 = 51.3 mm")
print("  In pixels: 51.3 / 0.1 = 513 pixels")