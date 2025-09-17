#!/usr/bin/env python3
"""
nanoBragg Startup Warning System
================================

Detects dangerous parameter combinations that can trigger undocumented convention switching.
This script MUST be run before any nanoBragg simulation to prevent correlation bugs.

CRITICAL: The most dangerous combination is using -twotheta_axis with MOSFLM rotations,
which silently switches to CUSTOM convention without warning.
"""

import sys
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

# ASCII Art Warning Banners
CRITICAL_BANNER = """
╔════════════════════════════════════════════════════════════════════════════╗
║                                 CRITICAL                                   ║
║                            CONVENTION CONFLICT                             ║
║                                                                            ║
║  🚨 DANGER: This parameter combination triggers CUSTOM convention! 🚨      ║
║                                                                            ║
║  Your simulation will NOT match expected MOSFLM results.                   ║
║  Correlation with C reference will be <0.9 instead of >0.999              ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

WARNING_BANNER = """
┌────────────────────────────────────────────────────────────────────────────┐
│                                 WARNING                                    │
│                         POTENTIAL CONFIGURATION ISSUE                     │
│                                                                            │
│  ⚠️  This combination may cause unexpected behavior                        │
│                                                                            │
│  Please review the safe examples in examples/ directory                   │
└────────────────────────────────────────────────────────────────────────────┘
"""

INFO_BANNER = """
┌────────────────────────────────────────────────────────────────────────────┐
│                                  INFO                                      │
│                          CONVENTION DETECTION                             │
│                                                                            │
│  ℹ️  Detected explicit convention specification                            │
│                                                                            │
│  Make sure this matches your intended coordinate system                    │
└────────────────────────────────────────────────────────────────────────────┘
"""

@dataclass
class Parameter:
    """Represents a nanoBragg command-line parameter."""
    name: str
    value: Optional[str] = None
    present: bool = False

@dataclass
class ConventionContext:
    """Context about which convention should be active."""
    explicit_convention: Optional[str] = None
    implicit_convention: Optional[str] = None
    triggers: List[str] = None
    
    def __post_init__(self):
        if self.triggers is None:
            self.triggers = []

@dataclass
class Warning:
    """Represents a warning about parameter configuration."""
    level: str  # 'CRITICAL', 'WARNING', 'INFO'
    title: str
    message: str
    parameters: List[str]
    solution: str
    reference_docs: List[str]

class NanoBraggParameterParser:
    """Parses nanoBragg command-line parameters and detects dangerous combinations."""
    
    # Parameters that trigger CUSTOM convention
    CUSTOM_TRIGGERS = {
        '-twotheta_axis',
        '-spindle_axis',
        '-vert_axis'
    }
    
    # Rotation parameters that expect MOSFLM convention
    MOSFLM_ROTATIONS = {
        '-detector_rotx',
        '-detector_roty', 
        '-detector_rotz',
        '-twotheta'
    }
    
    # Parameters that explicitly set convention
    EXPLICIT_CONVENTIONS = {
        '-convention'
    }
    
    def __init__(self):
        self.parameters: Dict[str, Parameter] = {}
        self.warnings: List[Warning] = []
    
    def parse_command_line(self, args: List[str]) -> None:
        """Parse command-line arguments into parameter objects."""
        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith('-'):
                param = Parameter(name=arg, present=True)
                # Check if next arg is a value (not starting with -)
                if i + 1 < len(args) and not args[i + 1].startswith('-'):
                    param.value = args[i + 1]
                    i += 2
                else:
                    i += 1
                self.parameters[arg] = param
            else:
                i += 1
    
    def parse_command_string(self, command: str) -> None:
        """Parse a command string (e.g., from shell script) into parameters."""
        # Split on whitespace but preserve quoted strings
        import shlex
        try:
            args = shlex.split(command)
            self.parse_command_line(args)
        except ValueError as e:
            print(f"Warning: Could not parse command string: {e}")
            # Fallback to simple split
            args = command.split()
            self.parse_command_line(args)
    
    def detect_convention_context(self) -> ConventionContext:
        """Detect which convention should be active based on parameters."""
        context = ConventionContext()
        
        # Check for explicit convention
        if '-convention' in self.parameters:
            context.explicit_convention = self.parameters['-convention'].value
        
        # Check for CUSTOM triggers
        custom_triggers = []
        for trigger in self.CUSTOM_TRIGGERS:
            if trigger in self.parameters:
                custom_triggers.append(trigger)
        
        if custom_triggers:
            context.implicit_convention = 'CUSTOM'
            context.triggers = custom_triggers
        else:
            # Default is MOSFLM if no explicit convention
            context.implicit_convention = 'MOSFLM'
        
        return context
    
    def check_critical_conflicts(self) -> List[Warning]:
        """Check for critical parameter conflicts that cause silent bugs."""
        warnings = []
        context = self.detect_convention_context()
        
        # CRITICAL: CUSTOM triggers with MOSFLM rotations
        custom_triggers = [p for p in self.CUSTOM_TRIGGERS if p in self.parameters]
        mosflm_rotations = [p for p in self.MOSFLM_ROTATIONS if p in self.parameters]
        
        if custom_triggers and mosflm_rotations and not context.explicit_convention:
            warnings.append(Warning(
                level='CRITICAL',
                title='SILENT CONVENTION SWITCHING DETECTED',
                message=f"""
