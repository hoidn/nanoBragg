"""
Unit tests for physics functions.

Tests the correctness of individual physics functions against known values
from the C implementation.
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import pytest
from nanobrag_torch.utils.physics import sincg


class TestPhysicsFunctions:
    """Test suite for physics utility functions."""
    
    def test_sincg_against_c_value(self):
        """Verify the sincg function for a typical non-zero case.
        
        For h=0.5, N=5:
        - π*h = π*0.5 = π/2
        - sin(N*π*h) = sin(5π/2) = sin(π/2) = 1
        - sin(π*h) = sin(π/2) = 1
        - Result = 1/1 = 1.0
        """
        # Test input - use a value that gives a clear result
        h = 0.5
        N = 5
        
        # Calculate using PyTorch implementation
        # Note: sincg now expects pre-multiplied π input
        result = sincg(torch.pi * torch.tensor(h, dtype=torch.float64), 
                      torch.tensor(N, dtype=torch.float64))
        
        # Expected value 
        expected = 1.0
        
        # Assert with tight tolerance
        torch.testing.assert_close(
            result, 
            torch.tensor(expected, dtype=torch.float64),
            rtol=1e-9,
            atol=1e-9
        )
        
    def test_sincg_fractional_miller_index(self):
        """Test sincg with a fractional Miller index that gives a non-trivial result.
        
        For h=0.1, N=5:
        sin(5*π*0.1)/sin(π*0.1) = sin(π/2)/sin(π/10) ≈ 3.236068
        """
        h = 0.1
        N = 5
        
        result = sincg(torch.pi * torch.tensor(h, dtype=torch.float64),
                      torch.tensor(N, dtype=torch.float64))
        
        # Calculate expected value
        import numpy as np
        expected = np.sin(N * np.pi * h) / np.sin(np.pi * h)
        
        torch.testing.assert_close(
            result,
            torch.tensor(expected, dtype=torch.float64),
            rtol=1e-9,
            atol=1e-9
        )
    
    def test_sincg_at_zero(self):
        """Test sincg function at u=0 returns N."""
        N = torch.tensor(7.0, dtype=torch.float64)
        u = torch.tensor(0.0, dtype=torch.float64)
        
        result = sincg(u, N)
        
        torch.testing.assert_close(result, N)
    
    def test_sincg_vectorized(self):
        """Test sincg function with vector inputs."""
        # Multiple h values
        h_values = torch.tensor([0.0, 1.0, 2.0, 3.2], dtype=torch.float64)
        N = torch.tensor(5.0, dtype=torch.float64)
        
        # Calculate for all values at once
        results = sincg(torch.pi * h_values, N)
        
        # Check shape
        assert results.shape == h_values.shape
        
        # Check specific values
        assert results[0].item() == 5.0  # sincg(0, 5) = 5
        
    def test_sincg_broadcast_N(self):
        """Test sincg function broadcasts scalar N correctly."""
        h_values = torch.randn(10, 20, dtype=torch.float64)
        N = torch.tensor(3.0, dtype=torch.float64)
        
        results = sincg(torch.pi * h_values, N)
        
        assert results.shape == h_values.shape