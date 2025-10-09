#!/usr/bin/env python3
"""
Vectorization Loop Inventory — AST-Based Analysis

Scans Python source for `For`/`While` loops in the target package and generates
an inventory with code locations and iteration driver heuristics.

Follows nanoBragg tooling standards (testing_strategy.md §6):
- Located in scripts/analysis/
- ASCII-only output
- Saves to structured reports directory
- Exit non-zero on errors

Usage:
    python scripts/analysis/vectorization_inventory.py \
        --package src/nanobrag_torch \
        --outdir reports/2026-01-vectorization-gap/phase_a/<STAMP>/
"""

import ast
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import argparse


class LoopVisitor(ast.NodeVisitor):
    """AST visitor that collects For and While loop information."""

    def __init__(self, module_path: Path):
        self.module_path = module_path
        self.loops: List[Dict[str, Any]] = []

    def visit_For(self, node: ast.For):
        """Record For loop details."""
        loop_info = self._extract_loop_info(node, "for")
        self.loops.append(loop_info)
        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        """Record While loop details."""
        loop_info = self._extract_loop_info(node, "while")
        self.loops.append(loop_info)
        self.generic_visit(node)

    def _extract_loop_info(self, node: ast.AST, loop_type: str) -> Dict[str, Any]:
        """Extract structured information from a loop node."""
        # Get source code snippet if available
        try:
            if loop_type == "for":
                # Get iterator target and source
                target = ast.unparse(node.target) if hasattr(ast, 'unparse') else "<unparseable>"
                iter_src = ast.unparse(node.iter) if hasattr(ast, 'unparse') else "<unparseable>"
                loop_header = f"for {target} in {iter_src}"
            else:
                test = ast.unparse(node.test) if hasattr(ast, 'unparse') else "<unparseable>"
                loop_header = f"while {test}"
        except Exception:
            loop_header = f"<{loop_type} loop at line {node.lineno}>"

        # Heuristic: guess iteration drivers based on common patterns
        iteration_hint = self._guess_iteration_driver(node, loop_type)

        return {
            "module": str(self.module_path),
            "line": node.lineno,
            "col_offset": node.col_offset,
            "loop_type": loop_type,
            "loop_header": loop_header,
            "iteration_hint": iteration_hint,
        }

    def _guess_iteration_driver(self, node: ast.AST, loop_type: str) -> str:
        """Heuristic to identify likely iteration drivers."""
        if loop_type == "for":
            iter_src = ast.unparse(node.iter) if hasattr(ast, 'unparse') else ""

            # Common patterns
            if "range" in iter_src:
                return "range-based (likely hot if large N)"
            elif "enumerate" in iter_src:
                return "enumerate (check underlying collection size)"
            elif "zip" in iter_src:
                return "zip (parallel iteration)"
            elif ".items()" in iter_src or ".keys()" in iter_src or ".values()" in iter_src:
                return "dict iteration (usually small)"
            elif any(x in iter_src for x in ["mosaic", "sources", "phi", "oversample", "thick"]):
                return "simulation parameter loop (HOT PATH - should be vectorized)"
            else:
                return "unknown iterable"
        else:
            # While loops are often problematic for vectorization
            return "while loop (typically hard to vectorize)"


