# nanoBragg C Parameter Dictionary

## 1. Introduction

This document serves as a definitive reference for all command-line parameters accepted by `nanoBragg.c`. It maps each command-line flag to its corresponding internal C variable, specifies its data type, expected units, default value, and provides a clear description of its function.

This dictionary is essential for:
*   Understanding how to configure a `nanoBragg` simulation.
*   Guiding the implementation of a new configuration system (e.g., Python `dataclasses`).
*   Debugging by tracing user input to its effect in the code.

**Note on Conventions:** The C code handles multiple geometry conventions (e.g., MOSFLM, XDS) via conditional logic. The PyTorch architecture will use a single, canonical internal coordinate system. The user-facing command-line interface will be responsible for parsing legacy convention flags and converting them into the application's canonical parameter set before the simulation begins.

## 2. Parameter Tables

The parameters are grouped by their physical domain for clarity.

### 2.1 Crystal & Sample Parameters

These parameters define the crystal's structure, size, and orientation.

| Command-Line Flag | C Variable Name | Data Type | Units / Convention | Default Value | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `-cell a b c al be ga` | `a[0]`, `b[0]`, `c[0]`, `alpha`, `beta`, `gamma` | `double` | Å and degrees (converted to radians internally) | `0.0` | Defines the unit cell dimensions and angles. Activates `user_cell=1`. |
| `-mat <file>` | `matfilename` | `char*` | Path | `NULL` | Path to a MOSFLM-style matrix file defining the reciprocal lattice vectors. |
| `-misset dx dy dz` | `misset[1]`, `[2]`, `[3]` | `double` | Degrees (converted to radians) | `0.0` | Applies a rotation around the lab X, Y, and Z axes to the crystal orientation. |
| `-misset random` | `misset[0]` | `double` | Flag | `0.0` | Sets `misset[0]` to `-1`, which triggers random orientation generation. |
| `-N <val>` | `Na`, `Nb`, `Nc` | `double` | Number of unit cells | `1.0` | Sets the number of unit cells along a, b, and c axes to `<val>`. |
| `-Na <val>` | `Na` | `double` | Number of unit cells | `1.0` | Number of unit cells along the a-axis. |
| `-Nb <val>` | `Nb` | `double` | Number of unit cells | `1.0` | Number of unit cells along the b-axis. |
| `-Nc <val>` | `Nc` | `double` | Number of unit cells | `1.0` | Number of unit cells along the c-axis. |
| `-xtalsize <val>` | `sample_x`, `_y`, `_z` | `double` | Millimeters (converted to meters) | `0.0` | Alternative to `-N`. Specifies crystal size in mm, from which `Na,Nb,Nc` are calculated. |
| `-mosaic <val>` | `mosaic_spread` | `double` | Degrees (converted to radians) | `-1.0` | Isotropic mosaic spread. A value of 90 degrees simulates a powder. |
| `-mosaic_domains <val>` | `mosaic_domains` | `int` | Count | `-1` | Number of discrete mosaic domains to simulate. |
| `-hkl <file>` | `hklfilename` | `char*` | Path | `NULL` | Path to the structure factor file (h, k, l, F). |
| `-default_F <val>` | `default_F` | `double` | Electrons | `0.0` | Structure factor value to use for reflections not found in the HKL file. |

### 2.2 Beam & Source Parameters

These parameters define the properties of the incident X-ray beam.

| Command-Line Flag | C Variable Name | Data Type | Units / Convention | Default Value | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `-lambda <val>` | `lambda0` | `double` | Ångstroms (converted to meters) | `1.0e-10` | The central wavelength of the X-ray beam. |
| `-energy <val>` | `lambda0` | `double` | eV (converted to meters) | (derived) | Alternative to `-lambda`. Wavelength is calculated via `12398.42/energy`. |
| `-fluence <val>` | `fluence` | `double` | photons / m² | `1.259e29` | Total integrated beam intensity. Used for calculating absolute photon counts. |
| `-flux <val>` | `flux` | `double` | photons / s | `0.0` | Alternative to `-fluence`. Requires `-exposure` and `-beamsize`. |
| `-exposure <val>` | `exposure` | `double` | seconds | `1.0` | Exposure time. Used with `-flux`. |
| `-beamsize <val>` | `beamsize` | `double` | Millimeters (converted to meters) | `1e-4` | Beam diameter. Used with `-flux`. |
| `-dispersion <val>` | `dispersion` | `double` | Percent (converted to fraction) | `0.0` | Spectral dispersion (Δλ/λ). |
| `-dispsteps <val>` | `dispsteps` | `int` | Count | `-1` | Number of discrete wavelength steps to simulate across the dispersion range. |
| `-hdivrange <val>` | `hdivrange` | `double` | Milliradians (converted to radians) | `-1.0` | Full angular range of horizontal beam divergence. |
| `-vdivrange <val>` | `vdivrange` | `double` | Milliradians (converted to radians) | `-1.0` | Full angular range of vertical beam divergence. |
| `-hdivsteps <val>` | `hdivsteps` | `int` | Count | `-1` | Number of discrete horizontal divergence steps. |
| `-vdivsteps <val>` | `vdivsteps` | `int` | Count | `-1` | Number of discrete vertical divergence steps. |
| `-polar <val>` | `polarization` | `double` | Kahn factor (0 to 1) | `0.0` | Polarization factor. `1.0` for fully polarized, `0.0` for unpolarized. |

