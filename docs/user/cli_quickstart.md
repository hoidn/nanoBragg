# CLI Quickstart

This guide shows how to install and run the nanoBragg PyTorch CLI.

Requirements
- Python 3.11+
- PyTorch (CPU or CUDA)

Install
- From the repo root: `pip install -e .`
  - Installs console script `nanoBragg = nanobrag_torch.__main__:main` (see `pyproject.toml`).

Run
- Installed console script:
  - `nanoBragg -hkl P1.hkl -cell 100 100 100 90 90 90 -lambda 1.0 -distance 100 -floatfile out.bin`
- Without install (module runner):
  - `PYTHONPATH=src python -m nanobrag_torch -hkl P1.hkl -cell 100 100 100 90 90 90 -lambda 1.0 -distance 100 -floatfile out.bin`

Minimum Inputs
- Provide structure factors via `-hkl` (or pre-existing `Fdump.bin`), or set a fallback with `-default_F > 0`.
- Provide unit cell either via `-mat` (MOSFLM A*) or `-cell a b c alpha beta gamma` (Å, degrees).

Quick Test (no HKL)
- `nanoBragg -default_F 1 -cell 100 100 100 90 90 90 -lambda 1.0 -distance 100 -detpixels 128 -pgmfile test.pgm`
  - Produces an 8‑bit PGM preview. Scale with `-pgmscale` if needed.

Common Flags
- Geometry: `-pixel`, `-detpixels[_f|_s]` or `-detsize[_f|_s]`, `-distance` or `-close_distance`, `-roi xmin xmax ymin ymax`.
- Orientation: `-detector_rotx/-roty/-rotz`, `-twotheta`, `-twotheta_axis x y z`.
- Conventions: `-mosflm | -adxv | -denzo | -xds | -dials` (with pivot defaults), or custom vectors (`-fdet_vector` etc.).
- Beam: `-lambda` or `-energy`, divergence/dispersion ranges and steps, `-polar` or `-nopolar`.
- Sampling: `-phisteps`, `-oversample`, `-oversample_thick`, `-oversample_polar`, `-oversample_omega`, `-dmin`.
- Outputs: `-floatfile`, `-intfile` (SMV), `-noisefile` (Poisson), `-pgmfile`.

Headers & Masks
- `-img`/`-mask` read SMV headers; last read wins for shared fields. For `-mask`, Y beam center is interpreted as `detsize_s - value_mm` per spec.

Tips
- Use `-roi` to iterate quickly on small regions.
- Set seeds for determinism: `-seed`, `-mosaic_seed`, `-misset_seed`.
- For triclinic crystals, use smaller misset angles (<45°) to avoid pattern offsets. See [Known Limitations](known_limitations.md).

Troubleshooting
- For issues with triclinic crystals or other limitations, see [Known Limitations](known_limitations.md).

