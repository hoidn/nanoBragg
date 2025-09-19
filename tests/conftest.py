"""
Test configuration and fixtures for nanoBragg PyTorch tests.

This file contains pytest configuration, fixtures, and environment setup
that is shared across all test modules.
"""

import os
import sys
from pathlib import Path

# Set environment variable to prevent MKL library conflicts with PyTorch
# This must be set before importing torch in any test module
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Add src to path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))