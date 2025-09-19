#!/usr/bin/env python
"""Debug script to compare triclinic crystal vectors between C and PyTorch."""

import os
import subprocess
import torch
import numpy as np

# Set up environment
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Import PyTorch implementation
from nanobrag_torch.config import CrystalConfig, BeamConfig
from nanobrag_torch.models import Crystal

def run_c_trace():
    """Run C code with trace output to get real-space vectors."""
    # Create a simple C program to output the vectors
    c_code = """
#include <stdio.h>
#include <math.h>

int main() {
    // Triclinic cell parameters matching test
    double a = 70.0, b = 80.0, c = 90.0;
    double alpha = 85.0 * M_PI / 180.0;
    double beta = 95.0 * M_PI / 180.0;
    double gamma = 105.0 * M_PI / 180.0;

    // Calculate volume using C formula
    double aavg = (alpha + beta + gamma) / 2.0;
    double skew = sin(aavg) * sin(aavg - alpha) * sin(aavg - beta) * sin(aavg - gamma);
    if (skew < 0) skew = -skew;
    double V = 2.0 * a * b * c * sqrt(skew);

    // Calculate reciprocal cell parameters
    double V_star = 1.0 / V;
    double a_star_length = b * c * sin(alpha) * V_star;
    double b_star_length = c * a * sin(beta) * V_star;
    double c_star_length = a * b * sin(gamma) * V_star;

    // Calculate reciprocal angles
    double cos_alpha = cos(alpha);
    double cos_beta = cos(beta);
    double cos_gamma = cos(gamma);
    double sin_gamma = sin(gamma);

    double cos_alpha_star = (cos_beta * cos_gamma - cos_alpha) / (sin(beta) * sin_gamma);
    double cos_beta_star = (cos_gamma * cos_alpha - cos_beta) / (sin_gamma * sin(alpha));
    double cos_gamma_star = (cos_alpha * cos_beta - cos_gamma) / (sin(alpha) * sin(beta));
    double sin_gamma_star = sqrt(1.0 - cos_gamma_star * cos_gamma_star);

    // Construct reciprocal vectors in default orientation
    double a_star[3] = {a_star_length, 0.0, 0.0};
    double b_star[3] = {b_star_length * cos_gamma_star, b_star_length * sin_gamma_star, 0.0};
    double c_star[3] = {
        c_star_length * cos_beta_star,
        c_star_length * (cos_alpha_star - cos_beta_star * cos_gamma_star) / sin_gamma_star,
        c_star_length * V / (a * b * c * sin_gamma_star)
    };

    // Calculate real-space vectors from reciprocal
    // Cross products
    double b_star_cross_c_star[3] = {
        b_star[1] * c_star[2] - b_star[2] * c_star[1],
        b_star[2] * c_star[0] - b_star[0] * c_star[2],
        b_star[0] * c_star[1] - b_star[1] * c_star[0]
    };

    double c_star_cross_a_star[3] = {
        c_star[1] * a_star[2] - c_star[2] * a_star[1],
        c_star[2] * a_star[0] - c_star[0] * a_star[2],
        c_star[0] * a_star[1] - c_star[1] * a_star[0]
    };

    double a_star_cross_b_star[3] = {
        a_star[1] * b_star[2] - a_star[2] * b_star[1],
        a_star[2] * b_star[0] - a_star[0] * b_star[2],
        a_star[0] * b_star[1] - a_star[1] * b_star[0]
    };

    // Real-space vectors
    double a_vec[3], b_vec[3], c_vec[3];
    for (int i = 0; i < 3; i++) {
        a_vec[i] = b_star_cross_c_star[i] * V;
        b_vec[i] = c_star_cross_a_star[i] * V;
        c_vec[i] = a_star_cross_b_star[i] * V;
    }

    printf("C calculation results:\\n");
    printf("Volume: %.8f\\n", V);
    printf("a_star: %.8f %.8f %.8f\\n", a_star[0], a_star[1], a_star[2]);
    printf("b_star: %.8f %.8f %.8f\\n", b_star[0], b_star[1], b_star[2]);
    printf("c_star: %.8f %.8f %.8f\\n", c_star[0], c_star[1], c_star[2]);
    printf("a_vec: %.8f %.8f %.8f\\n", a_vec[0], a_vec[1], a_vec[2]);
    printf("b_vec: %.8f %.8f %.8f\\n", b_vec[0], b_vec[1], b_vec[2]);
    printf("c_vec: %.8f %.8f %.8f\\n", c_vec[0], c_vec[1], c_vec[2]);

    return 0;
}
"""

    # Write and compile the C code
    with open('/tmp/test_triclinic.c', 'w') as f:
        f.write(c_code)

    subprocess.run(['gcc', '-o', '/tmp/test_triclinic', '/tmp/test_triclinic.c', '-lm'], check=True)
    result = subprocess.run(['/tmp/test_triclinic'], capture_output=True, text=True)
    print("=" * 60)
    print(result.stdout)
    print("=" * 60)

    return result.stdout

