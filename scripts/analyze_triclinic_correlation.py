#!/usr/bin/env python
"""Analyze why triclinic correlation is still low after F_latt fix."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
from pathlib import Path
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.config import CrystalConfig, DetectorConfig

# Set up triclinic crystal exactly as in the test
device = torch.device("cpu")
dtype = torch.float64

# Triclinic crystal parameters from test
triclinic_config = CrystalConfig(
    cell_a=70.0,
    cell_b=80.0,
    cell_c=90.0,
    cell_alpha=75.0391,
    cell_beta=85.0136,
    cell_gamma=95.0081,
    N_cells=[5, 5, 5],  # From params.json: N_cells=5
    misset_deg=[-89.968546, -31.328953, 177.753396],
)

crystal = Crystal(config=triclinic_config, device=device, dtype=dtype)

# Create detector config that matches triclinic golden data parameters
from nanobrag_torch.config import DetectorPivot
triclinic_detector_config = DetectorConfig(
    distance_mm=100.0,      # From params.json
    pixel_size_mm=0.1,      # From params.json  
    spixels=512,            # From params.json (detpixels)
    fpixels=512,            # From params.json (detpixels)
    beam_center_s=25.6,     # Center of 512x512 detector: 256 pixels * 0.1mm = 25.6mm
    beam_center_f=25.6,     # Center of 512x512 detector: 256 pixels * 0.1mm = 25.6mm
    detector_pivot=DetectorPivot.BEAM  # C-code uses BEAM pivot: "pivoting detector around direct beam spot"
)

detector = Detector(config=triclinic_detector_config, device=device, dtype=dtype)

crystal_rot_config = CrystalConfig(
    phi_start_deg=torch.tensor(0.0, device=device, dtype=dtype),
    osc_range_deg=torch.tensor(0.0, device=device, dtype=dtype),
    mosaic_spread_deg=torch.tensor(0.0, device=device, dtype=dtype),
    mosaic_domains=1,
)

simulator = Simulator(
    crystal,
    detector,
    crystal_config=crystal_rot_config,
    device=device,
    dtype=dtype,
)

# Override wavelength to match golden data
simulator.wavelength = 1.0

print("Running PyTorch simulation...")

# Debug: Check detector properties that affect intensity scaling
print(f"Detector distance (Angstroms): {detector.distance}")
print(f"Detector pixel_size (Angstroms): {detector.pixel_size}")
print(f"Crystal N_cells: {crystal.N_cells_a}, {crystal.N_cells_b}, {crystal.N_cells_c}")

pytorch_image = simulator.run()

# Load golden data
golden_path = Path("tests/golden_data/triclinic_P1/image.bin")
if golden_path.exists():
    golden_data = torch.from_numpy(
        np.fromfile(str(golden_path), dtype=np.float32).reshape(512, 512)
    ).to(dtype=torch.float64)
    
    # Calculate correlation
    correlation = torch.corrcoef(
        torch.stack([pytorch_image.flatten(), golden_data.flatten()])
    )[0, 1]
    
    print(f"\nCorrelation: {correlation:.6f}")
    print(f"PyTorch max: {torch.max(pytorch_image):.3e}")
    print(f"Golden max: {torch.max(golden_data):.3e}")
    print(f"PyTorch sum: {torch.sum(pytorch_image):.3e}")
    print(f"Golden sum: {torch.sum(golden_data):.3e}")
    
    # Analyze the differences
    diff = pytorch_image - golden_data
    abs_diff = torch.abs(diff)
    rel_diff = abs_diff / (golden_data + 1e-10)
    
    print(f"\nDifference statistics:")
    print(f"Max absolute diff: {torch.max(abs_diff):.3e}")
    print(f"Mean absolute diff: {torch.mean(abs_diff):.3e}")
    print(f"Max relative diff: {torch.max(rel_diff[golden_data > 0.1]):.3f}")
    
    # Find pixels with largest differences
    flat_diff = abs_diff.flatten()
    top_diffs = torch.topk(flat_diff, 10)
    
    print(f"\nTop 10 pixel differences:")
    for i, (diff_val, idx) in enumerate(zip(top_diffs.values, top_diffs.indices)):
        row = idx // 512
        col = idx % 512
        py_val = pytorch_image[row, col]
        gold_val = golden_data[row, col]
        print(f"  ({row}, {col}): PyTorch={py_val:.3f}, Golden={gold_val:.3f}, Diff={diff_val:.3f}")
    
    # Check if it's a systematic scale issue
    scale = torch.sum(pytorch_image) / torch.sum(golden_data)
    scaled_pytorch = pytorch_image / scale
    scaled_corr = torch.corrcoef(
        torch.stack([scaled_pytorch.flatten(), golden_data.flatten()])
    )[0, 1]
    print(f"\nIf we scale PyTorch by {scale:.3f}:")
    print(f"Scaled correlation: {scaled_corr:.6f}")
    
    # Save difference image for visualization
    diff_img = (abs_diff / torch.max(abs_diff) * 255).to(torch.uint8).numpy()
    from PIL import Image
    Image.fromarray(diff_img).save("triclinic_difference_map.png")
    print("\nSaved difference map to triclinic_difference_map.png")
else:
    print(f"Golden data not found at {golden_path}")