#!/usr/bin/env python3
"""
Interactive Behavior Discovery Tools

These tools help discover hidden behaviors in legacy codebases through
systematic exploration and comparison. Designed to prevent the months-long
debugging cycles caused by undocumented parameter interactions.
"""

import os
import sys
import subprocess
import tempfile
import itertools
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Set
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import click
import pandas as pd
import hashlib


@dataclass
class ParameterCombination:
    """Represents a specific parameter combination for testing."""
    base_params: List[str]
    additional_params: List[str]
    expected_behavior: Optional[str] = None
    test_id: str = ""
    
    def __post_init__(self):
        if not self.test_id:
            # Generate unique ID from parameter combination
            param_str = " ".join(self.base_params + self.additional_params)
            self.test_id = hashlib.md5(param_str.encode()).hexdigest()[:8]
    
    def get_full_command(self, executable: str) -> List[str]:
        return [executable] + self.base_params + self.additional_params
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass  
class ExecutionResult:
    """Results from executing a parameter combination."""
    test_id: str
    command: List[str]
    return_code: int
    stdout: str
    stderr: str
    execution_time: float
    output_files: List[str] = None
    
    def __post_init__(self):
        if self.output_files is None:
            self.output_files = []
    
    def get_key_indicators(self) -> Dict[str, Any]:
        """Extract key indicators from output for comparison."""
        indicators = {}
        
        # Check for mode/convention messages
        stderr_lower = self.stderr.lower()
        for keyword in ['convention', 'mode', 'selected', 'using', 'detected']:
            if keyword in stderr_lower:
                # Extract lines containing these keywords
                lines = [line.strip() for line in self.stderr.split('\n') 
                        if keyword in line.lower()]
                indicators[f'{keyword}_messages'] = lines
        
        # Extract numerical indicators
        indicators['return_code'] = self.return_code
        indicators['stdout_lines'] = len(self.stdout.split('\n'))
        indicators['stderr_lines'] = len(self.stderr.split('\n'))
        
        return indicators
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BehaviorDiscoveryEngine:
    """Core engine for discovering hidden behaviors through systematic testing."""
    
    def __init__(self, executable_path: str, timeout: int = 30):
        self.executable_path = executable_path
        self.timeout = timeout
        self.results: List[ExecutionResult] = []
        
    def discover_parameter_effects(
        self, 
        base_params: List[str], 
        test_parameters: Dict[str, List[str]],
        max_combinations: int = 100
    ) -> Dict[str, List[ExecutionResult]]:
        """
        Systematically test parameter combinations to find hidden behaviors.
        
        Args:
            base_params: Basic parameters that work (baseline)
            test_parameters: Dict of parameter_name -> list_of_values to test
            max_combinations: Maximum number of combinations to test
        
        Returns:
            Dict mapping behavior_type -> list of results showing that behavior
        """
        
        print(f"🔍 Discovering parameter effects for {self.executable_path}")
        print(f"📋 Base parameters: {' '.join(base_params)}")
        print(f"🧪 Test parameters: {list(test_parameters.keys())}")
        
        # Generate parameter combinations
        combinations = self._generate_combinations(base_params, test_parameters, max_combinations)
        print(f"🎯 Testing {len(combinations)} parameter combinations...")
        
        # Execute all combinations
        results = self._execute_combinations(combinations)
        
        # Analyze for hidden behaviors
        behaviors = self._analyze_for_behaviors(results)
        
        return behaviors
    
    def compare_equivalent_specifications(
        self, 
        base_params: List[str],
        equivalent_variants: List[List[str]]
    ) -> Dict[str, Any]:
        """
        Test if different ways of specifying the same thing actually produce the same results.
        This catches the "explicit default parameter" hidden behavior bug.
        """
        
        print("🔄 Testing equivalent parameter specifications...")
        
        results = {}
        baseline_result = self._execute_single_combination(
            ParameterCombination(base_params, [])
        )
        results['baseline'] = baseline_result
        
        for i, variant in enumerate(equivalent_variants):
            print(f"   Testing variant {i+1}: {' '.join(variant)}")
            result = self._execute_single_combination(
                ParameterCombination(base_params, variant)
            )
            results[f'variant_{i+1}'] = result
        
        # Compare all variants to baseline
        differences = self._compare_results(baseline_result, list(results.values())[1:])
        
        return {
            'results': results,
            'differences': differences,
            'has_hidden_behavior': len(differences) > 0
        }
    
    def test_parameter_order_sensitivity(
        self, 
        base_params: List[str], 
        reorderable_params: List[str]
    ) -> Dict[str, Any]:
        """Test if parameter order affects results."""
        
        print("🔀 Testing parameter order sensitivity...")
        
        if len(reorderable_params) > 6:
            print(f"⚠️  Too many parameters to test all orders ({len(reorderable_params)}). Testing sample.")
            # Test original order and reverse order
            orders = [reorderable_params, reorderable_params[::-1]]
        else:
            # Test all permutations for smaller sets
            orders = list(itertools.permutations(reorderable_params))[:10]  # Limit to 10 permutations
        
        results = {}
        for i, order in enumerate(orders):
            print(f"   Testing order {i+1}: {' '.join(order)}")
            result = self._execute_single_combination(
                ParameterCombination(base_params, list(order))
            )
            results[f'order_{i+1}'] = result
        
        # Check if all results are identical
        first_result = list(results.values())[0]
        differences = self._compare_results(first_result, list(results.values())[1:])
        
        return {
            'results': results,
            'differences': differences,
            'is_order_sensitive': len(differences) > 0
        }
    
    def _generate_combinations(
        self, 
        base_params: List[str], 
        test_parameters: Dict[str, List[str]], 
        max_combinations: int
    ) -> List[ParameterCombination]:
        """Generate systematic parameter combinations."""
        
        combinations = []
        
        # Test each parameter individually first
        for param_name, values in test_parameters.items():
            for value in values[:3]:  # Limit to first 3 values per parameter
                additional = [f"-{param_name}"] + ([value] if value != "" else [])
                combo = ParameterCombination(
                    base_params=base_params,
                    additional_params=additional,
                    expected_behavior=f"single_param_{param_name}"
                )
                combinations.append(combo)
        
        # Test pairs of parameters
        param_names = list(test_parameters.keys())
        for param1, param2 in itertools.combinations(param_names[:5], 2):  # Limit combinations
            val1 = test_parameters[param1][0]  # Use first value
            val2 = test_parameters[param2][0]
            
            additional = [f"-{param1}"] + ([val1] if val1 != "" else []) + \
                        [f"-{param2}"] + ([val2] if val2 != "" else [])
            
            combo = ParameterCombination(
                base_params=base_params,
                additional_params=additional,
                expected_behavior=f"pair_{param1}_{param2}"
            )
            combinations.append(combo)
        
        # Limit total combinations
        return combinations[:max_combinations]
    
    def _execute_combinations(self, combinations: List[ParameterCombination]) -> List[ExecutionResult]:
        """Execute parameter combinations, potentially in parallel."""
        
        results = []
        
        # Use ThreadPoolExecutor for parallel execution
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_combo = {
                executor.submit(self._execute_single_combination, combo): combo
                for combo in combinations
            }
            
            for i, future in enumerate(as_completed(future_to_combo)):
                combo = future_to_combo[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(f"   ✅ Completed {i+1}/{len(combinations)}: {combo.test_id}")
                except Exception as e:
                    print(f"   ❌ Failed {combo.test_id}: {e}")
        
        return results
    
    def _execute_single_combination(self, combo: ParameterCombination) -> ExecutionResult:
        """Execute a single parameter combination."""
        
        cmd = combo.get_full_command(self.executable_path)
        
        import time
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=self.timeout
            )
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                test_id=combo.test_id,
                command=cmd,
                return_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=execution_time
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                test_id=combo.test_id,
                command=cmd,
                return_code=-1,
                stdout="",
                stderr=f"Timeout after {self.timeout} seconds",
                execution_time=self.timeout
            )
        
        except Exception as e:
            return ExecutionResult(
                test_id=combo.test_id,
                command=cmd,
                return_code=-999,
                stdout="",
                stderr=f"Execution error: {e}",
                execution_time=0.0
            )
    
    def _analyze_for_behaviors(self, results: List[ExecutionResult]) -> Dict[str, List[ExecutionResult]]:
        """Analyze results for patterns indicating hidden behaviors."""
        
        behaviors = {
            'mode_switches': [],
            'convention_changes': [],
            'error_patterns': [],
            'output_differences': [],
            'suspicious_stderr': []
        }
        
        for result in results:
            indicators = result.get_key_indicators()
            
            # Check for mode/convention switches
            if 'convention_messages' in indicators:
                behaviors['convention_changes'].append(result)
            if 'mode_messages' in indicators:
                behaviors['mode_switches'].append(result)
            
            # Check for errors
            if result.return_code != 0:
                behaviors['error_patterns'].append(result)
            
            # Check for suspicious stderr content
            suspicious_keywords = ['warning', 'switching', 'detected', 'using']
            if any(keyword in result.stderr.lower() for keyword in suspicious_keywords):
                behaviors['suspicious_stderr'].append(result)
        
        return behaviors
    
    def _compare_results(self, baseline: ExecutionResult, variants: List[ExecutionResult]) -> List[Dict[str, Any]]:
        """Compare results to find differences."""
        
        differences = []
        baseline_indicators = baseline.get_key_indicators()
        
        for variant in variants:
            variant_indicators = variant.get_key_indicators()
            
            diff = {}
            for key in set(baseline_indicators.keys()) | set(variant_indicators.keys()):
                baseline_val = baseline_indicators.get(key)
                variant_val = variant_indicators.get(key)
                
                if baseline_val != variant_val:
                    diff[key] = {
                        'baseline': baseline_val,
                        'variant': variant_val
                    }
            
            if diff:
                diff['variant_command'] = variant.command
                differences.append(diff)
        
        return differences


