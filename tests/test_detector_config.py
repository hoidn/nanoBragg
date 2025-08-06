"""
Test DetectorConfig dataclass and Detector initialization.
"""

import pytest
import torch
import os

# Set environment variable before importing torch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from src.nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot
from src.nanobrag_torch.models.detector import Detector


class TestDetectorConfig:
    """Test DetectorConfig dataclass."""
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        config = DetectorConfig()
        
        # Basic geometry
        assert config.distance_mm == 100.0
        assert config.pixel_size_mm == 0.1
        
        # Dimensions
        assert config.spixels == 1024
        assert config.fpixels == 1024
        
        # Beam center
        assert config.beam_center_s == 51.2
        assert config.beam_center_f == 51.2
        
        # Rotations
        assert config.detector_rotx_deg == 0.0
        assert config.detector_roty_deg == 0.0
        assert config.detector_rotz_deg == 0.0
        assert config.detector_twotheta_deg == 0.0
        
        # Convention and pivot
        assert config.detector_convention == DetectorConvention.MOSFLM
        assert config.detector_pivot == DetectorPivot.SAMPLE
        
        # Sampling
        assert config.oversample == 1
        
    def test_post_init_defaults(self):
        """Test that post_init sets default twotheta axis."""
        config = DetectorConfig()
        assert config.twotheta_axis is not None
        torch.testing.assert_close(config.twotheta_axis, torch.tensor([0.0, 1.0, 0.0]))
        
    def test_custom_twotheta_axis(self):
        """Test that custom twotheta axis is preserved."""
        custom_axis = torch.tensor([1.0, 0.0, 0.0])
        config = DetectorConfig(twotheta_axis=custom_axis)
        torch.testing.assert_close(config.twotheta_axis, custom_axis)
        
    def test_invalid_pixel_counts(self):
        """Test that invalid pixel counts raise errors."""
        with pytest.raises(ValueError, match="Pixel counts must be positive"):
            DetectorConfig(spixels=0)
            
        with pytest.raises(ValueError, match="Pixel counts must be positive"):
            DetectorConfig(fpixels=-1)
            
    def test_invalid_distance(self):
        """Test that invalid distance raises error."""
        with pytest.raises(ValueError, match="Distance must be positive"):
            DetectorConfig(distance_mm=0.0)
            
        with pytest.raises(ValueError, match="Distance must be positive"):
            DetectorConfig(distance_mm=-10.0)
            
    def test_invalid_pixel_size(self):
        """Test that invalid pixel size raises error."""
        with pytest.raises(ValueError, match="Pixel size must be positive"):
            DetectorConfig(pixel_size_mm=0.0)
            
        with pytest.raises(ValueError, match="Pixel size must be positive"):
            DetectorConfig(pixel_size_mm=-0.1)
            
    def test_invalid_oversample(self):
        """Test that invalid oversample raises error."""
        with pytest.raises(ValueError, match="Oversample must be at least 1"):
            DetectorConfig(oversample=0)
            
    def test_tensor_parameters(self):
        """Test that tensor parameters are accepted."""
        distance = torch.tensor(200.0)
        pixel_size = torch.tensor(0.2)
        beam_s = torch.tensor(100.0)
        beam_f = torch.tensor(100.0)
        rotx = torch.tensor(5.0)
        
        config = DetectorConfig(
            distance_mm=distance,
            pixel_size_mm=pixel_size,
            beam_center_s=beam_s,
            beam_center_f=beam_f,
            detector_rotx_deg=rotx
        )
        
        assert config.distance_mm is distance
        assert config.pixel_size_mm is pixel_size
        assert config.beam_center_s is beam_s
        assert config.beam_center_f is beam_f
        assert config.detector_rotx_deg is rotx


class TestDetectorInitialization:
    """Test Detector class initialization with DetectorConfig."""
    
    def test_default_initialization(self):
        """Test that Detector initializes with default config."""
        detector = Detector()
        
        # Check that config was created
        assert detector.config is not None
        assert isinstance(detector.config, DetectorConfig)
        
        # Check unit conversions
        assert detector.distance == 1e6  # 100 mm = 1e6 Angstroms
        assert detector.pixel_size == 1000  # 0.1 mm = 1000 Angstroms
        
        # Check dimensions
        assert detector.spixels == 1024
        assert detector.fpixels == 1024
        
        # Check beam center in pixels
        assert detector.beam_center_s == 512.0  # 51.2 mm / 0.1 mm per pixel
        assert detector.beam_center_f == 512.0
        
    def test_custom_config_initialization(self):
        """Test that Detector initializes with custom config."""
        config = DetectorConfig(
            distance_mm=200.0,
            pixel_size_mm=0.2,
            spixels=2048,
            fpixels=2048,
            beam_center_s=204.8,  # 1024 pixels * 0.2 mm
            beam_center_f=204.8
        )
        detector = Detector(config)
        
        # Check unit conversions
        assert detector.distance == 2e6  # 200 mm = 2e6 Angstroms
        assert detector.pixel_size == 2000  # 0.2 mm = 2000 Angstroms
        
        # Check dimensions
        assert detector.spixels == 2048
        assert detector.fpixels == 2048
        
        # Check beam center in pixels
        assert detector.beam_center_s == 1024.0  # 204.8 mm / 0.2 mm per pixel
        assert detector.beam_center_f == 1024.0
        
    def test_backward_compatibility_check(self):
        """Test that _is_default_config works correctly."""
        # Default config should be detected
        detector = Detector()
        assert detector._is_default_config()
        
        # Config with tensor values but default numbers should be detected
        tensor_config = DetectorConfig(
            detector_rotx_deg=torch.tensor(0.0),
            detector_roty_deg=torch.tensor(0.0)
        )
        detector = Detector(tensor_config)
        assert detector._is_default_config()
        
    def test_custom_config_not_default(self):
        """Test that custom config is not detected as default."""
        # Custom config should not be detected as default
        custom_config = DetectorConfig(distance_mm=200.0)
        detector = Detector(custom_config)
        assert not detector._is_default_config()
        
    def test_basis_vectors_initialization(self):
        """Test that basis vectors are initialized correctly."""
        detector = Detector()
        
        # Check default basis vectors (use correct dtype)
        torch.testing.assert_close(detector.fdet_vec, torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64))
        torch.testing.assert_close(detector.sdet_vec, torch.tensor([0.0, -1.0, 0.0], dtype=torch.float64))
        torch.testing.assert_close(detector.odet_vec, torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64))
        
    def test_device_and_dtype(self):
        """Test that device and dtype are handled correctly."""
        if torch.cuda.is_available():
            device = torch.device("cuda")
        else:
            device = torch.device("cpu")
            
        detector = Detector(device=device, dtype=torch.float32)
        
        assert detector.device == device
        assert detector.dtype == torch.float32
        assert detector.fdet_vec.device == device
        assert detector.fdet_vec.dtype == torch.float32