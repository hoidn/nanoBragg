#!/usr/bin/env python3
"""
Main entry point for nanoBragg PyTorch CLI.

Implements the Reference CLI Binding Profile from spec-a.md,
mapping command-line flags to engine parameters per spec requirements.
"""

import os
import sys
import argparse
import time
import warnings
import torch
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

# Set environment variable for MKL conflicts
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from .config import (
    DetectorConfig, CrystalConfig, BeamConfig, NoiseConfig,
    DetectorConvention, DetectorPivot, CrystalShape
)
from .models.detector import Detector
from .models.crystal import Crystal
from .simulator import Simulator
from .io.hkl import read_hkl_file, try_load_hkl_or_fdump
from .io.smv import write_smv
from .io.pgm import write_pgm
from .io.mask import read_smv_mask, parse_smv_header, apply_smv_header_to_config
from .io.source import read_sourcefile
from .utils.units import (
    mm_to_meters, micrometers_to_meters, degrees_to_radians,
    angstroms_to_meters, mrad_to_radians
)
from .utils.noise import generate_poisson_noise
from .utils.auto_selection import auto_select_divergence, auto_select_dispersion


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser with all spec-defined flags."""

    parser = argparse.ArgumentParser(
        prog='nanoBragg',
        description='PyTorch implementation of nanoBragg diffraction simulator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic simulation
  nanoBragg -hkl P1.hkl -mat A.mat -lambda 6.2 -N 5 -distance 100

  # With detector rotation and output
  nanoBragg -hkl P1.hkl -cell 100 100 100 90 90 90 -lambda 6.2 \\
            -distance 100 -detector_rotx 5 -floatfile output.bin
""")

    # Input files
    parser.add_argument('-hkl', type=str, metavar='FILE',
                        help='Text file of "h k l F" (P1 reflections)')
    parser.add_argument('-mat', type=str, metavar='FILE',
                        help='3×3 MOSFLM-style A matrix (reciprocal vectors)')
    parser.add_argument('-cell', nargs=6, type=float,
                        metavar=('a', 'b', 'c', 'α', 'β', 'γ'),
                        help='Direct cell in Å and degrees')
    parser.add_argument('-img', type=str, metavar='FILE',
                        help='Read SMV header to set geometry')
    parser.add_argument('-mask', type=str, metavar='FILE',
                        help='Read SMV mask (0 values are skipped)')
    parser.add_argument('-sourcefile', type=str, metavar='FILE',
                        help='Multi-column text file with sources')

    # Structure factors
    parser.add_argument('-default_F', type=float, default=0.0,
                        help='Default structure factor (default: 0)')

    # Detector geometry
    parser.add_argument('-pixel', type=float, metavar='MM',
                        help='Pixel size in mm (default: 0.1)')
    parser.add_argument('-detpixels', type=int, metavar='N',
                        help='Square detector pixel count')
    parser.add_argument('-detpixels_f', '-detpixels_x', type=int, metavar='N',
                        dest='detpixels_f', help='Fast-axis pixels')
    parser.add_argument('-detpixels_s', '-detpixels_y', type=int, metavar='N',
                        dest='detpixels_s', help='Slow-axis pixels')
    parser.add_argument('-detsize', type=float, metavar='MM',
                        help='Square detector side in mm')
    parser.add_argument('-detsize_f', type=float, metavar='MM',
                        help='Fast-axis size in mm')
    parser.add_argument('-detsize_s', type=float, metavar='MM',
                        help='Slow-axis size in mm')
    parser.add_argument('-distance', type=float, metavar='MM',
                        help='Sample-to-detector distance in mm')
    parser.add_argument('-close_distance', type=float, metavar='MM',
                        help='Minimum distance to detector plane in mm')
    parser.add_argument('-point_pixel', action='store_true',
                        help='Use 1/R^2 solid-angle only (no obliquity)')

    # Detector orientation
    parser.add_argument('-detector_rotx', type=float, default=0.0, metavar='DEG',
                        help='Detector rotation about X axis (degrees)')
    parser.add_argument('-detector_roty', type=float, default=0.0, metavar='DEG',
                        help='Detector rotation about Y axis (degrees)')
    parser.add_argument('-detector_rotz', type=float, default=0.0, metavar='DEG',
                        help='Detector rotation about Z axis (degrees)')
    parser.add_argument('-twotheta', type=float, default=0.0, metavar='DEG',
                        help='Detector rotation about twotheta axis')
    parser.add_argument('-twotheta_axis', nargs=3, type=float,
                        metavar=('X', 'Y', 'Z'),
                        help='Unit vector for twotheta rotation')
    parser.add_argument('-curved_det', action='store_true',
                        help='Pixels on sphere equidistant from sample')

    # Detector absorption
    parser.add_argument('-detector_abs', type=str, metavar='µm',
                        help='Attenuation depth in µm (inf or 0 to disable)')
    parser.add_argument('-detector_thick', type=float, metavar='µm',
                        help='Sensor thickness in µm')
    parser.add_argument('-detector_thicksteps', '-thicksteps', type=int,
                        dest='detector_thicksteps',
                        help='Discretization layers through thickness')

    # Beam/conventions
    parser.add_argument('-mosflm', action='store_const', const='MOSFLM',
                        dest='convention', help='Use MOSFLM convention')
    parser.add_argument('-xds', action='store_const', const='XDS',
                        dest='convention', help='Use XDS convention')
    parser.add_argument('-adxv', action='store_const', const='ADXV',
                        dest='convention', help='Use ADXV convention')
    parser.add_argument('-denzo', action='store_const', const='DENZO',
                        dest='convention', help='Use DENZO convention')
    parser.add_argument('-dials', action='store_const', const='DIALS',
                        dest='convention', help='Use DIALS convention')

    parser.add_argument('-pivot', choices=['beam', 'sample'],
                        help='Override pivot mode')

    # Custom vectors (set convention to CUSTOM)
    parser.add_argument('-fdet_vector', nargs=3, type=float,
                        metavar=('X', 'Y', 'Z'),
                        help='Fast axis unit vector')
    parser.add_argument('-sdet_vector', nargs=3, type=float,
                        metavar=('X', 'Y', 'Z'),
                        help='Slow axis unit vector')
    parser.add_argument('-odet_vector', nargs=3, type=float,
                        metavar=('X', 'Y', 'Z'),
                        help='Detector normal unit vector')
    parser.add_argument('-beam_vector', nargs=3, type=float,
                        metavar=('X', 'Y', 'Z'),
                        help='Beam unit vector')
    parser.add_argument('-polar_vector', nargs=3, type=float,
                        metavar=('X', 'Y', 'Z'),
                        help='Polarization unit vector')
    parser.add_argument('-spindle_axis', nargs=3, type=float,
                        metavar=('X', 'Y', 'Z'),
                        help='Spindle rotation axis')
    parser.add_argument('-pix0_vector', nargs=3, type=float,
                        metavar=('X', 'Y', 'Z'),
                        help='Detector origin offset (meters)')

    # Beam centers
    parser.add_argument('-Xbeam', type=float, metavar='MM',
                        help='Direct-beam X position (mm)')
    parser.add_argument('-Ybeam', type=float, metavar='MM',
                        help='Direct-beam Y position (mm)')
    parser.add_argument('-Xclose', type=float, metavar='MM',
                        help='Near point X (mm)')
    parser.add_argument('-Yclose', type=float, metavar='MM',
                        help='Near point Y (mm)')
    parser.add_argument('-ORGX', type=float, metavar='PIXELS',
                        help='XDS-style beam center X')
    parser.add_argument('-ORGY', type=float, metavar='PIXELS',
                        help='XDS-style beam center Y')

    # Beam spectrum/divergence
    parser.add_argument('-lambda', '-wave', type=float, metavar='Å',
                        dest='wavelength', help='Central wavelength in Å')
    parser.add_argument('-energy', type=float, metavar='eV',
                        help='Central energy in eV')
    parser.add_argument('-dispersion', type=float, metavar='%',
                        help='Spectral width (percent)')
    parser.add_argument('-dispsteps', type=int,
                        help='Number of wavelength steps')
    parser.add_argument('-divergence', type=float, metavar='mrad',
                        help='Sets both H and V divergence')
    parser.add_argument('-hdivrange', type=float, metavar='mrad',
                        help='Horizontal divergence range')
    parser.add_argument('-vdivrange', type=float, metavar='mrad',
                        help='Vertical divergence range')
    parser.add_argument('-hdivstep', type=float, metavar='mrad',
                        help='Horizontal divergence step size')
    parser.add_argument('-vdivstep', type=float, metavar='mrad',
                        help='Vertical divergence step size')
    parser.add_argument('-hdivsteps', type=int,
                        help='Horizontal divergence step count')
    parser.add_argument('-vdivsteps', type=int,
                        help='Vertical divergence step count')
    parser.add_argument('-divsteps', type=int,
                        help='Sets both H and V step counts')

    # Polarization
    parser.add_argument('-polar', type=float, metavar='K',
                        help='Kahn polarization factor (0-1)')
    parser.add_argument('-nopolar', action='store_true',
                        help='Disable polarization correction')

    # Crystal size/shape
    parser.add_argument('-Na', type=int, help='Unit cells along a')
    parser.add_argument('-Nb', type=int, help='Unit cells along b')
    parser.add_argument('-Nc', type=int, help='Unit cells along c')
    parser.add_argument('-N', type=int, help='Unit cells (all axes)')

    parser.add_argument('-samplesize', '-xtalsize', type=float, metavar='MM',
                        dest='samplesize', help='Crystal size in mm')
    parser.add_argument('-sample_thick', '-sample_x', '-xtal_thick', '-xtal_x',
                        type=float, metavar='MM', dest='sample_x',
                        help='Crystal thickness (x) in mm')
    parser.add_argument('-sample_width', '-sample_y', '-width', '-xtal_width',
                        '-xtal_y', type=float, metavar='MM', dest='sample_y',
                        help='Crystal width (y) in mm')
    parser.add_argument('-sample_height', '-sample_z', '-height', '-xtal_height',
                        '-xtal_z', type=float, metavar='MM', dest='sample_z',
                        help='Crystal height (z) in mm')

    parser.add_argument('-square_xtal', action='store_const', const='SQUARE',
                        dest='crystal_shape', help='Square crystal shape (default)')
    parser.add_argument('-round_xtal', action='store_const', const='ROUND',
                        dest='crystal_shape', help='Round crystal shape')
    parser.add_argument('-gauss_xtal', action='store_const', const='GAUSS',
                        dest='crystal_shape', help='Gaussian crystal shape')
    parser.add_argument('-binary_spots', '-tophat_spots', action='store_const',
                        const='TOPHAT', dest='crystal_shape',
                        help='Binary/tophat spots')
    parser.add_argument('-fudge', type=float, default=1.0,
                        help='Shape parameter scaling')

    # Mosaicity
    parser.add_argument('-mosaic', '-mosaici', '-mosaic_spr', type=float,
                        metavar='DEG', dest='mosaic',
                        help='Isotropic mosaic spread (degrees)')
    parser.add_argument('-mosaic_dom', type=int,
                        help='Number of mosaic domains')
    parser.add_argument('-mosaic_seed', type=int,
                        help='Seed for mosaic rotations')
    parser.add_argument('-misset', nargs='*',
                        help='Misset angles (deg) or "random"')
    parser.add_argument('-misset_seed', type=int,
                        help='Seed for random misset')

    # Sampling
    parser.add_argument('-phi', type=float, metavar='DEG',
                        help='Starting spindle rotation angle')
    parser.add_argument('-osc', type=float, metavar='DEG',
                        help='Oscillation range')
    parser.add_argument('-phistep', type=float, metavar='DEG',
                        help='Step size')
    parser.add_argument('-phisteps', type=int,
                        help='Number of phi steps')
    parser.add_argument('-dmin', type=float, metavar='Å',
                        help='Minimum d-spacing cutoff')
    parser.add_argument('-oversample', type=int,
                        help='Sub-pixel sampling per axis')
    parser.add_argument('-oversample_thick', action='store_true',
                        help='Recompute absorption per subpixel')
    parser.add_argument('-oversample_polar', action='store_true',
                        help='Recompute polarization per subpixel')
    parser.add_argument('-oversample_omega', action='store_true',
                        help='Recompute solid angle per subpixel')
    parser.add_argument('-roi', nargs=4, type=int,
                        metavar=('xmin', 'xmax', 'ymin', 'ymax'),
                        help='Pixel index limits (inclusive, zero-based)')

    # Background
    parser.add_argument('-water', type=float, metavar='µm',
                        help='Water background size (µm)')

    # Source intensity
    parser.add_argument('-fluence', type=float, metavar='photons/m^2',
                        help='Fluence (photons/m^2)')
    parser.add_argument('-flux', type=float, metavar='photons/s',
                        help='Flux (photons/s)')
    parser.add_argument('-exposure', type=float, metavar='s',
                        help='Exposure time (seconds)')
    parser.add_argument('-beamsize', type=float, metavar='MM',
                        help='Beam size (mm)')

    # Output files
    parser.add_argument('-floatfile', '-floatimage', type=str, metavar='FILE',
                        dest='floatfile', help='Raw float output')
    parser.add_argument('-intfile', '-intimage', type=str, metavar='FILE',
                        dest='intfile', help='SMV integer output')
    parser.add_argument('-scale', type=float,
                        help='Scale factor for SMV output')
    parser.add_argument('-adc', type=float, default=40.0,
                        help='ADC offset for SMV (default: 40)')
    parser.add_argument('-pgmfile', '-pgmimage', type=str, metavar='FILE',
                        dest='pgmfile', help='PGM preview output')
    parser.add_argument('-pgmscale', type=float,
                        help='Scale factor for PGM output')
    parser.add_argument('-noisefile', '-noiseimage', type=str, metavar='FILE',
                        dest='noisefile', help='SMV with Poisson noise')
    parser.add_argument('-nopgm', action='store_true',
                        help='Disable PGM output')

    # Interpolation
    parser.add_argument('-interpolate', action='store_true',
                        help='Enable tricubic interpolation')
    parser.add_argument('-nointerpolate', action='store_true',
                        help='Disable interpolation')

    # Misc
    parser.add_argument('-printout', action='store_true',
                        help='Verbose pixel prints')
    parser.add_argument('-printout_pixel', nargs=2, type=int,
                        metavar=('f', 's'),
                        help='Limit prints to specified pixel')
    parser.add_argument('-trace_pixel', nargs=2, type=int,
                        metavar=('s', 'f'),
                        help='Instrument trace for a pixel')
    parser.add_argument('-noprogress', action='store_true',
                        help='Disable progress meter')
    parser.add_argument('-progress', action='store_true',
                        help='Enable progress meter')
    parser.add_argument('-seed', type=int,
                        help='Noise RNG seed')

    return parser


