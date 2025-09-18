"""
Test for AT-SRC-002: Auto-selection of count/range/step

From spec:
- AT-SRC-002 Auto-selection of count/range/step
  - Setup: Provide only step (or only range, or only count) for divergence/dispersion;
    also thickness sampling.
  - Expectation: The missing quantities SHALL resolve to count/range/step per the rules
    in the spec, with angles default range=1.0 rad and thickness default range=0.5e-6 m
    when only count is provided.

Auto-selection rules from spec:
- No parameters → count=1, range=0, step=0
- Only step → range=step, count=2
- Only range → step=range, count=2
- Only count → range set to finite default and step derived as range/(count-1)
"""

import pytest
from nanobrag_torch.utils.auto_selection import (
    auto_select_sampling,
    auto_select_divergence,
    auto_select_dispersion,
    auto_select_thickness,
    SamplingParams
)


class TestAT_SRC_002:
    """Test auto-selection of count/range/step parameters."""

    def test_no_parameters_provided(self):
        """No parameters → count=1, range=0, step=0"""
        # Test for angle parameters
        result = auto_select_sampling()
        assert result.count == 1
        assert result.range == 0.0
        assert result.step == 0.0

        # Test for thickness parameters
        result = auto_select_sampling(parameter_type="thickness")
        assert result.count == 1
        assert result.range == 0.0
        assert result.step == 0.0

    def test_only_step_provided(self):
        """Only step → range=step, count=2"""
        # Test for angle with step=0.1 rad
        result = auto_select_sampling(step=0.1)
        assert result.count == 2
        assert result.range == 0.1
        assert result.step == 0.1

        # Test for thickness with step=1e-7 m
        result = auto_select_sampling(step=1e-7, parameter_type="thickness")
        assert result.count == 2
        assert result.range == 1e-7
        assert result.step == 1e-7

    def test_only_range_provided(self):
        """Only range → step=range, count=2"""
        # Test for angle with range=0.5 rad
        result = auto_select_sampling(range_val=0.5)
        assert result.count == 2
        assert result.range == 0.5
        assert result.step == 0.5

        # Test for thickness with range=2e-6 m
        result = auto_select_sampling(range_val=2e-6, parameter_type="thickness")
        assert result.count == 2
        assert result.range == 2e-6
        assert result.step == 2e-6

    def test_only_count_provided_angles(self):
        """Only count → range=1.0 rad for angles, step=range/(count-1)"""
        # Test with count=5
        result = auto_select_sampling(count=5, parameter_type="angle")
        assert result.count == 5
        assert result.range == 1.0  # Default for angles
        assert abs(result.step - 0.25) < 1e-9  # 1.0/(5-1) = 0.25

        # Test with count=10
        result = auto_select_sampling(count=10, parameter_type="angle")
        assert result.count == 10
        assert result.range == 1.0
        assert abs(result.step - 1.0/9) < 1e-9

        # Test with count=1 (should be coerced to 2 for nonzero range)
        result = auto_select_sampling(count=1, parameter_type="angle")
        assert result.count == 2  # Coerced to ≥2
        assert result.range == 1.0
        assert result.step == 1.0  # 1.0/(2-1) = 1.0

    def test_only_count_provided_thickness(self):
        """Only count → range=0.5e-6 m for thickness, step=range/(count-1)"""
        # Test with count=5
        result = auto_select_sampling(count=5, parameter_type="thickness", default_range=0.5e-6)
        assert result.count == 5
        assert result.range == 0.5e-6  # Default for thickness
        assert abs(result.step - 0.125e-6) < 1e-15  # 0.5e-6/(5-1)

        # Test with count=10
        result = auto_select_sampling(count=10, parameter_type="thickness", default_range=0.5e-6)
        assert result.count == 10
        assert result.range == 0.5e-6
        assert abs(result.step - 0.5e-6/9) < 1e-15

    def test_range_and_step_provided(self):
        """Range and step provided → count=ceil(range/step)"""
        # Test with range=1.0, step=0.3
        result = auto_select_sampling(range_val=1.0, step=0.3)
        assert result.count == 4  # ceil(1.0/0.3) = 4
        assert result.range == 1.0
        assert result.step == 0.3

        # Test with exact division
        result = auto_select_sampling(range_val=1.0, step=0.25)
        assert result.count == 4  # ceil(1.0/0.25) = 4
        assert result.range == 1.0
        assert result.step == 0.25

    def test_count_and_range_provided(self):
        """Count and range provided → step=range/max(count-1, 1)"""
        # Test with count=5, range=2.0
        result = auto_select_sampling(count=5, range_val=2.0)
        assert result.count == 5
        assert result.range == 2.0
        assert abs(result.step - 0.5) < 1e-9  # 2.0/(5-1) = 0.5

        # Test with count=1, range=1.0
        result = auto_select_sampling(count=1, range_val=1.0)
        assert result.count == 1
        assert result.range == 1.0
        assert result.step == 1.0  # range/max(1-1, 1) = 1.0/1

    def test_divergence_auto_selection(self):
        """Test auto-selection for horizontal and vertical divergence."""
        # Test with only hdivsteps and vdivrange
        h_params, v_params = auto_select_divergence(
            hdivsteps=5,
            vdivrange=0.3
        )

        assert h_params.count == 5
        assert h_params.range == 1.0  # Default for angles
        assert abs(h_params.step - 0.25) < 1e-9

        assert v_params.count == 2
        assert v_params.range == 0.3
        assert v_params.step == 0.3

    def test_dispersion_auto_selection(self):
        """Test auto-selection for spectral dispersion."""
        # Test with only dispsteps
        result = auto_select_dispersion(dispsteps=5)
        assert result.count == 5
        assert result.range == 0.1  # Default 10% dispersion
        assert abs(result.step - 0.025) < 1e-9  # 0.1/(5-1)

        # Test with only dispersion
        result = auto_select_dispersion(dispersion=0.05)
        assert result.count == 2
        assert result.range == 0.05
        assert result.step == 0.05

    def test_thickness_auto_selection(self):
        """Test auto-selection for detector thickness sampling."""
        # Test with only thicksteps
        result = auto_select_thickness(thicksteps=5)
        assert result.count == 5
        assert result.range == 0.5e-6  # Default 0.5 μm
        assert abs(result.step - 0.125e-6) < 1e-15

        # Test with only detector_thick
        result = auto_select_thickness(detector_thick=1e-6)
        assert result.count == 2
        assert result.range == 1e-6
        assert result.step == 1e-6

    def test_all_parameters_provided(self):
        """When all parameters are provided, use them as-is."""
        result = auto_select_sampling(count=10, range_val=2.0, step=0.2)
        assert result.count == 10
        assert result.range == 2.0
        assert result.step == 0.2

    def test_conflicting_parameters(self):
        """Test handling of conflicting parameters per spec rules."""
        # When count > 0 but range < 0 and step > 0: range=step, count=2 (override)
        result = auto_select_sampling(count=10, step=0.3)
        assert result.count == 2  # Override provided count
        assert result.range == 0.3
        assert result.step == 0.3

        # When count ≤ 0, range < 0, step > 0: range=step, count=2
        result = auto_select_sampling(count=0, step=0.5)
        assert result.count == 2
        assert result.range == 0.5
        assert result.step == 0.5