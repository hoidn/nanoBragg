"""
AT-PERF-008: CUDA Large-Tensor Residency Test
Tests that large tensors (>=65536 elements) stay on GPU during simulation when CUDA is available.

This test validates that the PyTorch implementation efficiently uses GPU memory
by keeping large tensors on device throughout the computation.
"""

import pytest
import torch
import numpy as np
from unittest.mock import patch
from contextlib import contextmanager
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from nanobrag_torch.simulator import Simulator
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig


class TensorDeviceTracker:
    """Track tensor operations to ensure large tensors stay on GPU."""

    def __init__(self, min_size=65536):
        """
        Initialize the tracker.

        Args:
            min_size: Minimum tensor size to track (default 65536)
        """
        self.min_size = min_size
        self.cpu_operations = []
        self.gpu_operations = []
        self.violations = []

    def check_tensor_device(self, tensor, operation_name):
        """Check if a tensor is on the expected device."""
        if not isinstance(tensor, torch.Tensor):
            return

        if tensor.numel() >= self.min_size:
            device_type = str(tensor.device).split(':')[0]

            if device_type == 'cpu':
                self.cpu_operations.append({
                    'operation': operation_name,
                    'size': tensor.numel(),
                    'shape': tuple(tensor.shape),
                    'device': str(tensor.device)
                })
                self.violations.append(f"{operation_name}: Large tensor ({tensor.numel()} elements) on CPU")
            else:
                self.gpu_operations.append({
                    'operation': operation_name,
                    'size': tensor.numel(),
                    'shape': tuple(tensor.shape),
                    'device': str(tensor.device)
                })

    def report(self):
        """Generate a report of tensor operations."""
        return {
            'total_cpu_ops': len(self.cpu_operations),
            'total_gpu_ops': len(self.gpu_operations),
            'violations': self.violations,
            'cpu_operations': self.cpu_operations[:5],  # First 5 for brevity
            'gpu_operations': self.gpu_operations[:5]   # First 5 for brevity
        }


@contextmanager
def track_tensor_devices(min_size=65536):
    """
    Context manager to track tensor operations during execution.

    Uses PyTorch hooks to monitor tensor operations and ensure
    large tensors stay on GPU.
    """
    tracker = TensorDeviceTracker(min_size=min_size)

    # Store original functions that we'll patch
    original_add = torch.add
    original_mul = torch.mul
    original_matmul = torch.matmul
    original_sum = torch.sum
    original_mean = torch.mean
    original_maximum = torch.maximum

    def wrapped_operation(op_name, original_fn):
        """Wrap a torch operation to track device usage."""
        def wrapper(*args, **kwargs):
            # Check input tensors
            for i, arg in enumerate(args):
                if isinstance(arg, torch.Tensor):
                    tracker.check_tensor_device(arg, f"{op_name}_input_{i}")

            # Call original operation
            result = original_fn(*args, **kwargs)

            # Check output tensor
            if isinstance(result, torch.Tensor):
                tracker.check_tensor_device(result, f"{op_name}_output")

            return result
        return wrapper

    # Patch torch operations
    torch.add = wrapped_operation("add", original_add)
    torch.mul = wrapped_operation("mul", original_mul)
    torch.matmul = wrapped_operation("matmul", original_matmul)
    torch.sum = wrapped_operation("sum", original_sum)
    torch.mean = wrapped_operation("mean", original_mean)
    torch.maximum = wrapped_operation("maximum", original_maximum)

    try:
        yield tracker
    finally:
        # Restore original functions
        torch.add = original_add
        torch.mul = original_mul
        torch.matmul = original_matmul
        torch.sum = original_sum
        torch.mean = original_mean
        torch.maximum = original_maximum


