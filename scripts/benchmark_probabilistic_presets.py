"""Tunable geometry presets for probabilistic benchmarks.

This module defines BenchmarkScenario dataclass and PRESETS dictionary
for different detector/beam configurations used in mosaic refinement benchmarks.
"""

from dataclasses import dataclass


@dataclass
class BenchmarkScenario:
    """Tunable geometry preset for probabilistic benchmarks."""
    cell_edge_A: float
    wavelength_A: float
    distance_mm: float
    pixel_size_mm: float
    fpixels: int
    spixels: int


PRESETS = {
    "default": BenchmarkScenario(
        cell_edge_A=100.0,
        wavelength_A=1.0,
        distance_mm=100.0,
        pixel_size_mm=0.1,
        fpixels=64,
        spixels=64,
    ),
    "hi_res_a": BenchmarkScenario(
        cell_edge_A=40.0,
        wavelength_A=0.65,
        distance_mm=80.0,
        pixel_size_mm=0.075,
        fpixels=96,
        spixels=96,
    ),
    "hi_res_b": BenchmarkScenario(
        cell_edge_A=30.0,
        wavelength_A=0.5,
        distance_mm=60.0,
        pixel_size_mm=0.05,
        fpixels=128,
        spixels=128,
    ),
}
