#!/usr/bin/env python
"""
Run AT-PARALLEL tests with visual outputs organized in sensibly named directories.

This script runs the parallel validation tests and organizes their outputs
(especially PNG files) in a structured directory tree for easy visual comparison.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import json

# Ensure we can import nanobrag_torch
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def setup_output_directory():
    """Create main output directory with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"parallel_test_outputs_{timestamp}")
    output_dir.mkdir(exist_ok=True)
    return output_dir

def run_nb_compare(test_name, args, output_dir):
    """Run nb-compare tool and organize outputs."""
    test_output_dir = output_dir / test_name
    test_output_dir.mkdir(exist_ok=True)

    # Build command - use python script directly
    cmd = [
        "python", "scripts/nb_compare.py",
        "--outdir", str(test_output_dir),
        "--save-diff",
        "--"
    ] + args.split()

    print(f"\n{'='*60}")
    print(f"Running: {test_name}")
    print(f"Command: {' '.join(cmd)}")
    print(f"Output: {test_output_dir}")

    try:
        # Set environment for C code
        env = os.environ.copy()
        env["KMP_DUPLICATE_LIB_OK"] = "TRUE"
        env["NB_C_BIN"] = "./golden_suite_generator/nanoBragg"

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            cwd=Path(__file__).parent.parent
        )

        # Look for actual output directory created by nb-compare
        comparisons_dir = Path("comparisons")
        if comparisons_dir.exists():
            # Find the most recent comparison directory
            comp_dirs = sorted(comparisons_dir.glob("*"), key=lambda p: p.stat().st_mtime)
            if comp_dirs:
                latest_dir = comp_dirs[-1]
                # Move contents to our organized directory
                for item in latest_dir.iterdir():
                    shutil.move(str(item), str(test_output_dir / item.name))
                # Remove the empty directory
                latest_dir.rmdir()

        # Save stdout/stderr for debugging
        with open(test_output_dir / "run_log.txt", "w") as f:
            f.write(f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n")

        # Parse summary if it exists
        summary_file = test_output_dir / "summary.json"
        if summary_file.exists():
            with open(summary_file) as f:
                summary = json.load(f)
                correlation = summary.get("correlation", "N/A")
                print(f"✓ Correlation: {correlation:.4f}" if isinstance(correlation, (int, float)) else f"✗ Failed to compute correlation")
        else:
            print("✗ No summary.json found")

        return result.returncode == 0

    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Run all parallel tests with visual outputs."""

    output_dir = setup_output_directory()
    print(f"Output directory: {output_dir}")

    # Define test configurations
    tests = {
        "AT-PARALLEL-001_64x64": "-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -detpixels 64 -distance 100 -mosflm",
        "AT-PARALLEL-001_256x256": "-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -detpixels 256 -distance 100 -mosflm",
        "AT-PARALLEL-001_512x512": "-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -detpixels 512 -distance 100 -mosflm",

        "AT-PARALLEL-002_pixel_0.05mm": "-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -detpixels 256 -pixel 0.05 -distance 100 -mosflm",
        "AT-PARALLEL-002_pixel_0.1mm": "-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -detpixels 256 -pixel 0.1 -distance 100 -mosflm",
        "AT-PARALLEL-002_pixel_0.2mm": "-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -detpixels 256 -pixel 0.2 -distance 100 -mosflm",

        "AT-PARALLEL-003_offset_20_20": "-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -detpixels 256 -distance 100 -Xbeam 20 -Ybeam 20 -mosflm",
        "AT-PARALLEL-003_offset_30_40": "-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -detpixels 256 -distance 100 -Xbeam 30 -Ybeam 40 -mosflm",

        "AT-PARALLEL-004_MOSFLM": "-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -detpixels 256 -distance 100 -mosflm",
        "AT-PARALLEL-004_XDS": "-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -detpixels 256 -distance 100 -xds",

        "AT-PARALLEL-007_with_rotations": "-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -detpixels 256 -pixel 0.1 -distance 100 -detector_rotx 5 -detector_roty 3 -detector_rotz 2 -twotheta 10 -mosflm",

        "AT-PARALLEL-008_triclinic": "-default_F 100 -cell 70 80 90 75 85 95 -N 5 -lambda 6.2 -detpixels 512 -pixel 0.1 -distance 100 -mosflm",

        "AT-PARALLEL-009_N1": "-default_F 100 -cell 100 100 100 90 90 90 -N 1 -lambda 6.2 -detpixels 256 -distance 100 -mosflm",
        "AT-PARALLEL-009_N5": "-default_F 100 -cell 100 100 100 90 90 90 -N 5 -lambda 6.2 -detpixels 256 -distance 100 -mosflm",
        "AT-PARALLEL-009_N10": "-default_F 100 -cell 100 100 100 90 90 90 -N 10 -lambda 6.2 -detpixels 256 -distance 100 -mosflm",

        "AT-PARALLEL-010_dist_50mm": "-default_F 100 -cell 100 100 100 90 90 90 -N 5 -lambda 6.2 -detpixels 256 -distance 50 -mosflm",
        "AT-PARALLEL-010_dist_100mm": "-default_F 100 -cell 100 100 100 90 90 90 -N 5 -lambda 6.2 -detpixels 256 -distance 100 -mosflm",
        "AT-PARALLEL-010_dist_200mm": "-default_F 100 -cell 100 100 100 90 90 90 -N 5 -lambda 6.2 -detpixels 256 -distance 200 -mosflm",

        "AT-PARALLEL-011_unpolarized": "-default_F 100 -cell 100 100 100 90 90 90 -N 5 -lambda 6.2 -detpixels 256 -distance 100 -polar 0.0 -mosflm",
        "AT-PARALLEL-011_polarized": "-default_F 100 -cell 100 100 100 90 90 90 -N 5 -lambda 6.2 -detpixels 256 -distance 100 -polar 0.95 -mosflm",

        "AT-PARALLEL-021_phi_single": "-default_F 100 -cell 100 100 100 90 90 90 -N 5 -lambda 6.2 -detpixels 256 -distance 100 -phi 0 -osc 90 -phisteps 1 -mosflm",
        "AT-PARALLEL-021_phi_multi": "-default_F 100 -cell 100 100 100 90 90 90 -N 5 -lambda 6.2 -detpixels 256 -distance 100 -phi 0 -osc 90 -phisteps 9 -mosflm",

        "AT-PARALLEL-022_combined": "-default_F 100 -cell 100 100 100 90 90 90 -N 5 -lambda 6.2 -detpixels 256 -distance 100 -phi 0 -osc 90 -phisteps 1 -detector_rotx 5 -detector_roty 3 -detector_rotz 2 -twotheta 10 -mosflm",

        "AT-PARALLEL-023_misset_0": "-default_F 100 -cell 100 100 100 90 90 90 -N 5 -lambda 6.2 -detpixels 256 -distance 100 -misset 0 0 0 -mosflm",
        "AT-PARALLEL-023_misset_10_0_0": "-default_F 100 -cell 100 100 100 90 90 90 -N 5 -lambda 6.2 -detpixels 256 -distance 100 -misset 10 0 0 -mosflm",
        "AT-PARALLEL-023_misset_15_20_30": "-default_F 100 -cell 100 100 100 90 90 90 -N 5 -lambda 6.2 -detpixels 256 -distance 100 -misset 15 20 30 -mosflm",

        "AT-PARALLEL-025_cubic_center": "-default_F 100 -cell 100 100 100 90 90 90 -N 1 -lambda 1.0 -detpixels 64 -pixel 0.1 -distance 100 -mosflm",
        "AT-PARALLEL-025_cubic_offset": "-default_F 100 -cell 100 100 100 90 90 90 -N 1 -lambda 1.0 -detpixels 128 -pixel 0.1 -distance 100 -Xbeam 8.0 -Ybeam 10.0 -mosflm",
    }

    # Run tests
    results = {}
    for test_name, args in tests.items():
        success = run_nb_compare(test_name, args, output_dir)
        results[test_name] = "PASS" if success else "FAIL"

    # Create summary report
    print(f"\n{'='*60}")
    print("SUMMARY REPORT")
    print(f"{'='*60}")

    summary_file = output_dir / "SUMMARY.txt"
    with open(summary_file, "w") as f:
        f.write("PARALLEL TEST VISUAL COMPARISON SUMMARY\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"{'='*60}\n\n")

        passed = sum(1 for r in results.values() if r == "PASS")
        total = len(results)

        for test_name, result in sorted(results.items()):
            line = f"{test_name}: {result}"
            print(line)
            f.write(line + "\n")

        print(f"\n{'='*60}")
        print(f"Total: {passed}/{total} tests passed")
        f.write(f"\n{'='*60}\n")
        f.write(f"Total: {passed}/{total} tests passed\n")

    # Create index.html for easy browsing
    create_html_index(output_dir, results)

    print(f"\nOutputs saved to: {output_dir}")
    print(f"Open {output_dir}/index.html in a browser for visual comparison")

def create_html_index(output_dir, results):
    """Create an HTML index for easy visual browsing."""
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Parallel Test Visual Comparison</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .test { border: 1px solid #ccc; margin: 20px 0; padding: 10px; }
        .test h2 { margin-top: 0; }
        .images { display: flex; gap: 10px; }
        .images div { text-align: center; }
        .images img { max-width: 300px; border: 1px solid #ddd; }
        .pass { background-color: #e8f5e9; }
        .fail { background-color: #ffebee; }
        .correlation { font-weight: bold; }
    </style>
</head>
<body>
    <h1>Parallel Test Visual Comparison</h1>
"""

    for test_name in sorted(results.keys()):
        test_dir = output_dir / test_name
        result_class = "pass" if results[test_name] == "PASS" else "fail"

        html += f'<div class="test {result_class}">\n'
        html += f'<h2>{test_name} - {results[test_name]}</h2>\n'

        # Check for summary.json
        summary_file = test_dir / "summary.json"
        if summary_file.exists():
            with open(summary_file) as f:
                summary = json.load(f)
                correlation = summary.get("correlation", "N/A")
                if isinstance(correlation, (int, float)):
                    html += f'<p class="correlation">Correlation: {correlation:.6f}</p>\n'

        html += '<div class="images">\n'

        # Add images if they exist
        for img_name, label in [("c.png", "C Code"), ("py.png", "PyTorch"), ("diff.png", "Difference")]:
            img_path = test_dir / img_name
            if img_path.exists():
                rel_path = f"{test_name}/{img_name}"
                html += f'<div><img src="{rel_path}" alt="{label}"><br>{label}</div>\n'

        html += '</div>\n</div>\n'

    html += """
</body>
</html>
"""

    with open(output_dir / "index.html", "w") as f:
        f.write(html)

if __name__ == "__main__":
    main()