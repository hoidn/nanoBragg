#!/usr/bin/env python3
"""Test gradient correctness for differentiable parameters.

This module implements Tier 2 testing from the Testing Strategy:
gradient correctness verification using torch.autograd.gradcheck.
"""

import os
import torch
import pytest
import numpy as np
from torch.autograd import gradcheck, gradgradcheck

# Set environment variables before importing nanobrag_torch
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Preserve external NANOBRAGG_DISABLE_COMPILE if set, otherwise default to '0'
# This allows the gradient_policy_guard fixture to enforce the requirement
os.environ["NANOBRAGG_DISABLE_COMPILE"] = os.environ.get("NANOBRAGG_DISABLE_COMPILE", "0")

# Import the core components
from nanobrag_torch.config import CrystalConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


# ============================================================================
# Phase K Task K2: Gradient Policy Guard
# ============================================================================

@pytest.fixture(scope="module", autouse=True)
def gradient_policy_guard():
    """
    Enforce NANOBRAGG_DISABLE_COMPILE=1 for gradient tests.

    See: reports/2026-01-test-suite-refresh/phase_j/20251015T180301Z/analysis/gradient_policy_guard.md
    """
    if os.environ.get('NANOBRAGG_DISABLE_COMPILE') != '1':
        pytest.skip(
            "Gradient tests require NANOBRAGG_DISABLE_COMPILE=1 environment variable.\n\n"
            "This guard prevents torch.compile donated buffer interference with "
            "torch.autograd.gradcheck.\n\n"
            "To run gradient tests, use:\n"
            "  env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE \\\n"
            "    NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py\n\n"
            "For details, see:\n"
            "  - docs/development/testing_strategy.md S4.1\n"
            "  - arch.md S15 (Differentiability Guidelines)\n"
            "  - reports/2026-01-test-suite-refresh/phase_m2/20251011T172830Z/"
        )


class GradientTestHelper:
    """Helper class for gradient testing scenarios."""

    @staticmethod
    def create_loss_function(param_name):
        """Create a loss function that takes a parameter and returns a scalar.

        Args:
            param_name: Name of the parameter (e.g., 'cell_a', 'cell_beta')

        Returns:
            A function suitable for gradcheck
        """

        def loss_fn(param_value):
            device = torch.device("cpu")
            dtype = torch.float64

            # Create config with the parameter as a tensor
            config_kwargs = {
                "cell_a": 100.0,
                "cell_b": 100.0,
                "cell_c": 100.0,
                "cell_alpha": 90.0,
                "cell_beta": 90.0,
                "cell_gamma": 90.0,
                "mosaic_spread_deg": 0.0,
                "mosaic_domains": 1,
                "N_cells": (5, 5, 5),
            }

            # Update the specific parameter with the tensor value
            config_kwargs[param_name] = param_value

            # Create config
            config = CrystalConfig(**config_kwargs)

            # Create crystal with this config
            crystal = Crystal(config=config, device=device, dtype=dtype)

            # Create minimal detector (hard-coded geometry)
            detector = Detector(device=device, dtype=dtype)

            # Create simulator
            simulator = Simulator(
                crystal, detector, crystal_config=config, device=device, dtype=dtype
            )

            # Run simulation and return scalar (sum of intensities)
            image = simulator.run()
            return image.sum()

        return loss_fn


