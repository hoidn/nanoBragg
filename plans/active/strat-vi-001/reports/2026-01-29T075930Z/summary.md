### Turn Summary
Documented the VI deprecation milestone by updating mainstrategy §8, fix_plan, and plan artifacts to point at 2026-01-29T075930Z.
Identified the remaining evidence gap (no pytest log for the DeprecationWarning guard) and mapped the next engineer action to capture it.
Next: run pytest tests/test_vi_mosaic.py::test_probabilistic_simulator_deprecated_warning -v on CPU and archive the log under the new STRAT-VI-001 artifact path.
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T075930Z/
