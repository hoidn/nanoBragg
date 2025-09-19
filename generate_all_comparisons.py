#!/usr/bin/env python
"""
Generate comparison PNGs for all passing AT-PARALLEL tests.
Organized approach to run C and PyTorch versions with test parameters.
"""

import os
import sys
import subprocess
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Define test scenarios based on passing tests
TEST_SCENARIOS = {
    "AT-PARALLEL-001": {
        "description": "Beam Center Scales with Detector Size",
        "scenarios": [
            {"name": "detector_64x64", "detpixels": 64},
            {"name": "detector_128x128", "detpixels": 128},
            {"name": "detector_256x256", "detpixels": 256},
            {"name": "detector_512x512", "detpixels": 512},
            {"name": "detector_1024x1024", "detpixels": 1024},
        ]
    },
    "AT-PARALLEL-003": {
        "description": "Detector Offset Preservation",
        "scenarios": [
            {"name": "offset_20_20", "detpixels": 256, "Xbeam": 20, "Ybeam": 20},
            {"name": "offset_30_40", "detpixels": 256, "Xbeam": 30, "Ybeam": 40},
            {"name": "offset_45_25", "detpixels": 256, "Xbeam": 45, "Ybeam": 25},
            {"name": "center_256", "detpixels": 256},  # Default center
            {"name": "center_512", "detpixels": 512},  # Default center
            {"name": "center_1024", "detpixels": 1024},  # Default center
        ]
    }
}

# Common parameters for all tests
COMMON_PARAMS = {
    "cell": "100 100 100 90 90 90",
    "lambda": "6.2",
    "N": "3",
    "distance": "100",
    "pixel": "0.1",
    "default_F": "100",
    "hkl": "test_comparison.hkl"
}


def ensure_hkl_file():
    """Create HKL file if it doesn't exist."""
    if not Path("test_comparison.hkl").exists():
        with open("test_comparison.hkl", "w") as f:
            f.write("0 0 0 100.0\n")
            f.write("1 0 0 50.0\n")
            f.write("0 1 0 50.0\n")
            f.write("0 0 1 50.0\n")
        print("Created test_comparison.hkl")


