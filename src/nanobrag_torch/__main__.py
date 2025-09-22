#!/usr/bin/env python3
"""
nanoBragg PyTorch CLI interface.

This module provides the command-line interface for nanoBragg, mapping CLI flags
to internal configuration objects and executing the simulation.
"""

import argparse
import os
import sys
from typing import Optional
import numpy as np
import torch

# Set environment variable for MKL conflicts
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from .config import CrystalConfig, DetectorConfig, DetectorConvention, BeamConfig
from .models.crystal import Crystal
from .models.detector import Detector
from .simulator import Simulator
from .utils.units import degrees_to_radians, mm_to_meters


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser per spec-a-cli.md."""
    parser = argparse.ArgumentParser(
        prog='nanoBragg',
        description='PyTorch implementation of nanoBragg diffraction simulator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  nanoBragg -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -default_F 100 \\
    -distance 100 -detpixels 512 -floatfile output.bin

  nanoBragg -hkl P1.hkl -mat A.mat -lambda 1.0 -distance 100 \\
    -intfile output.img -noisefile noise.img
        """
    )

    # Input files
    parser.add_argument('-hkl', type=str, help='HKL file with h k l F values')
    parser.add_argument('-mat', '--matrix', type=str, help='3x3 MOSFLM-style A matrix file')
    parser.add_argument('-cell', nargs=6, type=float, metavar=('a', 'b', 'c', 'alpha', 'beta', 'gamma'),
                        help='Direct cell parameters: a b c (Angstroms) alpha beta gamma (degrees)')
    parser.add_argument('-img', type=str, help='SMV image file to read headers from')
    parser.add_argument('-mask', type=str, help='SMV mask file (0 values skip pixels)')
    parser.add_argument('-sourcefile', type=str, help='Multi-column source file')

    # Structure factors
    parser.add_argument('-default_F', type=float, default=0.0,
                        help='Default structure factor for missing reflections (default: 0)')

    # Detector pixel geometry
    parser.add_argument('-pixel', type=float, default=0.1,
                        help='Pixel size in mm (default: 0.1)')
    parser.add_argument('-detpixels', type=int,
                        help='Square detector pixel count (sets both axes)')
    parser.add_argument('-detpixels_f', '-detpixels_x', type=int, dest='detpixels_f',
                        help='Fast-axis pixels')
    parser.add_argument('-detpixels_s', '-detpixels_y', type=int, dest='detpixels_s',
                        help='Slow-axis pixels')
    parser.add_argument('-detsize', type=float,
                        help='Square detector side in mm (sets both axes)')
    parser.add_argument('-detsize_f', type=float, help='Fast-axis size in mm')
    parser.add_argument('-detsize_s', type=float, help='Slow-axis size in mm')
    parser.add_argument('-distance', type=float,
                        help='Sample-to-detector distance in mm (sets pivot to BEAM)')
    parser.add_argument('-close_distance', type=float,
                        help='Minimum distance to detector plane in mm (sets pivot to SAMPLE)')
    parser.add_argument('-point_pixel', action='store_true',
                        help='Use 1/R^2 solid-angle only (no obliquity)')

    # Detector orientation
    parser.add_argument('-detector_rotx', type=float, default=0.0,
                        help='Detector rotation about X in degrees')
    parser.add_argument('-detector_roty', type=float, default=0.0,
                        help='Detector rotation about Y in degrees')
    parser.add_argument('-detector_rotz', type=float, default=0.0,
                        help='Detector rotation about Z in degrees')
    parser.add_argument('-twotheta', type=float, default=0.0,
                        help='Detector rotation about twotheta_axis in degrees')
    parser.add_argument('-twotheta_axis', nargs=3, type=float,
                        help='Axis for twotheta rotation (unit vector)')
    parser.add_argument('-curved_det', action='store_true',
                        help='Treat detector as spherical surface')

    # Detector absorption
    parser.add_argument('-detector_abs', type=str,
                        help='Attenuation depth in µm (or "inf"/0 to disable)')
    parser.add_argument('-detector_thick', '-detector_thickness', type=float, dest='detector_thickness',
                        help='Sensor thickness in µm')
    parser.add_argument('-detector_thicksteps', '-thicksteps', type=int, dest='thicksteps',
                        help='Discretization layers through thickness')

    # Beam/conventions
    parser.add_argument('-mosflm', action='store_const', const=DetectorConvention.MOSFLM,
                        dest='convention', help='Use MOSFLM detector convention')
    parser.add_argument('-xds', action='store_const', const=DetectorConvention.XDS,
                        dest='convention', help='Use XDS detector convention')
    parser.add_argument('-adxv', action='store_const', const=DetectorConvention.ADXV,
                        dest='convention', help='Use ADXV detector convention')
    parser.add_argument('-denzo', action='store_const', const=DetectorConvention.DENZO,
                        dest='convention', help='Use DENZO detector convention')
    parser.add_argument('-dials', action='store_const', const=DetectorConvention.DIALS,
                        dest='convention', help='Use DIALS detector convention')
    parser.add_argument('-pivot', choices=['beam', 'sample'],
                        help='Override pivot mode')

    # Custom vectors
    parser.add_argument('-fdet_vector', nargs=3, type=float,
                        help='Custom fast detector axis (sets CUSTOM convention)')
    parser.add_argument('-sdet_vector', nargs=3, type=float,
                        help='Custom slow detector axis (sets CUSTOM convention)')
    parser.add_argument('-odet_vector', nargs=3, type=float,
                        help='Custom detector normal (sets CUSTOM convention)')
    parser.add_argument('-beam_vector', nargs=3, type=float,
                        help='Custom beam vector (sets CUSTOM convention)')
    parser.add_argument('-polar_vector', nargs=3, type=float,
                        help='Custom polarization vector (sets CUSTOM convention)')
    parser.add_argument('-spindle_axis', nargs=3, type=float,
                        help='Custom spindle axis')
    parser.add_argument('-pix0_vector', nargs=3, type=float,
                        help='Detector origin offset in meters (sets CUSTOM convention)')

    # Beam centers
    parser.add_argument('-Xbeam', type=float, help='Direct beam X position in mm (sets pivot to BEAM)')
    parser.add_argument('-Ybeam', type=float, help='Direct beam Y position in mm (sets pivot to BEAM)')
    parser.add_argument('-Xclose', type=float, help='Near point X in mm (sets pivot to SAMPLE)')
    parser.add_argument('-Yclose', type=float, help='Near point Y in mm (sets pivot to SAMPLE)')
    parser.add_argument('-ORGX', type=float, help='XDS-style X beam center in pixels (sets pivot to SAMPLE)')
    parser.add_argument('-ORGY', type=float, help='XDS-style Y beam center in pixels (sets pivot to SAMPLE)')

    # Beam spectrum/divergence
    parser.add_argument('-lambda', '-wave', '--wavelength', type=float, dest='wavelength',
                        help='Central wavelength in Angstroms')
    parser.add_argument('-energy', type=float, help='Central energy in eV')
    parser.add_argument('-dispersion', type=float, help='Spectral width as percent')
    parser.add_argument('-dispsteps', type=int, help='Number of wavelength steps')
    parser.add_argument('-divergence', type=float, help='Angular divergence in mrad')
    parser.add_argument('-hdivrange', type=float, help='Horizontal divergence range in mrad')
    parser.add_argument('-vdivrange', type=float, help='Vertical divergence range in mrad')
    parser.add_argument('-hdivstep', type=float, help='Horizontal divergence step in mrad')
    parser.add_argument('-vdivstep', type=float, help='Vertical divergence step in mrad')
    parser.add_argument('-hdivsteps', type=int, help='Horizontal divergence steps')
    parser.add_argument('-vdivsteps', type=int, help='Vertical divergence steps')
    parser.add_argument('-divsteps', type=int, help='Divergence steps (both axes)')

    # Polarization
    parser.add_argument('-polar', type=float, help='Kahn polarization factor')
    parser.add_argument('-nopolar', action='store_true', help='Disable polarization correction')

    # Crystal size/shape and mosaicity
    parser.add_argument('-Na', type=int, help='Unit cells along a')
    parser.add_argument('-Nb', type=int, help='Unit cells along b')
    parser.add_argument('-Nc', type=int, help='Unit cells along c')
    parser.add_argument('-N', type=int, help='Unit cells along all axes')
    parser.add_argument('-samplesize', '-xtalsize', type=float, dest='samplesize',
                        help='Crystal size in mm (all dimensions)')
    parser.add_argument('-square_xtal', action='store_const', const='square', dest='shape',
                        help='Square crystal shape (default)')
    parser.add_argument('-round_xtal', action='store_const', const='round', dest='shape',
                        help='Round crystal shape')
    parser.add_argument('-gauss_xtal', action='store_const', const='gauss', dest='shape',
                        help='Gaussian crystal shape')
    parser.add_argument('-binary_spots', '-tophat_spots', action='store_const', const='tophat', dest='shape',
                        help='Top-hat spot shape')
    parser.add_argument('-fudge', type=float, help='Shape parameter scaling')
    parser.add_argument('-mosaic', '-mosaic_spread', '-mosaic_spr', type=float, dest='mosaic_spread',
                        help='Isotropic mosaic spread in degrees')
    parser.add_argument('-mosaic_dom', '-mosaic_domains', type=int, dest='mosaic_domains',
                        help='Number of mosaic domains')

    # Sampling
    parser.add_argument('-phi', type=float, help='Starting spindle rotation in degrees')
    parser.add_argument('-osc', type=float, help='Oscillation range in degrees')
    parser.add_argument('-phistep', type=float, help='Phi step size in degrees')
    parser.add_argument('-phisteps', type=int, help='Number of phi steps')
    parser.add_argument('-dmin', type=float, help='Minimum d-spacing cutoff in Angstroms')
    parser.add_argument('-oversample', type=int, help='Sub-pixel sampling per axis')
    parser.add_argument('-oversample_thick', action='store_true',
                        help='Recompute absorption per subpixel')
    parser.add_argument('-oversample_polar', action='store_true',
                        help='Recompute polarization per subpixel')
    parser.add_argument('-oversample_omega', action='store_true',
                        help='Recompute solid angle per subpixel')
    parser.add_argument('-roi', nargs=4, type=int, metavar=('xmin', 'xmax', 'ymin', 'ymax'),
                        help='Region of interest: xmin xmax ymin ymax')

    # Background
    parser.add_argument('-water', type=float, help='Water background cubic dimension in µm')

    # Source intensity
    parser.add_argument('-fluence', type=float, help='Fluence in photons/m^2')
    parser.add_argument('-flux', type=float, help='Flux in photons/s')
    parser.add_argument('-exposure', type=float, help='Exposure time in seconds')
    parser.add_argument('-beamsize', type=float, help='Beam size in mm')

    # Output
    parser.add_argument('-floatfile', '-floatimage', type=str, dest='floatfile',
                        help='Output raw float image file')
    parser.add_argument('-intfile', '-intimage', type=str, dest='intfile',
                        help='Output SMV format integer image')
    parser.add_argument('-scale', type=float, help='Scale factor for SMV output')
    parser.add_argument('-adc', type=float, default=40.0,
                        help='ADC offset for SMV output (default: 40)')
    parser.add_argument('-pgmfile', '-pgmimage', type=str, dest='pgmfile',
                        help='Output PGM format image')
    parser.add_argument('-pgmscale', type=float, help='Scale factor for PGM output')
    parser.add_argument('-noisefile', '-noiseimage', type=str, dest='noisefile',
                        help='Output SMV with Poisson noise')
    parser.add_argument('-nopgm', action='store_true', help='Disable PGM output')

    # Interpolation
    parser.add_argument('-interpolate', action='store_true',
                        help='Enable tricubic interpolation of structure factors')
    parser.add_argument('-nointerpolate', action='store_true',
                        help='Disable interpolation')

    # Misc
    parser.add_argument('-printout', action='store_true', help='Verbose pixel prints')
    parser.add_argument('-printout_pixel', nargs=2, type=int, help='Limit prints to pixel f s')
    parser.add_argument('-trace_pixel', nargs=2, type=int, help='Instrument trace for pixel s f')
    parser.add_argument('-noprogress', action='store_true', help='Disable progress meter')
    parser.add_argument('-progress', action='store_true', help='Enable progress meter')
    parser.add_argument('-seed', type=int, help='Noise RNG seed')
    parser.add_argument('-mosaic_seed', type=int, help='Mosaic domain RNG seed')
    parser.add_argument('-misset_seed', type=int, help='Misset RNG seed')
    parser.add_argument('-misset', nargs='*', help='Misset angles in degrees or "random"')
    parser.add_argument('-stol', type=str, help='S(Q) file (read but not used)')
    parser.add_argument('-4stol', type=str, help='4*S(Q) file (read but not used)')
    parser.add_argument('-Q', type=str, help='Q file (read but not used)')
    parser.add_argument('-stolout', type=str, help='Output S(Q) file')

    return parser


