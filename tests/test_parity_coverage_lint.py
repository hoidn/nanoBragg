#!/usr/bin/env python3
"""Tests for parity coverage linter.

Validates that the linter correctly identifies coverage gaps and structural issues.
"""

import os
import sys
import pytest
import tempfile
import yaml
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.lint_parity_coverage import ParityCoverageLinter


class TestParityCoverageLinter:
    """Test suite for parity coverage linter."""

    def test_linter_finds_repo_root(self):
        """Test that linter can find repo root."""
        repo_root = Path(__file__).parent.parent
        linter = ParityCoverageLinter(repo_root)
        assert linter.repo_root.exists()
        assert (linter.repo_root / "tests").exists()

    def test_linter_loads_yaml(self):
        """Test that linter can load parity_cases.yaml."""
        repo_root = Path(__file__).parent.parent
        yaml_path = repo_root / "tests" / "parity_cases.yaml"

        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        assert "cases" in data
        assert len(data["cases"]) > 0

    def test_yaml_structure_validation(self):
        """Test YAML structure validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            tests_dir = repo_root / "tests"
            tests_dir.mkdir()

            # Create valid YAML
            yaml_path = tests_dir / "parity_cases.yaml"
            valid_yaml = {
                "cases": [
                    {
                        "id": "AT-PARALLEL-001",
                        "description": "Test case",
                        "base_args": "-default_F 100",
                        "thresholds": {
                            "corr_min": 0.999,
                            "sum_ratio_min": 0.9,
                            "sum_ratio_max": 1.1
                        },
                        "runs": [
                            {"name": "test1", "extra_args": "-detpixels 256"}
                        ]
                    }
                ]
            }

            with open(yaml_path, "w") as f:
                yaml.dump(valid_yaml, f)

            # Create minimal spec
            specs_dir = repo_root / "specs"
            specs_dir.mkdir()
            spec_path = specs_dir / "spec-a-parallel.md"
            with open(spec_path, "w") as f:
                f.write("- AT-PARALLEL-001 Test\n  correlation ≥0.999\n")

            linter = ParityCoverageLinter(repo_root)
            result = linter.run_all_checks()

            # Should pass with valid structure
            errors = [r for r in linter.results if not r.passed and r.severity == "ERROR"]
            assert len(errors) == 0, f"Unexpected errors: {errors}"

    def test_missing_yaml_file(self):
        """Test handling of missing parity_cases.yaml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            linter = ParityCoverageLinter(repo_root)
            result = linter.run_all_checks()

            # Should fail with missing file
            assert not result
            assert any("not found" in r.message for r in linter.results if not r.passed)

    def test_invalid_yaml(self):
        """Test handling of invalid YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            tests_dir = repo_root / "tests"
            tests_dir.mkdir()

            yaml_path = tests_dir / "parity_cases.yaml"
            with open(yaml_path, "w") as f:
                f.write("invalid: yaml: content: [")

            linter = ParityCoverageLinter(repo_root)
            result = linter.run_all_checks()

            # Should fail with parse error
            assert not result
            assert any("parse" in r.message.lower() for r in linter.results if not r.passed)

    def test_real_repo_linting(self):
        """Test linting of actual repository."""
        repo_root = Path(__file__).parent.parent
        linter = ParityCoverageLinter(repo_root)
        result = linter.run_all_checks()

        # Should complete without errors (warnings are OK)
        errors = [r for r in linter.results if not r.passed and r.severity == "ERROR"]
        assert len(errors) == 0, f"Linter found errors: {[e.message for e in errors]}"

        # Should have found some AT cases
        yaml_ats_result = next((r for r in linter.results if "AT cases in parity_cases.yaml" in r.message), None)
        assert yaml_ats_result is not None
        assert yaml_ats_result.passed

    def test_extraction_of_spec_ats(self):
        """Test extraction of AT IDs from spec."""
        repo_root = Path(__file__).parent.parent
        linter = ParityCoverageLinter(repo_root)

        spec_ats = linter._extract_spec_ats()

        # Should find AT-PARALLEL-001 and others with correlation thresholds
        assert "AT-PARALLEL-001" in spec_ats
        assert "AT-PARALLEL-002" in spec_ats
        assert "AT-PARALLEL-006" in spec_ats

        # Should have found multiple ATs
        assert len(spec_ats) > 5

    def test_extraction_of_yaml_ats(self):
        """Test extraction of AT IDs from YAML."""
        repo_root = Path(__file__).parent.parent
        yaml_path = repo_root / "tests" / "parity_cases.yaml"

        with open(yaml_path) as f:
            yaml_data = yaml.safe_load(f)

        linter = ParityCoverageLinter(repo_root)
        yaml_ats = linter._extract_yaml_ats(yaml_data)

        # Should find AT-PARALLEL-001 and others
        assert "AT-PARALLEL-001" in yaml_ats
        assert "AT-PARALLEL-002" in yaml_ats

        # Should match number of cases in YAML
        assert len(yaml_ats) == len(yaml_data["cases"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])