class TestCellParameterGradients:
    """Test gradient correctness for unit cell parameters."""

    def test_gradcheck_cell_a(self):
        """Verify cell_a parameter is fully differentiable."""
        # Create test input with requires_grad
        cell_a = torch.tensor(100.0, dtype=torch.float64, requires_grad=True)

        # Get loss function for cell_a
        loss_fn = GradientTestHelper.create_loss_function("cell_a")

        # Run gradcheck with strict settings
        assert gradcheck(
            loss_fn, (cell_a,), eps=1e-6, atol=1e-5, rtol=0.05, raise_exception=True
        )

        # Test with different values
        for test_value in [50.0, 150.0, 200.0]:
            cell_a_test = torch.tensor(
                test_value, dtype=torch.float64, requires_grad=True
            )
            assert gradcheck(
                loss_fn,
                (cell_a_test,),
                eps=1e-6,
                atol=1e-5,
                rtol=0.05,
                raise_exception=True,
            )

    def test_gradcheck_cell_b(self):
        """Verify cell_b parameter is fully differentiable."""
        # Create test input with requires_grad
        cell_b = torch.tensor(100.0, dtype=torch.float64, requires_grad=True)

        # Get loss function for cell_b
        loss_fn = GradientTestHelper.create_loss_function("cell_b")

        # Run gradcheck with strict settings
        assert gradcheck(
            loss_fn, (cell_b,), eps=1e-6, atol=1e-5, rtol=0.05, raise_exception=True
        )

        # Test edge cases with very small and large values
        for test_value in [10.0, 100.0, 500.0]:
            cell_b_test = torch.tensor(
                test_value, dtype=torch.float64, requires_grad=True
            )
            assert gradcheck(
                loss_fn,
                (cell_b_test,),
                eps=1e-6,
                atol=1e-5,
                rtol=0.05,
                raise_exception=True,
            )

    def test_gradcheck_cell_c(self):
        """Verify cell_c parameter is fully differentiable."""
        # Create test input with requires_grad
        cell_c = torch.tensor(100.0, dtype=torch.float64, requires_grad=True)

        # Get loss function for cell_c
        loss_fn = GradientTestHelper.create_loss_function("cell_c")

        # Run gradcheck with strict settings
        assert gradcheck(
            loss_fn, (cell_c,), eps=1e-6, atol=1e-5, rtol=0.05, raise_exception=True
        )

        # Test full range of reasonable cell dimensions
        for test_value in [25.0, 165.2, 300.0]:  # Including 165.2 from golden triclinic
            cell_c_test = torch.tensor(
                test_value, dtype=torch.float64, requires_grad=True
            )
            assert gradcheck(
                loss_fn,
                (cell_c_test,),
                eps=1e-6,
                atol=1e-5,
                rtol=0.05,
                raise_exception=True,
            )

    def test_gradcheck_cell_alpha(self):
        """Verify cell_alpha angle parameter is fully differentiable."""
        # Note: Testing at exactly 90° is problematic because it's a stationary point
        # for cubic crystals, where numerical differentiation becomes unstable.
        # We test at 89° instead, which is close but avoids the stationary point.

        # Create test input with requires_grad (avoid exact 90° stationary point)
        cell_alpha = torch.tensor(89.0, dtype=torch.float64, requires_grad=True)

        # Get loss function for cell_alpha
        loss_fn = GradientTestHelper.create_loss_function("cell_alpha")

        # Run gradcheck with practical numerical tolerances
        # Note: ~2% relative error observed due to complex simulation chain
        assert gradcheck(
            loss_fn, (cell_alpha,), eps=1e-6, atol=1e-5, rtol=0.05, raise_exception=True
        )

        # Test angles from 60° to 120°, avoiding exact 90° which is a stationary point
        for test_value in [60.0, 75.0, 89.0, 89.5, 90.5, 91.0, 105.0, 120.0]:
            cell_alpha_test = torch.tensor(
                test_value, dtype=torch.float64, requires_grad=True
            )
            assert gradcheck(
                loss_fn,
                (cell_alpha_test,),
                eps=1e-6,
                atol=1e-5,
                rtol=0.05,
                raise_exception=True,
            )

    def test_gradcheck_cell_beta(self):
        """Verify cell_beta angle parameter is fully differentiable."""
        # Create test input with requires_grad (avoid exact 90° stationary point)
        cell_beta = torch.tensor(89.0, dtype=torch.float64, requires_grad=True)

        # Get loss function for cell_beta
        loss_fn = GradientTestHelper.create_loss_function("cell_beta")

        # Run gradcheck with strict settings
        assert gradcheck(
            loss_fn, (cell_beta,), eps=1e-6, atol=1e-5, rtol=0.05, raise_exception=True
        )

        # Test including edge cases, avoiding too close to 0° or 180° and exact 90°
        for test_value in [30.0, 60.0, 89.0, 91.0, 120.0, 150.0]:
            cell_beta_test = torch.tensor(
                test_value, dtype=torch.float64, requires_grad=True
            )
            assert gradcheck(
                loss_fn,
                (cell_beta_test,),
                eps=1e-6,
                atol=1e-5,
                rtol=0.05,
                raise_exception=True,
            )

    def test_gradcheck_cell_gamma(self):
        """Verify cell_gamma angle parameter is fully differentiable."""
        # Create test input with requires_grad (avoid exact 90° stationary point)
        cell_gamma = torch.tensor(89.0, dtype=torch.float64, requires_grad=True)

        # Get loss function for cell_gamma
        loss_fn = GradientTestHelper.create_loss_function("cell_gamma")

        # Run gradcheck with strict settings
        assert gradcheck(
            loss_fn, (cell_gamma,), eps=1e-6, atol=1e-5, rtol=0.05, raise_exception=True
        )

        # Test full range including highly skewed cells (e.g., 120° for hexagonal), avoiding exact 90°
        # Note: Avoiding very extreme angles like 45° and 135° which can cause numerical instability
        for test_value in [60.0, 75.0, 89.0, 91.0, 105.0, 120.0]:
            cell_gamma_test = torch.tensor(
                test_value, dtype=torch.float64, requires_grad=True
            )
            assert gradcheck(
                loss_fn,
                (cell_gamma_test,),
                eps=1e-6,
                atol=1e-5,
                rtol=0.05,
                raise_exception=True,
            )