def args_to_configs(args: argparse.Namespace) -> tuple[CrystalConfig, DetectorConfig, BeamConfig]:
    """Convert parsed arguments to configuration objects."""
    # Crystal configuration
    crystal_config = CrystalConfig()

    if args.cell:
        crystal_config.cell_a = args.cell[0]
        crystal_config.cell_b = args.cell[1]
        crystal_config.cell_c = args.cell[2]
        crystal_config.cell_alpha = args.cell[3]
        crystal_config.cell_beta = args.cell[4]
        crystal_config.cell_gamma = args.cell[5]

    if args.N:
        crystal_config.N_cells = [args.N, args.N, args.N]
    else:
        if args.Na:
            crystal_config.N_cells[0] = max(1, args.Na)
        if args.Nb:
            crystal_config.N_cells[1] = max(1, args.Nb)
        if args.Nc:
            crystal_config.N_cells[2] = max(1, args.Nc)

    if args.misset:
        if args.misset == ['random']:
            # TODO: Implement random misset
            pass
        elif len(args.misset) == 3:
            crystal_config.misset_angles = [
                degrees_to_radians(float(args.misset[0])),
                degrees_to_radians(float(args.misset[1])),
                degrees_to_radians(float(args.misset[2]))
            ]

    if args.phi is not None:
        crystal_config.phi_start = degrees_to_radians(args.phi)
    if args.osc is not None:
        crystal_config.oscillation_range = degrees_to_radians(args.osc)
    if args.phistep is not None:
        crystal_config.phi_step = degrees_to_radians(args.phistep)
    if args.phisteps is not None:
        crystal_config.phi_steps = args.phisteps

    if args.mosaic_spread is not None:
        crystal_config.mosaic_spread = degrees_to_radians(args.mosaic_spread)
    if args.mosaic_domains is not None:
        crystal_config.mosaic_domains = args.mosaic_domains

    # Detector configuration
    detector_config = DetectorConfig()

    if args.convention:
        detector_config.detector_convention = args.convention

    if args.detpixels:
        detector_config.fpixels = args.detpixels
        detector_config.spixels = args.detpixels
    if args.detpixels_f:
        detector_config.fpixels = args.detpixels_f
    if args.detpixels_s:
        detector_config.spixels = args.detpixels_s

    if args.pixel:
        detector_config.pixel_size = mm_to_meters(args.pixel)

    if args.detsize:
        size_m = mm_to_meters(args.detsize)
        detector_config.fpixels = int(size_m / detector_config.pixel_size)
        detector_config.spixels = int(size_m / detector_config.pixel_size)
    if args.detsize_f:
        size_m = mm_to_meters(args.detsize_f)
        detector_config.fpixels = int(size_m / detector_config.pixel_size)
    if args.detsize_s:
        size_m = mm_to_meters(args.detsize_s)
        detector_config.spixels = int(size_m / detector_config.pixel_size)

    if args.distance:
        detector_config.distance_mm = args.distance  # Keep in mm
        detector_config.pivot = 'BEAM'
    if args.close_distance:
        # Store close_distance as custom attribute for now
        detector_config.pivot = 'SAMPLE'

    if args.pivot:
        detector_config.pivot = args.pivot.upper()

    if args.detector_rotx:
        detector_config.detector_rotx = degrees_to_radians(args.detector_rotx)
    if args.detector_roty:
        detector_config.detector_roty = degrees_to_radians(args.detector_roty)
    if args.detector_rotz:
        detector_config.detector_rotz = degrees_to_radians(args.detector_rotz)
    if args.twotheta:
        detector_config.detector_twotheta = degrees_to_radians(args.twotheta)

    if args.twotheta_axis:
        detector_config.twotheta_axis = torch.tensor(args.twotheta_axis, dtype=torch.float64)
        detector_config._twotheta_axis_explicit = True

    # Custom vectors
    if args.fdet_vector:
        detector_config.fdet_vector = torch.tensor(args.fdet_vector, dtype=torch.float64)
    if args.sdet_vector:
        detector_config.sdet_vector = torch.tensor(args.sdet_vector, dtype=torch.float64)
    if args.odet_vector:
        detector_config.odet_vector = torch.tensor(args.odet_vector, dtype=torch.float64)
    if args.beam_vector:
        detector_config.beam_vector = torch.tensor(args.beam_vector, dtype=torch.float64)
    if args.polar_vector:
        detector_config.polar_vector = torch.tensor(args.polar_vector, dtype=torch.float64)
    if args.pix0_vector:
        detector_config.pix0_vector = torch.tensor(args.pix0_vector, dtype=torch.float64)

    # Beam centers
    if args.Xbeam is not None:
        detector_config.beam_center_f = args.Xbeam  # Already in mm
        detector_config.pivot = 'BEAM'
    if args.Ybeam is not None:
        detector_config.beam_center_s = args.Ybeam  # Already in mm
        detector_config.pivot = 'BEAM'

    # Beam configuration
    beam_config = BeamConfig()

    if args.wavelength:
        beam_config.wavelength = args.wavelength
    elif args.energy:
        # Convert energy (eV) to wavelength (Angstroms)
        beam_config.wavelength = 12398.42 / args.energy

    if args.fluence:
        beam_config.fluence = args.fluence
    elif args.flux and args.exposure and args.beamsize:
        # fluence = flux * exposure / beamsize^2
        beamsize_m = mm_to_meters(args.beamsize)
        beam_config.fluence = args.flux * args.exposure / (beamsize_m ** 2)

    return crystal_config, detector_config, beam_config


