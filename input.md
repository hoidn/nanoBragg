Summary: Probe the supervisor pixel’s structure-factor source so PyTorch can match C’s I_before_scaling.
Mode: Parity
Focus: CLI-FLAGS-003 › Phase L3a structure-factor verification
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_l/structure_factor/probe.py; reports/2025-10-cli-flags/phase_l/structure_factor/probe.log; reports/2025-10-cli-flags/phase_l/structure_factor/analysis.md; reports/2025-10-cli-flags/phase_l/structure_factor/blocked.md (only if needed)
Do Now: CLI-FLAGS-003 › Phase L3a Verify structure-factor coverage — author the probe detailed below, then run `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/structure_factor/probe.py --pixel 685 1039 --hkl scaled.hkl --fdump golden_suite_generator/Fdump.bin --fdump tmp/Fdump.bin`
If Blocked: Log the failure (command, stderr, git SHA) to `reports/2025-10-cli-flags/phase_l/structure_factor/blocked.md` and run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_trace_pixel.py` to verify imports remain stable.

Context Snapshot
- Phase L2 is complete; TRACE_C and TRACE_PY scaling chains live under `reports/2025-10-cli-flags/phase_l/scaling_audit/` with all factors aligned except I_before_scaling.
- The supervisor pixel (slow=685, fast=1039) maps to hkl≈(−7,−1,−14) per `c_trace_scaling.log:143-164`.
- PyTorch currently reports `F_cell=0` for that hkl while C reports `F_cell=190.27`, driving I_before_scaling to zero on the Py side.
- Existing HKL/Fdump assets in repo appear to cover only a tiny grid (ranges -2..2), so the C amplitude must stem from additional logic.
- Plan Phase L3 (plans/active/cli-noise-pix0/plan.md) now targets structure-factor ingestion before normalization code changes.
- docs/fix_plan.md entry CLI-FLAGS-003 has refreshed Next Actions (lines 457-461) aligning to this probe-first strategy.
- We must keep detector/beam configs identical to the supervisor command (`trace_harness.get_supervisor_params`) so comparisons remain valid.
- All work stays evidence-only this loop; no production module changes or new tests yet.

Success Criteria
- Probe captures HKL-grid coverage and reports whether (-7,-1,-14) exists in either `scaled.hkl` or generated Fdump caches.
- Output log clearly lists the amplitude returned by `Crystal.get_structure_factor` for each data source and device/dtype used.
- `analysis.md` summarises findings, cites the C reference value, and states whether further ingestion work is required.
- Any blockers are documented with enough data for the next loop to resume without repeating work.

Priorities & Rationale
- plans/active/cli-noise-pix0/plan.md:255 mandates L3a before touching simulator code; satisfying that plan gate keeps the initiative on track.
- docs/fix_plan.md:457 documents the current divergence (I_before_scaling) and explicitly calls for L3a/L3b evidence.
- specs/spec-a-cli.md:1 establishes that CLI parity depends on identical HKL/Fdump handling; diverging here explains the PyTorch zero amplitude.
- reports/2025-10-cli-flags/phase_l/scaling_audit/scaling_audit_summary.md:1 already proves all other scaling factors align, isolating the structure-factor gap.
- c_trace_scaling.log:143-164 is the authoritative C reference for the target hkl and F_cell; we must reproduce or explain that value.
- trace_harness.py lines 65-206 keep the configuration canonical; reusing it prevents accidental drift (beam, detector, or crystal mismatches).

Execution Sequence
- Create the directory `reports/2025-10-cli-flags/phase_l/structure_factor/` if missing.
- Copy or import `get_supervisor_params` from the scaling harness to guarantee identical configs.
- Build a small CLI around torch + numpy that accepts `--pixel`, `--hkl`, and multiple `--fdump` paths for experimentation.
- Load HKL data via `read_hkl_file`, attach to a `Crystal` constructed with the supervisor config, and query `crystal.get_structure_factor` for the rounded hkl from the C trace.
- Repeat the query for each provided Fdump path using `read_fdump` (note that some may not contain the hkl; report index status).
- Consider toggling dtype/device (float64 cpu vs float32 cpu) to show that the amplitude mismatch is not precision-driven; record both runs if feasible.
- Print and log metadata: min/max ranges, whether the hkl falls inside each grid, and the amplitude retrieved.
- Summarise findings and hypotheses in `analysis.md`, referencing any anomalies (e.g., if C amplitude cannot be reproduced from available data).

Tooling Prep
- Ensure editable install is in place (`pip install -e .`) so the probe can import `nanobrag_torch` modules without PYTHONPATH hacks beyond `PYTHONPATH=src`.
- Export `NB_C_BIN=./golden_suite_generator/nanoBragg` to keep future C comparisons consistent.
- Verify both `golden_suite_generator/Fdump.bin` and `tmp/Fdump.bin` exist before running the probe; list their `ls -l` output in the log for provenance.
- Run `git rev-parse HEAD` and record the SHA at the top of `probe.log`.
- Capture `torch.__version__`, `platform.platform()`, and device availability in the probe output to maintain context for later parity checks.
- If you need additional Fdump snapshots from C, document the exact command used to regenerate them (copy/paste from `c_trace_scaling.log` header) and store the binary copy under `reports/.../structure_factor/`.

Evidence Sources
- `reports/2025-10-cli-flags/phase_l/scaling_audit/instrumentation_notes.md` for prior harness setup steps.
- `docs/architecture/c_code_overview.md:310` (HKL handling) to cross-check the C ingestion pipeline while analysing probe results.
- `docs/architecture/pytorch_design.md:180` for the expected PyTorch HKL workflow; note any deltas when explaining outcomes.
- `reports/2025-10-cli-flags/phase_l/hkl_parity/summary_20251109.md` summarises prior HKL vs Fdump parity work—cite it if ranges conflict.
- `reports/2025-10-cli-flags/phase_k/base_lattice/summary.md` contains notes on MOSFLM scaling decisions that might influence structure-factor expectations.
- `tests/test_cli_scaling.py` (search for `TestHKLFdumpParity`) to understand existing coverage and gaps.

Open Questions to Address in analysis.md
- Does any existing Fdump (or a freshly generated one) actually contain the (-7,-1,-14) reflection, or is C deriving it procedurally?
- If the reflection is absent, which section of `nanoBragg.c` fabricates the amplitude (default_F fallback, symmetry expansion, or sinc evaluation)?
- Are there command-line flags (`-nonorm`, `-nointerpolate`) altering the structure-factor lookup in C that PyTorch is not mirroring?
- What hypotheses should Phase L3b test next (e.g., loading the on-disk Fdump vs synthesising a wider HKL grid)?

How-To Map
- Command template: `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/structure_factor/probe.py --pixel 685 1039 --hkl scaled.hkl --fdump golden_suite_generator/Fdump.bin --fdump tmp/Fdump.bin --dtype float64 --device cpu`.
- Inside the probe, after loading tensors, compute rounded hkl from detector geometry by calling the same helper as the harness (`Simulator` or `Crystal` as needed) to double-check indices.
- Use `Path('reports/.../probe.log')` to write a structured log (JSON or plain text) capturing source name, in-range flag, amplitude, and metadata; also echo to stdout.
- Store CLI invocation, git SHA, torch version, and timestamp in the log header for reproducibility.
- Append a markdown table to `analysis.md` with columns `[source, in_range, amplitude]` and note whether any source matches the C value.
- If the probe discovers a new data dependency (e.g., C writes a fresh Fdump during the command), note the path and copy it under `reports/.../structure_factor/` for archival.

Reporting Checklist
- Update `analysis.md` with bullet conclusions plus open questions for Phase L3b.
- Add a short paragraph to `docs/fix_plan.md` Attempts History only after supervisor review (defer for now unless instructed).
- Ensure `git status` is clean of unexpected files before handing off; only the new probe artifacts should appear.
- Record the executed command(s) and SHA in `probe.log` for traceability.

Pitfalls To Avoid
- Forgetting `KMP_DUPLICATE_LIB_OK=TRUE` will crash the probe; set it early.
- Do not relocate or edit protected assets named in docs/index.md while working.
- Avoid instantiating `Simulator` with altered oversample or beam parameters; stay aligned with the supervisor command.
- No edits to production HKL readers this loop; evidence first, implementation later.
- Skip GPU runs unless needed; parity proof starts on CPU float64 for clarity.
- Do not delete existing scaling audit artifacts; future loops rely on them for comparisons.
- Keep the probe deterministic; seed torch/numpy if random numbers are introduced.
- Document any assumptions about the Fdump path—if the file is missing, note it instead of silently failing.
- Avoid `.item()` on tensors that might later require gradients in the simulator; extraction is fine inside the isolated probe only.
- Respect vectorization rules: if you loop over hkl indices in the probe, keep it clearly separate from production pipelines.

Pointers
- docs/fix_plan.md:448 for the refreshed Next Actions and divergence context.
- plans/active/cli-noise-pix0/plan.md:255 detailing the L3a/L3b deliverables.
- reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log:143 for the C-side reference amplitude.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log:21 showing PyTorch’s current zero amplitude.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:70-220 for the canonical config helper.
- specs/spec-a-core.md:200 (structure-factor section) for the expected physical contract.

Next Up (if time allows)
- Initiate Phase L3b by diffing the probe outputs against the newly generated C Fdump (if any) and drafting the ingestion strategy.
- Queue notes for Phase L3c describing the normalization adjustments once the structure-factor source is resolved.