class InteractiveBehaviorExplorer:
    """Interactive CLI tool for exploring behaviors."""
    
    def __init__(self, executable_path: str):
        self.executable_path = executable_path
        self.engine = BehaviorDiscoveryEngine(executable_path)
        self.session_results = []
    
    def run_interactive_session(self):
        """Run an interactive behavior discovery session."""
        
        click.echo(click.style("🔍 Interactive Behavior Discovery Tool", fg='blue', bold=True))
        click.echo(f"Executable: {self.executable_path}")
        click.echo()
        
        while True:
            self._show_menu()
            choice = click.prompt("Select option", type=int, default=1)
            
            if choice == 1:
                self._test_equivalent_specifications()
            elif choice == 2:
                self._test_parameter_order()
            elif choice == 3:
                self._systematic_parameter_discovery()
            elif choice == 4:
                self._show_session_summary()
            elif choice == 5:
                self._export_results()
            elif choice == 6:
                break
            else:
                click.echo("Invalid choice. Please try again.")
    
    def _show_menu(self):
        """Display the interactive menu."""
        click.echo(click.style("Behavior Discovery Options:", fg='green', bold=True))
        click.echo("1. Test equivalent parameter specifications (catches hidden triggers)")
        click.echo("2. Test parameter order sensitivity")  
        click.echo("3. Systematic parameter discovery")
        click.echo("4. Show session summary")
        click.echo("5. Export results to file")
        click.echo("6. Exit")
        click.echo()
    
    def _test_equivalent_specifications(self):
        """Interactive equivalent specifications test."""
        click.echo(click.style("\n📋 Testing Equivalent Parameter Specifications", fg='blue', bold=True))
        
        base_params = click.prompt("Enter base parameters (space-separated)").split()
        
        click.echo("\nEnter equivalent parameter variants (one per line, empty line to finish):")
        variants = []
        while True:
            variant = click.prompt("Variant", default="", show_default=False)
            if not variant:
                break
            variants.append(variant.split())
        
        if not variants:
            click.echo("No variants specified. Skipping test.")
            return
        
        # Run the test
        results = self.engine.compare_equivalent_specifications(base_params, variants)
        
        # Display results
        if results['has_hidden_behavior']:
            click.echo(click.style("🚨 HIDDEN BEHAVIOR DETECTED!", fg='red', bold=True))
            for diff in results['differences']:
                click.echo(f"   Command: {' '.join(diff['variant_command'])}")
                for key, values in diff.items():
                    if key != 'variant_command':
                        click.echo(f"     {key}: {values['baseline']} → {values['variant']}")
        else:
            click.echo(click.style("✅ No hidden behaviors detected", fg='green'))
        
        self.session_results.append(('equivalent_specs', results))
    
    def _test_parameter_order(self):
        """Interactive parameter order test."""
        click.echo(click.style("\n🔀 Testing Parameter Order Sensitivity", fg='blue', bold=True))
        
        base_params = click.prompt("Enter base parameters (space-separated)").split()
        reorderable = click.prompt("Enter reorderable parameters (space-separated)").split()
        
        results = self.engine.test_parameter_order_sensitivity(base_params, reorderable)
        
        if results['is_order_sensitive']:
            click.echo(click.style("⚠️ PARAMETER ORDER AFFECTS RESULTS!", fg='yellow', bold=True))
            for diff in results['differences']:
                click.echo(f"   Different behavior detected")
        else:
            click.echo(click.style("✅ Parameter order doesn't affect results", fg='green'))
        
        self.session_results.append(('parameter_order', results))
    
    def _systematic_parameter_discovery(self):
        """Interactive systematic parameter discovery."""
        click.echo(click.style("\n🧪 Systematic Parameter Discovery", fg='blue', bold=True))
        
        base_params = click.prompt("Enter base parameters (space-separated)").split()
        
        click.echo("\nEnter test parameters (format: param_name:value1,value2,value3):")
        test_parameters = {}
        while True:
            param_spec = click.prompt("Parameter spec", default="", show_default=False)
            if not param_spec:
                break
            
            try:
                param_name, values_str = param_spec.split(':')
                values = [v.strip() for v in values_str.split(',')]
                test_parameters[param_name] = values
            except ValueError:
                click.echo("Invalid format. Use param_name:value1,value2,value3")
        
        if not test_parameters:
            click.echo("No test parameters specified. Skipping.")
            return
        
        max_combinations = click.prompt("Maximum combinations to test", type=int, default=50)
        
        # Run discovery
        results = self.engine.discover_parameter_effects(base_params, test_parameters, max_combinations)
        
        # Display summary
        for behavior_type, behavior_results in results.items():
            if behavior_results:
                click.echo(f"   {behavior_type}: {len(behavior_results)} instances")
        
        self.session_results.append(('systematic_discovery', results))
    
    def _show_session_summary(self):
        """Show summary of session findings."""
        click.echo(click.style("\n📊 Session Summary", fg='blue', bold=True))
        
        if not self.session_results:
            click.echo("No tests run yet.")
            return
        
        for i, (test_type, results) in enumerate(self.session_results, 1):
            click.echo(f"{i}. {test_type}:")
            if test_type == 'equivalent_specs':
                status = "🚨 HIDDEN BEHAVIOR" if results['has_hidden_behavior'] else "✅ No issues"
                click.echo(f"   Status: {status}")
            elif test_type == 'parameter_order':
                status = "⚠️  ORDER SENSITIVE" if results['is_order_sensitive'] else "✅ Order independent"  
                click.echo(f"   Status: {status}")
            elif test_type == 'systematic_discovery':
                total_behaviors = sum(len(behavior_list) for behavior_list in results.values())
                click.echo(f"   Behaviors found: {total_behaviors}")
    
    def _export_results(self):
        """Export results to file."""
        if not self.session_results:
            click.echo("No results to export.")
            return
        
        filename = click.prompt("Export filename", default="behavior_discovery_results.json")
        
        export_data = {
            'executable': self.executable_path,
            'session_results': []
        }
        
        for test_type, results in self.session_results:
            # Convert results to serializable format
            serializable_results = self._make_serializable(results)
            export_data['session_results'].append({
                'test_type': test_type,
                'results': serializable_results
            })
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        click.echo(f"Results exported to {filename}")
    
    def _make_serializable(self, obj):
        """Convert results to JSON-serializable format."""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        else:
            return obj