### 2.3 Detector & Geometry Parameters

These parameters define the detector's physical properties, position, and orientation.

| Command-Line Flag | C Variable Name | Data Type | Units / Convention | Default Value | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `-distance <val>` | `distance` | `double` | Millimeters (converted to meters) | `100.0e-3` | Crystal-to-detector distance. Assumes `detector_pivot = BEAM`. |
| `-detsize <val>` | `detsize_f`, `detsize_s` | `double` | Millimeters (converted to meters) | `102.4e-3` | Sets both fast and slow detector dimensions. |
| `-pixel <val>` | `pixel_size` | `double` | Millimeters (converted to meters) | `0.1e-3` | The size of a square pixel. |
| `-detpixels <val>` | `fpixels`, `spixels` | `int` | Count | `0` | Sets both fast and slow pixel counts. |
| `-Xbeam <val>` | `Xbeam` | `double` | Millimeters (converted to meters) | `NAN` | Fast-axis coordinate of the direct beam. Implies `detector_pivot = BEAM`. |
| `-Ybeam <val>` | `Ybeam` | `double` | Millimeters (converted to meters) | `NAN` | Slow-axis coordinate of the direct beam. Implies `detector_pivot = BEAM`. |
| `-twotheta <val>` | `detector_twotheta` | `double` | Degrees (converted to radians) | `0.0` | Rotation of the detector arm around the main spindle axis. |
| `-oversample <val>` | `oversample` | `int` | Count | `-1` | Number of sub-pixels to sample in each dimension per pixel. |
| `-adc <val>` | `adc_offset` | `double` | ADU | `40.0` | An offset added to the final integer pixel values before writing image files. |
| `-phi <val>` | `phi0` | `double` | Degrees (converted to radians) | `0.0` | Starting angle of the crystal rotation (spindle). |
| `-osc <val>` | `osc` | `double` | Degrees (converted to radians) | `-1.0` | Total oscillation range for a still or rotation image. |
| `-phisteps <val>` | `phisteps` | `int` | Count | `-1` | Number of steps to simulate across the oscillation range. |

### 2.4 Simulation & Output Control

These parameters control the simulation algorithm and file outputs.

| Command-Line Flag | C Variable Name | Data Type | Units / Convention | Default Value | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `-interpolate` | `interpolate` | `int` | Flag | `1` | Force tricubic interpolation of structure factors. |
| `-nointerpolate` | `interpolate` | `int` | Flag | `0` | Force nearest-neighbor lookup of structure factors. |
| `-round_xtal` | `xtal_shape` | `shapetype` | Enum (`ROUND`) | `SQUARE` | Use a spherical crystal shape model (`sinc3`). |
| `-square_xtal` | `xtal_shape` | `shapetype` | Enum (`SQUARE`) | `SQUARE` | Use a parallelepiped crystal shape model (`sincg`). |
| `-gauss_xtal` | `xtal_shape` | `shapetype` | Enum (`GAUSS`) | `SQUARE` | Use a Gaussian spot profile (no side lobes). |
| `-floatfile <file>` | `floatfilename` | `char*` | Path | `"floatimage.bin"` | Output filename for the raw, unscaled floating-point image. |
| `-intfile <file>` | `intfilename` | `char*` | Path | `"intimage.img"` | Output filename for the scaled, noiseless SMV-formatted image. |
| `-noisefile <file>` | `noisefilename` | `char*` | Path | `"noiseimage.img"` | Output filename for the image with added Poisson noise. |
| `-pgmfile <file>` | `pgmfilename` | `char*` | Path | `"image.pgm"` | Output filename for the 8-bit PGM image. |
| `-nonoise` | `calculate_noise` | `int` | Flag | `0` | Disables the Poisson noise calculation and `noisefile` output. |
| `-seed <val>` | `seed` | `long` | Integer | `-time(0)` | Seed for the Poisson noise random number generator. |
| `-mosaic_seed <val>` | `mosaic_seed` | `long` | Integer | `-12345678` | Seed for the mosaic domain orientation generator. |