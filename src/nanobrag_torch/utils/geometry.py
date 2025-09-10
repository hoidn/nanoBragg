"""
Vectorized 3D geometry utilities for nanoBragg PyTorch implementation.

This module contains PyTorch implementations of all vector and geometry
operations from the original C code, designed for broadcasting and GPU acceleration.
"""

from typing import Tuple

import torch


def dot_product(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    """
    Calculate dot product of vectors x and y.

    Args:
        x, y: Tensors with shape (..., 3) representing 3D vectors

    Returns:
        torch.Tensor: Scalar dot product for each vector pair
    """
    return torch.sum(x * y, dim=-1)


def cross_product(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    """
    Calculate cross product of vectors x and y.

    Args:
        x, y: Tensors with shape (..., 3) representing 3D vectors

    Returns:
        torch.Tensor: Cross product vectors with shape (..., 3)
    """
    return torch.cross(x, y, dim=-1)


def magnitude(vector: torch.Tensor) -> torch.Tensor:
    """
    Calculate magnitude of vectors.

    Args:
        vector: Tensor with shape (..., 3) representing 3D vectors

    Returns:
        torch.Tensor: Magnitude for each vector
    """
    # Use torch.sqrt with protection against negative values to prevent complex gradients
    # This can happen due to numerical errors in floating point arithmetic
    squared_sum = torch.sum(vector * vector, dim=-1)
    # Clamp to prevent negative values that could cause complex gradients
    squared_sum = torch.clamp(squared_sum, min=0.0)
    return torch.sqrt(squared_sum)


def unitize(vector: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Normalize vectors to unit length.

    Args:
        vector: Tensor with shape (..., 3) representing 3D vectors

    Returns:
        Tuple of (unit_vector, original_magnitude)
    """
    mag = magnitude(vector)
    # Use a small epsilon to avoid division by zero
    safe_mag = torch.where(mag > 1e-12, mag, torch.ones_like(mag))
    unit_vector = vector / safe_mag.unsqueeze(-1)
    # Ensure zero vectors remain zero
    unit_vector = torch.where(
        mag.unsqueeze(-1) > 1e-12, unit_vector, torch.zeros_like(unit_vector)
    )
    return unit_vector, mag


def rotate_axis(v: torch.Tensor, axis: torch.Tensor, phi: torch.Tensor) -> torch.Tensor:
    """
    Rotate vectors around arbitrary axes using Rodrigues' formula.

    Args:
        v: Vectors to rotate with shape (..., 3)
        axis: Unit vectors defining rotation axes with shape (..., 3)
        phi: Rotation angles in radians

    Returns:
        torch.Tensor: Rotated vectors with shape (..., 3)
    """
    # Ensure axis is unit vector for stability
    axis_unit, _ = unitize(axis)

    # Rodrigues' formula: v_rot = v*cos(phi) + (axis × v)*sin(phi) + axis*(axis·v)*(1-cos(phi))
    cos_phi = torch.cos(phi).unsqueeze(-1)
    sin_phi = torch.sin(phi).unsqueeze(-1)

    axis_dot_v = dot_product(axis_unit, v).unsqueeze(-1)
    axis_cross_v = cross_product(axis_unit, v)

    v_rot = (
        v * cos_phi + axis_cross_v * sin_phi + axis_unit * axis_dot_v * (1 - cos_phi)
    )

    return v_rot


def rotate_umat(v: torch.Tensor, umat: torch.Tensor) -> torch.Tensor:
    """
    Rotate vectors using rotation matrices.

    Args:
        v: Vectors to rotate with shape (..., 3)
        umat: Rotation matrices with shape (..., 3, 3)

    Returns:
        torch.Tensor: Rotated vectors with shape (..., 3)
    """
    # Matrix multiplication: umat @ v (broadcasting over leading dimensions)
    return torch.matmul(umat, v.unsqueeze(-1)).squeeze(-1)


def angles_to_rotation_matrix(
    phi_x: torch.Tensor, phi_y: torch.Tensor, phi_z: torch.Tensor
) -> torch.Tensor:
    """
    Convert three Euler angles to a rotation matrix using XYZ convention.

    This implements the same rotation sequence as nanoBragg.c, applying
    rotations in the order: X-axis, then Y-axis, then Z-axis (extrinsic rotations).

    C-Code Implementation Reference (from nanoBragg.c, lines 3295-3345):
    ```c
    double *rotate(double *v, double *newv, double phix, double phiy, double phiz) {
        double rxx,rxy,rxz,ryx,ryy,ryz,rzx,rzy,rzz;
        double new_x,new_y,new_z,rotated_x,rotated_y,rotated_z;

        new_x=v[1];
        new_y=v[2];
        new_z=v[3];

        if(phix != 0){
            /* rotate around x axis */
            //rxx= 1;         rxy= 0;         rxz= 0;
            ryx= 0;         ryy= cos(phix); ryz=-sin(phix);
            rzx= 0;         rzy= sin(phix); rzz= cos(phix);

            rotated_x = new_x;
            rotated_y = new_y*ryy + new_z*ryz;
            rotated_z = new_y*rzy + new_z*rzz;
            new_x = rotated_x; new_y = rotated_y; new_z = rotated_z;
        }

        if(phiy != 0) {
            /* rotate around y axis */
            rxx= cos(phiy); rxy= 0;         rxz= sin(phiy);
            //ryx= 0;         ryy= 1;         ryz= 0;
            rzx=-sin(phiy); rzy= 0;         rzz= cos(phiy);

            rotated_x = new_x*rxx + new_y*rxy + new_z*rxz;
            rotated_y = new_y;
            rotated_z = new_x*rzx + new_y*rzy + new_z*rzz;
            new_x = rotated_x; new_y = rotated_y; new_z = rotated_z;
        }

        if(phiz != 0){
            /* rotate around z axis */
            rxx= cos(phiz); rxy=-sin(phiz); rxz= 0;
            ryx= sin(phiz); ryy= cos(phiz); ryz= 0;
            //rzx= 0;         rzy= 0;         rzz= 1;

            rotated_x = new_x*rxx + new_y*rxy ;
            rotated_y = new_x*ryx + new_y*ryy;
            rotated_z = new_z;
            new_x = rotated_x; new_y = rotated_y; new_z = rotated_z;
        }

        newv[1]=new_x;
        newv[2]=new_y;
        newv[3]=new_z;

        return newv;
    }
    ```

    Args:
        phi_x: Rotation angle around X-axis in radians
        phi_y: Rotation angle around Y-axis in radians
        phi_z: Rotation angle around Z-axis in radians

    Returns:
        torch.Tensor: 3x3 rotation matrix that applies rotations in XYZ order
    """
    # Extract device and dtype from input angles
    # Ensure all angles have the same dtype - convert to the highest precision dtype
    if hasattr(phi_x, "dtype") and hasattr(phi_y, "dtype") and hasattr(phi_z, "dtype"):
        # All are tensors
        dtype = torch.promote_types(
            torch.promote_types(phi_x.dtype, phi_y.dtype), phi_z.dtype
        )
        device = phi_x.device
        phi_x = phi_x.to(dtype=dtype)
        phi_y = phi_y.to(dtype=dtype)
        phi_z = phi_z.to(dtype=dtype)
    else:
        # Mixed or scalar inputs - default to float64
        device = torch.device("cpu")
        dtype = torch.float64
        if not isinstance(phi_x, torch.Tensor):
            phi_x = torch.tensor(phi_x, dtype=dtype, device=device)
        if not isinstance(phi_y, torch.Tensor):
            phi_y = torch.tensor(phi_y, dtype=dtype, device=device)
        if not isinstance(phi_z, torch.Tensor):
            phi_z = torch.tensor(phi_z, dtype=dtype, device=device)

    # Calculate sin and cos for all angles
    cos_x = torch.cos(phi_x)
    sin_x = torch.sin(phi_x)
    cos_y = torch.cos(phi_y)
    sin_y = torch.sin(phi_y)
    cos_z = torch.cos(phi_z)
    sin_z = torch.sin(phi_z)

    # Construct rotation matrix for X-axis rotation
    # Rx = [[1, 0, 0], [0, cos(x), -sin(x)], [0, sin(x), cos(x)]]
    Rx = torch.zeros(3, 3, device=device, dtype=dtype)
    Rx[0, 0] = 1.0
    Rx[1, 1] = cos_x
    Rx[1, 2] = -sin_x
    Rx[2, 1] = sin_x
    Rx[2, 2] = cos_x

    # Construct rotation matrix for Y-axis rotation
    # Ry = [[cos(y), 0, sin(y)], [0, 1, 0], [-sin(y), 0, cos(y)]]
    Ry = torch.zeros(3, 3, device=device, dtype=dtype)
    Ry[0, 0] = cos_y
    Ry[0, 2] = sin_y
    Ry[1, 1] = 1.0
    Ry[2, 0] = -sin_y
    Ry[2, 2] = cos_y

    # Construct rotation matrix for Z-axis rotation
    # Rz = [[cos(z), -sin(z), 0], [sin(z), cos(z), 0], [0, 0, 1]]
    Rz = torch.zeros(3, 3, device=device, dtype=dtype)
    Rz[0, 0] = cos_z
    Rz[0, 1] = -sin_z
    Rz[1, 0] = sin_z
    Rz[1, 1] = cos_z
    Rz[2, 2] = 1.0

    # Compose rotations in XYZ order: R = Rz @ Ry @ Rx
    # This means we first rotate by X, then Y, then Z
    R = torch.matmul(torch.matmul(Rz, Ry), Rx)

    return R
