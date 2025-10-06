"""MOSFLM matrix file I/O utilities.

This module provides functions for reading MOSFLM-style orientation matrices,
which contain reciprocal lattice vectors scaled by wavelength.
"""

import numpy as np
from pathlib import Path
from typing import Tuple, Union


def read_mosflm_matrix(filepath: Union[str, Path], wavelength_A: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Read MOSFLM A matrix file and extract reciprocal lattice vectors.

    The MOSFLM A matrix format contains 9 values (3x3 matrix) where each row
    is a reciprocal lattice vector (a*, b*, c*) in units of Å^-1·(1/λ_Å).

    C-Code Implementation Reference (from nanoBragg.c, lines 3135-3148):
    ```c
    if(matfilename != NULL)
    {
        infile = fopen(matfilename,"r");
        if(infile != NULL)
        {
            printf("reading %s\n",matfilename);
            if(! fscanf(infile,"%lg%lg%lg",a_star+1,b_star+1,c_star+1)) {perror("fscanf");};
            if(! fscanf(infile,"%lg%lg%lg",a_star+2,b_star+2,c_star+2)) {perror("fscanf");};
            if(! fscanf(infile,"%lg%lg%lg",a_star+3,b_star+3,c_star+3)) {perror("fscanf");};
            fclose(infile);

            /* mosflm A matrix includes the wavelength, so remove it */
            /* calculate reciprocal cell lengths, store in 0th element */
            vector_scale(a_star,a_star,1e-10/lambda0);
            vector_scale(b_star,b_star,1e-10/lambda0);
            vector_scale(c_star,c_star,1e-10/lambda0);
        }
    }
    ```

    Args:
        filepath: Path to the MOSFLM matrix file
        wavelength_A: Wavelength in Angstroms for scaling

    Returns:
        Tuple of (a_star, b_star, c_star) reciprocal vectors in Å^-1

    Raises:
        FileNotFoundError: If the matrix file doesn't exist
        ValueError: If the file doesn't contain exactly 9 numeric values
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"MOSFLM matrix file not found: {filepath}")

    # Read all values from the file
    values = []
    with open(filepath, 'r') as f:
        for line in f:
            # Skip comments and empty lines
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Parse numeric values
            parts = line.split()
            for part in parts:
                try:
                    values.append(float(part))
                except ValueError:
                    continue

    if len(values) != 9:
        raise ValueError(
            f"MOSFLM matrix file must contain exactly 9 numeric values, "
            f"found {len(values)} in {filepath}"
        )

    # Reshape into 3x3 matrix (row-major order from file)
    matrix = np.array(values).reshape(3, 3)

    # C-code reads this matrix in column-major order (see lines 26-28 above):
    # First row  -> a_star[1], b_star[1], c_star[1]  (components of each vector)
    # Second row -> a_star[2], b_star[2], c_star[2]
    # Third row  -> a_star[3], b_star[3], c_star[3]
    # This means C extracts COLUMNS as reciprocal vectors, not rows.
    # We need to transpose to match C convention.
    matrix = matrix.T

    # Extract reciprocal vectors (now columns of original, rows after transpose)
    a_star_raw = matrix[0, :]
    b_star_raw = matrix[1, :]
    c_star_raw = matrix[2, :]

    # Scale to remove wavelength and convert to Å^-1
    # The values in the file are in units of Å^-1·(1/λ_Å)
    # We scale by (1e-10/lambda_m) where lambda_m = wavelength_A * 1e-10
    lambda_m = wavelength_A * 1e-10
    scale_factor = 1e-10 / lambda_m  # This equals 1/wavelength_A

    a_star = a_star_raw * scale_factor
    b_star = b_star_raw * scale_factor
    c_star = c_star_raw * scale_factor

    return a_star, b_star, c_star


def reciprocal_to_real_cell(a_star: np.ndarray,
                           b_star: np.ndarray,
                           c_star: np.ndarray) -> Tuple[float, float, float, float, float, float]:
    """Convert reciprocal lattice vectors to real-space cell parameters.

    Given reciprocal lattice vectors, compute the real-space unit cell
    parameters (a, b, c, alpha, beta, gamma).

    Args:
        a_star: Reciprocal vector a* in Å^-1
        b_star: Reciprocal vector b* in Å^-1
        c_star: Reciprocal vector c* in Å^-1

    Returns:
        Tuple of (a, b, c, alpha, beta, gamma) where lengths are in Å
        and angles are in degrees
    """
    # Calculate reciprocal space volume
    V_star = np.dot(a_star, np.cross(b_star, c_star))

    # Calculate real space volume
    V_cell = 1.0 / V_star

    # Calculate real-space basis vectors
    a = V_cell * np.cross(b_star, c_star)
    b = V_cell * np.cross(c_star, a_star)
    c = V_cell * np.cross(a_star, b_star)

    # Calculate cell lengths
    a_length = np.linalg.norm(a)
    b_length = np.linalg.norm(b)
    c_length = np.linalg.norm(c)

    # Calculate cell angles
    cos_alpha = np.dot(b, c) / (b_length * c_length)
    cos_beta = np.dot(a, c) / (a_length * c_length)
    cos_gamma = np.dot(a, b) / (a_length * b_length)

    # Clamp to avoid numerical issues
    cos_alpha = np.clip(cos_alpha, -1.0, 1.0)
    cos_beta = np.clip(cos_beta, -1.0, 1.0)
    cos_gamma = np.clip(cos_gamma, -1.0, 1.0)

    # Convert to degrees
    alpha = np.degrees(np.arccos(cos_alpha))
    beta = np.degrees(np.arccos(cos_beta))
    gamma = np.degrees(np.arccos(cos_gamma))

    return a_length, b_length, c_length, alpha, beta, gamma