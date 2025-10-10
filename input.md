Summary: Regenerate all stale golden datasets (Phase B) so VECTOR-PARITY Phase E parity checks can resume.
Mode: Parity
Focus: docs/fix_plan.md [TEST-GOLDEN-001] Regenerate golden data post Phase D5
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-golden-refresh/phase_b/$STAMP/
Do Now: docs/fix_plan.md [TEST-GOLDEN-001] Regenerate golden data post Phase D5 — execute the Phase B canonical C regeneration suite (see How-To Map for commands).
If Blocked: Capture the command that failed, stdout/stderr, and partial checksum notes in reports/2026-01-golden-refresh/phase_b/$STAMP/attempt_failed.txt, then ping supervisor with blockers and collected logs.
Priorities & Rationale:
- docs/fix_plan.md:197 — Next Actions now call for Phase B regeneration before any further parity runs.
- plans/active/test-golden-refresh.md — Phase A marked [D]; Phase B is the gating milestone for VECTOR-PARITY Phase E.
- tests/golden_data/README.md — canonical commands and provenance expectations.
- specs/spec-a-parallel.md:1 — AT-PARALLEL-012 depends on refreshed high-resolution golden data.
- docs/development/testing_strategy.md §2.5 — authoritative parity/ROI thresholds to verify after regeneration.
How-To Map:
- export AUTHORITATIVE_CMDS_DOC=docs/development/testing_strategy.md; set NB_C_BIN=./golden_suite_generator/nanoBragg (confirm binary exists).
- Set STAMP=$(date -u +%Y%m%dT%H%M%SZ) and BASE=reports/2026-01-golden-refresh/phase_b/$STAMP; mkdir -p "$BASE"/{simple_cubic,simple_cubic_mosaic,triclinic_P1,cubic_tilted_detector,high_resolution_4096}.
- Record git rev-parse HEAD > "$BASE"/repo_sha.txt and NB_C_BIN checksum (sha256sum "$NB_C_BIN" > "$BASE"/c_binary_checksum.txt).
- For each dataset, run from repo root:
  * simple_cubic:
    ```bash
    pushd golden_suite_generator
    KMP_DUPLICATE_LIB_OK=TRUE "$NB_C_BIN" -hkl P1.hkl -matrix A.mat -lambda 6.2 -N 5 -default_F 100 -distance 100 -detsize 102.4 -pixel 0.1 -floatfile ../tests/golden_data/simple_cubic.bin -intfile ../tests/golden_data/simple_cubic.img |& tee ../"$BASE"/simple_cubic/command.log
    popd
    sha256sum tests/golden_data/simple_cubic.bin tests/golden_data/simple_cubic.img > "$BASE"/simple_cubic/checksums.txt
    ```
  * simple_cubic_mosaic:
    ```bash
    pushd golden_suite_generator
    KMP_DUPLICATE_LIB_OK=TRUE "$NB_C_BIN" -hkl P1.hkl -matrix A.mat -lambda 6.2 -N 5 -default_F 100 -distance 100 -detsize 100 -pixel 0.1 -mosaic_spread 1.0 -mosaic_domains 10 -floatfile ../tests/golden_data/simple_cubic_mosaic.bin -intfile ../tests/golden_data/simple_cubic_mosaic.img |& tee ../"$BASE"/simple_cubic_mosaic/command.log
    popd
    sha256sum tests/golden_data/simple_cubic_mosaic.bin tests/golden_data/simple_cubic_mosaic.img > "$BASE"/simple_cubic_mosaic/checksums.txt
    ```
  * triclinic_P1:
    ```bash
    pushd golden_suite_generator
    KMP_DUPLICATE_LIB_OK=TRUE "$NB_C_BIN" -misset -89.968546 -31.328953 177.753396 -cell 70 80 90 75 85 95 -default_F 100 -N 5 -lambda 1.0 -detpixels 512 -floatfile ../tests/golden_data/triclinic_P1/image.bin |& tee ../"$BASE"/triclinic_P1/command.log
    popd
    sha256sum tests/golden_data/triclinic_P1/image.bin > "$BASE"/triclinic_P1/checksums.txt
    ```
  * cubic_tilted_detector:
    ```bash
    pushd golden_suite_generator
    KMP_DUPLICATE_LIB_OK=TRUE "$NB_C_BIN" -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 -distance 100 -detsize 102.4 -detpixels 1024 -Xbeam 61.2 -Ybeam 61.2 -detector_rotx 5 -detector_roty 3 -detector_rotz 2 -twotheta 15 -oversample 1 -floatfile ../tests/golden_data/cubic_tilted_detector/image.bin |& tee ../"$BASE"/cubic_tilted_detector/command.log
    popd
    sha256sum tests/golden_data/cubic_tilted_detector/image.bin > "$BASE"/cubic_tilted_detector/checksums.txt
    ```
  * high_resolution_4096:
    ```bash
    pushd golden_suite_generator
    KMP_DUPLICATE_LIB_OK=TRUE "$NB_C_BIN" -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05 -floatfile ../tests/golden_data/high_resolution_4096/image.bin |& tee ../"$BASE"/high_resolution_4096/command.log
    popd
    sha256sum tests/golden_data/high_resolution_4096/image.bin > "$BASE"/high_resolution_4096/checksums.txt
    ```
- After each command, capture stderr by default via tee; if failures occur, archive the failing stdout/stderr under the dataset directory before retrying.
- Update tests/golden_data/README.md provenance entries: adjust timestamps, git SHA, and SHA256 values; log the edit path in "$BASE"/readme_updates.txt.
- Leave regenerated binaries tracked; keep all "$BASE" artifacts untracked (reports/ excluded via .gitignore).
Pitfalls To Avoid:
- Do not delete or rename any files referenced in docs/index.md (golden data and README are protected assets).
- Ensure `$NB_C_BIN` points at the instrumented binary; do not rebuild the frozen root ./nanoBragg.
- Run commands from repo root with pushd/popd—no ad-hoc cwd changes or relative paths that bypass Protected Assets.
- Maintain device/dtype neutrality in follow-up parity checks; no `.cpu()` shims.
- Avoid overwriting prior reports directories; always create a fresh $STAMP per run.
- Record SHA256 for every regenerated artifact; missing checksums will block review.
- Keep command logs in ASCII; no editors that may introduce BOM/UTF-16 encoding.
- Don’t commit reports/ artifacts; only stage updated tests/golden_data/* and README edits.
- Validate commands complete without prompts; rerun with tee capturing stderr if a retry is needed.
- Note MKL env (`KMP_DUPLICATE_LIB_OK=TRUE`) on every invocation to prevent runtime crashes.
Pointers:
- docs/fix_plan.md:180 — `[TEST-GOLDEN-001]` context, attempts, and updated Next Actions.
- plans/active/test-golden-refresh.md — Phase B guidance and deliverables checklist.
- tests/golden_data/README.md — canonical command blocks and provenance formatting.
- docs/development/testing_strategy.md:120 — ROI parity thresholds for AT-PARALLEL-012.
- reports/2026-01-golden-refresh/phase_a/20251010T084007Z/scope_summary.md — Phase A scope audit for cross-checking datasets/tests.
Next Up (optional): Phase C ROI nb-compare + targeted pytest after regeneration artifacts and README updates are staged.