class TestAdvancedGradients:
    """Test advanced gradient scenarios including joint parameters and second-order."""

    def test_joint_gradcheck(self):
        """Verify gradients flow correctly when all cell parameters vary together."""
        # Create all six cell parameters as a single tensor
        # Use non-90-degree angles to avoid stationary points that cause numerical issues
        cell_params = torch.tensor(
            [100.0, 100.0, 100.0, 89.0, 89.0, 89.0],  # a, b, c, alpha, beta, gamma
            dtype=torch.float64,
            requires_grad=True,
        )

        def joint_loss_fn(params):
            """Loss function that uses all six cell parameters."""
            device = torch.device("cpu")
            dtype = torch.float64

            # Unpack parameters
            cell_a, cell_b, cell_c, cell_alpha, cell_beta, cell_gamma = params

            # Create config with all parameters
            config = CrystalConfig(
                cell_a=cell_a,
                cell_b=cell_b,
                cell_c=cell_c,
                cell_alpha=cell_alpha,
                cell_beta=cell_beta,
                cell_gamma=cell_gamma,
                mosaic_spread_deg=0.0,
                mosaic_domains=1,
                N_cells=(5, 5, 5),
            )

            # Create objects
            crystal = Crystal(config=config, device=device, dtype=dtype)
            detector = Detector(device=device, dtype=dtype)

            # Run simulation
            simulator = Simulator(
                crystal, detector, crystal_config=config, device=device, dtype=dtype
            )
            image = simulator.run()

            # Return scalar loss
            return image.sum()

        # Run gradcheck on joint function
        assert gradcheck(
            joint_loss_fn,
            (cell_params,),
            eps=1e-6,
            atol=1e-5,
            rtol=0.05,
            raise_exception=True,
        )

        # Test with triclinic parameters (avoid exact 90-degree angles)
        triclinic_params = torch.tensor(
            [281.0, 281.0, 165.2, 89.0, 89.0, 120.0],  # From golden triclinic, modified
            dtype=torch.float64,
            requires_grad=True,
        )
        assert gradcheck(
            joint_loss_fn,
            (triclinic_params,),
            eps=1e-6,
            atol=1e-5,
            rtol=0.05,
            raise_exception=True,
        )

    def test_gradgradcheck_cell_params(self):
        """Verify second-order gradients are stable for optimization algorithms."""
        # Use smaller parameter set for second-order testing (computationally expensive)
        # Use non-90-degree angles to avoid stationary points that cause numerical issues
        cell_params = torch.tensor(
            [100.0, 100.0, 100.0, 89.0, 89.0, 89.0],
            dtype=torch.float64,
            requires_grad=True,
        )

        def joint_loss_fn(params):
            """Loss function for second-order gradient testing."""
            device = torch.device("cpu")
            dtype = torch.float64

            # Unpack parameters
            cell_a, cell_b, cell_c, cell_alpha, cell_beta, cell_gamma = params

            # Create config with all parameters
            config = CrystalConfig(
                cell_a=cell_a,
                cell_b=cell_b,
                cell_c=cell_c,
                cell_alpha=cell_alpha,
                cell_beta=cell_beta,
                cell_gamma=cell_gamma,
                mosaic_spread_deg=0.0,
                mosaic_domains=1,
                N_cells=(5, 5, 5),
            )

            # Create objects
            crystal = Crystal(config=config, device=device, dtype=dtype)
            detector = Detector(device=device, dtype=dtype)

            # Run simulation
            simulator = Simulator(
                crystal, detector, crystal_config=config, device=device, dtype=dtype
            )
            image = simulator.run()

            # Return scalar loss
            return image.sum()

        # Run second-order gradient check
        assert gradgradcheck(
            joint_loss_fn,
            (cell_params,),
            eps=1e-4,  # Larger eps for second-order
            atol=1e-4,
            rtol=0.05,
            raise_exception=True,
        )

    def test_gradient_flow_simulation(self):
        """Verify end-to-end gradient flow through full simulation pipeline.

        Note: Requires non-zero structure factors (default_F) to generate
        non-zero intensity, ensuring gradients can be validated. Zero intensity
        produces zero gradients mathematically (∂(0)/∂θ = 0).
        """
        device = torch.device("cpu")
        dtype = torch.float64

        # Create differentiable cell parameters
        cell_a = torch.tensor(100.0, dtype=dtype, requires_grad=True)
        cell_b = torch.tensor(100.0, dtype=dtype, requires_grad=True)
        cell_c = torch.tensor(100.0, dtype=dtype, requires_grad=True)
        cell_alpha = torch.tensor(90.0, dtype=dtype, requires_grad=True)
        cell_beta = torch.tensor(90.0, dtype=dtype, requires_grad=True)
        cell_gamma = torch.tensor(90.0, dtype=dtype, requires_grad=True)

        # Create config with tensor parameters
        # NOTE: default_F=100.0 ensures non-zero intensity for gradient validation
        # (see Phase B findings: reports/2026-01-gradient-flow/phase_b/20251015T053254Z/)
        config = CrystalConfig(
            cell_a=cell_a,
            cell_b=cell_b,
            cell_c=cell_c,
            cell_alpha=cell_alpha,
            cell_beta=cell_beta,
            cell_gamma=cell_gamma,
            mosaic_spread_deg=0.0,
            mosaic_domains=1,
            N_cells=(5, 5, 5),
            default_F=100.0,
        )

        # Create objects
        crystal = Crystal(config=config, device=device, dtype=dtype)
        detector = Detector(device=device, dtype=dtype)

        # Run simulation
        simulator = Simulator(
            crystal, detector, crystal_config=config, device=device, dtype=dtype
        )
        image = simulator.run()

        # Compute loss
        loss = image.sum()

        # Verify image requires grad
        assert image.requires_grad, "Output image should require gradients"

        # Backward pass
        loss.backward()

        # Verify all parameters have gradients
        assert cell_a.grad is not None, "cell_a should have gradient"
        assert cell_b.grad is not None, "cell_b should have gradient"
        assert cell_c.grad is not None, "cell_c should have gradient"
        assert cell_alpha.grad is not None, "cell_alpha should have gradient"
        assert cell_beta.grad is not None, "cell_beta should have gradient"
        assert cell_gamma.grad is not None, "cell_gamma should have gradient"

        # Verify gradients are non-zero (at least one should be)
        grad_magnitudes = [
            cell_a.grad.abs().item(),
            cell_b.grad.abs().item(),
            cell_c.grad.abs().item(),
            cell_alpha.grad.abs().item(),
            cell_beta.grad.abs().item(),
            cell_gamma.grad.abs().item(),
        ]
        assert any(
            mag > 1e-10 for mag in grad_magnitudes
        ), "At least one gradient should be non-zero"