class TestATPERF008CUDATensorResidency:
    """
    AT-PERF-008: CUDA Large-Tensor Residency

    Validates that large tensors (>=65536 elements) remain on GPU throughout
    the simulation when CUDA is available.
    """

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    @pytest.mark.xfail(reason="GPU device propagation not fully implemented yet - Detector and Crystal need device parameter support")
    def test_large_tensor_gpu_residency(self):
        """Test that large tensors stay on GPU during simulation."""
        # Setup: Create 512x512 detector (262,144 pixels)
        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=(5, 5, 5),
            default_F=100.0
        )

        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=512,
            fpixels=512
        )

        beam_config = BeamConfig(
            wavelength_A=6.2,
            fluence=1e20
        )

        # Create simulator with CUDA device
        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)

        # Use 'cuda' device directly (not 'auto' as spec mentions, since that's not implemented)
        device = torch.device('cuda')
        simulator = Simulator(
            crystal=crystal,
            detector=detector,
            beam_config=beam_config,
            device=device,
            dtype=torch.float32  # Use float32 for better GPU performance
        )

        # Track tensor operations during simulation
        with track_tensor_devices(min_size=65536) as tracker:
            # Run simulation
            result = simulator.run()

        # Verify result is on GPU
        assert result.device.type == 'cuda', "Output tensor should be on GPU"

        # Get tracking report
        report = tracker.report()

        # Assertions based on spec requirements
        assert len(report['violations']) == 0, (
            f"Large tensors were found on CPU during GPU simulation:\n" +
            "\n".join(report['violations'])
        )

        # Additional validation
        assert report['total_gpu_ops'] > 0, "No GPU operations were tracked"
        assert report['total_cpu_ops'] == 0 or all(
            op['size'] < 65536 for op in tracker.cpu_operations
        ), "Large tensors should not be on CPU"

        # Verify the output has expected size
        assert result.shape == (512, 512), "Output should be 512x512"
        assert result.numel() == 262144, "Output should have 262,144 elements"

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    @pytest.mark.xfail(reason="Auto device selection and GPU propagation not fully implemented yet")
    def test_auto_device_selection_uses_cuda(self):
        """Test that 'auto' device selection chooses CUDA when available."""
        # Note: The spec requires device='auto' but this is not implemented yet
        # This test documents the expected behavior for future implementation

        # Setup small test case
        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(1, 1, 1), default_F=100.0
        )

        detector_config = DetectorConfig(
            distance_mm=100.0, pixel_size_mm=0.1,
            spixels=512, fpixels=512
        )

        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)

        # Currently, we need to manually specify cuda device
        # Future: device='auto' should automatically select cuda when available
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        simulator = Simulator(
            crystal=crystal,
            detector=detector,
            device=device
        )

        # Check that simulator uses CUDA
        assert simulator.device.type == 'cuda', "Should use CUDA when available"

        # Run a quick simulation to ensure it works
        result = simulator.run()
        assert result.device.type == 'cuda', "Result should be on CUDA"

    @pytest.mark.skipif(torch.cuda.is_available(), reason="CUDA is available")
    def test_skip_when_cuda_unavailable(self):
        """Test that CUDA tests are properly skipped when CUDA is not available."""
        # This test will only run when CUDA is NOT available
        # It verifies that the skip mechanism works correctly
        assert not torch.cuda.is_available(), "This test should only run without CUDA"

        # Create a minimal simulator on CPU
        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(1, 1, 1), default_F=100.0
        )

        detector_config = DetectorConfig(
            distance_mm=100.0, pixel_size_mm=0.1,
            spixels=64, fpixels=64  # Small for CPU
        )

        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)

        simulator = Simulator(
            crystal=crystal,
            detector=detector,
            device=torch.device('cpu')
        )

        # Verify it runs on CPU
        result = simulator.run()
        assert result.device.type == 'cpu', "Should run on CPU when CUDA unavailable"

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    @pytest.mark.xfail(reason="GPU device propagation not fully implemented yet")
    def test_memory_efficient_gpu_usage(self):
        """Test that GPU memory is used efficiently for large simulations."""
        # Test with a larger detector to stress GPU memory
        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5), default_F=100.0
        )

        detector_config = DetectorConfig(
            distance_mm=100.0, pixel_size_mm=0.1,
            spixels=1024, fpixels=1024  # 1M pixels
        )

        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)

        # Clear GPU cache before test
        torch.cuda.empty_cache()

        # Get initial memory
        initial_memory = torch.cuda.memory_allocated()

        simulator = Simulator(
            crystal=crystal,
            detector=detector,
            device=torch.device('cuda'),
            dtype=torch.float32  # Use float32 for memory efficiency
        )

        # Run simulation
        result = simulator.run()

        # Get memory after simulation
        peak_memory = torch.cuda.max_memory_allocated()
        current_memory = torch.cuda.memory_allocated()

        # Verify memory usage is reasonable
        # 1024x1024 float32 = 4MB for output, expect <100MB total with intermediates
        memory_mb = (peak_memory - initial_memory) / (1024 * 1024)
        assert memory_mb < 200, f"Excessive GPU memory usage: {memory_mb:.1f} MB"

        # Verify result
        assert result.shape == (1024, 1024)
        assert result.device.type == 'cuda'

        # Clean up
        del simulator, result
        torch.cuda.empty_cache()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])