# CLI Commands

@click.group()
def behavior_discovery():
    """Tools for discovering hidden behaviors in executables."""
    pass


@behavior_discovery.command()
@click.argument('executable_path')
@click.option('--base-params', help='Base parameters that work (space-separated)')
@click.option('--test-params', help='Test parameters as param1:val1,val2 param2:val3,val4')
def discover(executable_path, base_params, test_params):
    """Run systematic parameter discovery."""
    
    base = base_params.split() if base_params else []
    
    # Parse test parameters
    test_parameters = {}
    if test_params:
        for param_spec in test_params.split():
            param_name, values_str = param_spec.split(':')
            values = values_str.split(',')
            test_parameters[param_name] = values
    
    engine = BehaviorDiscoveryEngine(executable_path)
    results = engine.discover_parameter_effects(base, test_parameters)
    
    click.echo("Discovery Results:")
    for behavior_type, behavior_results in results.items():
        if behavior_results:
            click.echo(f"  {behavior_type}: {len(behavior_results)} instances")


@behavior_discovery.command()
@click.argument('executable_path')
def interactive(executable_path):
    """Run interactive behavior discovery session."""
    
    if not Path(executable_path).exists():
        click.echo(f"Error: Executable not found: {executable_path}")
        return
    
    explorer = InteractiveBehaviorExplorer(executable_path)
    explorer.run_interactive_session()