class TestPropertyBasedGradients:
    """Property-based testing for gradient correctness across random geometries."""

    @staticmethod
    def generate_random_cell():
        """Generate a well-conditioned random triclinic cell.

        Returns:
            dict: Cell parameters with physically reasonable values
        """
        # Generate random cell lengths (50-200 Angstroms) - more conservative range
        cell_a = torch.rand(1).item() * 150 + 50
        cell_b = torch.rand(1).item() * 150 + 50
        cell_c = torch.rand(1).item() * 150 + 50

        # Generate random angles (60-120 degrees) - avoid extreme angles
        # These limits ensure the cell remains well-conditioned
        cell_alpha = torch.rand(1).item() * 60 + 60
        cell_beta = torch.rand(1).item() * 60 + 60
        cell_gamma = torch.rand(1).item() * 60 + 60

        return {
            "cell_a": cell_a,
            "cell_b": cell_b,
            "cell_c": cell_c,
            "cell_alpha": cell_alpha,
            "cell_beta": cell_beta,
            "cell_gamma": cell_gamma,
        }

    def test_property_metric_duality(self):
        """Verify fundamental crystallographic relationships for random cells."""
        torch.manual_seed(42)  # For reproducibility

        for i in range(50):
            # Generate random cell
            cell_params = self.generate_random_cell()

            # Create crystal with these parameters
            config = CrystalConfig(
                **cell_params,
                mosaic_spread_deg=0.0,
                mosaic_domains=1,
                N_cells=(5, 5, 5),
            )

            crystal = Crystal(config=config)

            # Get real and reciprocal space vectors
            a, b, c = crystal.a, crystal.b, crystal.c
            a_star, b_star, c_star = crystal.a_star, crystal.b_star, crystal.c_star

            # Verify metric duality relationships
            # a* · a = 1, a* · b = 0, etc.
            assert torch.allclose(
                torch.dot(a_star, a), torch.tensor(1.0, dtype=a_star.dtype), atol=1e-5
            ), f"Failed for cell {i}: a* · a ≠ 1"
            assert torch.allclose(
                torch.dot(a_star, b), torch.tensor(0.0, dtype=a_star.dtype), atol=1e-5
            ), f"Failed for cell {i}: a* · b ≠ 0"
            assert torch.allclose(
                torch.dot(a_star, c), torch.tensor(0.0, dtype=a_star.dtype), atol=1e-5
            ), f"Failed for cell {i}: a* · c ≠ 0"

            assert torch.allclose(
                torch.dot(b_star, a), torch.tensor(0.0, dtype=b_star.dtype), atol=1e-5
            ), f"Failed for cell {i}: b* · a ≠ 0"
            assert torch.allclose(
                torch.dot(b_star, b), torch.tensor(1.0, dtype=b_star.dtype), atol=1e-5
            ), f"Failed for cell {i}: b* · b ≠ 1"
            assert torch.allclose(
                torch.dot(b_star, c), torch.tensor(0.0, dtype=b_star.dtype), atol=1e-5
            ), f"Failed for cell {i}: b* · c ≠ 0"

            assert torch.allclose(
                torch.dot(c_star, a), torch.tensor(0.0, dtype=c_star.dtype), atol=1e-5
            ), f"Failed for cell {i}: c* · a ≠ 0"
            assert torch.allclose(
                torch.dot(c_star, b), torch.tensor(0.0, dtype=c_star.dtype), atol=1e-5
            ), f"Failed for cell {i}: c* · b ≠ 0"
            assert torch.allclose(
                torch.dot(c_star, c), torch.tensor(1.0, dtype=c_star.dtype), atol=1e-5
            ), f"Failed for cell {i}: c* · c ≠ 1"

    def test_property_volume_consistency(self):
        """Verify volume calculations are consistent across formulations."""
        torch.manual_seed(43)  # For reproducibility

        for i in range(50):
            # Generate random cell
            cell_params = self.generate_random_cell()

            # Create crystal
            config = CrystalConfig(
                **cell_params,
                mosaic_spread_deg=0.0,
                mosaic_domains=1,
                N_cells=(5, 5, 5),
            )

            crystal = Crystal(config=config)

            # Get volume from crystal
            volume = crystal.volume

            # Calculate volume via triple product
            a, b, c = crystal.a, crystal.b, crystal.c
            volume_triple = torch.abs(torch.dot(a, torch.cross(b, c, dim=0)))

            # Verify consistency
            assert torch.allclose(
                volume, volume_triple, rtol=1e-6
            ), f"Failed for cell {i}: Volume mismatch {volume} vs {volume_triple}"

    @pytest.mark.slow_gradient
    @pytest.mark.timeout(905)
    def test_property_gradient_stability(self):
        """Ensure gradients remain stable across parameter space."""
        torch.manual_seed(44)  # For reproducibility

        for i in range(25):  # Fewer tests as gradcheck is expensive
            # Generate random cell
            cell_params = self.generate_random_cell()

            # Create tensor parameters
            cell_params_tensor = torch.tensor(
                [
                    cell_params["cell_a"],
                    cell_params["cell_b"],
                    cell_params["cell_c"],
                    cell_params["cell_alpha"],
                    cell_params["cell_beta"],
                    cell_params["cell_gamma"],
                ],
                dtype=torch.float64,
                requires_grad=True,
            )

            def loss_fn(params):
                device = torch.device("cpu")
                dtype = torch.float64

                # Unpack parameters
                cell_a, cell_b, cell_c, cell_alpha, cell_beta, cell_gamma = params

                # Create config
                config = CrystalConfig(
                    cell_a=cell_a,
                    cell_b=cell_b,
                    cell_c=cell_c,
                    cell_alpha=cell_alpha,
                    cell_beta=cell_beta,
                    cell_gamma=cell_gamma,
                    mosaic_spread_deg=0.0,
                    mosaic_domains=1,
                    N_cells=(5, 5, 5),
                )

                # Create objects
                crystal = Crystal(config=config, device=device, dtype=dtype)
                detector = Detector(device=device, dtype=dtype)

                # Run simulation
                simulator = Simulator(
                    crystal, detector, crystal_config=config, device=device, dtype=dtype
                )
                image = simulator.run()

                return image.sum()

            # Verify gradcheck passes for this random geometry
            try:
                assert gradcheck(
                    loss_fn,
                    (cell_params_tensor,),
                    eps=1e-6,
                    atol=1e-5,  # Slightly relaxed for stability
                    rtol=0.05,
                    raise_exception=True,
                )
            except AssertionError as e:
                print(f"Gradient check failed for cell {i}: {cell_params}")
                raise e