The parameter(s) {', '.join(custom_triggers)} will silently switch nanoBragg 
from MOSFLM to CUSTOM convention, but you're also using MOSFLM rotation 
parameters {', '.join(mosflm_rotations)}.

This combination causes:
• Detector basis vectors to use different coordinate systems
• Beam center calculations to differ by 0.5 pixels  
• Correlation with C reference to drop from >0.999 to <0.9
• Results that look "almost right" but are scientifically wrong

THIS IS THE #1 SOURCE OF BUGS IN nanoBragg simulations.
                """,
                parameters=custom_triggers + mosflm_rotations,
                solution="""
CHOOSE ONE:
1. REMOVE axis parameters and use pure MOSFLM (RECOMMENDED):
   Remove: {custom_params}
   Keep: {mosflm_params}

2. OR explicitly use CUSTOM convention:
   Add: -convention CUSTOM
   Keep all parameters but verify results manually

3. OR use XDS convention if appropriate:
   Change: -convention XDS
   Verify: All rotations use XDS coordinate system
                """.format(
                    custom_params=', '.join(custom_triggers),
                    mosflm_params=', '.join(mosflm_rotations)
                ),
                reference_docs=[
                    'docs/debugging/detector_geometry_checklist.md',
                    'docs/development/c_to_pytorch_config_map.md',
                    'examples/safe_mosflm_rotation.sh'
                ]
            ))
        
        return warnings
    
    def check_warnings(self) -> List[Warning]:
        """Check for potentially problematic configurations."""
        warnings = []
        context = self.detect_convention_context()
        
        # Check for twotheta without axis specification
        if '-twotheta' in self.parameters and '-twotheta_axis' not in self.parameters:
            warnings.append(Warning(
                level='WARNING',
                title='TWOTHETA WITHOUT AXIS SPECIFICATION',
                message="""
You're using -twotheta but haven't specified -twotheta_axis.
This will use the default axis (Y in MOSFLM, X in XDS).

If this is not what you intended, you may get unexpected rotation behavior.
                """,
                parameters=['-twotheta'],
                solution="""
VERIFY: The default twotheta axis is correct for your setup
- MOSFLM convention: twotheta rotates around Y-axis
- XDS convention: twotheta rotates around X-axis

OR SPECIFY explicitly:
- Add: -twotheta_axis Y  (for MOSFLM-style)
- Add: -twotheta_axis X  (for XDS-style)
WARNING: Adding -twotheta_axis triggers CUSTOM convention!
                """,
                reference_docs=[
                    'docs/architecture/c_parameter_dictionary.md',
                    'examples/safe_mosflm_rotation.sh'
                ]
            ))
        
        # Check for missing beam center with detector distance
        if '-distance' in self.parameters:
            if '-Xbeam' not in self.parameters and '-Ybeam' not in self.parameters:
                warnings.append(Warning(
                    level='WARNING', 
                    title='DETECTOR DISTANCE WITHOUT BEAM CENTER',
                    message="""
You've specified detector distance but no beam center (-Xbeam, -Ybeam).
This will use the default beam center (detector center).

For tilted detectors or non-centered beams, this may not be correct.
                    """,
                    parameters=['-distance'],
                    solution="""
VERIFY: Default beam center is correct for your geometry
- Default: Center of detector (detpixels/2, detpixels/2)

OR SPECIFY beam position:
- Add: -Xbeam <x_position_in_pixels>  
- Add: -Ybeam <y_position_in_pixels>
                    """,
                    reference_docs=[
                        'docs/architecture/detector.md',
                        'examples/safe_mosflm_rotation.sh'
                    ]
                ))
        
        return warnings
    
    def check_info(self) -> List[Warning]:
        """Check for informational items about convention usage."""
        warnings = []
        context = self.detect_convention_context()
        
        # Info about explicit convention
        if context.explicit_convention:
            warnings.append(Warning(
                level='INFO',
                title=f'EXPLICIT {context.explicit_convention} CONVENTION',
                message=f"""
