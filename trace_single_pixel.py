import torch
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.config import DetectorConfig, CrystalConfig

# Setup matching C config
detector_config = DetectorConfig(
    distance_mm=100.0,
    pixel_size_mm=0.1,
    beam_center_s=51.2,
    beam_center_f=51.2
)

crystal_config = CrystalConfig(
    cell_a=100.0,
    cell_b=100.0,
    cell_c=100.0
)

detector = Detector(detector_config)
crystal = Crystal(crystal_config)

# Get position of pixel 512,512
positions = detector.get_pixel_coords()
pixel_pos = positions[512, 512]

print(f"Pixel (512,512) position: {pixel_pos.numpy()} meters")

# The issue might be in unit mixing - detector uses meters, crystal uses Angstroms
print(f"Detector distance: {detector.distance} meters")
print(f"Crystal cell_a: {crystal.cell_a} Angstroms")

# This is the problem - we're mixing unit systems!
# Detector geometry is in METERS
# Crystal/physics calculations are in ANGSTROMS
# We need to convert properly

pixel_pos_angstroms = pixel_pos * 1e10  # Convert meters to Angstroms
print(f"Pixel position in Angstroms: {pixel_pos_angstroms.numpy()}")

# Now calculate scattering
wavelength = 6.2  # Angstroms
incident = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)

# Diffracted beam - but pixel_pos needs to be in same units!
# This is likely THE BUG - unit mismatch between detector (meters) and physics (Angstroms)
diffracted = pixel_pos_angstroms / torch.norm(pixel_pos_angstroms)
print(f"Diffracted direction: {diffracted.numpy()}")

# Scattering vector
S = (diffracted - incident) / wavelength
print(f"Scattering vector S: {S.numpy()} (1/Å)")