def scan_package(package_path: Path) -> List[Dict[str, Any]]:
    """Scan all Python files in package and collect loop inventory."""
    all_loops = []

    # Find all .py files
    py_files = sorted(package_path.rglob("*.py"))

    for py_file in py_files:
        # Skip __pycache__ and test files unless they're critical
        if "__pycache__" in str(py_file) or py_file.name.startswith("test_"):
            continue

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()

            # Parse AST
            tree = ast.parse(source, filename=str(py_file))

            # Visit and collect loops
            visitor = LoopVisitor(py_file)
            visitor.visit(tree)

            all_loops.extend(visitor.loops)

        except SyntaxError as e:
            print(f"WARNING: Syntax error in {py_file}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"WARNING: Failed to process {py_file}: {e}", file=sys.stderr)

    return all_loops


def filter_hot_loops(loops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter likely runtime-critical loops."""
    hot_keywords = [
        "simulator", "crystal", "detector", "physics",
        "mosaic", "sources", "phi", "oversample", "thick"
    ]

    hot_loops = []
    for loop in loops:
        module_lower = loop["module"].lower()
        header_lower = loop["loop_header"].lower()

        # Check if loop is in critical modules or has hot iteration patterns
        is_hot = (
            any(kw in module_lower for kw in hot_keywords) or
            any(kw in header_lower for kw in hot_keywords) or
            "simulation parameter loop" in loop["iteration_hint"]
        )

        if is_hot:
            hot_loops.append(loop)

    return hot_loops


def generate_summary(loops: List[Dict[str, Any]], hot_loops: List[Dict[str, Any]],
                     output_dir: Path) -> None:
    """Generate human-readable summary markdown."""
    summary_path = output_dir / "summary.md"

    with open(summary_path, 'w', encoding='ascii', errors='replace') as f:
        f.write("# Vectorization Loop Inventory Summary\n\n")
        f.write(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")

        f.write("## Overview\n\n")
        f.write(f"- Total loops found: {len(loops)}\n")
        f.write(f"- Likely hot loops: {len(hot_loops)}\n")
        f.write(f"- Scan target: src/nanobrag_torch/\n\n")

        # Group by module
        by_module = {}
        for loop in loops:
            module = loop["module"]
            if module not in by_module:
                by_module[module] = []
            by_module[module].append(loop)

        f.write("## Loops by Module\n\n")
        for module in sorted(by_module.keys()):
            module_loops = by_module[module]
            f.write(f"### {module}\n\n")
            f.write(f"Loop count: {len(module_loops)}\n\n")

            for loop in module_loops:
                f.write(f"- Line {loop['line']}: `{loop['loop_header']}`\n")
                f.write(f"  - Type: {loop['loop_type']}\n")
                f.write(f"  - Hint: {loop['iteration_hint']}\n\n")

        f.write("## Hot Path Candidates\n\n")
        f.write("Loops likely to affect simulation performance:\n\n")

        if hot_loops:
            for loop in hot_loops:
                f.write(f"### {loop['module']}:{loop['line']}\n\n")
                f.write(f"```python\n{loop['loop_header']}\n```\n\n")
                f.write(f"- **Type:** {loop['loop_type']}\n")
                f.write(f"- **Iteration hint:** {loop['iteration_hint']}\n")
                f.write(f"- **Priority:** HIGH if in simulator/crystal hot path\n\n")
        else:
            f.write("*No obvious hot loops detected. Manual review recommended.*\n\n")

        f.write("## Next Steps\n\n")
        f.write("1. Cross-reference with profiler traces (Phase B1)\n")
        f.write("2. Mark loops for vectorization or document why they're safe\n")
        f.write("3. Update fix_plan.md with findings\n")

    print(f"Summary written to: {summary_path}")


def main():
    parser = argparse.ArgumentParser(
        description="AST-based loop inventory for vectorization gap analysis"
    )
    parser.add_argument(
        "--package",
        type=str,
        required=True,
        help="Package path to scan (e.g., src/nanobrag_torch)"
    )
    parser.add_argument(
        "--outdir",
        type=str,
        required=True,
        help="Output directory for results"
    )
    args = parser.parse_args()

    # Validate inputs
    package_path = Path(args.package)
    if not package_path.exists():
        print(f"ERROR: Package path does not exist: {package_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.outdir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Scanning package: {package_path}")
    print(f"Output directory: {output_dir}")
    print()

    # Scan for loops
    all_loops = scan_package(package_path)
    print(f"Found {len(all_loops)} total loops")

    # Filter hot loops
    hot_loops = filter_hot_loops(all_loops)
    print(f"Identified {len(hot_loops)} likely hot loops")

    # Save JSON inventory
    json_path = output_dir / "loop_inventory.json"
    with open(json_path, 'w', encoding='ascii', errors='replace') as f:
        json.dump({
            "scan_timestamp": datetime.utcnow().isoformat() + "Z",
            "package_path": str(package_path),
            "total_loops": len(all_loops),
            "hot_loops_count": len(hot_loops),
            "all_loops": all_loops,
            "hot_loops": hot_loops,
        }, f, indent=2, ensure_ascii=True)

    print(f"JSON inventory written to: {json_path}")

    # Generate summary markdown
    generate_summary(all_loops, hot_loops, output_dir)

    print()
    print("Inventory complete. Artifacts:")
    print(f"  - {json_path}")
    print(f"  - {output_dir / 'summary.md'}")
    print()
    print("Phase A1 complete. Proceed to Phase A2 execution.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
