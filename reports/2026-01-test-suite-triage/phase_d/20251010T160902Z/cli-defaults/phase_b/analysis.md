# Phase B Analysis Question

**Initiative ID:** cli-defaults-b1

**Timestamp:** 2025-10-10T16:09:02Z

**Analysis Question:**
Why does the CLI default_F run emit zeros while the direct API run yields intensities?

**Context:**
- **CLI path:** `python -m nanobrag_torch -cell 100 100 100 90 90 90 -default_F 100 -detpixels 32 -pixel 0.1 -distance 100 -lambda 6.2 -N 5 -floatfile /tmp/cli.bin` → produces all-zero float image
- **API path:** Direct instantiation via `debug_default_f.py` → produces non-zero output (max=154.7, mean=20.2, 73 non-zero pixels)
- **Configuration parity verified:** Both paths use identical CrystalConfig, DetectorConfig, BeamConfig (Phase A evidence under `reports/2026-01-test-suite-triage/phase_d/20251010T155808Z/cli-defaults/phase_a/`)

**Scope Hints:**
- CLI orchestration (`src/nanobrag_torch/__main__.py`)
- Config→Simulator handoff
- Simulator.run pipeline
- HKL / structure factor fallback logic
- Output writing and buffer initialization

**ROI Hint:**
- Small 32×32 detector
- Pixel (16, 16) or similar central pixel expected to show intensity
- Simple cubic crystal (100 Å cell, N=5×5×5)
- default_F=100 with no HKL file

**Namespace Filter:**
- `nanobrag_torch`

**Time Budget:**
- 30 minutes

**Expected Deliverables:**
1. `callchain/static.md` — CLI entry → config → core → sink
2. `api_callchain/static.md` — API entry → config → core → sink
3. `trace/tap_points.md` — 5-7 numeric taps for first divergence
4. `summary.md` — First divergent variable and confirmation plan
5. `env/trace_env.json` — Runtime metadata

**Exit Criteria:**
- Identified first point where CLI and API execution diverge
- File:line anchors for divergent code paths
- Proposed tap points for Phase C confirmation
