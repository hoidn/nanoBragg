from src.nanobrag_torch.config import DetectorConfig
from src.nanobrag_torch.models.detector import Detector
import torch

config = DetectorConfig(
    beam_center_s=51.2,  # mm
    beam_center_f=51.2,  # mm
    pixel_size_mm=0.1
)

detector = Detector(config)

print(f"Config beam_center_s: {config.beam_center_s} mm")
print(f"Config beam_center_f: {config.beam_center_f} mm")
print(f"Detector beam_center_s: {detector.beam_center_s} pixels")
print(f"Detector beam_center_f: {detector.beam_center_f} pixels")

# Should be 51.2 / 0.1 = 512 pixels
expected = 51.2 / 0.1
print(f"Expected: {expected} pixels")

# Test the pixel_size conversion
print(f"Config pixel_size_mm: {config.pixel_size_mm} mm") 
print(f"Detector pixel_size: {detector.pixel_size} meters")
expected_pixel_size = config.pixel_size_mm / 1000.0
print(f"Expected pixel_size: {expected_pixel_size} meters")

# Test the BEAM pivot calculation
print(f"\nTesting BEAM pivot calculation:")
print(f"Fbeam_pixels = {config.beam_center_s / config.pixel_size_mm} pixels")  # S→F swap
print(f"Sbeam_pixels = {config.beam_center_f / config.pixel_size_mm} pixels")  # F→S swap
fbeam = (config.beam_center_s / config.pixel_size_mm + 0.5) * detector.pixel_size
sbeam = (config.beam_center_f / config.pixel_size_mm + 0.5) * detector.pixel_size
print(f"Fbeam: {fbeam} meters")
print(f"Sbeam: {sbeam} meters")

# This should be around 0.0512 meters for beam_center=51.2mm, pixel=0.1mm
expected_fbeam = (51.2/0.1 + 0.5) * 0.0001  # meters
print(f"Expected Fbeam: {expected_fbeam} meters")