def run_simulation(is_c_version, scenario, output_file):
    """Run either C or PyTorch simulation with given parameters."""
    if is_c_version:
        cmd = ["./nanoBragg"]
    else:
        cmd = [sys.executable, "-m", "nanobrag_torch"]

    # Add common parameters
    cmd.extend([
        "-hkl", COMMON_PARAMS["hkl"],
        "-cell"] + COMMON_PARAMS["cell"].split() + [
        "-lambda", COMMON_PARAMS["lambda"],
        "-N", COMMON_PARAMS["N"],
        "-distance", COMMON_PARAMS["distance"],
        "-pixel", COMMON_PARAMS["pixel"],
        "-default_F", COMMON_PARAMS["default_F"],
        "-detpixels", str(scenario["detpixels"]),
        "-floatfile", output_file
    ])

    # Add optional beam center if specified
    if "Xbeam" in scenario and "Ybeam" in scenario:
        cmd.extend(["-Xbeam", str(scenario["Xbeam"]), "-Ybeam", str(scenario["Ybeam"])])

    # Run with environment variable for PyTorch
    env = os.environ.copy()
    env["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        print(f"Error running {'C' if is_c_version else 'PyTorch'}: {result.stderr}")
        return False
    return True


def generate_comparison(c_file, pytorch_file, output_dir, scenario_name, detpixels):
    """Generate comparison plots for C and PyTorch outputs."""
    # Load the binary files
    with open(c_file, 'rb') as f:
        c_data = np.frombuffer(f.read(), dtype=np.float32)
        c_image = c_data.reshape(detpixels, detpixels)

    with open(pytorch_file, 'rb') as f:
        pytorch_data = np.frombuffer(f.read(), dtype=np.float32)
        pytorch_image = pytorch_data.reshape(detpixels, detpixels)

    # Calculate statistics
    c_peak = np.unravel_index(np.argmax(c_image), c_image.shape)
    pytorch_peak = np.unravel_index(np.argmax(pytorch_image), pytorch_image.shape)
    correlation = np.corrcoef(c_image.flatten(), pytorch_image.flatten())[0, 1]
    diff = pytorch_image - c_image

    # Create comparison plot
    fig = plt.figure(figsize=(15, 5))

    # C output
    ax1 = plt.subplot(1, 3, 1)
    im1 = ax1.imshow(c_image, origin='lower', cmap='hot')
    ax1.set_title(f'C Output\nMax={c_image.max():.3f} at {c_peak}')
    ax1.plot(c_peak[1], c_peak[0], 'c+', markersize=10)
    plt.colorbar(im1, ax=ax1)

    # PyTorch output
    ax2 = plt.subplot(1, 3, 2)
    im2 = ax2.imshow(pytorch_image, origin='lower', cmap='hot')
    ax2.set_title(f'PyTorch Output\nMax={pytorch_image.max():.3f} at {pytorch_peak}')
    ax2.plot(pytorch_peak[1], pytorch_peak[0], 'c+', markersize=10)
    plt.colorbar(im2, ax=ax2)

    # Difference
    ax3 = plt.subplot(1, 3, 3)
    im3 = ax3.imshow(diff, origin='lower', cmap='RdBu',
                      vmin=-np.abs(diff).max(), vmax=np.abs(diff).max())
    ax3.set_title(f'Difference (PyTorch - C)\nCorr={correlation:.4f}, Max|Δ|={np.abs(diff).max():.3f}')
    plt.colorbar(im3, ax=ax3)

    plt.suptitle(f'{scenario_name} ({detpixels}x{detpixels} pixels)')
    plt.tight_layout()

    # Save comparison
    comparison_path = os.path.join(output_dir, "comparison.png")
    plt.savefig(comparison_path, dpi=150)
    plt.close()

    # Also save individual images
    # C output
    plt.figure(figsize=(6, 6))
    plt.imshow(c_image, origin='lower', cmap='hot')
    plt.colorbar()
    plt.title(f'C Output ({scenario_name})')
    plt.savefig(os.path.join(output_dir, "c_output.png"), dpi=150)
    plt.close()

    # PyTorch output
    plt.figure(figsize=(6, 6))
    plt.imshow(pytorch_image, origin='lower', cmap='hot')
    plt.colorbar()
    plt.title(f'PyTorch Output ({scenario_name})')
    plt.savefig(os.path.join(output_dir, "pytorch_output.png"), dpi=150)
    plt.close()

    return correlation


def main():
    """Main function to generate all comparisons."""
    print("=" * 60)
    print("Generating Comparison PNGs for Passing AT-PARALLEL Tests")
    print("=" * 60)

    # Ensure HKL file exists
    ensure_hkl_file()

    # Process each test suite
    for test_suite, test_data in TEST_SCENARIOS.items():
        print(f"\n### {test_suite}: {test_data['description']}")
        print("-" * 50)

        # Create base directory for this test suite
        base_dir = Path("tmp") / test_suite
        base_dir.mkdir(parents=True, exist_ok=True)

        # Process each scenario
        for scenario in test_data["scenarios"]:
            scenario_name = scenario["name"]
            detpixels = scenario["detpixels"]

            print(f"\nProcessing {scenario_name}...")

            # Create output directory
            output_dir = base_dir / scenario_name
            output_dir.mkdir(exist_ok=True)

            # File paths
            c_output = str(output_dir / "c_output.bin")
            pytorch_output = str(output_dir / "pytorch_output.bin")

            # Run C version
            print(f"  Running C version...")
            if not run_simulation(True, scenario, c_output):
                print(f"  Failed to run C version for {scenario_name}")
                continue

            # Run PyTorch version
            print(f"  Running PyTorch version...")
            if not run_simulation(False, scenario, pytorch_output):
                print(f"  Failed to run PyTorch version for {scenario_name}")
                continue

            # Generate comparison
            print(f"  Generating comparison plots...")
            correlation = generate_comparison(
                c_output, pytorch_output, str(output_dir),
                scenario_name, detpixels
            )

            print(f"  ✓ Correlation: {correlation:.4f}")
            print(f"  ✓ Saved to: {output_dir}/")

            # Create summary file
            summary_file = output_dir / "summary.txt"
            with open(summary_file, "w") as f:
                f.write(f"Test Suite: {test_suite}\n")
                f.write(f"Scenario: {scenario_name}\n")
                f.write(f"Detector Size: {detpixels}x{detpixels}\n")
                if "Xbeam" in scenario:
                    f.write(f"Beam Center: ({scenario['Xbeam']}, {scenario['Ybeam']}) mm\n")
                else:
                    f.write(f"Beam Center: Auto-calculated (detector center)\n")
                f.write(f"Correlation: {correlation:.6f}\n")

    print("\n" + "=" * 60)
    print("✓ All comparisons generated successfully!")
    print(f"✓ Output saved to: tmp/AT-PARALLEL-001/ and tmp/AT-PARALLEL-003/")
    print("=" * 60)


if __name__ == "__main__":
    main()