@behavior_discovery.command()
@click.argument('executable_path')
@click.argument('base_params')
@click.argument('variants', nargs=-1)
def test_equivalent(executable_path, base_params, variants):
    """Test if equivalent parameter specifications produce identical results."""
    
    base = base_params.split()
    variant_lists = [variant.split() for variant in variants]
    
    engine = BehaviorDiscoveryEngine(executable_path)
    results = engine.compare_equivalent_specifications(base, variant_lists)
    
    if results['has_hidden_behavior']:
        click.echo(click.style("🚨 HIDDEN BEHAVIOR DETECTED!", fg='red', bold=True))
        click.echo("This executable has parameter side effects that change behavior.")
        sys.exit(1)
    else:
        click.echo(click.style("✅ No hidden behaviors detected", fg='green'))


if __name__ == "__main__":
    behavior_discovery()


# Example usage:
"""
# Interactive exploration
python behavior_discovery_tools.py interactive ./nanoBragg

# Test specific equivalent specifications
python behavior_discovery_tools.py test-equivalent ./nanoBragg "-distance 100 -twotheta 20" "-distance 100 -twotheta 20 -twotheta_axis 0 0 -1"

# Systematic discovery
python behavior_discovery_tools.py discover ./nanoBragg --base-params "-distance 100" --test-params "twotheta:0,10,20 pivot:beam,sample"
"""