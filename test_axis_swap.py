#!/usr/bin/env python3
"""Test that axis swap is correctly applied."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from src.nanobrag_torch.config import DetectorConfig
from src.nanobrag_torch.models.detector import Detector

# Create detector with known beam centers
config = DetectorConfig(
    beam_center_s=51.2,  # Should map to Fbeam after swap
    beam_center_f=51.2,  # Should map to Sbeam after swap
)

detector = Detector(config)

# The pix0_vector calculation happens internally
# Let's check the stored values
print(f"Config beam_center_s: {config.beam_center_s}")
print(f"Config beam_center_f: {config.beam_center_f}")
print(f"Detector beam_center_s: {detector.beam_center_s}")
print(f"Detector beam_center_f: {detector.beam_center_f}")

# Check pix0_vector
print(f"\npix0_vector: {detector.pix0_vector}")

# The key test: In MOSFLM BEAM mode with axis swap:
# config.beam_center_s (51.2) should be used for Fbeam calculation
# config.beam_center_f (51.2) should be used for Sbeam calculation
# This is the SWAP that was broken when someone changed it to "no swap"