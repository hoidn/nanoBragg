# Phase Q Config Updates

## Q2: pytest Configuration (pyproject.toml)

Added to `[tool.pytest.ini_options]`:
- New marker: `slow_gradient` (marks gradient tests with extended runtime tolerance, 900s default)
- Default timeout: 300s
- timeout_func_only: true (only times out test functions, not fixtures)

File: pyproject.toml lines 48-57

## Q3: Test Annotation (tests/test_gradients.py)

Added decorators to `test_property_gradient_stability`:
- `@pytest.mark.slow_gradient`
- `@pytest.mark.timeout(900)` 

File: tests/test_gradients.py lines 574-576

Rationale:
- Phase P validation (STAMP 20251015T061848Z) confirmed 839.95s runtime
- 900s tolerance provides 6.7% margin (60.05s headroom)
- References: reports/2026-01-test-suite-triage/phase_p/20251015T060354Z/c18_timing.md