def parse_and_validate_args(args: argparse.Namespace) -> Dict[str, Any]:
    """Parse and validate command-line arguments into configuration."""

    config = {}

    # Check required inputs
    has_hkl = args.hkl is not None or Path('Fdump.bin').exists()
    has_cell = args.mat is not None or args.cell is not None

    if not has_hkl and args.default_F == 0:
        print("Error: Need -hkl file, Fdump.bin, or -default_F > 0")
        print("Usage: nanoBragg -hkl <file> -mat <file> [options...]")
        sys.exit(1)

    if not has_cell:
        print("Error: Need -mat file or -cell parameters")
        print("Usage: nanoBragg -hkl <file> -mat <file> [options...]")
        sys.exit(1)

    # Load crystal cell
    if args.mat:
        # TODO: Load MOSFLM matrix file
        raise NotImplementedError("MOSFLM matrix file loading not yet implemented")
    elif args.cell:
        config['cell_params'] = args.cell

    # Load HKL data
    config['hkl_data'] = None
    config['default_F'] = args.default_F
    if args.hkl:
        config['hkl_data'] = read_hkl_file(args.hkl, default_F=args.default_F)
    elif Path('Fdump.bin').exists():
        config['hkl_data'] = try_load_hkl_or_fdump(None, fdump_path="Fdump.bin", default_F=args.default_F)

    # Wavelength/energy
    if args.energy:
        # λ = (12398.42 / E_eV) * 1e-10 meters
        config['wavelength_A'] = 12398.42 / args.energy
    elif args.wavelength:
        config['wavelength_A'] = args.wavelength
    else:
        config['wavelength_A'] = 1.0  # Default

    # Convention and pivot
    if any([args.fdet_vector, args.sdet_vector, args.odet_vector,
            args.beam_vector, args.polar_vector, args.spindle_axis,
            args.pix0_vector]):
        config['convention'] = 'CUSTOM'
    elif args.convention:
        config['convention'] = args.convention
    else:
        config['convention'] = 'MOSFLM'  # Default

    # Pivot mode precedence
    # First set default pivot based on convention (per spec)
    pivot = None
    convention = config['convention']
    if convention in ['MOSFLM', 'DENZO', 'ADXV']:
        # These conventions default to BEAM pivot
        pivot = 'BEAM'
    elif convention in ['XDS', 'DIALS']:
        # These conventions default to SAMPLE pivot
        pivot = 'SAMPLE'

    # Then apply flag-based overrides
    if args.distance and not args.close_distance:
        pivot = 'BEAM'
    elif args.close_distance:
        pivot = 'SAMPLE'

    if args.Xbeam is not None or args.Ybeam is not None:
        pivot = 'BEAM'
    elif any([args.Xclose is not None, args.Yclose is not None,
              args.ORGX is not None, args.ORGY is not None]):
        pivot = 'SAMPLE'

    if args.pivot:  # Explicit override wins
        pivot = args.pivot.upper()

    config['pivot'] = pivot

    # Detector parameters
    config['pixel_size_mm'] = args.pixel if args.pixel else 0.1

    # Pixel counts
    if args.detpixels:
        config['fpixels'] = args.detpixels
        config['spixels'] = args.detpixels
    else:
        config['fpixels'] = args.detpixels_f if args.detpixels_f else 1024
        config['spixels'] = args.detpixels_s if args.detpixels_s else 1024

    # Detector size (alternative to pixel count)
    if args.detsize:
        config['fpixels'] = int(args.detsize / config['pixel_size_mm'])
        config['spixels'] = int(args.detsize / config['pixel_size_mm'])
    elif args.detsize_f and args.detsize_s:
        config['fpixels'] = int(args.detsize_f / config['pixel_size_mm'])
        config['spixels'] = int(args.detsize_s / config['pixel_size_mm'])

    config['distance_mm'] = args.distance if args.distance else 100.0
    config['close_distance_mm'] = args.close_distance

    # Beam centers
    if args.Xbeam is not None:
        config['beam_center_x_mm'] = args.Xbeam
    if args.Ybeam is not None:
        config['beam_center_y_mm'] = args.Ybeam

    # Detector rotations
    config['detector_rotx_deg'] = args.detector_rotx
    config['detector_roty_deg'] = args.detector_roty
    config['detector_rotz_deg'] = args.detector_rotz
    config['twotheta_deg'] = args.twotheta
    if args.twotheta_axis:
        config['twotheta_axis'] = args.twotheta_axis

    config['point_pixel'] = args.point_pixel
    config['curved_detector'] = args.curved_det

    # Detector absorption
    if args.detector_abs:
        if args.detector_abs in ['inf', '0']:
            config['detector_abs_um'] = 0.0
        else:
            config['detector_abs_um'] = float(args.detector_abs)

    if args.detector_thick:
        config['detector_thick_um'] = args.detector_thick

    if args.detector_thicksteps:
        config['detector_thicksteps'] = args.detector_thicksteps

    # Crystal parameters
    if args.N:
        config['Na'] = args.N
        config['Nb'] = args.N
        config['Nc'] = args.N
    else:
        config['Na'] = args.Na if args.Na else 5
        config['Nb'] = args.Nb if args.Nb else 5
        config['Nc'] = args.Nc if args.Nc else 5

    # Crystal shape
    if args.crystal_shape:
        config['crystal_shape'] = args.crystal_shape
    else:
        config['crystal_shape'] = 'SQUARE'

    config['fudge'] = args.fudge

    # Mosaicity
    if args.mosaic:
        config['mosaic_spread_deg'] = args.mosaic
    if args.mosaic_dom:
        config['mosaic_domains'] = args.mosaic_dom
    if args.mosaic_seed:
        config['mosaic_seed'] = args.mosaic_seed

    # Misset
    if args.misset:
        if args.misset[0] == 'random':
            config['misset_random'] = True
        else:
            config['misset_deg'] = [float(x) for x in args.misset[:3]]
    if args.misset_seed:
        config['misset_seed'] = args.misset_seed

    # Phi rotation
    config['phi_deg'] = args.phi if args.phi else 0.0
    config['osc_deg'] = args.osc if args.osc else 0.0
    config['phi_steps'] = args.phisteps if args.phisteps else 1

    # Sampling
    config['dmin'] = args.dmin if args.dmin else 0.0
    config['oversample'] = args.oversample if args.oversample else 1
    config['oversample_thick'] = args.oversample_thick
    config['oversample_polar'] = args.oversample_polar
    config['oversample_omega'] = args.oversample_omega

    # Process -img and -mask files with proper precedence (AT-CLI-004)
    # Per spec: last file read wins for shared header keys
    if args.img or args.mask:
        # Process -img first if provided
        if args.img:
            try:
                img_header = parse_smv_header(args.img)
                apply_smv_header_to_config(img_header, config, is_mask=False)
                print(f"Read header from -img file: {args.img}")
            except (FileNotFoundError, ValueError) as e:
                print(f"Warning: Failed to read -img file: {e}", file=sys.stderr)

        # Process -mask second (wins if both provided per AT-CLI-004)
        if args.mask:
            try:
                mask_header = parse_smv_header(args.mask)
                apply_smv_header_to_config(mask_header, config, is_mask=True)
                config['mask_file'] = args.mask  # Store mask file for later loading
                print(f"Read header from -mask file: {args.mask}")
            except (FileNotFoundError, ValueError) as e:
                print(f"Warning: Failed to read -mask file header: {e}", file=sys.stderr)
                config['mask_file'] = args.mask  # Still try to load mask data

    # ROI
    if args.roi:
        config['roi'] = args.roi

    # Background
    if args.water:
        config['water_size_um'] = args.water

    # Fluence calculation
    if args.flux and args.exposure and args.beamsize:
        config['flux'] = args.flux
        config['exposure'] = args.exposure
        config['beamsize_mm'] = args.beamsize
    elif args.fluence:
        config['fluence'] = args.fluence

    # Polarization
    if args.nopolar:
        config['nopolar'] = True
    elif args.polar is not None:
        config['polarization_factor'] = args.polar

    # Interpolation
    if args.interpolate:
        config['interpolate'] = True
    elif args.nointerpolate:
        config['interpolate'] = False

    # Output files
    config['floatfile'] = args.floatfile
    config['intfile'] = args.intfile
    config['pgmfile'] = args.pgmfile
    config['noisefile'] = args.noisefile
    config['scale'] = args.scale
    config['adc'] = args.adc
    config['pgmscale'] = args.pgmscale
    config['seed'] = args.seed if args.seed else int(-time.time())

    # Sources
    if args.sourcefile:
        config['sources'] = read_sourcefile(args.sourcefile)

    return config


