Summary: Capture Phase B design artifacts for φ carryover removal before code edits
Mode: Docs
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_cli_scaling_phi0.py
Artifacts: reports/2025-10-cli-flags/phase_phi_removal/phase_b/<timestamp>/
Do Now: CLI-FLAGS-003 B0 design review — run `pytest --collect-only -q tests/test_cli_scaling_phi0.py`, then write `design_review.md` + `commands.txt` under `reports/2025-10-cli-flags/phase_phi_removal/phase_b/<timestamp>/` describing planned edits/tests (no code changes yet)
If Blocked: Capture failure in `reports/2025-10-cli-flags/phase_phi_removal/phase_b/<timestamp>/attempts.log` and ping supervisor via docs/fix_plan.md Attempts
Priorities & Rationale:
- plans/active/phi-carryover-removal/plan.md:41 — Phase B0 requires a design bundle before removing the shim
- docs/bugs/verified_c_bugs.md:167 — Confirms φ carryover is a C-only bug; PyTorch must default to spec behavior once shim is gone
- specs/spec-a-core.md:204 — Normative φ rotation pipeline demands identity at φ=0, informing acceptance gates after removal
- docs/fix_plan.md:457 — Next Actions now depend on completing the Phase B design artifact
- plans/active/cli-noise-pix0/plan.md:33 — Plan snapshot expects Phase B work before scaling parity resumes
How-To Map:
- mkdir -p reports/2025-10-cli-flags/phase_phi_removal/phase_b/<timestamp>
- pytest --collect-only -q tests/test_cli_scaling_phi0.py | tee reports/.../collect.log
- Document impacted files/tests/specs in reports/.../design_review.md (reference plan + spec sections)
- Log shell history in reports/.../commands.txt and capture env via `python -m json.tool` dumping git SHA + python version
Pitfalls To Avoid:
- Do not touch production code or tests during this design loop
- Keep artifact directory names timestamped and unique
- Preserve vectorization assumptions when outlining planned edits (no promises to add loops)
- Respect Protected Assets; never move files listed in docs/index.md
- Verify pytest selector via collect-only; no full regression runs this loop
- Record exact spec/doc references in design_review.md for traceability
- Avoid committing binary artifacts; keep reports ASCII/markdown/JSON only
Pointers:
- plans/active/phi-carryover-removal/plan.md:37
- docs/fix_plan.md:457
- docs/bugs/verified_c_bugs.md:167
- specs/spec-a-core.md:204
- plans/active/cli-noise-pix0/plan.md:31
Next Up: Begin Phase B1–B3 code removal once design bundle is reviewed
