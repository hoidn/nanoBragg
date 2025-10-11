# Phase M2b — Gradient Compile Guard Implementation

## Rationale
The gradient tests (`tests/test_gradients.py`) use `torch.autograd.gradcheck` to verify numerical gradient correctness. However, `torch.compile` has known bugs with:
1. C++ array declarations in backward passes (conflicting `tmp_acc*` arrays)
2. Donated buffers in backward functions that break gradcheck

Since gradcheck is testing numerical correctness (not performance), disabling compilation is safe and appropriate for these tests.

## Implementation
The `NANOBRAGG_DISABLE_COMPILE=1` environment flag is implemented in two places:

### 1. Test File (`tests/test_gradients.py` lines 17-23)
The test module sets the environment variable **before** importing torch to prevent Dynamo from caching compiled graphs:
```python
os.environ["NANOBRAGG_DISABLE_COMPILE"] = "1"
```

### 2. Simulator (`src/nanobrag_torch/simulator.py` line 617)
The simulator respects the flag when deciding whether to compile the physics kernel:
```python
disable_compile = os.environ.get("NANOBRAGG_DISABLE_COMPILE", "0") == "1"
if not disable_compile:
    # Attempt torch.compile
    ...
```

When the flag is set, the simulator uses the eager-mode uncompiled physics kernel, bypassing torch.compile entirely.

## Verification
The implementation has been verified by:
1. Confirming both locations (test and simulator) respect the flag
2. Running the gradcheck test suite with the flag set
3. Verifying that compilation is skipped when expected

## References
- `arch.md` §15 — Differentiability Guidelines
- `docs/development/testing_strategy.md` §4.1 — Gradient Checks
- `docs/development/pytorch_runtime_checklist.md` — Runtime guardrails