def run_pytorch_trace():
    """Run PyTorch code to get real-space vectors."""
    # Create crystal with same parameters as test
    crystal_config = CrystalConfig(
        cell_a=70.0,
        cell_b=80.0,
        cell_c=90.0,
        cell_alpha=85.0,
        cell_beta=95.0,
        cell_gamma=105.0,
        N_cells=(1, 1, 1),
        default_F=100.0
    )

    beam_config = BeamConfig(wavelength_A=1.5)

    # Create crystal
    crystal = Crystal(crystal_config, beam_config)

    # Get the vectors
    print("PyTorch calculation results:")
    print(f"Volume: {crystal.V.item():.8f}")
    print(f"a_star: {crystal.a_star[0].item():.8f} {crystal.a_star[1].item():.8f} {crystal.a_star[2].item():.8f}")
    print(f"b_star: {crystal.b_star[0].item():.8f} {crystal.b_star[1].item():.8f} {crystal.b_star[2].item():.8f}")
    print(f"c_star: {crystal.c_star[0].item():.8f} {crystal.c_star[1].item():.8f} {crystal.c_star[2].item():.8f}")
    print(f"a_vec: {crystal.a[0].item():.8f} {crystal.a[1].item():.8f} {crystal.a[2].item():.8f}")
    print(f"b_vec: {crystal.b[0].item():.8f} {crystal.b[1].item():.8f} {crystal.b[2].item():.8f}")
    print(f"c_vec: {crystal.c[0].item():.8f} {crystal.c[1].item():.8f} {crystal.c[2].item():.8f}")

    # Calculate magnitudes for comparison
    a_mag = torch.norm(crystal.a).item()
    b_mag = torch.norm(crystal.b).item()
    c_mag = torch.norm(crystal.c).item()

    print(f"\nMagnitudes: |a|={a_mag:.8f} |b|={b_mag:.8f} |c|={c_mag:.8f}")

    # Check metric duality
    a_dot_a_star = torch.dot(crystal.a, crystal.a_star).item()
    b_dot_b_star = torch.dot(crystal.b, crystal.b_star).item()
    c_dot_c_star = torch.dot(crystal.c, crystal.c_star).item()

    print(f"Metric duality check: a·a*={a_dot_a_star:.8f} b·b*={b_dot_b_star:.8f} c·c*={c_dot_c_star:.8f}")

if __name__ == "__main__":
    # Run both traces and compare
    c_output = run_c_trace()
    print()
    run_pytorch_trace()

    # Parse and compare vectors
    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)

    # Extract values from C output
    c_lines = c_output.strip().split('\n')
    c_values = {}
    for line in c_lines:
        if ':' in line:
            key, vals = line.split(':')
            if key.strip() in ['a_vec', 'b_vec', 'c_vec', 'a_star', 'b_star', 'c_star']:
                c_values[key.strip()] = [float(v) for v in vals.strip().split()]

    # Compare with PyTorch
    crystal_config = CrystalConfig(
        cell_a=70.0,
        cell_b=80.0,
        cell_c=90.0,
        cell_alpha=85.0,
        cell_beta=95.0,
        cell_gamma=105.0,
        N_cells=(1, 1, 1),
        default_F=100.0
    )
    beam_config = BeamConfig(wavelength_A=1.5)
    crystal = Crystal(crystal_config, beam_config)

    for vec_name in ['a_vec', 'b_vec', 'c_vec']:
        if vec_name in c_values:
            c_vec = np.array(c_values[vec_name])
            if vec_name == 'a_vec':
                py_vec = crystal.a.numpy()
            elif vec_name == 'b_vec':
                py_vec = crystal.b.numpy()
            else:
                py_vec = crystal.c.numpy()

            diff = py_vec - c_vec
            print(f"\n{vec_name} difference (PyTorch - C):")
            print(f"  {diff[0]:.8f} {diff[1]:.8f} {diff[2]:.8f}")
            print(f"  |diff| = {np.linalg.norm(diff):.8f}")