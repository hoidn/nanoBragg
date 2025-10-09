Summary: Generate fresh C/PyTorch float images for the supervisor ROI so Phase N nb-compare can proceed with Option 1 spec mode.
Mode: Parity
Focus: CLI-FLAGS-003 / Phase N1 ROI regeneration
Branch: feature/spec-based-2
Mapped tests:
- pytest -v tests/test_cli_scaling_phi0.py
- pytest -v tests/test_cli_scaling_phi0.py::TestCLIScalingPhi0::test_rot_b_matches_c
- pytest -v tests/test_cli_scaling_phi0.py::TestCLIScalingPhi0::test_k_frac_phi0_matches_c
- pytest --collect-only -q tests/test_cli_scaling_phi0.py
Mapped tests (CUDA follow-up when available):
- pytest -v tests/test_cli_scaling_phi0.py --device cuda --maxfail=1
Artifacts:
- reports/2025-10-cli-flags/phase_l/nb_compare/<STAMP>/inputs/c_roi_float.bin
- reports/2025-10-cli-flags/phase_l/nb_compare/<STAMP>/inputs/py_roi_float.bin
- reports/2025-10-cli-flags/phase_l/nb_compare/<STAMP>/inputs/{commands.txt,env.txt,git_sha.txt,version.txt,sha256.txt,file_sizes.txt}
- reports/2025-10-cli-flags/phase_l/nb_compare/<STAMP>/inputs/{c_cli_stdout.txt,py_cli_stdout.txt}
- reports/2025-10-cli-flags/phase_l/nb_compare/<STAMP>/tests/{pytest_cpu.log,pytest_cuda.log}
- reports/2025-10-cli-flags/phase_l/nb_compare/<STAMP>/notes/{template_command.txt,todo_nb_compare.md}
- docs/fix_plan.md (new Attempt referencing <STAMP> bundle)
- plans/active/cli-noise-pix0/plan.md (Phase N1 state update)
Do Now: CLI-FLAGS-003 Phase N1 — `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py`; then regenerate ROI float images for both implementations in `reports/2025-10-cli-flags/phase_l/nb_compare/<STAMP>/inputs/` using the supervisor command verbatim (C via `$NB_C_BIN`, PyTorch via `PYTHONPATH=src python -m nanobrag_torch`).
If Blocked: If pytest or either CLI run fails, capture stdout/stderr into `<STAMP>/inputs/commands.txt` and `<STAMP>/inputs/*.txt`, rerun `pytest --collect-only -q tests/test_cli_scaling_phi0.py`, record the failure signature plus environment in docs/fix_plan.md Attempt, and stop—phase progression requires supervisor review before touching nb-compare.
Context Recap:
- Phase M6 optional shim work is formally skipped (Attempt #198); spec-only Option 1 path is the canonical parity trajectory.
- Option 1 bundle (`reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/20251009T013046Z/`) defines the expected −14.6% `I_before_scaling` delta while all downstream factors match ≤1e-6.
- `reports/2025-10-cli-flags/phase_l/nb_compare/20251009T014553Z/inputs/` currently holds metadata only; new float images are still required before Phase N2.
- Beam vector plumbing (Attempt #189) and normalization fix (Attempt #189) are merged; only the φ rotation carryover delta remains as documented behavior.
- Long-term Goal 1 (phi-carryover removal) is complete; this loop advances Goal 2 (spec/doc parity) and sets up Goal 5 (full-suite validation) by clearing CLI backlog items.
- Protected Assets rule (docs/index.md) covers input.md, loop.sh, supervisor.sh; ensure they remain untouched aside from this memo update.
Reference Artifacts:
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/summary.md — normalization fix history.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/analysis_20251008T212459Z.md — quantitative k_frac/rot_b divergence context.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md — H4/H5 closure rationale.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T231211Z/per_phi_trace.log — enhanced traces confirming spec rotation pipeline.
Attempts History (recent):
- Attempt #197 (docs) refreshed Option 1 bundle and validation script notes.
- Attempt #198 (docs) logged Phase M6 skip decision and seeded N1 metadata stub (commands/env only).
- No Phase N Attempts yet; this loop should create Attempt #199 (placeholder numbering) documenting ROI regeneration.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:80–82 explicitly requires generating both ROI float files before nb-compare (VG‑3/VG‑4) can execute.
- plans/active/cli-noise-pix0/plan.md:73–76 states Phase N exit criteria (correlation ≥0.9995) which depend on N1 outputs.
- docs/fix_plan.md:472–510 lists Phase N1 as the active gate after the M6 skip; ledger alignment prevents duplicate effort.
- prompts/supervisor.md:118–151 preserves the authoritative flag set; copying it prevents regression when comparing C vs PyTorch.
- docs/development/testing_strategy.md:65–105 mandates targeted pytest before bespoke tooling and requires logs go under reports/.
- docs/bugs/verified_c_bugs.md:166–204 provides Option 1 justification—cite in Attempt so future readers track the expected delta.
- arch.md:52–160 summarises detector/basis behavior; use it when sanity-checking CLI arguments and env captures.
- scripts/validation/README.md:12–80 explains report directory conventions to follow for the new bundle.
How-To Map:
- Export environment: `export NB_C_BIN=./golden_suite_generator/nanoBragg`; `export KMP_DUPLICATE_LIB_OK=TRUE`; `echo NB_C_BIN=$NB_C_BIN >> $OUT/inputs/env.txt` once `OUT` exists.
- Verify binaries: `command -v python -m nanobrag_torch >/dev/null`; `ls -l $NB_C_BIN >> $OUT/inputs/env.txt` to confirm timestamp and permissions.
- Establish bundle: `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `OUT=reports/2025-10-cli-flags/phase_l/nb_compare/$STAMP`; `mkdir -p $OUT/inputs $OUT/tests $OUT/notes`.
- Metadata capture: `git rev-parse HEAD > $OUT/inputs/git_sha.txt`; `python -m nanobrag_torch --version > $OUT/inputs/version.txt`; `python -V > $OUT/inputs/env.txt`; append `env | sort | grep -E "^(NB_C_BIN|CUDA|CONDA|PYTHONPATH|KMP_DUPLICATE_LIB_OK)" >> $OUT/inputs/env.txt`.
- Template command: copy supervisor command block into `$OUT/notes/template_command.txt` (helps future diffs).
- Targeted pytest (CPU): `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py | tee $OUT/tests/pytest_cpu.log`; check exit code before continuing.
- Optional CUDA smoke: if `torch.cuda.is_available()`, run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py --device cuda --maxfail=1 | tee $OUT/tests/pytest_cuda.log`; otherwise `echo "cuda not available" > $OUT/tests/pytest_cuda.log`.
- C reference command (tee to stdout log):
  `"$NB_C_BIN" -mat A.mat -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 -floatfile "$OUT/inputs/c_roi_float.bin" 2>&1 | tee $OUT/inputs/c_cli_stdout.txt`.
- PyTorch CLI command (tee to stdout log):
  `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -mat A.mat -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 -floatfile "$OUT/inputs/py_roi_float.bin" 2>&1 | tee $OUT/inputs/py_cli_stdout.txt`.
- Log executed commands (with exit codes) into `$OUT/inputs/commands.txt`; include working directory and runtime seconds.
- Validate outputs: `ls -lh $OUT/inputs/*.bin > $OUT/inputs/file_sizes.txt`; `sha256sum $OUT/inputs/*.bin > $OUT/inputs/sha256.txt`; inspect sizes roughly equal (expected ~24 MB) and note any anomalies.
- Optional diagnostic: `python scripts/diagnostic_detector.py --summary "$OUT/inputs/py_roi_float.bin" >> $OUT/notes/todo_nb_compare.md` if script available; otherwise note TODO for Phase N2.
- Documentation: append new Attempt to `docs/fix_plan.md` (CLI-FLAGS-003) referencing `<STAMP>` and summarising pytest + sha256 results; update `plans/active/cli-noise-pix0/plan.md` row N1 to `[P]` (ready for nb-compare) or `[D]` once N2 finishes next loop.
Pitfalls To Avoid:
- Do not run `nb-compare` yet; Phase N2 should start only after verifying both float files and logs.
- Keep `KMP_DUPLICATE_LIB_OK=TRUE` set for every PyTorch invocation to prevent MKL duplicate symbol crashes.
- Ensure `$NB_C_BIN` points to `./golden_suite_generator/nanoBragg`; the frozen root binary lacks latest instrumentation.
- Stay in repo root so relative paths resolve; commands assume working directory `/home/ollie/Documents/nanoBragg4/nanoBragg`.
- Do not overwrite existing timestamp directories; always create a new `<STAMP>` for traceability.
- Avoid adding or committing `.bin` artifacts; leave them untracked but present in the reports directory.
- Record command exit codes (`${PIPESTATUS[0]}` when using `tee`) before claiming success in Attempt notes.
- Verify pixel grid sizes match plan expectation (float files ~2463×2527) before proceeding to nb-compare.
- Include Option 1 rationale in Attempt; omitting it risks future confusion about the persistent intensity delta.
- Leave Protected Assets listed in docs/index.md untouched (input.md, loop.sh, supervisor.sh) besides this memo update.
Pointers:
- plans/active/cli-noise-pix0/plan.md:73–120 — Phase N structure, Phase M5 closure, M6 skip rationale.
- docs/fix_plan.md:452–540 — CLI-FLAGS-003 ledger, Next Actions, Attempt logging requirements.
- prompts/supervisor.md:118–151 — Canonical supervisor command and flag ordering.
- docs/development/testing_strategy.md:65–105 — Test cadence, logging requirements, CPU vs CUDA expectations.
- docs/bugs/verified_c_bugs.md:166–204 — C-PARITY-001 summary to cite in Attempt notes.
- arch.md:52–160 — Detector/beam architecture for sanity checks upon reviewing logs.
- scripts/validation/README.md:12–80 — Reports directory conventions and metadata expectations.
- reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/20251009T013046Z/summary.md — Option 1 evidence to reference while documenting.
Verification Targets (for next loop reference):
- nb-compare correlation ≥0.9995, sum_ratio within 0.99–1.01, max intensity delta <2% within ROI.
- CLI parity Attempt should note expected −14.6% `I_before_scaling` delta with downstream factors ≤1e-6.
- pytest logs must show 2/2 passes on CPU; CUDA log may note “cuda not available” if skipped.
Next Up: N2 — Run `nb-compare --roi 100 156 100 156 --resample --threshold 0.98 --outdir .../results/ -- [command args]` using the freshly generated float files, capture metrics/PNGs, and update fix_plan once Phase N1 artifacts are confirmed.
Attempt Writeup Checklist:
- Add Attempt # (increment sequentially) under docs/fix_plan.md CLI-FLAGS-003 with <STAMP>, pytest summary, floatfile sha hashes, Option 1 citation.
- Note whether CUDA smoke ran (available vs skipped) and reference `$OUT/tests/pytest_cuda.log` location.
- Link to `$OUT/inputs/commands.txt` and `$OUT/inputs/sha256.txt` so future auditors can rerun commands or verify integrity.
- Mention that nb-compare has not yet been executed (Phase N2 pending) to prevent premature closure.
Environment Cleanup Reminders:
- Leave `<STAMP>` directory untracked; confirm `.gitignore` keeps `reports/**` ignored.
- If temporary files land outside reports/, remove them before concluding (e.g., stray `img.bin`).
- Reset exported vars (`unset NB_C_BIN KMP_DUPLICATE_LIB_OK`) only after recording them in env.txt to avoid accidental reuse next loop.
Resource Links For Quick Access:
- README_PYTORCH.md:210–340 — CLI usage notes if argument parsing errors occur.
- docs/architecture/detector.md:180–320 — Pix0 vector interpretation when reviewing outputs.
- docs/development/c_to_pytorch_config_map.md:200–310 — Flag-to-config mapping for detector/beam parameters.
