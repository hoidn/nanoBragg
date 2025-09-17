#!/usr/bin/env python3
"""Test PyTorch configuration echo output."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from src.nanobrag_torch.config import DetectorConfig, DetectorConvention
from src.nanobrag_torch.models.detector import Detector

# Test 1: Default MOSFLM configuration
print("Test 1: Default MOSFLM configuration")
config = DetectorConfig()
detector = Detector(config)
print()

# Test 2: CUSTOM convention with twotheta_axis
print("Test 2: Custom twotheta_axis (should trigger mode change)")
config = DetectorConfig(
    twotheta_axis=[0, 0, -1]  # Same as MOSFLM default but explicitly set
)
detector = Detector(config)
print()

# Test 3: Non-default twotheta_axis
print("Test 3: Non-default twotheta_axis")
config = DetectorConfig(
    twotheta_axis=[1, 0, 0]  # Different from MOSFLM default
)
detector = Detector(config)
print()

# Test 4: Explicit CUSTOM convention
print("Test 4: Explicit CUSTOM convention")
config = DetectorConfig(
    detector_convention=DetectorConvention.CUSTOM
)
detector = Detector(config)