import torch
from nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models.detector import Detector

config = DetectorConfig(
    distance_mm=100.0,
    pixel_size_mm=0.1,
    beam_center_s=10.0,  # 10mm offset on SLOW axis
    beam_center_f=0.0,  # 0mm offset on FAST axis
    detector_convention=DetectorConvention.MOSFLM,
    detector_pivot=DetectorPivot.BEAM,
)

print("Config values:")
print(f"  distance_mm: {config.distance_mm}")
print(f"  pixel_size_mm: {config.pixel_size_mm}")
print(f"  beam_center_s: {config.beam_center_s}")
print(f"  beam_center_f: {config.beam_center_f}")
print()

detector = Detector(config=config, dtype=torch.float64)

print("Detector internal values:")
print(f"  distance: {detector.distance}")
print(f"  pixel_size: {detector.pixel_size}")
print(f"  beam_center_s: {detector.beam_center_s}")
print(f"  beam_center_f: {detector.beam_center_f}")
print()

# Manual calculation as the test expects:
# Fbeam = (Ybeam + 0.5*pixel_size)/1000 = (0 + 0.05)/1000 = 0.00005 m
# Sbeam = (Xbeam + 0.5*pixel_size)/1000 = (10 + 0.05)/1000 = 0.01005 m
# pix0 = -Fbeam*fdet - Sbeam*sdet + dist*beam
#      = -0.00005*[0,0,1] - 0.01005*[0,-1,0] + 0.1*[1,0,0]
#      = [0.1, +0.01005, -0.00005]

print("Expected manual calculation:")
fdet_vec = torch.tensor([0., 0., 1.])
sdet_vec = torch.tensor([0., -1., 0.])
beam_vec = torch.tensor([1., 0., 0.])

# Test expectation: beam_center_f (fast axis) -> Ybeam -> Fbeam
# Test expectation: beam_center_s (slow axis) -> Xbeam -> Sbeam
Fbeam_expected = (config.beam_center_f + 0.5 * config.pixel_size_mm) / 1000.0  # 0.00005
Sbeam_expected = (config.beam_center_s + 0.5 * config.pixel_size_mm) / 1000.0  # 0.01005

print(f"  Fbeam_expected: {Fbeam_expected}")
print(f"  Sbeam_expected: {Sbeam_expected}")

expected_pix0 = -Fbeam_expected * fdet_vec - Sbeam_expected * sdet_vec + detector.distance * beam_vec
print(f"  expected_pix0: {expected_pix0}")
print(f"  actual_pix0:   {detector.pix0_vector}")