def save_float_image(image: torch.Tensor, filename: str):
    """Save raw float image in binary format."""
    # Convert to numpy and save as binary
    image_np = image.cpu().numpy().astype(np.float32)
    image_np.tofile(filename)
    print(f"Saved float image to {filename}")


def save_smv_image(image: torch.Tensor, filename: str, config: DetectorConfig,
                   wavelength: float, scale: Optional[float] = None, adc: float = 40.0):
    """Save image in SMV format with header."""
    # Convert to numpy
    image_np = image.cpu().numpy()

    # Auto-scale if needed
    if scale is None or scale <= 0:
        max_val = image_np.max()
        if max_val > 0:
            scale = 55000.0 / max_val
        else:
            scale = 1.0

    # Apply scale and ADC offset
    image_int = np.clip(image_np * scale + adc, 0, 65535).astype(np.uint16)

    # Calculate beam center in mm
    # beam_center_f and beam_center_s are in mm already in the config
    beam_x_mm = float(config.beam_center_f) if isinstance(config.beam_center_f, torch.Tensor) else config.beam_center_f
    beam_y_mm = float(config.beam_center_s) if isinstance(config.beam_center_s, torch.Tensor) else config.beam_center_s

    # Get distance in mm
    distance_mm = float(config.distance_mm) if isinstance(config.distance_mm, torch.Tensor) else config.distance_mm

    # Create SMV header
    header_lines = [
        "{",
        f"HEADER_BYTES=512;",
        f"DIM=2;",
        f"BYTE_ORDER={'little_endian' if sys.byteorder == 'little' else 'big_endian'};",
        f"TYPE=unsigned_short;",
        f"SIZE1={config.fpixels};",
        f"SIZE2={config.spixels};",
        f"PIXEL_SIZE={config.pixel_size * 1000:.6f};",  # Convert m to mm
        f"DISTANCE={distance_mm:.6f};",  # Already in mm
        f"WAVELENGTH={wavelength:.6f};",
        f"BEAM_CENTER_X={beam_x_mm:.6f};",
        f"BEAM_CENTER_Y={beam_y_mm:.6f};",
        f"ADXV_CENTER_X={beam_x_mm:.6f};",
        f"ADXV_CENTER_Y={beam_y_mm:.6f};",
        f"MOSFLM_CENTER_X={beam_x_mm:.6f};",
        f"MOSFLM_CENTER_Y={beam_y_mm:.6f};",
        f"DENZO_X_BEAM={beam_x_mm:.6f};",
        f"DENZO_Y_BEAM={beam_y_mm:.6f};",
        f"DIALS_ORIGIN={beam_x_mm:.6f},{beam_y_mm:.6f},0.000;",
        f"XDS_ORGX={beam_x_mm / (config.pixel_size * 1000):.2f};",
        f"XDS_ORGY={beam_y_mm / (config.pixel_size * 1000):.2f};",
        f"CLOSE_DISTANCE={distance_mm:.6f};",  # Use distance if close_distance not available
        f"PHI=0.00;",
        f"OSC_START=0.00;",
        f"OSC_RANGE=0.00;",
        f"TWOTHETA=0.00;",
        f"DETECTOR_SN=000;",
        f"BEAMLINE=fake;",
        "}\f"
    ]

    header = "\n".join(header_lines)
    # Pad header to 512 bytes
    header_bytes = header.encode('ascii')
    if len(header_bytes) < 512:
        header_bytes += b' ' * (512 - len(header_bytes))

    # Write file
    with open(filename, 'wb') as f:
        f.write(header_bytes[:512])
        # Fast-major ordering
        image_int.T.tofile(f)

    print(f"Saved SMV image to {filename}")


