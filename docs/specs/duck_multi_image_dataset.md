# Duck Multi-Image Dataset Specification

> Reference: Strategy §7, docs/plans/2026-01-29-m2-amortized-mosaicity.md Task 1

## Directory Layout

```
duck_multi_image/
  metadata.json
  counts/
    img_00.pt  # (H, W) float tensor
    img_01.pt
    ...
```

## metadata.json Schema

| Key | Type | Description |
|-----|------|-------------|
| `n_images` | int | Number of images |
| `spixels` | int | Slow dimension pixels |
| `fpixels` | int | Fast dimension pixels |
| `orientations` | list[list[list[float]]] | Per-image 3x3 misset matrices |
| `per_image` | list[dict] | Per-image metadata (see below) |
| `crystal_config` | dict | Shared crystal parameters |
| `beam_config` | dict | Shared beam parameters |
| `detector_config` | dict | Shared detector parameters |
| `observation_meta` | dict | Observation scaling info |
| `structure_factors_path` | str | Relative path to dense HKL tensor (`.pt`) |
| `structure_factors_shape` | list[int] | `[H, K, L]` cube describing the Miller index span |
| `structure_factors_dtype` | str | Optional torch dtype string (defaults to `float64`) |

### Structure Factor Payload (M3 joint mode)

- The canonical Duck dataset ships `structure_factors.pt` (7×7×7 cube covering `h,k,l ∈ [-3,3]`) initialised to `crystal_config.default_F`.
- When the metadata omits `structure_factors_*`, loaders SHOULD return `None` (legacy behavior) so M1/M2 workflows continue to function; joint-mode call sites must then instantiate a uniform tensor (e.g., via `StructureFactorLatent.from_uniform`).
- Consumers (`DuckDataset.structure_factors`, `StructureFactorLatent.from_dataset`) must respect the recorded shape/dtype and propagate the metadata into `Crystal.hkl_data` per `specs/spec-a-core.md §Structure Factors & Fdump`.

### per_image entry

| Key | Type | Description |
|-----|------|-------------|
| `mosaic_spread_deg` | float | Ground truth mosaic spread (degrees) |
| `misset_deg` | list[float] | Euler angles [rx, ry, rz] in degrees |
| `mean_counts` | float | Mean photon counts after Poisson sampling |
| `max_counts` | float | Maximum photon counts |
| `scale` | float | Observation scale factor |

## Sampling Conventions

- Mosaic spreads: `N(2.0, 0.3)` clamped to `[0.5, 3.0]`
- Misset angles: `U(-5, +5)` degrees per Euler axis
- Poisson sampling with configurable mean count level
