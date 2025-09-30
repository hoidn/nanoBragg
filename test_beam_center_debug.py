"""Debug beam center and pix0_vector calculation."""
import torch
from src.nanobrag_torch.config import DetectorConfig, DetectorConvention
from src.nanobrag_torch.models.detector import Detector

pixel_sizes = [0.05, 0.1, 0.2, 0.4]
fixed_beam_mm = 25.6

print("Beam Center Debug")
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
    
    # Calculate expected beam center in pixels (MOSFLM +0.5)
    expected_beam_px = fixed_beam_mm / px + 0.5
    
    # Get pixel coordinates
    pixel_coords = detector.get_pixel_coords()
    
    # Get center pixel (128, 128) coordinates
    center_coord = pixel_coords[128, 128]
    R_center = torch.norm(center_coord)
    
    # Calculate beam center position from detector internals
    # beam_center_s and beam_center_f are in PIXELS (with MOSFLM +0.5)
    beam_s_px = detector.beam_center_s
    beam_f_px = detector.beam_center_f
    
    # Convert to mm
    beam_s_mm = (beam_s_px - 0.5) * px  # Remove MOSFLM offset and convert
    beam_f_mm = (beam_f_px - 0.5) * px
    
    # Get pix0_vector
    pix0 = detector.pix0_vector
    
    print(f"\nPixel size: {px} mm")
    print(f"  Detector spixels × fpixels: {detector.spixels} × {detector.fpixels}")
    print(f"  Expected beam center (pixels): {expected_beam_px:.2f}")
    print(f"  Detector beam_center_s (pixels): {beam_s_px:.4f}")
    print(f"  Detector beam_center_f (pixels): {beam_f_px:.4f}")
    print(f"  Reconstructed beam_s (mm): {beam_s_mm:.4f} (should be {fixed_beam_mm})")
    print(f"  Reconstructed beam_f (mm): {beam_f_mm:.4f} (should be {fixed_beam_mm})")
    print(f"  pixel_size (m): {detector.pixel_size:.6f}")
    print(f"  pix0_vector: [{pix0[0]:.6f}, {pix0[1]:.6f}, {pix0[2]:.6f}]")
    print(f"  Center pixel coord: [{center_coord[0]:.6f}, {center_coord[1]:.6f}, {center_coord[2]:.6f}]")
    print(f"  R_center (m): {R_center:.6f}")
    print(f"  Expected R_center (m): ~0.102 (should be roughly constant)")