def main():
    """Main entry point for CLI."""

    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()

    try:
        # Validate and convert arguments
        config = parse_and_validate_args(args)

        # Create configuration objects
        if 'cell_params' in config:
            crystal_config = CrystalConfig(
                cell_a=config['cell_params'][0],
                cell_b=config['cell_params'][1],
                cell_c=config['cell_params'][2],
                cell_alpha=config['cell_params'][3],
                cell_beta=config['cell_params'][4],
                cell_gamma=config['cell_params'][5],
                N_cells=(config.get('Na', 5), config.get('Nb', 5), config.get('Nc', 5)),
                phi_start_deg=config.get('phi_deg', 0.0),
                osc_range_deg=config.get('osc_deg', 0.0),
                phi_steps=config.get('phi_steps', 1),
                mosaic_spread_deg=config.get('mosaic_spread_deg', 0.0),
                mosaic_domains=config.get('mosaic_domains', 1),
                shape=CrystalShape[config.get('crystal_shape', 'SQUARE')],
                fudge=config.get('fudge', 1.0),
                default_F=config.get('default_F', 0.0)
            )

            if 'misset_deg' in config:
                crystal_config.misset_deg = tuple(config['misset_deg'])

        # Create detector config
        detector_config = DetectorConfig(
            distance_mm=config.get('distance_mm', 100.0),
            close_distance_mm=config.get('close_distance_mm'),
            pixel_size_mm=config.get('pixel_size_mm', 0.1),
            spixels=config.get('spixels', 1024),
            fpixels=config.get('fpixels', 1024),
            detector_rotx_deg=config.get('detector_rotx_deg', 0.0),
            detector_roty_deg=config.get('detector_roty_deg', 0.0),
            detector_rotz_deg=config.get('detector_rotz_deg', 0.0),
            detector_twotheta_deg=config.get('twotheta_deg', 0.0),
            detector_convention=DetectorConvention[config.get('convention', 'MOSFLM')],
            detector_pivot=DetectorPivot[config.get('pivot', 'BEAM')] if config.get('pivot') else None,
            oversample=config.get('oversample', 1),
            point_pixel=config.get('point_pixel', False),
            curved_detector=config.get('curved_detector', False),
            oversample_omega=config.get('oversample_omega', False),
            oversample_polar=config.get('oversample_polar', False),
            oversample_thick=config.get('oversample_thick', False)
        )

        # Set beam center if provided
        if 'beam_center_x_mm' in config:
            detector_config.beam_center_s = config['beam_center_x_mm']  # Will be mapped per convention
        if 'beam_center_y_mm' in config:
            detector_config.beam_center_f = config['beam_center_y_mm']

        # ROI
        if 'roi' in config:
            detector_config.roi_xmin = config['roi'][0]
            detector_config.roi_xmax = config['roi'][1]
            detector_config.roi_ymin = config['roi'][2]
            detector_config.roi_ymax = config['roi'][3]

        # Mask
        if 'mask_file' in config:
            mask_data, _ = read_smv_mask(config['mask_file'])  # Returns tuple (mask, header)
            detector_config.mask_array = mask_data

        # Absorption
        if 'detector_abs_um' in config:
            detector_config.detector_abs_um = config['detector_abs_um']
        if 'detector_thick_um' in config:
            detector_config.detector_thick_um = config['detector_thick_um']
        if 'detector_thicksteps' in config:
            detector_config.detector_thicksteps = config['detector_thicksteps']

        # Create beam config
        beam_config = BeamConfig(
            wavelength_A=config.get('wavelength_A', 1.0),
            dmin=config.get('dmin', 0.0),
            water_size_um=config.get('water_size_um', 0.0)
        )

        # Fluence
        if 'flux' in config:
            beam_config.flux = config['flux']
            beam_config.exposure = config['exposure']
            beam_config.beamsize_mm = config['beamsize_mm']
        elif 'fluence' in config:
            beam_config.fluence = config['fluence']

        # Polarization
        if config.get('nopolar'):
            beam_config.nopolar = True
        elif 'polarization_factor' in config:
            beam_config.polarization_factor = config['polarization_factor']

        # Create models
        detector = Detector(detector_config)
        crystal = Crystal(crystal_config, beam_config=beam_config)

        # Set HKL data if available
        if 'hkl_data' in config and config['hkl_data'] is not None:
            hkl_array, hkl_metadata = config['hkl_data']
            if isinstance(hkl_array, torch.Tensor):
                crystal.hkl_data = hkl_array.clone().detach().to(dtype=torch.float64)
            else:
                crystal.hkl_data = torch.tensor(hkl_array, dtype=torch.float64)
            crystal.hkl_metadata = hkl_metadata

        # Check interpolation settings
        if 'interpolate' in config:
            crystal.interpolation_enabled = config['interpolate']

        # Create and run simulator
        simulator = Simulator(crystal, detector, beam_config=beam_config)

        print(f"Running simulation...")
        print(f"  Detector: {detector_config.fpixels}x{detector_config.spixels} pixels")
        print(f"  Crystal: {crystal_config.cell_a:.1f}x{crystal_config.cell_b:.1f}x{crystal_config.cell_c:.1f} Å")
        print(f"  Wavelength: {beam_config.wavelength_A:.2f} Å")

        # Run simulation
        intensity = simulator.run()

        # Compute statistics
        stats = simulator.compute_statistics(intensity)
        print(f"\nStatistics:")
        print(f"  Max intensity: {stats['max_I']:.3e} at pixel ({stats['max_I_slow']}, {stats['max_I_fast']})")
        print(f"  Mean: {stats['mean']:.3e}")
        print(f"  RMS: {stats['RMS']:.3e}")
        print(f"  RMSD: {stats['RMSD']:.3e}")

        # Write outputs
        if config.get('floatfile'):
            # Write raw float image
            data = intensity.cpu().numpy().astype(np.float32)
            data.tofile(config['floatfile'])
            print(f"Wrote float image to {config['floatfile']}")

        if config.get('intfile'):
            # Scale and write SMV
            scale = config.get('scale')
            if not scale or scale <= 0:
                max_val = intensity.max().item()
                scale = 55000.0 / max_val if max_val > 0 else 1.0

            # Apply scaling and ADC offset only to non-zero pixels (AT-CLI-005)
            # Pixels outside ROI should remain zero
            scaled = intensity * scale
            adc_offset = config.get('adc', 40.0)

            if adc_offset > 0:
                # Only add ADC where intensity > 0 (inside ROI)
                # Note: Due to floating point precision, we may need a small threshold
                threshold = 1e-10
                mask = intensity > threshold
                scaled = torch.where(mask, scaled + adc_offset, scaled)
            scaled = scaled.clip(0, 65535)
            scaled_int = scaled.to(torch.int16).cpu().numpy().astype(np.uint16)

            write_smv(
                filepath=config['intfile'],
                image_data=scaled_int,
                pixel_size_mm=detector_config.pixel_size_mm,
                distance_mm=detector_config.distance_mm,
                wavelength_angstrom=beam_config.wavelength_A,
                beam_center_x_mm=detector_config.beam_center_s * detector_config.pixel_size_mm,
                beam_center_y_mm=detector_config.beam_center_f * detector_config.pixel_size_mm,
                close_distance_mm=detector_config.close_distance_mm,
                phi_deg=config.get('phi_deg', 0.0),
                osc_start_deg=config.get('phi_deg', 0.0),
                osc_range_deg=config.get('osc_deg', 0.0),
                twotheta_deg=config.get('twotheta_deg', 0.0),
                convention=detector_config.detector_convention.name,
                scale=1.0,  # Already scaled
                adc_offset=0.0  # Already applied ADC
            )
            print(f"Wrote SMV image to {config['intfile']}")

        if config.get('pgmfile'):
            # Write PGM
            pgmscale = config.get('pgmscale', 1.0)
            write_pgm(config['pgmfile'], intensity.cpu().numpy(), pgmscale)
            print(f"Wrote PGM image to {config['pgmfile']}")

        if config.get('noisefile'):
            # Generate and write noise image
            noise_config = NoiseConfig(
                seed=config.get('seed'),
                adc_offset=config.get('adc', 40.0)
            )
            # For noise generation, we need to handle ROI properly (AT-CLI-005)
            # Only apply noise and ADC to pixels inside ROI
            # First, create a mask for where intensity > 0 (inside ROI)
            roi_mask = intensity > 0

            # Generate noise for the entire image (but without readout noise)
            noisy, overloads = generate_poisson_noise(
                intensity,
                seed=noise_config.seed,
                adc_offset=0.0,  # Don't apply ADC globally
                readout_noise=0.0,  # Don't apply readout noise globally
                overload_value=noise_config.overload_value
            )

            # noisy is now an integer tensor, convert back to float for additional operations
            noisy = noisy.float()

            # Add ADC offset and readout noise only to pixels inside ROI
            if roi_mask.any():
                # Apply readout noise only inside ROI
                if noise_config.readout_noise > 0:
                    generator = torch.Generator(device=intensity.device)
                    if noise_config.seed is not None:
                        generator.manual_seed(noise_config.seed + 1)  # Different seed for readout
                    readout = torch.normal(
                        mean=torch.zeros_like(noisy),
                        std=noise_config.readout_noise,
                        generator=generator
                    )
                    noisy = torch.where(roi_mask, noisy + readout, noisy)

                # Add ADC offset only inside ROI
                if noise_config.adc_offset > 0:
                    noisy = torch.where(roi_mask, noisy + noise_config.adc_offset, noisy)

            # Ensure pixels outside ROI remain exactly zero
            noisy = torch.where(roi_mask, noisy, torch.zeros_like(noisy))

            noisy_int = noisy.to(torch.int16).cpu().numpy().astype(np.uint16)

            write_smv(
                filepath=config['noisefile'],
                image_data=noisy_int,
                pixel_size_mm=detector_config.pixel_size_mm,
                distance_mm=detector_config.distance_mm,
                wavelength_angstrom=beam_config.wavelength_A,
                beam_center_x_mm=detector_config.beam_center_s * detector_config.pixel_size_mm,
                beam_center_y_mm=detector_config.beam_center_f * detector_config.pixel_size_mm,
                close_distance_mm=detector_config.close_distance_mm,
                phi_deg=config.get('phi_deg', 0.0),
                osc_start_deg=config.get('phi_deg', 0.0),
                osc_range_deg=config.get('osc_deg', 0.0),
                twotheta_deg=config.get('twotheta_deg', 0.0),
                convention=detector_config.detector_convention.name,
                scale=1.0,  # Already scaled
                adc_offset=0.0  # Already applied ADC
            )
            print(f"Wrote noise image to {config['noisefile']} ({overloads} overloads)")

        print("\nSimulation complete.")

    except Exception as e:
        import traceback
        print(f"Error: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()