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
detector = Detector(config=config, dtype=torch.float64)

print(f"Actual pix0_vector: {detector.pix0_vector}")
print(f"Expected:           [0.1, 0.01005, -0.00005]")

# Debug the calculation components
print(f"fdet_vec: {detector.fdet_vec}")
print(f"sdet_vec: {detector.sdet_vec}")
print(f"odet_vec: {detector.odet_vec}")
print(f"distance: {detector.distance}")
print(f"beam_center_s: {detector.beam_center_s}")
print(f"beam_center_f: {detector.beam_center_f}")
print(f"pixel_size: {detector.pixel_size}")
