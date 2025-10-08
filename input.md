Summary: Establish pyrefly supervision runway so static-analysis backlog can be delegated safely.
Mode: Docs
Focus: STATIC-PYREFLY-001 / Run pyrefly analysis and triage (docs/fix_plan.md)
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/pyrefly/<timestamp>/{commands.txt,summary.md,env.json,pyrefly.log}
Do Now: STATIC-PYREFLY-001 Phase A (A1–A3). Run `rg -n "^\[tool\.pyrefly\]" pyproject.toml`, `pyrefly --version`, and scaffold `reports/pyrefly/<timestamp>/` with empty `commands.txt` + `README.md`; record outputs per plan.
If Blocked: Capture missing-tool diagnostics in `reports/pyrefly/<timestamp>/commands.txt`, add a TODO to docs/fix_plan.md noting install prerequisites, then halt before running any linters.
Priorities & Rationale:
- docs/fix_plan.md:2943 — Item now in_progress; needs Phase A evidence before any baseline scan.
- plans/active/static-pyrefly.md — Phase A defines the exact pre-flight checks; follow state columns.
- prompts/pyrefly.md — SOP forbids new tool installs; confirms two-message cadence for future loops.
- pyproject.toml:11 — `[tool.pyrefly]` entry is the configuration guard we must verify.
How-To Map:
- Commands: `rg -n "^\[tool\.pyrefly\]" pyproject.toml`; `pyrefly --version`.
- Artifact scaffold: `mkdir -p reports/pyrefly/$(date -u +%Y%m%dT%H%M%SZ)`; touch `commands.txt` & `README.md` in that directory.
- Logging: Append the exact commands & outputs to `commands.txt`; note git SHA plus branch name.
Pitfalls To Avoid:
- Do not run `pyrefly check src` until Phase B.
- Keep reports under `reports/pyrefly/`; never commit logs.
- Leave `[tool.pyrefly]` untouched—configuration is canonical.
- No code edits or test runs this loop; documentation/evidence only.
- Respect Protected Assets; do not modify files listed in docs/index.md.
- Avoid creating multiple timestamp folders; stick to one per loop.
- Capture UTC timestamps for reproducibility.
- Record exit codes for every command executed.
Pointers:
- docs/fix_plan.md:2943 — STATIC-PYREFLY-001 overview and next actions.
- plans/active/static-pyrefly.md — Phase breakdown and checklist.
- prompts/pyrefly.md — Tool SOP and guardrails.
Next Up: Phase B (baseline `pyrefly check src` run) once Phase A evidence is logged.
