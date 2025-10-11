Summary: Kick off Sprint 1.2 by documenting source weighting scope and capturing the failing baseline.
Mode: Parity
Focus: [SOURCE-WEIGHT-002] Simulator source weighting
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py
Artifacts: plans/active/source-weighting.md, reports/2026-01-test-suite-triage/phase_j/<STAMP>/source_weighting/
Do Now: Execute [SOURCE-WEIGHT-002] Phase A baseline — author the plan scaffold under plans/active/source-weighting.md, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py` and archive commands/logs/env in reports/2026-01-test-suite-triage/phase_j/<STAMP>/source_weighting/.
If Blocked: Capture the failure output and env snapshot in reports/2026-01-test-suite-triage/phase_j/blockers/<STAMP>/, note the blocker in docs/fix_plan.md Attempts, and stop for supervisor review.
Priorities & Rationale:
- docs/fix_plan.md:5-7 — Active focus now targets Sprint 1.2 `[SOURCE-WEIGHT-002]`.
- docs/fix_plan.md:54-55 — Next Actions call for plan creation + baseline capture before moving to Detector Config.
- plans/active/test-suite-triage.md:85-108 — Sprint 1.2 sequence defines the required tests and exit criteria.
- reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md:32-47,95-119 — C3 remains open with six failures; tracker expects plan + regression evidence.
How-To Map:
- Create a fresh UTC stamp (e.g., 20260117THHMMSSZ) and `mkdir -p reports/2026-01-test-suite-triage/phase_j/<STAMP>/source_weighting/` before running commands.
- Draft plans/active/source-weighting.md using the phased template (Context + Phase A/B sections); cite specs/spec-a-core.md §§3.4–3.5 and remediation_sequence Sprint 1.2 guidance.
- Log the exact pytest command, env vars, and git status into `commands.txt`; capture stdout/stderr in `pytest.log`; record `python -m nanobrag_torch --version` (or equivalent) plus `torch.__version__` in `env.json`.
- After the run, summarise failure counts + key stack traces in `summary.md` and update docs/fix_plan.md Attempts with the stamp/location.
- Finish by running `pytest --collect-only -q` if you modify tests/plan files, and note results in the artifact bundle.
Pitfalls To Avoid:
- Do not edit simulator physics yet; this loop is evidence-only.
- Keep ASCII formatting in the new plan/documentation.
- Always set `KMP_DUPLICATE_LIB_OK=TRUE`; no other env tweaks unless documented.
- No full `pytest tests/` runs; stay on the two mapped selectors.
- Preserve Protected Assets referenced in docs/index.md (e.g., loop.sh, input.md).
- Avoid removing existing remediation tracker history; append new notes instead.
- Capture timestamps consistently; include sha256 manifest if you add binaries/logs.
- Maintain device/dtype neutrality—do not hard-code `.cpu()`/`.cuda()` in any scratch scripts.
Pointers:
- docs/fix_plan.md:5-8,54-55
- plans/active/test-suite-triage.md:85-108
- reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_sequence.md:85-109
- reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md:32-47,95-119
Next Up: Stage Detector Config plan refresh for Sprint 1.3 once source weighting baseline is logged.
