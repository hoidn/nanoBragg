"""Find strong on-peak pixels in AT-PARALLEL-012 triclinic case."""
import os
import struct
import numpy as np
from pathlib import Path
from scipy.ndimage import maximum_filter

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


def load_float_image(filename, shape):
    """Load binary float image."""
    with open(filename, 'rb') as f:
        data = f.read()
        n_floats = len(data) // 4
        floats = struct.unpack(f'{n_floats}f', data)
        return np.array(floats).reshape(shape)


def find_peaks(image, n_peaks=10, percentile=99.9):
    """Find local maxima peaks."""
    threshold = np.percentile(image, percentile)
    local_max = maximum_filter(image, size=3) == image
    peaks = np.where((local_max) & (image > threshold))

    if len(peaks[0]) == 0:
        return np.array([]).reshape(0, 2), np.array([])

    intensities = image[peaks]
    peak_coords = np.column_stack([peaks[0], peaks[1]])

    sorted_indices = np.argsort(intensities)[::-1][:n_peaks]
    return peak_coords[sorted_indices], intensities[sorted_indices]


def main():
    golden_file = Path(__file__).parent.parent / "tests/golden_data/triclinic_P1/image.bin"
    golden_image = load_float_image(str(golden_file), (512, 512))

    print("=== Strong Peaks in Triclinic Golden Data ===")
    print()

    peaks, intensities = find_peaks(golden_image, n_peaks=20, percentile=99.9)

    print("Top 20 peaks (slow, fast, intensity):")
    for i, (peak, intensity) in enumerate(zip(peaks, intensities)):
        s, f = peak
        print(f"  {i+1:2d}. ({s:3d}, {f:3d})  I = {intensity:10.3f}")

    print()
    print("Suggested pixels for tracing:")
    print(f"  - Strongest peak: ({peaks[0][0]}, {peaks[0][1]}) with I = {intensities[0]:.3f}")
    print(f"  - Mid-intensity peak: ({peaks[5][0]}, {peaks[5][1]}) with I = {intensities[5]:.3f}")
    print()

    # Check beam center region
    beam_center = (256, 256)  # 512/2 for MOSFLM
    print(f"Beam center (approximate): {beam_center}")
    print(f"Beam center intensity: {golden_image[beam_center[0], beam_center[1]]:.3f}")


if __name__ == "__main__":
    main()