You've explicitly specified -convention {context.explicit_convention}.
This will override any implicit convention switching.

Make sure all your parameters are consistent with {context.explicit_convention} coordinate system.
                """,
                parameters=['-convention'],
                solution=f"""
VERIFY: All parameters use {context.explicit_convention} conventions
- Check rotation axis definitions
- Check beam center calculations  
- Check detector geometry setup

REFERENCE: See {context.explicit_convention} examples in examples/ directory
                """,
                reference_docs=[
                    f'examples/safe_{context.explicit_convention.lower()}_rotation.sh',
                    'docs/architecture/detector.md'
                ]
            ))
        
        return warnings
    
    def analyze(self) -> List[Warning]:
        """Run complete analysis and return all warnings."""
        self.warnings = []
        self.warnings.extend(self.check_critical_conflicts())
        self.warnings.extend(self.check_warnings())
        self.warnings.extend(self.check_info())
        return self.warnings

def print_warning(warning: Warning) -> None:
    """Print a formatted warning to stdout."""
    if warning.level == 'CRITICAL':
        print(CRITICAL_BANNER)
    elif warning.level == 'WARNING':
        print(WARNING_BANNER)
    else:
        print(INFO_BANNER)
    
    print(f"\n{warning.level}: {warning.title}")
    print("=" * (len(warning.level) + len(warning.title) + 2))
    print(warning.message)
    
    if warning.parameters:
        print(f"\nAFFECTED PARAMETERS: {', '.join(warning.parameters)}")
    
    print(f"\nSOLUTION:")
    print(warning.solution)
    
    if warning.reference_docs:
        print(f"\nREFERENCE DOCUMENTATION:")
        for doc in warning.reference_docs:
            print(f"  • {doc}")
    
    print("\n" + "="*80 + "\n")

def analyze_command_line(args: List[str]) -> bool:
    """Analyze command line arguments and return True if safe to proceed."""
    parser = NanoBraggParameterParser()
    parser.parse_command_line(args)
    warnings = parser.analyze()
    
    has_critical = False
    for warning in warnings:
        print_warning(warning)
        if warning.level == 'CRITICAL':
            has_critical = True
    
    if has_critical:
        print("🛑 CRITICAL ISSUES FOUND - DO NOT PROCEED WITH SIMULATION")
        print("Fix the above issues before running nanoBragg.")
        return False
    elif warnings:
        print("⚠️  Issues found - please review before proceeding.")
        response = input("Continue anyway? [y/N]: ")
        return response.lower() in ['y', 'yes']
    else:
        print("✅ No configuration issues detected.")
        return True

def analyze_script_file(script_path: str) -> bool:
    """Analyze a shell script file for nanoBragg commands."""
    try:
        with open(script_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Could not find script file: {script_path}")
        return False
    
    # Find nanoBragg command lines
    lines = content.split('\n')
    nanoBragg_commands = []
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if line and not line.startswith('#'):
            if './nanoBragg' in line or 'nanoBragg' in line:
                nanoBragg_commands.append((line_num, line))
    
    if not nanoBragg_commands:
        print(f"No nanoBragg commands found in {script_path}")
        return True
    
    print(f"Analyzing {len(nanoBragg_commands)} nanoBragg command(s) in {script_path}:")
    print("="*80)
    
    all_safe = True
    for line_num, command in nanoBragg_commands:
        print(f"\nLine {line_num}: {command}")
        print("-" * 40)
        
        parser = NanoBraggParameterParser() 
        parser.parse_command_string(command)
        warnings = parser.analyze()
        
        if not warnings:
            print("✅ No issues detected for this command.")
        else:
            for warning in warnings:
                print_warning(warning)
                if warning.level == 'CRITICAL':
                    all_safe = False
    
    return all_safe

def main():
    """Main entry point for the warning system."""
    if len(sys.argv) < 2:
        print("""
nanoBragg Startup Warning System
================================

Usage:
  python startup_warnings.py <script_file>              # Analyze shell script
  python startup_warnings.py -- <nanoBragg_args...>     # Analyze command line
  
Examples:
  python startup_warnings.py my_simulation.sh
  python startup_warnings.py -- -lambda 6.2 -twotheta 15 -twotheta_axis Y
  
The script will check for dangerous parameter combinations that can cause
silent convention switching and correlation bugs.
        """)
        sys.exit(1)
    
    if sys.argv[1] == '--':
        # Analyze command line arguments
        safe = analyze_command_line(sys.argv[2:])
    else:
        # Analyze script file
        safe = analyze_script_file(sys.argv[1])
    
    sys.exit(0 if safe else 1)

if __name__ == '__main__':
    main()