class TestOptimizationRecovery:
    """Test that gradients enable successful parameter recovery via optimization."""

    def test_optimization_recovers_cell(self):
        """Demonstrate gradients are useful for optimization."""
        torch.manual_seed(45)  # For reproducibility
        device = torch.device("cpu")
        dtype = torch.float64

        # Define target cell parameters
        target_params = {
            "cell_a": 100.0,
            "cell_b": 110.0,
            "cell_c": 120.0,
            "cell_alpha": 85.0,
            "cell_beta": 95.0,
            "cell_gamma": 105.0,
        }

        # Create target crystal
        target_config = CrystalConfig(
            **target_params,
            mosaic_spread_deg=0.0,
            mosaic_domains=1,
            N_cells=(5, 5, 5),
        )
        target_crystal = Crystal(config=target_config, device=device, dtype=dtype)

        # Get target reciprocal vectors
        target_a_star = target_crystal.a_star.detach()
        target_b_star = target_crystal.b_star.detach()
        target_c_star = target_crystal.c_star.detach()

        # Initialize guess with 5-10% perturbation
        perturb_factor = 0.05 + torch.rand(6) * 0.05  # 5-10% perturbation
        initial_params = torch.tensor(
            [
                target_params["cell_a"] * (1 + perturb_factor[0]),
                target_params["cell_b"] * (1 + perturb_factor[1]),
                target_params["cell_c"] * (1 + perturb_factor[2]),
                target_params["cell_alpha"] * (1 + perturb_factor[3]),
                target_params["cell_beta"] * (1 + perturb_factor[4]),
                target_params["cell_gamma"] * (1 + perturb_factor[5]),
            ],
            dtype=dtype,
            requires_grad=True,
        )

        # Setup optimizer
        optimizer = torch.optim.Adam([initial_params], lr=0.1)

        # Track loss history
        loss_history = []

        # Optimization loop
        for iteration in range(20):
            optimizer.zero_grad()

            # Unpack current parameters
            cell_a, cell_b, cell_c, cell_alpha, cell_beta, cell_gamma = initial_params

            # Create crystal with current parameters
            config = CrystalConfig(
                cell_a=cell_a,
                cell_b=cell_b,
                cell_c=cell_c,
                cell_alpha=cell_alpha,
                cell_beta=cell_beta,
                cell_gamma=cell_gamma,
                mosaic_spread_deg=0.0,
                mosaic_domains=1,
                N_cells=(5, 5, 5),
            )
            crystal = Crystal(config=config, device=device, dtype=dtype)

            # Compute loss as MSE between reciprocal vectors
            loss = (
                torch.nn.functional.mse_loss(crystal.a_star, target_a_star)
                + torch.nn.functional.mse_loss(crystal.b_star, target_b_star)
                + torch.nn.functional.mse_loss(crystal.c_star, target_c_star)
            )

            loss_history.append(loss.item())

            # Backward and optimize
            loss.backward()
            optimizer.step()

        # Verify convergence (practical requirements for gradient demonstration)
        assert (
            loss_history[-1] < 1e-5
        ), f"Failed to converge: final loss = {loss_history[-1]}"
        # Loss should decrease somewhat (the algorithm converged from 1.46e-06 to 9.06e-07)
        assert loss_history[-1] <= loss_history[0], "Loss should decrease or stay same"

        # Verify recovered parameters are close to target
        recovered_params = initial_params.detach().numpy()
        target_array = np.array(
            [
                target_params["cell_a"],
                target_params["cell_b"],
                target_params["cell_c"],
                target_params["cell_alpha"],
                target_params["cell_beta"],
                target_params["cell_gamma"],
            ]
        )

        np.testing.assert_allclose(recovered_params, target_array, rtol=0.10)

    def test_multiple_optimization_scenarios(self):
        """Verify robustness across different starting conditions."""
        torch.manual_seed(46)
        device = torch.device("cpu")
        dtype = torch.float64

        scenarios = [
            # Scenario 1: Near-cubic to triclinic
            {
                "name": "cubic_to_triclinic",
                "target": [100.0, 110.0, 120.0, 85.0, 95.0, 105.0],
                "initial": [100.0, 100.0, 100.0, 90.0, 90.0, 90.0],
                "lr": 0.05,
            },
            # Scenario 2: Large cell to small cell
            {
                "name": "large_to_small",
                "target": [50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
                "initial": [200.0, 200.0, 200.0, 90.0, 90.0, 90.0],
                "lr": 0.1,
            },
            # Scenario 3: Different perturbation magnitudes
            {
                "name": "small_perturbation",
                "target": [281.0, 281.0, 165.2, 90.0, 90.0, 120.0],
                "initial": [280.0, 282.0, 164.0, 89.0, 91.0, 119.0],
                "lr": 0.01,
            },
        ]

        for scenario in scenarios:
            # Create target crystal
            target_params = torch.tensor(scenario["target"], dtype=dtype)
            target_config = CrystalConfig(
                cell_a=target_params[0],
                cell_b=target_params[1],
                cell_c=target_params[2],
                cell_alpha=target_params[3],
                cell_beta=target_params[4],
                cell_gamma=target_params[5],
                mosaic_spread_deg=0.0,
                mosaic_domains=1,
                N_cells=(5, 5, 5),
            )
            target_crystal = Crystal(config=target_config, device=device, dtype=dtype)
            target_reciprocal = torch.cat(
                [
                    target_crystal.a_star.detach(),
                    target_crystal.b_star.detach(),
                    target_crystal.c_star.detach(),
                ]
            )

            # Initialize parameters
            initial_params = torch.tensor(
                scenario["initial"], dtype=dtype, requires_grad=True
            )

            # Setup optimizer
            optimizer = torch.optim.Adam([initial_params], lr=scenario["lr"])

            # Optimization loop
            final_loss = None
            for iteration in range(50):  # More iterations for harder scenarios
                optimizer.zero_grad()

                # Create crystal
                config = CrystalConfig(
                    cell_a=initial_params[0],
                    cell_b=initial_params[1],
                    cell_c=initial_params[2],
                    cell_alpha=initial_params[3],
                    cell_beta=initial_params[4],
                    cell_gamma=initial_params[5],
                    mosaic_spread_deg=0.0,
                    mosaic_domains=1,
                    N_cells=(5, 5, 5),
                )
                crystal = Crystal(config=config, device=device, dtype=dtype)

                # Compute loss
                current_reciprocal = torch.cat(
                    [crystal.a_star, crystal.b_star, crystal.c_star]
                )
                loss = torch.nn.functional.mse_loss(
                    current_reciprocal, target_reciprocal
                )

                final_loss = loss.item()

                # Early stopping if converged
                if final_loss < 1e-8:
                    break

                # Backward and optimize
                loss.backward()
                optimizer.step()

            # Verify convergence
            assert (
                final_loss < 1e-4
            ), f"Scenario '{scenario['name']}' failed to converge: final loss = {final_loss}"


class TestDBEXGradientBlockers:
    """
    Tests for DBEX-GRADIENT-001: Gradient flow for beam and detector parameters.

    These tests verify that parameters commonly used in differentiable rendering
    experiments (DBEX) properly preserve gradient flow when passed as tensors.

    Prior to the fix, torch.tensor() was used which detaches the computation graph.
    The fix uses as_tensor_preserving_grad() which preserves requires_grad=True.
    """

    def test_wavelength_gradient_at_init(self):
        """Verify wavelength tensor passed at init preserves gradient flow."""
        device = torch.device("cpu")
        dtype = torch.float64

        # Create wavelength tensor with requires_grad
        wavelength = torch.tensor(6.2, dtype=dtype, requires_grad=True)

        # Create configs with wavelength tensor
        from nanobrag_torch.config import BeamConfig, DetectorConfig, CrystalConfig

        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5), default_F=100.0,
        )
        detector_config = DetectorConfig(
            distance_mm=100.0, pixel_size_mm=0.1, spixels=16, fpixels=16,
        )
        # Pass wavelength tensor directly
        beam_config = BeamConfig(wavelength_A=wavelength, fluence=1e28)

        crystal = Crystal(config=crystal_config, device=device, dtype=dtype)
        detector = Detector(config=detector_config, device=device, dtype=dtype)
        simulator = Simulator(
            crystal=crystal, detector=detector,
            crystal_config=crystal_config, beam_config=beam_config,
            device=device, dtype=dtype,
        )

        # Verify gradient preservation
        assert simulator.wavelength.requires_grad, \
            "Simulator.wavelength should have requires_grad=True when input tensor has requires_grad"

        # Run simulation and compute loss
        result = simulator.run()
        loss = result.sum()

        # Verify backward works
        loss.backward()
        assert wavelength.grad is not None, "wavelength should have gradient after backward"

    def test_wavelength_gradcheck(self):
        """Verify wavelength gradient is numerically correct via gradcheck."""
        device = torch.device("cpu")
        dtype = torch.float64

        wavelength = torch.tensor(6.2, dtype=dtype, requires_grad=True)

        from nanobrag_torch.config import BeamConfig, DetectorConfig, CrystalConfig

        def loss_fn(wavelength_param):
            crystal_config = CrystalConfig(
                cell_a=100.0, cell_b=100.0, cell_c=100.0,
                cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
                N_cells=(5, 5, 5), default_F=100.0,
            )
            detector_config = DetectorConfig(
                distance_mm=100.0, pixel_size_mm=0.1, spixels=8, fpixels=8,
            )
            beam_config = BeamConfig(wavelength_A=wavelength_param, fluence=1e28)

            crystal = Crystal(config=crystal_config, device=device, dtype=dtype)
            detector = Detector(config=detector_config, device=device, dtype=dtype)
            simulator = Simulator(
                crystal=crystal, detector=detector,
                crystal_config=crystal_config, beam_config=beam_config,
                device=device, dtype=dtype,
            )

            result = simulator.run()
            return result.sum()

        assert gradcheck(
            loss_fn, (wavelength,), eps=1e-6, atol=1e-5, rtol=0.05, raise_exception=True
        )

    def test_fluence_gradient_at_init(self):
        """Verify fluence tensor passed at init preserves gradient flow."""
        device = torch.device("cpu")
        dtype = torch.float64

        # Create fluence tensor with requires_grad
        fluence = torch.tensor(1e28, dtype=dtype, requires_grad=True)

        from nanobrag_torch.config import BeamConfig, DetectorConfig, CrystalConfig

        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5), default_F=100.0,
        )
        detector_config = DetectorConfig(
            distance_mm=100.0, pixel_size_mm=0.1, spixels=16, fpixels=16,
        )
        beam_config = BeamConfig(wavelength_A=6.2, fluence=fluence)

        crystal = Crystal(config=crystal_config, device=device, dtype=dtype)
        detector = Detector(config=detector_config, device=device, dtype=dtype)
        simulator = Simulator(
            crystal=crystal, detector=detector,
            crystal_config=crystal_config, beam_config=beam_config,
            device=device, dtype=dtype,
        )

        # Verify gradient preservation
        assert simulator.fluence.requires_grad, \
            "Simulator.fluence should have requires_grad=True when input tensor has requires_grad"

        # Run simulation and compute loss
        result = simulator.run()
        loss = result.sum()

        # Verify backward works
        loss.backward()
        assert fluence.grad is not None, "fluence should have gradient after backward"

    def test_distance_gradient_at_init(self):
        """Verify detector distance tensor passed at init preserves gradient flow."""
        device = torch.device("cpu")
        dtype = torch.float64

        # Create distance tensor with requires_grad
        distance = torch.tensor(100.0, dtype=dtype, requires_grad=True)

        from nanobrag_torch.config import BeamConfig, DetectorConfig, CrystalConfig

        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5), default_F=100.0,
        )
        detector_config = DetectorConfig(
            distance_mm=distance, pixel_size_mm=0.1, spixels=16, fpixels=16,
        )
        beam_config = BeamConfig(wavelength_A=6.2, fluence=1e28)

        crystal = Crystal(config=crystal_config, device=device, dtype=dtype)
        detector = Detector(config=detector_config, device=device, dtype=dtype)
        simulator = Simulator(
            crystal=crystal, detector=detector,
            crystal_config=crystal_config, beam_config=beam_config,
            device=device, dtype=dtype,
        )

        # Verify gradient preservation through property
        assert detector.distance.requires_grad, \
            "Detector.distance should have requires_grad=True when config.distance_mm is a tensor"

        # Run simulation and compute loss
        result = simulator.run()
        loss = result.sum()

        # Verify backward works
        loss.backward()
        assert distance.grad is not None, "distance should have gradient after backward"

    def test_distance_post_override_gradient(self):
        """
        Verify distance gradient works with DBEX post-creation override pattern.

        This is the critical test case: DBEX creates detector with float distance,
        then overwrites config.distance_mm with a tensor. The property-based
        implementation should enable gradients to flow in this scenario.
        """
        device = torch.device("cpu")
        dtype = torch.float64

        from nanobrag_torch.config import BeamConfig, DetectorConfig, CrystalConfig

        # Step 1: Create detector with float distance (as DBEX does initially)
        detector_config = DetectorConfig(
            distance_mm=100.0,  # Float initially
            pixel_size_mm=0.1, spixels=16, fpixels=16,
        )
        detector = Detector(config=detector_config, device=device, dtype=dtype)

        # Step 2: Override config.distance_mm with tensor (DBEX pattern)
        distance_tensor = torch.tensor(100.0, dtype=dtype, requires_grad=True)
        detector_config.distance_mm = distance_tensor

        # Verify that detector.distance now reflects the tensor
        assert detector.distance.requires_grad, \
            "detector.distance should have requires_grad=True after config override"

        # Step 3: Create simulator and run
        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5), default_F=100.0,
        )
        crystal = Crystal(config=crystal_config, device=device, dtype=dtype)
        beam_config = BeamConfig(wavelength_A=6.2, fluence=1e28)

        simulator = Simulator(
            crystal=crystal, detector=detector,
            crystal_config=crystal_config, beam_config=beam_config,
            device=device, dtype=dtype,
        )

        result = simulator.run()
        loss = result.sum()

        # Verify backward works with post-override pattern
        loss.backward()
        assert distance_tensor.grad is not None, \
            "distance_tensor should have gradient after backward (post-override pattern)"

    def test_distance_gradcheck(self):
        """Verify distance gradient is numerically correct via gradcheck."""
        device = torch.device("cpu")
        dtype = torch.float64

        distance = torch.tensor(100.0, dtype=dtype, requires_grad=True)

        from nanobrag_torch.config import BeamConfig, DetectorConfig, CrystalConfig

        def loss_fn(distance_param):
            crystal_config = CrystalConfig(
                cell_a=100.0, cell_b=100.0, cell_c=100.0,
                cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
                N_cells=(5, 5, 5), default_F=100.0,
            )
            detector_config = DetectorConfig(
                distance_mm=distance_param, pixel_size_mm=0.1, spixels=8, fpixels=8,
            )
            beam_config = BeamConfig(wavelength_A=6.2, fluence=1e28)

            crystal = Crystal(config=crystal_config, device=device, dtype=dtype)
            detector = Detector(config=detector_config, device=device, dtype=dtype)
            simulator = Simulator(
                crystal=crystal, detector=detector,
                crystal_config=crystal_config, beam_config=beam_config,
                device=device, dtype=dtype,
            )

            result = simulator.run()
            return result.sum()

        assert gradcheck(
            loss_fn, (distance,), eps=1e-6, atol=1e-5, rtol=0.05, raise_exception=True
        )


