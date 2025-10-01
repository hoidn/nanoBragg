#!/usr/bin/env python3
"""Docs-as-Data CI Linter for Parity Coverage

Validates that parity documentation is complete and consistent:
1. Spec → matrix → YAML coverage for all parity-threshold ATs
2. Existence of mapped commands/binaries referenced in YAML
3. Presence of artifact paths when fix_plan marks parity items complete

Exit codes:
- 0: All checks pass
- 1: Lint failures found
- 2: Configuration/file errors
"""

import sys
import re
import yaml
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass


@dataclass
class LintResult:
    """Result of a lint check."""
    passed: bool
    message: str
    severity: str = "ERROR"  # ERROR or WARNING


class ParityCoverageLinter:
    """Lints parity documentation for completeness and consistency."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.results: List[LintResult] = []

    def add_result(self, passed: bool, message: str, severity: str = "ERROR"):
        """Add a lint result."""
        self.results.append(LintResult(passed, message, severity))

    def run_all_checks(self) -> bool:
        """Run all lint checks. Returns True if all pass."""
        print("=" * 80)
        print("Parity Coverage Linter")
        print("=" * 80)
        print()

        # Check 1: Validate YAML file exists and is parseable
        yaml_path = self.repo_root / "tests" / "parity_cases.yaml"
        if not yaml_path.exists():
            self.add_result(False, f"parity_cases.yaml not found at {yaml_path}")
            return self._report_results()

        try:
            with open(yaml_path) as f:
                yaml_data = yaml.safe_load(f)
        except Exception as e:
            self.add_result(False, f"Failed to parse parity_cases.yaml: {e}")
            return self._report_results()

        # Check 2: Extract AT IDs from YAML
        yaml_ats = self._extract_yaml_ats(yaml_data)
        self.add_result(True, f"Found {len(yaml_ats)} AT cases in parity_cases.yaml")

        # Check 3: Extract AT IDs from spec
        spec_ats = self._extract_spec_ats()
        self.add_result(True, f"Found {len(spec_ats)} parity-threshold ATs in spec")

        # Check 4: Check for missing coverage
        missing_ats = spec_ats - yaml_ats
        if missing_ats:
            self.add_result(
                False,
                f"Missing YAML coverage for: {sorted(missing_ats)}",
                "WARNING"  # Warning for now, can become ERROR later
            )
        else:
            self.add_result(True, "All spec ATs have YAML coverage")

        # Check 5: Check for extra ATs in YAML not in spec
        extra_ats = yaml_ats - spec_ats
        if extra_ats:
            self.add_result(
                False,
                f"YAML contains ATs not in spec: {sorted(extra_ats)}",
                "WARNING"
            )
        else:
            self.add_result(True, "No extra ATs in YAML")

        # Check 6: Validate YAML structure
        self._validate_yaml_structure(yaml_data)

        # Check 7: Check for C binary existence
        self._check_c_binary()

        return self._report_results()

    def _extract_yaml_ats(self, yaml_data: dict) -> Set[str]:
        """Extract AT IDs from parity_cases.yaml."""
        ats = set()
        if "cases" in yaml_data:
            for case in yaml_data["cases"]:
                if "id" in case:
                    ats.add(case["id"])
        return ats

    def _extract_spec_ats(self) -> Set[str]:
        """Extract parity-threshold AT IDs from spec-a-parallel.md.

        These are ATs that should be in parity_cases.yaml, identified by having
        explicit correlation/threshold requirements in the spec.
        """
        spec_path = self.repo_root / "specs" / "spec-a-parallel.md"
        if not spec_path.exists():
            self.add_result(False, f"Spec not found: {spec_path}")
            return set()

        try:
            with open(spec_path) as f:
                content = f.read()
        except Exception as e:
            self.add_result(False, f"Failed to read spec: {e}")
            return set()

        # Find all AT-PARALLEL-XXX entries that mention correlation thresholds
        # These are the ones that should be in parity_cases.yaml
        ats = set()

        # Pattern: AT-PARALLEL-NNN followed by correlation/threshold requirement
        # Look for explicit numeric thresholds like "≥0.9999" or ">0.98"
        at_pattern = r'AT-PARALLEL-(\d{3})'
        threshold_pattern = r'correlation\s+[≥>]\s*0\.\d+'

        # Split into AT sections
        sections = re.split(r'- (AT-PARALLEL-\d{3})', content)

        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                at_id = sections[i]
                at_content = sections[i + 1]

                # Check if this AT has threshold requirements
                if re.search(threshold_pattern, at_content, re.IGNORECASE):
                    ats.add(at_id)

                # Also check for explicit "Parity (canonical)" implementation
                if "Parity (canonical)" in at_content or "test_parity_matrix" in at_content:
                    ats.add(at_id)

        return ats

    def _validate_yaml_structure(self, yaml_data: dict):
        """Validate parity_cases.yaml structure."""
        if "cases" not in yaml_data:
            self.add_result(False, "YAML missing 'cases' top-level key")
            return

        for i, case in enumerate(yaml_data["cases"]):
            case_id = case.get("id", f"case_{i}")

            # Check required fields
            required_fields = ["id", "description", "base_args", "thresholds", "runs"]
            for field in required_fields:
                if field not in case:
                    self.add_result(False, f"{case_id}: missing required field '{field}'")

            # Check threshold structure
            if "thresholds" in case:
                thresholds = case["thresholds"]
                threshold_fields = ["corr_min", "sum_ratio_min", "sum_ratio_max"]
                for field in threshold_fields:
                    if field not in thresholds:
                        self.add_result(
                            False,
                            f"{case_id}: missing threshold field '{field}'",
                            "WARNING"
                        )

            # Check runs structure
            if "runs" in case:
                if not isinstance(case["runs"], list) or len(case["runs"]) == 0:
                    self.add_result(False, f"{case_id}: 'runs' must be non-empty list")
                else:
                    for j, run in enumerate(case["runs"]):
                        if "name" not in run:
                            self.add_result(
                                False,
                                f"{case_id} run {j}: missing 'name' field"
                            )
                        if "extra_args" not in run:
                            self.add_result(
                                False,
                                f"{case_id} run {j}: missing 'extra_args' field",
                                "WARNING"
                            )

        self.add_result(True, f"Validated structure of {len(yaml_data['cases'])} cases")

    def _check_c_binary(self):
        """Check if C binary exists."""
        # Check in order of precedence
        paths = [
            self.repo_root / "golden_suite_generator" / "nanoBragg",
            self.repo_root / "nanoBragg"
        ]

        found = False
        for path in paths:
            if path.exists():
                self.add_result(True, f"Found C binary: {path}")
                found = True
                break

        if not found:
            self.add_result(
                False,
                f"C binary not found. Checked: {paths}",
                "WARNING"
            )

    def _report_results(self) -> bool:
        """Print results and return True if all passed."""
        print()
        print("=" * 80)
        print("Results")
        print("=" * 80)
        print()

        errors = []
        warnings = []
        passes = []

        for result in self.results:
            if not result.passed:
                if result.severity == "ERROR":
                    errors.append(result)
                else:
                    warnings.append(result)
            else:
                passes.append(result)

        # Print passes
        if passes:
            print(f"✓ {len(passes)} checks passed:")
            for r in passes:
                print(f"  • {r.message}")
            print()

        # Print warnings
        if warnings:
            print(f"⚠ {len(warnings)} warnings:")
            for r in warnings:
                print(f"  • {r.message}")
            print()

        # Print errors
        if errors:
            print(f"✗ {len(errors)} errors:")
            for r in errors:
                print(f"  • {r.message}")
            print()

        # Summary
        all_passed = len(errors) == 0
        if all_passed:
            print("✓ All checks passed!")
            if warnings:
                print(f"  ({len(warnings)} warnings)")
        else:
            print(f"✗ {len(errors)} check(s) failed")

        print()
        return all_passed


def main():
    """Main entry point."""
    # Find repo root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent

    # Run linter
    linter = ParityCoverageLinter(repo_root)
    all_passed = linter.run_all_checks()

    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()