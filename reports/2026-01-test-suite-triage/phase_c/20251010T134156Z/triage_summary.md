# Phase C Failure Classification — Partial Suite (2025-10-10T13:24:06Z bundle)

## Context
- Source bundle: `reports/2026-01-test-suite-triage/phase_b/20251010T132406Z/`
- Coverage: 34 failures observed before 600 s timeout (~75 % of suite executed). Remaining ~172 tests unclassified.
- Inputs referenced: `failures_raw.md`, `logs/pytest_full.log`, spec shards (`specs/spec-a-core.md` Source/Detector sections), `docs/development/testing_strategy.md`, `docs/architecture/pytorch_design.md`, `docs/fix_plan.md`, `plans/active/test-suite-triage.md`.
- Goal: bucket each observed failure into Implementation Bug vs Test Deprecation vs Config gap and map to existing or new fix-plan work.

## Summary
All 34 observed failures correspond to known implementation gaps or incomplete features. No evidence of obsolete/deprecated tests surfaced; each suite aligns with spec-A acceptance criteria. Focus next loops on remediation sequencing rather than test retirement.

## Classification Table
| Cluster ID | Test Nodes (count) | Category | Hypothesis / Notes | Existing Tracking | Recommended Next Step |
| --- | --- | --- | --- | --- | --- |
| C1 | `tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F` (1) | Implementation bug | CLI runner still exits non-zero for minimal `-default_F` invocation (likely missing default HKL fallback or SMV header population). Spec-A CLI AT-CLI-002 demands success. | None — add subtask under `[TEST-SUITE-TRIAGE-001]` → spawn dedicated CLI fix item. | Reproduce targeted command; capture stderr; draft fix plan (CLI defaults/outputs). |
| C2 | `tests/test_at_parallel_013.py` deterministic trio (3) | Implementation bug | PyTorch simulator not deterministic under identical seeds; violates spec §5.3 RNG determinism. Likely mosaic/source sampling randomness not gated by provided seeds. | None — new determinism remediation effort required. | Instrument RNG seeding path; design plan to enforce seed propagation across torch + numpy. |
| C3 | `tests/test_at_parallel_015.py::test_mixed_units_comprehensive` (1) | Implementation bug | Mixed-unit acceptance still fails; ties directly to open scattering-vector/fluence parity findings (`CONVENTION-004/005/006`). | `[VECTOR-PARITY-001]` Phase D/E (Tap 5 HKL/units) | Prioritise Tap 5.1/5.2 remediation; mark this test as acceptance gating for unit fix. |
| C4 | `tests/test_at_parallel_017.py` grazing incidence set (4) | Implementation bug | Extreme detector angles misbehave (likely pivot/obliquity math). Spec §4.6 requires accurate rotation order + unit handling. | `[VECTOR-PARITY-001]` (detector geometry backlog) | After Tap 5 parity fixes, schedule detector geometry audit focusing on extreme angles; may need new plan. |
| C5 | `tests/test_at_parallel_024.py` determinism + mosaic umat (3) | Implementation bug | Same root as C2 plus mosaic rotation reproducibility (mosaic RNG). | None | Fold into determinism remediation plan; ensure crystal.mosaic RNG uses seeded generators. |
| C6 | `tests/test_at_parallel_026.py::test_triclinic_absolute_peak_position_vs_c` (1) | Implementation bug | PyTorch absolute peak location drifts vs C; consistent with HKL lookup bug identified in Tap 5 hypotheses. | `[VECTOR-PARITY-001]` Tap 5 HKL indexing | Blocked on Tap 5 confirmation; record as acceptance-level failure to validate once HKL fix lands. |
| C7 | `tests/test_at_src_001.py` + `tests/test_at_src_001_simple.py` (6) | Implementation bug | Sourcefile weighting still incorrect in simulator despite IO support; weights ignored during flux normalization per log review. Contradiction noted between spec text and implementation comment. | Past `[SOURCE-WEIGHT-001]` marked complete but simulation path still broken → reopen via new subphase. | Author follow-up plan to ensure `Simulator` multiplies weights and normalization matches spec; add regression tests. |
| C8 | `tests/test_at_str_003.py` GAUSS + comparison (2) | Implementation bug | GAUSS lattice shape path deviates from spec (likely missing 3D sinc or normalization). | `[VECTOR-TRICUBIC-002]` backlog | Extend vectorization plan with GAUSS parity tap; treat as high-priority once Tap 5 resolves. |
| C9 | `tests/test_at_tools_001.py::test_script_integration` (1) | Implementation bug | Dual-runner helper not wired for PyTorch binary (probably missing CLI integration). | None | Create tooling plan to restore dual-runner parity (C vs PyTorch). |
| C10 | `tests/test_cli_flags.py` (`pix0_vector_mm_*`, `test_scaled_hkl_roundtrip`) (3) | Implementation bug | `-pix0_vector_mm` semantics not implemented; HKL/Fdump parity missing. Matches active CLI flag initiative. | `[CLI-FLAGS-003]` | Keep CLI plan priority high; these tests are the gating acceptance cases. |
| C11 | `tests/test_debug_trace.py` suite (4) | Implementation bug | Debug flags (`--printout`, `--trace_pixel`) unsupported yet; spec requires parity with C trace instrumentation. | None | Need new debugging/trace instrumentation plan; consider delegating after triage. |
| C12 | `tests/test_detector_config.py` initialization tests (2) | Implementation bug | Detector defaults/custom config diverge from spec (likely due to incomplete dataclass defaults). | None | Audit detector config dataclass + CLI mapping; capture reproduction commands; spawn fix item. |
| C13 | `tests/test_detector_conventions.py::test_denzo_beam_center_mapping` (1) | Implementation bug | Denzo convention mapping unresolved. | `[VECTOR-PARITY-001]` / detector plan backlog | Schedule parity tap for Denzo mapping once Tap 5 done. |
| C14 | `tests/test_detector_pivots.py` pivot behavior (2) | Implementation bug | BEAM vs SAMPLE pivot semantics off (likely missing 0.5-pixel adjustments). | `[VECTOR-PARITY-001]` pivot tasks | Elevate pivot remediation after Tap 5 HKL fix; treat as acceptance gating. |

## Unclassified / Deferred
- Remaining ~172 tests were not executed in Attempt #2. Phase C triage must be revisited after a complete run (Phase B rerun with ≥30 min budget or split suites).

## Proposed Follow-ups
1. Update `docs/fix_plan.md` `[TEST-SUITE-TRIAGE-001]` with Phase C Attempt #3 referencing this summary and noting “all observed failures = implementation bugs”.
2. Under `[TEST-SUITE-TRIAGE-001]` Next Actions, add bullet to spawn targeted remediation items (determinism, source weighting, debug trace).
3. Refresh `plans/active/test-suite-triage.md` Phase C table: mark `C1` complete, add checklist rows for mapping clusters to fix-plan entries (C2–C14 pending once owners assigned).
4. Prepare Phase C `pending_actions.md` (future loop) once owner/plan IDs assigned; blocked on decision about determinism plan structure.