def save_pgm_image(image: torch.Tensor, filename: str, pgm_scale: Optional[float] = None):
    """Save image in PGM format."""
    # Convert to numpy
    image_np = image.cpu().numpy()

    # Auto-scale if needed
    if pgm_scale is None:
        max_val = image_np.max()
        if max_val > 0:
            pgm_scale = 255.0 / max_val
        else:
            pgm_scale = 1.0

    # Apply scale
    image_byte = np.clip(image_np * pgm_scale, 0, 255).astype(np.uint8)

    # Write PGM file
    height, width = image_byte.shape
    with open(filename, 'wb') as f:
        f.write(f"P5\n{width} {height}\n".encode('ascii'))
        f.write(f"# pixels scaled by {pgm_scale}\n".encode('ascii'))
        f.write(b"255\n")
        # Fast-major ordering
        image_byte.T.tofile(f)

    print(f"Saved PGM image to {filename}")


def main():
    """Main entry point for nanoBragg CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Check minimal requirements
    if not args.cell and not args.matrix:
        if not args.hkl and args.default_F == 0.0:
            parser.print_help()
            sys.exit(1)

    # Convert args to configs
    crystal_config, detector_config, beam_config = args_to_configs(args)

    # Create objects
    device = torch.device('cpu')
    dtype = torch.float64

    crystal = Crystal(config=crystal_config, device=device, dtype=dtype)
    detector = Detector(config=detector_config, device=device, dtype=dtype)

    # Load HKL data if provided
    if args.hkl:
        crystal.load_hkl(args.hkl)
    elif args.default_F > 0:
        # Create default structure factors
        # For now, use a simple default pattern
        crystal.default_F = args.default_F

    # Create and run simulator
    simulator = Simulator(
        crystal=crystal,
        detector=detector,
        crystal_config=crystal_config,
        beam_config=beam_config,
        device=device,
        dtype=dtype
    )

    # Update wavelength if specified
    if beam_config.wavelength:
        simulator.wavelength = beam_config.wavelength

    # Run simulation
    print(f"Running simulation...")
    image = simulator.run()

    # Save outputs
    if args.floatfile:
        save_float_image(image, args.floatfile)

    if args.intfile:
        save_smv_image(image, args.intfile, detector_config,
                      simulator.wavelength, args.scale, args.adc)

    if args.pgmfile:
        save_pgm_image(image, args.pgmfile, args.pgmscale)

    if args.noisefile:
        # TODO: Implement Poisson noise
        print(f"Warning: Noise image generation not yet implemented")

    print(f"Simulation complete")
    return 0


if __name__ == '__main__':
    sys.exit(main())