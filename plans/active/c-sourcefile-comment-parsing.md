## Context
- Initiative: C-SOURCEFILE-001 — catalogue and triage the nanoBragg.c sourcefile parsing bug discovered during SOURCE-WEIGHT-001 Phase G. The C binary currently treats lines starting with `#` as valid sources (direction `[0,0,0]`, weight `0`), inflating the source count and corrupting normalization. We must document the behaviour, establish the spec-compliant expectation (comments ignored), and provide guardrails for PyTorch parity work until the C bug is patched or documented upstream.
- Phase Goal: Deliver a reproducible evidence bundle, authoritative specification reference, and a downstream plan for documentation/tests so the PyTorch implementation and supervising plans stay aligned while the C defect is tracked separately.
- Dependencies:
  - `specs/spec-a-cli.md` — defines the `-sourcefile` format but does not mention comments; needs clarification or additive guidance.
  - `specs/spec-a-core.md` §4 (Sources) — states weight and wavelength columns are ignored; use this section to justify equal weighting regardless of file decorations.
  - `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` — records the discovery and requires a sibling entry for this bug so parity evidence can proceed without conflation.
  - `reports/2025-11-source-weights/phase_g/20251009T225052Z/notes.md` & `metrics.json` — original reproduction logs showing 4 sources created from a 2-line fixture.
  - `plans/active/source-weight-normalization.md` — Phase G5 references this plan; keep guidance synchronised.

### Phase A — Evidence Capture & Minimal Reproduction
Goal: Produce a clean, timestamped bundle that proves the parsing bug exists and quantifies its impact on normalization.
Prereqs: Rebuilt `NB_C_BIN` with debug symbols; sanitizer fixture with and without `#` comment lines; `reports/2025-11-source-weights/phase_g` baseline reviewed.
Exit Criteria: New `<STAMP>` directory under `reports/2025-11-source-weights/comment_parsing/<STAMP>/` containing commands, stdout/stderr, metrics, and a succinct summary proving the ghost sources.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Stage paired fixtures | [ ] | Copy the two-source file used in SOURCE-WEIGHT-001 and create two variants: `with_comments.txt` (original) and `without_comments.txt` (comments stripped). Store checksums in `README.md` inside the new reports directory. |
| A2 | Run comparative CLI commands | [ ] | Execute C nanoBragg with each fixture (identical geometry, `-interpolate 0`, `-default_F 100`). Capture stdout/stderr to `c_with_comments.log` / `c_without_comments.log` and note the reported source counts and sums. |
| A3 | Quantify divergence | [ ] | Use a small Python snippet (stored alongside the logs) to compute total intensity and correlation between the two runs. Highlight the normalization gap (expected large ratio when comments present) in `summary.md`. |

### Phase B — Specification Alignment & Decision Record
Goal: Determine the normative expectation for sourcefile parsing and document whether the current C behaviour violates the spec or requires a spec amendment.
Prereqs: Phase A bundle complete.
Exit Criteria: Decision note stored under `reports/2025-11-source-weights/comment_parsing/<STAMP>/decision.md` citing relevant spec sections and concluding the desired behaviour (ignore comments) plus interim guidance for PyTorch parity.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Review spec shards | [ ] | Summarise `specs/spec-a-cli.md` and `specs/spec-a-core.md` language on `-sourcefile`; note absence of comment handling guidance and the explicit equal-weight clause. |
| B2 | Draft decision memo | [ ] | Document why comments must be ignored (e.g., compatibility with existing tests, alignment with spec equal weighting). Include excerpted nanoBragg.c code (Rule #11) showing the bug. |
| B3 | Update fix_plan linkage | [ ] | Add findings to `docs/fix_plan.md` entry `[C-SOURCEFILE-001]` (to be created) and note the decision reference for SOURCE-WEIGHT-001 Phase G5. |

### Phase C — Guardrails & Delegation Prep
Goal: Ensure PyTorch parity work and tests remain stable despite the C bug; prepare follow-up tasks for documentation and eventual C fix.
Prereqs: Phase B decision memo approved.
Exit Criteria: Guard instructions captured in fix_plan and, if needed, a small PyTorch regression test validating comment handling.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Document interim guardrails | [ ] | Update `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` next actions with guidance to use the sanitised fixture and reference the comment parsing bug entry. |
| C2 | Propose PyTorch regression | [ ] | If not already covered, draft a test plan (not implementation yet) ensuring PyTorch ignores comment lines (`tests/test_cli_scaling.py` or new unit test). Record plan under `reports/2025-11-source-weights/comment_parsing/<STAMP>/test_plan.md`. |
| C3 | Prepare delegation packet | [ ] | Outline future work (C fix or documentation PR) with references, including required acceptance tests and documentation updates, so Ralph can pick it up when prioritised. |

### Phase D — Closure & Archival
Goal: Close the bug documentation loop once mitigation is in place or responsibility is handed off to upstream maintainers.
Prereqs: Phase C guardrails enacted, follow-up ownership decided.
Exit Criteria: Fix-plan entry updated with resolution, optional archival note added to `plans/archive/`, and galph memory summarises remaining risks.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Track upstream fix or documentation | [ ] | If a C patch is proposed, monitor and capture final metrics. Otherwise, record the decision to document-and-mitigate, including links to upstream ticket or internal memo. |
| D2 | Archive plan | [ ] | Once residual actions are complete or deferred with rationale, update `docs/fix_plan.md` status to `done/deferred`, move this plan to `plans/archive/`, and log closure in `galph_memory.md`. |

## Reporting Expectations
- Store new artifacts under `reports/2025-11-source-weights/comment_parsing/<STAMP>/`; include `commands.txt`, `summary.md`, metrics JSON, and fixture checksums. Do not commit the reports directory — reference paths only in fix_plan attempts.
- Always run `pytest --collect-only` for any selectors referenced in delegation packets to keep command provenance verifiable.
- Coordinate updates with `plans/active/source-weight-normalization.md` (Phase G5) so parity evidence and bug tracking remain in lockstep.