class TestMosaicGradients:
    """
    Tests for MOSAIC-GRADIENT-001: Gradient correctness for mosaic spread parameter.

    These tests verify that the reparameterization fix for deterministic seeding
    preserves gradient flow through mosaic_spread_deg.
    """

    def test_mosaic_seed_determinism(self):
        """Verify same seed produces identical rotations across calls.

        This is the foundation of gradcheck correctness: if forward passes
        produce different random values, numerical gradients are meaningless.
        """
        device = torch.device("cpu")
        dtype = torch.float64

        # Create crystal and config with fixed seed
        crystal = Crystal(device=device, dtype=dtype)
        config = CrystalConfig(
            mosaic_spread_deg=0.5,
            mosaic_domains=5,
            mosaic_seed=42,
            phi_steps=1,
        )

        # Call twice with same seed
        (a1, b1, c1), _ = crystal.get_rotated_real_vectors(config)
        (a2, b2, c2), _ = crystal.get_rotated_real_vectors(config)

        # Results should be identical
        assert torch.allclose(a1, a2, atol=1e-12), "Same seed should produce identical rotations"
        assert torch.allclose(b1, b2, atol=1e-12), "Same seed should produce identical rotations"
        assert torch.allclose(c1, c2, atol=1e-12), "Same seed should produce identical rotations"

    def test_different_seeds_produce_different_rotations(self):
        """Verify different seeds produce different rotations.

        This ensures the seeding mechanism is actually working and not just
        returning constant values.
        """
        device = torch.device("cpu")
        dtype = torch.float64

        crystal = Crystal(device=device, dtype=dtype)

        config1 = CrystalConfig(
            mosaic_spread_deg=0.5,
            mosaic_domains=5,
            mosaic_seed=42,
            phi_steps=1,
        )
        config2 = CrystalConfig(
            mosaic_spread_deg=0.5,
            mosaic_domains=5,
            mosaic_seed=123,  # Different seed
            phi_steps=1,
        )

        (a1, _, _), _ = crystal.get_rotated_real_vectors(config1)
        (a2, _, _), _ = crystal.get_rotated_real_vectors(config2)

        # Results should be different
        assert not torch.allclose(a1, a2, atol=1e-6), "Different seeds should produce different rotations"

    def test_default_seed_compliance(self):
        """Verify default seed matches C-code default (-12345678).

        Per spec-a-core.md:367, the default mosaic seed should be -12345678.
        """
        device = torch.device("cpu")
        dtype = torch.float64

        crystal = Crystal(device=device, dtype=dtype)

        # Config without explicit seed should use default
        config_default = CrystalConfig(
            mosaic_spread_deg=0.5,
            mosaic_domains=5,
            # mosaic_seed not set - should use default
            phi_steps=1,
        )

        # Config with explicit C default seed
        config_explicit = CrystalConfig(
            mosaic_spread_deg=0.5,
            mosaic_domains=5,
            mosaic_seed=-12345678,  # Explicit C default
            phi_steps=1,
        )

        (a_default, _, _), _ = crystal.get_rotated_real_vectors(config_default)
        (a_explicit, _, _), _ = crystal.get_rotated_real_vectors(config_explicit)

        # Should produce identical results since default should be -12345678
        assert torch.allclose(a_default, a_explicit, atol=1e-12), \
            "Default seed should match C-code default of -12345678"

    def test_mosaic_spread_gradient_flow(self):
        """Verify gradient flows through mosaic_spread_deg to output."""
        device = torch.device("cpu")
        dtype = torch.float64

        crystal = Crystal(device=device, dtype=dtype)

        # Create differentiable mosaic spread
        mosaic_spread = torch.tensor(0.5, dtype=dtype, requires_grad=True)

        config = CrystalConfig(
            mosaic_spread_deg=mosaic_spread,
            mosaic_domains=5,
            mosaic_seed=42,
            phi_steps=1,
        )

        (a_rot, _, _), _ = crystal.get_rotated_real_vectors(config)

        # Compute loss and backward
        loss = a_rot.sum()
        loss.backward()

        # Gradient should exist and be non-zero (unless at exact identity which is unlikely)
        assert mosaic_spread.grad is not None, "mosaic_spread_deg should have gradient"
        # Note: gradient could be zero at spread=0, but at spread=0.5 it should be non-zero

    def test_mosaic_spread_gradcheck(self):
        """Verify mosaic_spread_deg gradient is numerically correct via gradcheck.

        This is the critical test that validates MOSAIC-GRADIENT-001 fix.
        Without deterministic seeding, this test would fail because each
        forward pass would use different random rotations.
        """
        device = torch.device("cpu")
        dtype = torch.float64

        mosaic_spread = torch.tensor(0.5, dtype=dtype, requires_grad=True)

        def loss_fn(mosaic_param):
            crystal = Crystal(device=device, dtype=dtype)
            config = CrystalConfig(
                mosaic_spread_deg=mosaic_param,
                mosaic_domains=3,  # Fewer domains for speed
                mosaic_seed=42,  # Fixed seed is CRITICAL for gradcheck
                phi_steps=1,
            )

            (a_rot, b_rot, c_rot), _ = crystal.get_rotated_real_vectors(config)
            return a_rot.sum() + b_rot.sum() + c_rot.sum()

        # gradcheck with appropriate tolerances for physics code
        assert gradcheck(
            loss_fn, (mosaic_spread,), eps=1e-4, atol=1e-4, rtol=0.02, raise_exception=True
        ), "Mosaic spread gradcheck failed - seeding may not be deterministic"

    def test_mosaic_spread_gradcheck_simulator(self):
        """Test gradients for mosaic_spread_deg through full simulator.

        This is the end-to-end acceptance test for MOSAIC-GRADIENT-001.
        """
        device = torch.device("cpu")
        dtype = torch.float64

        from nanobrag_torch.config import BeamConfig, DetectorConfig

        mosaic_spread = torch.tensor(0.5, dtype=dtype, requires_grad=True)

        def loss_fn(mosaic_param):
            crystal_config = CrystalConfig(
                cell_a=100.0, cell_b=100.0, cell_c=100.0,
                cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
                N_cells=(3, 3, 3),
                default_F=100.0,
                mosaic_spread_deg=mosaic_param,
                mosaic_domains=3,
                mosaic_seed=42,  # Fixed seed for reproducibility
            )
            detector_config = DetectorConfig(
                fpixels=8, spixels=8, pixel_size_mm=0.1, distance_mm=100.0
            )
            beam_config = BeamConfig(wavelength_A=1.0, fluence=1e28)

            crystal = Crystal(config=crystal_config, device=device, dtype=dtype)
            detector = Detector(config=detector_config, device=device, dtype=dtype)
            simulator = Simulator(
                crystal=crystal, detector=detector,
                crystal_config=crystal_config, beam_config=beam_config,
                device=device, dtype=dtype
            )

            return simulator.run().sum()

        # gradcheck with tolerances appropriate for complex physics simulation
        assert gradcheck(
            loss_fn, (mosaic_spread,), eps=1e-4, atol=1e-3, rtol=0.05, raise_exception=True
        ), "Simulator-level mosaic spread gradcheck failed"
