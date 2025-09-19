# C-CLI to PyTorch Configuration Map

## Critical Importance Notice

**This document is the authoritative source of truth for configuration parity between nanoBragg.c and the PyTorch implementation.**

Before writing any test or implementation that involves C-code validation, you **MUST** consult this document. Failure to ensure 1:1 configuration parity is the most common source of bugs, particularly with:
- Implicit pivot mode logic
- Convention-dependent beam center calculations
- Rotation axis defaults
- Unit conversions

## Quick Reference Table

### Crystal Parameters

| C-CLI Flag | PyTorch Config Field | C Variable | Units/Convention | Critical Notes |
|------------|---------------------|------------|------------------|----------------|
| `-cell a b c al be ga` | `CrystalConfig.cell_a/b/c/alpha/beta/gamma` | `a[0], b[0], c[0], alpha, beta, gamma` | Å and degrees → radians | Must convert degrees to radians internally |
| `-N <val>` | `CrystalConfig.N_cells` | `Na, Nb, Nc` | Number of unit cells | Sets all three axes to same value |
| `-Na/-Nb/-Nc <val>` | `CrystalConfig.N_cells[0/1/2]` | `Na, Nb, Nc` | Number of unit cells | Individual axis control |
| `-misset dx dy dz` | `CrystalConfig.misset_deg` | `misset[1], [2], [3]` | Degrees → radians | Applied as XYZ rotations to reciprocal vectors |
| `-mosaic <val>` | `CrystalConfig.mosaic_spread_deg` | `mosaic_spread` | Degrees → radians | Isotropic mosaic spread |
| `-mosaic_domains <val>` | `CrystalConfig.mosaic_domains` | `mosaic_domains` | Count | Number of discrete domains |
| `-mosaic_seed <val>` | `CrystalConfig.mosaic_seed` | `mosaic_seed` | Integer | RNG seed for mosaic orientations |
| `-default_F <val>` | `CrystalConfig.default_F` | `default_F` | Electrons | Structure factor for missing reflections |
| `-phi <val>` | `CrystalConfig.phi_start_deg` | `phi0` | Degrees → radians | Starting spindle angle |
| `-osc <val>` | `CrystalConfig.osc_range_deg` | `osc` | Degrees → radians | Oscillation range |
| `-phisteps <val>` | `CrystalConfig.phi_steps` | `phisteps` | Count | Steps across oscillation |

### Beam Parameters

| C-CLI Flag | PyTorch Config Field | C Variable | Units/Convention | Critical Notes |
|------------|---------------------|------------|------------------|----------------|
| `-lambda <val>` | `BeamConfig.wavelength_A` | `lambda0` | Å → meters | Convert to meters internally |
| `-energy <val>` | `BeamConfig.wavelength_A` | `lambda0` | eV → Å via 12398.42/E | Alternative to `-lambda` |
| `-fluence <val>` | `BeamConfig.fluence` | `fluence` | photons/m² | Total integrated intensity |
| `-flux <val>` | `BeamConfig.flux` | `flux` | photons/s | Used with exposure & beamsize |
| `-exposure <val>` | `BeamConfig.exposure_s` | `exposure` | seconds | Duration for flux calculation |
| `-beamsize <val>` | `BeamConfig.beam_size_mm` | `beamsize` | mm → meters | Beam diameter |
| `-dispersion <val>` | `BeamConfig.dispersion_pct` | `dispersion` | Percent → fraction | Spectral width Δλ/λ |
| `-dispsteps <val>` | `BeamConfig.dispersion_steps` | `dispsteps` | Count | Wavelength sampling |
| `-hdivrange <val>` | `BeamConfig.hdiv_range_mrad` | `hdivrange` | mrad → radians | Horizontal divergence |
| `-vdivrange <val>` | `BeamConfig.vdiv_range_mrad` | `vdivrange` | mrad → radians | Vertical divergence |
| `-hdivsteps <val>` | `BeamConfig.hdiv_steps` | `hdivsteps` | Count | Horizontal divergence samples |
| `-vdivsteps <val>` | `BeamConfig.vdiv_steps` | `vdivsteps` | Count | Vertical divergence samples |
| `-polar <val>` | `BeamConfig.polarization` | `polarization` | Kahn factor [0,1] | 1.0=fully polarized, 0.0=unpolarized |

### Detector Parameters

| C-CLI Flag | PyTorch Config Field | C Variable | Units/Convention | Critical Notes |
|------------|---------------------|------------|------------------|----------------|
| `-distance <val>` | `DetectorConfig.distance_mm` | `distance` | mm → meters | **Sets pivot=BEAM implicitly** |
| `-detsize <val>` | Derived from pixels × pixel_size | `detsize_f, detsize_s` | mm → meters | Sets both dimensions |
| `-pixel <val>` | `DetectorConfig.pixel_size_mm` | `pixel_size` | mm → meters | Square pixels |
| `-detpixels <val>` | `DetectorConfig.spixels/fpixels` | `fpixels, spixels` | Count | Sets both dimensions |
| `-Xbeam <val>` | `DetectorConfig.beam_center_f` | `Xbeam` | mm → meters | **MOSFLM: → Fbeam directly** |
| `-Ybeam <val>` | `DetectorConfig.beam_center_s` | `Ybeam` | mm → meters | **MOSFLM: → Sbeam = detsize_s - Ybeam** |
| `-twotheta <val>` | `DetectorConfig.detector_twotheta_deg` | `detector_twotheta` | Degrees → radians | **Sets pivot=SAMPLE implicitly** |
| `-detector_rotx <val>` | `DetectorConfig.detector_rotx_deg` | `detector_rotx` | Degrees → radians | Rotation around X axis |
| `-detector_roty <val>` | `DetectorConfig.detector_roty_deg` | `detector_roty` | Degrees → radians | Rotation around Y axis |
| `-detector_rotz <val>` | `DetectorConfig.detector_rotz_deg` | `detector_rotz` | Degrees → radians | Rotation around Z axis |
| `-oversample <val>` | `SimulatorConfig.oversample` | `oversample` | Count | Sub-pixel sampling |
| `-adc <val>` | `SimulatorConfig.adc_offset` | `adc_offset` | ADU | Integer output offset |

## Critical Implicit Logic (pointer)

Implicit pivot rules, beam-center mappings (including MOSFLM +0.5 pixel adjustment), default twotheta axes per convention, and coordinate transforms are defined in `specs/spec-a.md` (Geometry Model & Conventions). Refer there for canonical behavior. For practical debugging/validation checklists, use `docs/debugging/detector_geometry_checklist.md`.

## References

- Source: `nanoBragg.c` lines 506-1850 (configuration parsing and setup)
- Parameter Dictionary: [`docs/architecture/c_parameter_dictionary.md`](../architecture/c_parameter_dictionary.md)
- PyTorch Config: [`src/nanobrag_torch/config.py`](../../src/nanobrag_torch/config.py)
- Detector Architecture: [`docs/architecture/detector.md`](../architecture/detector.md)
