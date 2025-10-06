Validation Scripts

Purpose
- Centralize reproducible validation and parity helpers invoked from prompts and supervisor input.

Guidelines
- Prefer small, composable scripts that wrap canonical pytest nodes or nb-compare flows.
- Accept configuration via CLI args and environment variables documented in docs/development/testing_strategy.md.
- Do not assume editable installs are absent; rely on the package being installed in editable mode.
- Keep scripts device/dtype neutral and avoid hard-coded paths.

Examples (future)
- Add targeted wrappers such as `run_parity_case.py` or `emit_metrics.py` as needed by the plan.

