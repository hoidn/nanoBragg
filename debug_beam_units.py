from src.nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot
from src.nanobrag_torch.models.detector import Detector
import torch

# Create config matching C command: -Xbeam 51.2 -Ybeam 51.2  
config = DetectorConfig(
    beam_center_s=51.2,  # mm -> Should map to Ybeam in C
    beam_center_f=51.2,  # mm -> Should map to Xbeam in C
    pixel_size_mm=0.1,
    distance_mm=100.0,
    detector_convention=DetectorConvention.MOSFLM,
    detector_pivot=DetectorPivot.BEAM
)

detector = Detector(config)

print(f"Config values:")
print(f"  beam_center_s: {config.beam_center_s} mm")
print(f"  beam_center_f: {config.beam_center_f} mm") 
print(f"  pixel_size_mm: {config.pixel_size_mm} mm")
print()

print(f"Detector properties:")
print(f"  beam_center_s (pixels): {detector.beam_center_s}")
print(f"  beam_center_f (pixels): {detector.beam_center_f}")
print(f"  pixel_size: {detector.pixel_size} meters")
print()

# Test _apply_mosflm_beam_convention
adjusted_f, adjusted_s = detector._apply_mosflm_beam_convention()
print(f"_apply_mosflm_beam_convention results:")
print(f"  adjusted_f: {adjusted_f} meters")
print(f"  adjusted_s: {adjusted_s} meters")
print()

# Test BEAM pivot calculation manually
Fbeam_pixels = config.beam_center_s / config.pixel_size_mm  # S→F axis swap  
Sbeam_pixels = config.beam_center_f / config.pixel_size_mm  # F→S axis swap
Fbeam = (Fbeam_pixels + 0.5) * detector.pixel_size
Sbeam = (Sbeam_pixels + 0.5) * detector.pixel_size

print(f"BEAM pivot calculation:")
print(f"  Fbeam_pixels: {Fbeam_pixels}")
print(f"  Sbeam_pixels: {Sbeam_pixels}")
print(f"  Fbeam: {Fbeam} meters")
print(f"  Sbeam: {Sbeam} meters")
print()

# According to trace, C expects:
# TRACE_C:Fbeam_m=0.05125
# TRACE_C:Sbeam_m=0.05125
print(f"Expected C values:")
print(f"  Fbeam_C: 0.05125 meters")
print(f"  Sbeam_C: 0.05125 meters")
print()

# Check if our values match
print(f"Python vs C comparison:")
print(f"  Fbeam: {float(Fbeam):.6f} vs 0.05125 (ratio: {float(Fbeam)/0.05125:.3f})")
print(f"  Sbeam: {float(Sbeam):.6f} vs 0.05125 (ratio: {float(Sbeam)/0.05125:.3f})")