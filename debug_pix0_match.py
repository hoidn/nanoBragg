import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from src.nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot
from src.nanobrag_torch.models.detector import Detector
import torch

# Match exact C configuration
config = DetectorConfig(
    distance_mm=100.0,
    pixel_size_mm=0.1, 
    spixels=1024,
    fpixels=1024,
    beam_center_s=51.2,  # mm
    beam_center_f=51.2,  # mm
    detector_rotx_deg=5.0,
    detector_roty_deg=3.0,
    detector_rotz_deg=2.0,
    detector_twotheta_deg=15.0,
    detector_convention=DetectorConvention.MOSFLM,
    detector_pivot=DetectorPivot.BEAM
)

detector = Detector(config)

print("Python pix0_vector:")
print(f"  {detector.pix0_vector}")

# From trace comparison report - C calculated pix0:
c_pix0 = [0.110113918740374, 0.0546471770153985, -0.0465243988887638]
print(f"\nC pix0_vector:")  
print(f"  {c_pix0}")

# Compare
python_pix0 = detector.pix0_vector.detach().numpy()
diff = python_pix0 - c_pix0
print(f"\nDifference (Python - C):")
print(f"  {diff}")
print(f"Max absolute difference: {max(abs(diff))}")
print(f"Relative error: {max(abs(diff / c_pix0)):.2e}")

# Check if they're essentially the same
if max(abs(diff)) < 1e-6:
    print("✅ PIX0 VECTORS MATCH - geometry calculations are correct!")
else:
    print("❌ PIX0 VECTORS DO NOT MATCH - geometry issue exists")