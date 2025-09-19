#!/usr/bin/env python
"""
Run a small subset of AT-PARALLEL tests with visual outputs.
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
        "--"
    ] + args.split()

    print(f"\n{'='*60}")
    print(f"Running: {test_name}")
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
            cwd=Path(__file__).parent.parent,
            timeout=60  # 60 second timeout per test
        )

        # Save stdout/stderr for debugging
        with open(test_output_dir / "run_log.txt", "w") as f:
            f.write(f"Command: {' '.join(cmd)}\n")
            f.write(f"Return code: {result.returncode}\n\n")
            f.write(f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n")

        # Parse summary if it exists
        summary_file = test_output_dir / "summary.json"
        if summary_file.exists():
            with open(summary_file) as f:
                summary = json.load(f)
                correlation = summary.get("correlation", "N/A")
                print(f"✓ Correlation: {correlation:.4f}" if isinstance(correlation, (int, float)) else f"✗ Failed to compute correlation")
        else:
            # Check if we have output from stdout
            if "Correlation:" in result.stdout:
                for line in result.stdout.split('\n'):
                    if "Correlation:" in line:
                        print(f"  {line.strip()}")
                        break

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print(f"✗ Timeout after 60 seconds")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Run selected parallel tests with visual outputs."""

    output_dir = setup_output_directory()
    print(f"Output directory: {output_dir}")

    # Define a small subset of test configurations
    # Note: Using -N 5 to get reasonable fluence defaults from C code
    tests = {
        "AT-PARALLEL-001_64x64": "-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -detpixels 64 -distance 100",
        "AT-PARALLEL-001_256x256": "-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -detpixels 256 -distance 100",

        "AT-PARALLEL-002_pixel_0.1mm": "-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -detpixels 256 -pixel 0.1 -distance 100",
        "AT-PARALLEL-002_pixel_0.2mm": "-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -detpixels 128 -pixel 0.2 -distance 100",

        "AT-PARALLEL-004_MOSFLM": "-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -detpixels 256 -distance 100 -mosflm",
        "AT-PARALLEL-004_XDS": "-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -detpixels 256 -distance 100 -xds",

        "AT-PARALLEL-007_with_rotations": "-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -detpixels 256 -pixel 0.1 -distance 100 -detector_rotx 5 -detector_roty 3 -detector_rotz 2 -twotheta 10",
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
    print(f"View PNG files in: {output_dir}/*/")

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
        .images { display: flex; gap: 10px; flex-wrap: wrap; }
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
        for img_name, label in [("c_image.png", "C Code"), ("pytorch_image.png", "PyTorch"), ("diff_image.png", "Difference")]:
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