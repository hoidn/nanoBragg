Summary: Capture baseline evidence for tricubic interpolation before touching implementation.
Mode: Docs
Focus: [VECTOR-TRICUBIC-001] Vectorize tricubic interpolation and detector absorption
Branch: feature/spec-based-2
Mapped tests:
- tests/test_at_str_002.py
- tests/test_at_abs_001.py
Artifacts:
- reports/2025-10-vectorization/phase_a/test_at_str_002.collect.log
- reports/2025-10-vectorization/phase_a/test_at_str_002.log
- reports/2025-10-vectorization/phase_a/test_at_abs_001.log
- reports/2025-10-vectorization/phase_a/tricubic_baseline.md
- reports/2025-10-vectorization/phase_a/tricubic_baseline_results.json
- reports/2025-10-vectorization/phase_a/absorption_baseline.md
- reports/2025-10-vectorization/phase_a/absorption_baseline_results.json
- reports/2025-10-vectorization/phase_a/env.json
Do Now: VECTOR-TRICUBIC-001 Phase A1 — env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_str_002.py -v
If Blocked: Run pytest --collect-only -q tests/test_at_str_002.py and record the output; if imports fail capture the traceback and drop it in reports/2025-10-vectorization/phase_a/blockers.log before stopping.
Priorities & Rationale:
- specs/spec-a-core.md:230 anchors tricubic neighborhood expectations; we need evidence the current path still hits the fallback.
- specs/spec-a-parallel.md:283 cements CLI semantics for -interpolate/-nointerpolate, so baseline logs must confirm current defaults.
- docs/development/testing_strategy.md:18-32 mandates targeted pytest commands in Do Now and collection-first discipline.
- docs/development/pytorch_runtime_checklist.md:6-23 enforces vectorization and device/dtype neutrality, informing the benchmark harness requirements.
- plans/active/vectorization.md:1-74 now encodes the Phase A evidence deliverables and env snapshot requirement.
How-To Map:
- export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md for reference while executing this loop.
- mkdir -p reports/2025-10-vectorization/phase_a before running any commands.
- Step 1 (A1): env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_at_str_002.py | tee reports/2025-10-vectorization/phase_a/test_at_str_002.collect.log
- Step 2 (A1): env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_str_002.py -v | tee reports/2025-10-vectorization/phase_a/test_at_str_002.log
- Step 3 (A2 harness authoring): create scripts/benchmarks/tricubic_baseline.py following plan guidance (device/dtype neutral, argument parser for --sizes/--repeats)
- Step 4 (A2 run CPU): PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/tricubic_baseline.py --sizes 256 512 --repeats 5 --devices cpu | tee reports/2025-10-vectorization/phase_a/tricubic_baseline.md
- Step 5 (A2 raw metrics): ensure the harness writes JSON to reports/2025-10-vectorization/phase_a/tricubic_baseline_results.json (append GPU block if CUDA available)
- Step 6 (env snapshot): python - <<'PY'
import json, os, platform
payload = {
    "python": platform.python_version(),
    "torch": __import__("torch").__version__,
    "devices": {
        "cuda_available": __import__("torch").cuda.is_available()
    }
}
os.makedirs("reports/2025-10-vectorization/phase_a", exist_ok=True)
with open("reports/2025-10-vectorization/phase_a/env.json", "w") as fh:
    json.dump(payload, fh, indent=2)
PY
- Step 7 (A3 harness authoring): mirror Step 3 as scripts/benchmarks/absorption_baseline.py, matching CLI signature and device handling.
- Step 8 (A3 tests): env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_abs_001.py -v | tee reports/2025-10-vectorization/phase_a/test_at_abs_001.log
- Step 9 (A3 run CPU): PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/absorption_baseline.py --sizes 256 512 --repeats 5 --devices cpu | tee reports/2025-10-vectorization/phase_a/absorption_baseline.md
- Step 10 (A3 raw metrics): confirm the absorption harness writes JSON results to reports/2025-10-vectorization/phase_a/absorption_baseline_results.json and updates env.json only if new device info appears.
- After each step, update docs/fix_plan.md Attempts History with command summaries once evidence is in place.
Pitfalls To Avoid:
- Do not edit simulator code yet; this loop is evidence-only per plan Phase A.
- Avoid running full pytest suites; stick to the mapped selectors and collection runs.
- Keep new scripts ASCII-only and place them under scripts/benchmarks/ as the plan states.
- Honour vectorization/device rules when drafting harnesses—do not bake in CPU-only shortcuts or dtype conversions.
- Capture logs with tee so artifacts are persisted even if commands fail midway.
- Respect Protected Assets: verify any touched files are not listed in docs/index.md before editing.
- When writing JSON, ensure separators are deterministic for future diffs (indent=2, sorted keys if feasible).
- If CUDA is unavailable, explicitly note that in env.json instead of faking GPU numbers.
- Run commands from repo root; rely on PYTHONPATH and env exports instead of cd.
Pointers:
- specs/spec-a-core.md:228-255
- specs/spec-a-parallel.md:283
- docs/development/testing_strategy.md:18-33
- docs/development/pytorch_runtime_checklist.md:6-23
- plans/active/vectorization.md:1-120
Next Up:
- Phase A2 baseline harness execution (extend to GPU if available once CPU metrics captured).
- Phase A3 absorption baseline completion and Attempt #1 entry in docs/fix_plan.md.
