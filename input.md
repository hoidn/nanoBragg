Summary: Harmonise the source weight fixture with the test geometry and record the comment-free variant before rerunning parity.
Mode: Docs
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: main
Mapped tests:
- tests/test_cli_scaling.py::TestSourceWeights
- tests/test_cli_scaling.py::TestSourceWeightsDivergence
Artifacts: reports/2025-11-source-weights/phase_g/<STAMP>/, reports/2025-11-source-weights/fixtures/
Do Now: [SOURCE-WEIGHT-001] Correct weighted source normalization — NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence
If Blocked: Capture `collect.log` and a short `attempts.md` under the STAMP directory summarising the blocker (e.g., missing fixture path), then stop and ping galph.
Priorities & Rationale:
- plans/active/source-weight-normalization.md:22 — Phase G0 now requires a sanitised fixture + checksums before parity reruns.
- docs/fix_plan.md:4040 — Next actions demand the new bundle references the comment-free fixture and bug hand-off.
- specs/spec-a-core.md:151 — Spec enforces equal weighting irrespective of file decorations; the fixture must reflect that contract.
- reports/2025-11-source-weights/phase_g/20251009T225052Z/notes.md#L12 — Prior attempt logged the mismatch; we need a reproducible follow-up bundle.
- plans/active/c-sourcefile-comment-parsing.md:14 — The new plan depends on a paired fixture set; completing G0 unblocks Phase A1 there.
How-To Map:
- `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `export OUTDIR="reports/2025-11-source-weights/phase_g/$STAMP"`; `mkdir -p "$OUTDIR"/logs`.
- `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee "$OUTDIR"/logs/collect.log`.
- `python - <<'PY'
from pathlib import Path
from hashlib import sha256
stamp = Path("$OUTDIR")
fixtures_dir = Path("reports/2025-11-source-weights/fixtures")
fixtures_dir.mkdir(parents=True, exist_ok=True)
source = Path("reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt")
clean = fixtures_dir / "two_sources_nocomments.txt"
lines = [l for l in source.read_text().splitlines() if not l.strip().startswith('#') and l.strip()]
clean.write_text("\n".join(lines) + "\n")
(stamp / "notes.md").write_text(
    "Sanitised fixture: {}\nSHA256: {}\n".format(
        clean.resolve(), sha256(clean.read_bytes()).hexdigest()
    ),
    encoding="utf-8"
)
PY`
- `diff -u reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt reports/2025-11-source-weights/fixtures/two_sources_nocomments.txt > "$OUTDIR"/fixture_diff.patch`.
- Append to `$OUTDIR/notes.md` the justification (test geometry vs CLI fixture delta) and link to `[C-SOURCEFILE-001]`.
Pitfalls To Avoid:
- Committing anything under `reports/`; record paths only.
- Skipping the collect-only run (needed to prove selectors still resolve before parity reruns).
- Forgetting to update `notes.md` with both fixture paths and SHA256 checksums.
- Overwriting the original `two_sources.txt`; always write to `fixtures/two_sources_nocomments.txt`.
- Using the sanitized fixture for parity before logging the diff and checksum.
- Neglecting to reference `[C-SOURCEFILE-001]` when noting the bug hand-off.
- Running full parity commands in this loop; stop after G0 deliverables.
- Leaving the repo dirty with generated binaries (floatfiles); keep artifacts under reports only.
- Omitting `KMP_DUPLICATE_LIB_OK=TRUE`, which will crash torch during collect-only.
- Forgetting to capture UTC timestamps in filenames (use `STAMP`).
Pointers:
- plans/active/source-weight-normalization.md:19
- docs/fix_plan.md:4040
- plans/active/c-sourcefile-comment-parsing.md:14
- specs/spec-a-core.md:151
- reports/2025-11-source-weights/phase_g/20251009T225052Z/notes.md
Next Up: Phase G1 parity commands once the sanitised fixture bundle is archived.
