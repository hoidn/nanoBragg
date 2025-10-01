#!/usr/bin/env python3
"""
Import Path Fixer for nanoBragg PyTorch Implementation

This script helps identify and fix incorrect import statements in Python files.
It searches for problematic imports and suggests corrections.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict


def find_problematic_imports(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Find lines with problematic import statements.

    Returns:
        List of (line_number, original_line, suggested_fix) tuples
    """
    problematic_patterns = [
        (r'from nanoBragg\.(.+) import', r'from nanobrag_torch.\1 import'),
        (r'import nanoBragg\.(.+)', r'import nanobrag_torch.\1'),
        (r'import nanoBragg(?![_a-zA-Z])', r'import nanobrag_torch'),
        (r'from nanobrag_torch\.components\.(.+) import', r'from nanobrag_torch.models.\1 import'),
    ]

    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            if line_stripped.startswith('#') or not line_stripped:
                continue

            # Skip lines that contain regex patterns (false positives)
            if "r'" in line and "nanoBragg" in line and "nanobrag_torch" in line:
                continue

            for pattern, replacement in problematic_patterns:
                if re.search(pattern, line):
                    fixed_line = re.sub(pattern, replacement, line)
                    issues.append((line_num, line.rstrip(), fixed_line.rstrip()))
                    break

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return issues


def scan_directory(directory: Path, extensions: List[str] = ['.py']) -> Dict[Path, List[Tuple[int, str, str]]]:
    """
    Scan directory for problematic imports.

    Returns:
        Dictionary mapping file paths to lists of issues
    """
    all_issues = {}

    for ext in extensions:
        for file_path in directory.rglob(f'*{ext}'):
            # Skip virtual environments and build directories
            if any(skip in str(file_path) for skip in ['.venv', '__pycache__', '.git', 'build']):
                continue

            issues = find_problematic_imports(file_path)
            if issues:
                all_issues[file_path] = issues

    return all_issues


def fix_file(file_path: Path, issues: List[Tuple[int, str, str]], dry_run: bool = True) -> bool:
    """
    Fix import issues in a file.

    Args:
        file_path: Path to the file to fix
        issues: List of (line_number, original_line, fixed_line) tuples
        dry_run: If True, just show what would be changed

    Returns:
        True if changes were made (or would be made in dry_run mode)
    """
    if not issues:
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Apply fixes (in reverse order to preserve line numbers)
        for line_num, original, fixed in reversed(issues):
            lines[line_num - 1] = fixed + '\n'

        if dry_run:
            print(f"\n📁 Would fix {file_path}:")
            for line_num, original, fixed in issues:
                print(f"  Line {line_num:3d}: {original}")
                print(f"           → {fixed}")
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"✓ Fixed {file_path}")

        return True

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def main():
    """Main function to scan and optionally fix import issues."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Find and fix problematic import statements in nanoBragg PyTorch code"
    )
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Directory or file to scan (default: current directory)'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Actually fix the issues (default: dry run)'
    )
    parser.add_argument(
        '--extensions',
        nargs='+',
        default=['.py'],
        help='File extensions to scan (default: .py)'
    )

    args = parser.parse_args()

    target_path = Path(args.path)
    if not target_path.exists():
        print(f"Error: Path {target_path} does not exist")
        return 1

    print(f"🔍 Scanning {target_path} for import issues...")

    if target_path.is_file():
        issues = find_problematic_imports(target_path)
        all_issues = {target_path: issues} if issues else {}
    else:
        all_issues = scan_directory(target_path, args.extensions)

    if not all_issues:
        print("✅ No import issues found!")
        return 0

    print(f"\n📊 Found import issues in {len(all_issues)} file(s):")

    total_issues = 0
    for file_path, issues in all_issues.items():
        total_issues += len(issues)
        print(f"  {file_path}: {len(issues)} issue(s)")

    print(f"\nTotal issues: {total_issues}")

    if args.fix:
        print("\n🔧 Applying fixes...")
        fixed_files = 0
        for file_path, issues in all_issues.items():
            if fix_file(file_path, issues, dry_run=False):
                fixed_files += 1
        print(f"\n✅ Fixed {fixed_files} file(s)")
    else:
        print("\n👀 Dry run mode - showing what would be fixed:")
        for file_path, issues in all_issues.items():
            fix_file(file_path, issues, dry_run=True)
        print(f"\n💡 Run with --fix to apply these changes")

    return 0


if __name__ == "__main__":
    sys.exit(main())