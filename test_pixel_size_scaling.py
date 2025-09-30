"""Quick test to verify beam center and omega scaling with pixel size."""
import torch
from src.nanobrag_torch.config import DetectorConfig, DetectorConvention
from src.nanobrag_torch.models.detector import Detector

# Test omega scaling
pixel_sizes = [0.05, 0.1, 0.2, 0.4]
fixed_beam_mm = 25.6

print("Omega Calculation Test (Center Pixel)")
print("=" * 80)

for px in pixel_sizes:
    config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        distance_mm=100.0,
        pixel_size_mm=px,
        spixels=256,
        fpixels=256,
        beam_center_s=fixed_beam_mm,
        beam_center_f=fixed_beam_mm,
    )
    
    detector = Detector(config)
    
    # Get center pixel omega
    center_s, center_f = 128, 128
    pixel_coords = detector.get_pixel_coords()
    R_center = torch.norm(pixel_coords[center_s, center_f])
    omega_grid = detector.get_solid_angle(pixel_coords)
    omega_center = omega_grid[center_s, center_f]
    
    # Manual calculation
    pixel_size_m = px / 1000.0
    expected_omega = (pixel_size_m ** 2) / (R_center ** 2) * (detector.close_distance / R_center)
    
    # Also calculate what omega SHOULD scale as (proportional to pixel_size^2)
    # If we fix R (approximately), omega ∝ pixel_size^2
    
    print(f"Pixel size: {px} mm")
    print(f"  pixel_size_m: {pixel_size_m:.6f}")
    print(f"  R_center (m): {R_center:.6f}")
    print(f"  close_distance (m): {detector.close_distance:.6f}")
    print(f"  Omega: {omega_center:.10e}")
    print(f"  Omega/px²: {omega_center / (pixel_size_m**2):.10e}")
    print()

print("\nScaling Check: Omega should scale as pixel_size²")
print("=" * 80)

# Reference: 0.1mm case
ref_px = 0.1
ref_config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    distance_mm=100.0,
    pixel_size_mm=ref_px,
    spixels=256,
    fpixels=256,
    beam_center_s=fixed_beam_mm,
    beam_center_f=fixed_beam_mm,
)
ref_detector = Detector(ref_config)
ref_coords = ref_detector.get_pixel_coords()
ref_omega = ref_detector.get_solid_angle(ref_coords)[128, 128]

for px in pixel_sizes:
    config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        distance_mm=100.0,
        pixel_size_mm=px,
        spixels=256,
        fpixels=256,
        beam_center_s=fixed_beam_mm,
        beam_center_f=fixed_beam_mm,
    )
    
    detector = Detector(config)
    pixel_coords = detector.get_pixel_coords()
    omega = detector.get_solid_angle(pixel_coords)[128, 128]
    
    expected_ratio = (px / ref_px) ** 2
    actual_ratio = omega / ref_omega
    
    print(f"Pixel size: {px} mm")
    print(f"  Expected omega ratio (vs 0.1mm): {expected_ratio:.6f}")
    print(f"  Actual omega ratio: {actual_ratio:.6f}")
    print(f"  Match: {abs(actual_ratio - expected_ratio) < 0.01}")
    print()
