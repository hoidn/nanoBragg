import torch
from nanobrag_torch.config import DetectorConfig, DetectorPivot, DetectorConvention
from nanobrag_torch.models.detector import Detector

def _unit(v): 
    return v / torch.norm(v)

def _beam_vec(det):
    # Incident beam direction by convention
    return torch.tensor([1.0, 0.0, 0.0], dtype=det.dtype, device=det.device) \
           if det.config.detector_convention == DetectorConvention.MOSFLM \
           else torch.tensor([0.0, 0.0, 1.0], dtype=det.dtype, device=det.device)

def _beam_point_world(det):
    # World-space location where the direct beam hits the detector plane
    return det.distance * _beam_vec(det)  # meters

def _beam_indices(det):
    """
    Return the continuous (s,f) indices (in pixel units) of the direct-beam hit,
    by projecting the beam point onto the detector basis.
    """
    bp = _beam_point_world(det)
    ds = torch.dot(bp - det.pix0_vector, det.sdet_vec) / det.pixel_size
    df = torch.dot(bp - det.pix0_vector, det.fdet_vec) / det.pixel_size
    return ds, df

def test_beam_pivot_keeps_beam_indices_and_alignment():
    cfg = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.BEAM,
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=1024, fpixels=1024,
        beam_center_s=51.2, beam_center_f=51.2,
        detector_twotheta_deg=0.0,
    )
    d = Detector(cfg, dtype=torch.float64)

    # 1) Direct beam fractional indices must be equal to beam_center_s and beam_center_f
    # (Note: MOSFLM +0.5 offset is already included in d.beam_center_s/f)
    s0, f0 = _beam_indices(d)
    assert torch.allclose(s0, d.beam_center_s, atol=1e-12)
    assert torch.allclose(f0, d.beam_center_f, atol=1e-12)

    # 2) Rotating two-theta under BEAM pivot preserves those indices
    d.config.detector_twotheta_deg = 15.0
    d.invalidate_cache()
    s1, f1 = _beam_indices(d)
    assert torch.allclose(s1, s0, atol=1e-12)
    assert torch.allclose(f1, f0, atol=1e-12)

    # 3) For the integer beam_center pixel, with center-based indexing (pixels at 0.5, 1.5, 2.5...)
    # the pixel center is at the beam position
    coords = d.get_pixel_coords()
    p_int = coords[int(d.beam_center_s.item()), int(d.beam_center_f.item())]
    # With center-based indexing, the pixel is centered at its index position
    expected = _unit(d.distance * _beam_vec(d))
    assert torch.allclose(_unit(p_int), expected, atol=1e-12)

def test_sample_pivot_moves_beam_indices_with_twotheta():
    cfg = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.SAMPLE,
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=1024, fpixels=1024,
        beam_center_s=51.2, beam_center_f=51.2,
        detector_twotheta_deg=0.0,
    )
    d = Detector(cfg, dtype=torch.float64)

    # At zero rotation with center-based indexing, beam indices equal beam centers
    s0, f0 = _beam_indices(d)
    assert torch.allclose(s0, d.beam_center_s, atol=1e-12)
    assert torch.allclose(f0, d.beam_center_f, atol=1e-12)

    # Under SAMPLE pivot, changing two-theta *moves* the beam's (s,f) indices
    d.config.detector_twotheta_deg = 15.0
    d.invalidate_cache()
    s1, f1 = _beam_indices(d)
    assert torch.abs(s1 - s0) > 1e-6 or torch.abs(f1 - f0) > 1e-6

    # And the old integer pixel index is no longer aligned with the beam
    coords = d.get_pixel_coords()
    p_old = coords[int(d.beam_center_s.item()), int(d.beam_center_f.item())]
    assert not torch.allclose(_unit(p_old), _unit(_beam_point_world(d)), atol=1e-6)