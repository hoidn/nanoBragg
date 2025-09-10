#!/usr/bin/env python3
"""
Hypothesis Testing Framework for 28mm Systematic Offset

This script provides a comprehensive framework for testing all 6 hypotheses
about the 28mm systematic offset in detector geometry calculations.
"""

import os
import json
import numpy as np
import torch
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import subprocess
import matplotlib.pyplot as plt
from datetime import datetime

# Set environment variable for PyTorch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

@dataclass
class TestConfiguration:
    """Configuration for a single hypothesis test"""
    hypothesis_id: int
    hypothesis_name: str
    test_name: str
    detector_distance_mm: float
    detector_rotx_deg: float
    detector_roty_deg: float
    detector_rotz_deg: float
    detector_twotheta_deg: float
    beam_center_s_mm: float
    beam_center_f_mm: float
    pixel_size_mm: float
    detector_pixels: int
    pivot_mode: str
    
    def to_dict(self):
        return asdict(self)

@dataclass
class TestResult:
    """Result from a single hypothesis test"""
    configuration: TestConfiguration
    correlation: float
    error_magnitude_mm: float
    error_magnitude_pixels: float
    error_vector_mm: List[float]  # [x, y, z]
    pix0_vector_c: List[float]
    pix0_vector_pytorch: List[float]
    execution_time: float
    notes: str
    
    def to_dict(self):
        result = asdict(self)
        result['configuration'] = self.configuration.to_dict()
        return result

class HypothesisTestFramework:
    """Framework for systematic hypothesis testing"""
    
    def __init__(self, output_dir: str = "hypothesis_test_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = []
        
    def create_test_configurations(self) -> List[TestConfiguration]:
        """Create all test configurations for hypothesis testing"""
        configs = []
        
        # Hypothesis 1: Different Rotation Centers
        # Test with different distances to see if error scales
        for distance in [50, 100, 200, 400]:
            configs.append(TestConfiguration(
                hypothesis_id=1,
                hypothesis_name="Different Rotation Centers",
                test_name=f"distance_{distance}mm",
                detector_distance_mm=distance,
                detector_rotx_deg=5.0,
                detector_roty_deg=3.0,
                detector_rotz_deg=2.0,
                detector_twotheta_deg=15.0,
                beam_center_s_mm=51.2,
                beam_center_f_mm=51.2,
                pixel_size_mm=0.1,
                detector_pixels=1024,
                pivot_mode="SAMPLE"
            ))
        
        # Test with different rotation angles
        for rotx, roty, rotz in [(0,0,0), (5,0,0), (0,5,0), (0,0,5), (10,10,10)]:
            configs.append(TestConfiguration(
                hypothesis_id=1,
                hypothesis_name="Different Rotation Centers",
                test_name=f"rot_{rotx}_{roty}_{rotz}",
                detector_distance_mm=100,
                detector_rotx_deg=rotx,
                detector_roty_deg=roty,
                detector_rotz_deg=rotz,
                detector_twotheta_deg=15.0,
                beam_center_s_mm=51.2,
                beam_center_f_mm=51.2,
                pixel_size_mm=0.1,
                detector_pixels=1024,
                pivot_mode="SAMPLE"
            ))
        
        # Hypothesis 2: Beam Position Interpretation
        # Test with different beam centers
        for beam_s, beam_f in [(0,0), (25.6,25.6), (51.2,51.2), (76.8,76.8)]:
            configs.append(TestConfiguration(
                hypothesis_id=2,
                hypothesis_name="Beam Position Interpretation",
                test_name=f"beam_{beam_s}_{beam_f}",
                detector_distance_mm=100,
                detector_rotx_deg=5.0,
                detector_roty_deg=3.0,
                detector_rotz_deg=2.0,
                detector_twotheta_deg=15.0,
                beam_center_s_mm=beam_s,
                beam_center_f_mm=beam_f,
                pixel_size_mm=0.1,
                detector_pixels=1024,
                pivot_mode="SAMPLE"
            ))
        
        # Test with different pixel sizes
        for pixel_size in [0.05, 0.1, 0.2]:
            configs.append(TestConfiguration(
                hypothesis_id=2,
                hypothesis_name="Beam Position Interpretation",
                test_name=f"pixel_size_{pixel_size}mm",
                detector_distance_mm=100,
                detector_rotx_deg=5.0,
                detector_roty_deg=3.0,
                detector_rotz_deg=2.0,
                detector_twotheta_deg=15.0,
                beam_center_s_mm=51.2,
                beam_center_f_mm=51.2,
                pixel_size_mm=pixel_size,
                detector_pixels=1024,
                pivot_mode="SAMPLE"
            ))
        
        # Hypothesis 3: Distance Definition Mismatch
        # Already covered by H1 distance tests
        
        # Hypothesis 4: Missing Coordinate Transformation
        # Test identity configuration
        configs.append(TestConfiguration(
            hypothesis_id=4,
            hypothesis_name="Missing Coordinate Transformation",
            test_name="identity",
            detector_distance_mm=100,
            detector_rotx_deg=0.0,
            detector_roty_deg=0.0,
            detector_rotz_deg=0.0,
            detector_twotheta_deg=0.0,
            beam_center_s_mm=51.2,
            beam_center_f_mm=51.2,
            pixel_size_mm=0.1,
            detector_pixels=1024,
            pivot_mode="BEAM"
        ))
        
        # Test BEAM vs SAMPLE pivot
        for pivot in ["BEAM", "SAMPLE"]:
            configs.append(TestConfiguration(
                hypothesis_id=4,
                hypothesis_name="Missing Coordinate Transformation",
                test_name=f"pivot_{pivot}",
                detector_distance_mm=100,
                detector_rotx_deg=5.0,
                detector_roty_deg=3.0,
                detector_rotz_deg=2.0,
                detector_twotheta_deg=15.0,
                beam_center_s_mm=51.2,
                beam_center_f_mm=51.2,
                pixel_size_mm=0.1,
                detector_pixels=1024,
                pivot_mode=pivot
            ))
        
        # Hypothesis 5: Detector Thickness/Parallax
        # Test with different incident angles (via rotations)
        for angle in [0, 15, 30, 45]:
            configs.append(TestConfiguration(
                hypothesis_id=5,
                hypothesis_name="Detector Thickness/Parallax",
                test_name=f"incident_angle_{angle}",
                detector_distance_mm=100,
                detector_rotx_deg=angle,
                detector_roty_deg=0.0,
                detector_rotz_deg=0.0,
                detector_twotheta_deg=0.0,
                beam_center_s_mm=51.2,
                beam_center_f_mm=51.2,
                pixel_size_mm=0.1,
                detector_pixels=1024,
                pivot_mode="BEAM"
            ))
        
        # Hypothesis 6: Integer vs Fractional Pixel
        # Test with different detector sizes
        for det_size in [512, 1024, 2048]:
            configs.append(TestConfiguration(
                hypothesis_id=6,
                hypothesis_name="Integer vs Fractional Pixel",
                test_name=f"detector_size_{det_size}",
                detector_distance_mm=100,
                detector_rotx_deg=5.0,
                detector_roty_deg=3.0,
                detector_rotz_deg=2.0,
                detector_twotheta_deg=15.0,
                beam_center_s_mm=51.2,
                beam_center_f_mm=51.2,
                pixel_size_mm=0.1,
                detector_pixels=det_size,
                pivot_mode="SAMPLE"
            ))
        
        # Test integer vs fractional beam centers
        for beam_val in [51.0, 51.2, 51.5, 51.7]:
            configs.append(TestConfiguration(
                hypothesis_id=6,
                hypothesis_name="Integer vs Fractional Pixel",
                test_name=f"beam_fraction_{beam_val}",
                detector_distance_mm=100,
                detector_rotx_deg=5.0,
                detector_roty_deg=3.0,
                detector_rotz_deg=2.0,
                detector_twotheta_deg=15.0,
                beam_center_s_mm=beam_val,
                beam_center_f_mm=beam_val,
                pixel_size_mm=0.1,
                detector_pixels=1024,
                pivot_mode="SAMPLE"
            ))
        
        return configs
    
    def run_single_test(self, config: TestConfiguration) -> TestResult:
        """Run a single hypothesis test"""
        import time
        start_time = time.time()
        
        # Run verify_detector_geometry.py with the configuration
        cmd = [
            "python", "scripts/verify_detector_geometry.py",
            "--distance", str(config.detector_distance_mm),
            "--rotx", str(config.detector_rotx_deg),
            "--roty", str(config.detector_roty_deg),
            "--rotz", str(config.detector_rotz_deg),
            "--twotheta", str(config.detector_twotheta_deg),
            "--beam", str(config.beam_center_s_mm), str(config.beam_center_f_mm),
            "--pixel_size", str(config.pixel_size_mm),
            "--detector_pixels", str(config.detector_pixels),
            "--pivot", config.pivot_mode.lower(),
            "--output", str(self.output_dir / f"test_{config.hypothesis_id}_{config.test_name}.json")
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse the output to extract metrics
            output_file = self.output_dir / f"test_{config.hypothesis_id}_{config.test_name}.json"
            if output_file.exists():
                with open(output_file, 'r') as f:
                    data = json.load(f)
                
                # Extract key metrics
                correlation = data.get('correlation', 0.0)
                pix0_c = data.get('pix0_vector_c', [0, 0, 0])
                pix0_py = data.get('pix0_vector_pytorch', [0, 0, 0])
                
                # Calculate error
                error_vector = [pix0_py[i] - pix0_c[i] for i in range(3)]
                error_magnitude = np.linalg.norm(error_vector) * 1000  # Convert to mm
                error_pixels = error_magnitude / config.pixel_size_mm
                
                return TestResult(
                    configuration=config,
                    correlation=correlation,
                    error_magnitude_mm=error_magnitude,
                    error_magnitude_pixels=error_pixels,
                    error_vector_mm=[e * 1000 for e in error_vector],
                    pix0_vector_c=pix0_c,
                    pix0_vector_pytorch=pix0_py,
                    execution_time=time.time() - start_time,
                    notes="Test completed successfully"
                )
            else:
                raise FileNotFoundError(f"Output file not created: {output_file}")
                
        except Exception as e:
            # Return error result
            return TestResult(
                configuration=config,
                correlation=0.0,
                error_magnitude_mm=0.0,
                error_magnitude_pixels=0.0,
                error_vector_mm=[0, 0, 0],
                pix0_vector_c=[0, 0, 0],
                pix0_vector_pytorch=[0, 0, 0],
                execution_time=time.time() - start_time,
                notes=f"Error: {str(e)}"
            )
    
    def run_all_tests(self, configs: Optional[List[TestConfiguration]] = None):
        """Run all hypothesis tests"""
        if configs is None:
            configs = self.create_test_configurations()
        
        print(f"Running {len(configs)} hypothesis tests...")
        print("=" * 60)
        
        for i, config in enumerate(configs, 1):
            print(f"\n[{i}/{len(configs)}] Testing Hypothesis {config.hypothesis_id}: {config.hypothesis_name}")
            print(f"  Test: {config.test_name}")
            
            result = self.run_single_test(config)
            self.results.append(result)
            
            print(f"  Correlation: {result.correlation:.4f}")
            print(f"  Error: {result.error_magnitude_mm:.2f}mm ({result.error_magnitude_pixels:.1f} pixels)")
            print(f"  Error vector: [{result.error_vector_mm[0]:.2f}, {result.error_vector_mm[1]:.2f}, {result.error_vector_mm[2]:.2f}] mm")
            
            # Save intermediate results
            self.save_results()
    
    def analyze_hypothesis(self, hypothesis_id: int) -> Dict:
        """Analyze results for a specific hypothesis"""
        h_results = [r for r in self.results if r.configuration.hypothesis_id == hypothesis_id]
        
        if not h_results:
            return {"error": "No results for this hypothesis"}
        
        analysis = {
            "hypothesis_id": hypothesis_id,
            "hypothesis_name": h_results[0].configuration.hypothesis_name,
            "num_tests": len(h_results),
            "correlations": [r.correlation for r in h_results],
            "error_magnitudes_mm": [r.error_magnitude_mm for r in h_results],
            "error_magnitudes_pixels": [r.error_magnitude_pixels for r in h_results],
            "mean_correlation": np.mean([r.correlation for r in h_results]),
            "mean_error_mm": np.mean([r.error_magnitude_mm for r in h_results]),
            "std_error_mm": np.std([r.error_magnitude_mm for r in h_results]),
            "tests": []
        }
        
        # Add individual test details
        for result in h_results:
            analysis["tests"].append({
                "test_name": result.configuration.test_name,
                "correlation": result.correlation,
                "error_mm": result.error_magnitude_mm,
                "error_vector_mm": result.error_vector_mm
            })
        
        return analysis
    
    def plot_results(self):
        """Create visualization plots for hypothesis testing"""
        if not self.results:
            print("No results to plot")
            return
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle("Hypothesis Testing Results", fontsize=16)
        
        for h_id in range(1, 7):
            ax = axes[(h_id-1)//3, (h_id-1)%3]
            h_results = [r for r in self.results if r.configuration.hypothesis_id == h_id]
            
            if h_results:
                # Plot error magnitude for each test
                test_names = [r.configuration.test_name for r in h_results]
                errors = [r.error_magnitude_mm for r in h_results]
                
                ax.bar(range(len(test_names)), errors)
                ax.set_title(f"H{h_id}: {h_results[0].configuration.hypothesis_name}")
                ax.set_ylabel("Error (mm)")
                ax.set_xticks(range(len(test_names)))
                ax.set_xticklabels(test_names, rotation=45, ha='right')
                ax.axhline(y=28, color='r', linestyle='--', label='28mm target')
                ax.legend()
        
        plt.tight_layout()
        plt.savefig(self.output_dir / "hypothesis_results.png", dpi=150)
        plt.show()
    
    def save_results(self):
        """Save all results to JSON file"""
        results_file = self.output_dir / "hypothesis_test_results.json"
        
        # Convert results to dictionary format
        results_dict = {
            "timestamp": datetime.now().isoformat(),
            "num_tests": len(self.results),
            "results": [r.to_dict() for r in self.results],
            "summary": {}
        }
        
        # Add analysis for each hypothesis
        for h_id in range(1, 7):
            results_dict["summary"][f"hypothesis_{h_id}"] = self.analyze_hypothesis(h_id)
        
        with open(results_file, 'w') as f:
            json.dump(results_dict, f, indent=2)
        
        print(f"\nResults saved to {results_file}")
    
    def generate_report(self):
        """Generate markdown report of hypothesis testing"""
        report_file = self.output_dir / "HYPOTHESIS_TEST_REPORT.md"
        
        with open(report_file, 'w') as f:
            f.write("# Hypothesis Testing Report\n\n")
            f.write(f"**Generated**: {datetime.now().isoformat()}\n")
            f.write(f"**Total Tests**: {len(self.results)}\n\n")
            
            # Summary table
            f.write("## Summary\n\n")
            f.write("| Hypothesis | Tests | Mean Correlation | Mean Error (mm) | Std Error (mm) |\n")
            f.write("|------------|-------|-----------------|-----------------|----------------|\n")
            
            for h_id in range(1, 7):
                analysis = self.analyze_hypothesis(h_id)
                if "error" not in analysis:
                    f.write(f"| H{h_id}: {analysis['hypothesis_name'][:30]} | ")
                    f.write(f"{analysis['num_tests']} | ")
                    f.write(f"{analysis['mean_correlation']:.4f} | ")
                    f.write(f"{analysis['mean_error_mm']:.2f} | ")
                    f.write(f"{analysis['std_error_mm']:.2f} |\n")
            
            # Detailed results for each hypothesis
            f.write("\n## Detailed Results\n\n")
            
            for h_id in range(1, 7):
                analysis = self.analyze_hypothesis(h_id)
                if "error" not in analysis:
                    f.write(f"### Hypothesis {h_id}: {analysis['hypothesis_name']}\n\n")
                    f.write(f"**Number of tests**: {analysis['num_tests']}\n")
                    f.write(f"**Mean correlation**: {analysis['mean_correlation']:.4f}\n")
                    f.write(f"**Mean error**: {analysis['mean_error_mm']:.2f}mm\n\n")
                    
                    f.write("| Test | Correlation | Error (mm) | Error Vector (mm) |\n")
                    f.write("|------|-------------|------------|-------------------|\n")
                    
                    for test in analysis['tests']:
                        f.write(f"| {test['test_name']} | ")
                        f.write(f"{test['correlation']:.4f} | ")
                        f.write(f"{test['error_mm']:.2f} | ")
                        f.write(f"[{test['error_vector_mm'][0]:.1f}, ")
                        f.write(f"{test['error_vector_mm'][1]:.1f}, ")
                        f.write(f"{test['error_vector_mm'][2]:.1f}] |\n")
                    
                    f.write("\n")
            
            # Conclusions
            f.write("## Conclusions\n\n")
            f.write("Based on the test results:\n\n")
            
            # Find hypothesis with error closest to 28mm
            best_match = None
            best_diff = float('inf')
            
            for h_id in range(1, 7):
                analysis = self.analyze_hypothesis(h_id)
                if "error" not in analysis:
                    diff = abs(analysis['mean_error_mm'] - 28.0)
                    if diff < best_diff:
                        best_diff = diff
                        best_match = (h_id, analysis['hypothesis_name'])
            
            if best_match:
                f.write(f"- **Most likely hypothesis**: H{best_match[0]} - {best_match[1]}\n")
                f.write(f"- **Error difference from 28mm**: {best_diff:.2f}mm\n")
        
        print(f"Report generated: {report_file}")

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test hypotheses for 28mm systematic offset")
    parser.add_argument("--hypothesis", type=int, help="Test specific hypothesis (1-6)")
    parser.add_argument("--output", default="hypothesis_test_results", help="Output directory")
    parser.add_argument("--plot", action="store_true", help="Generate plots")
    parser.add_argument("--report", action="store_true", help="Generate report only")
    
    args = parser.parse_args()
    
    framework = HypothesisTestFramework(args.output)
    
    if args.report:
        # Load existing results and generate report
        results_file = Path(args.output) / "hypothesis_test_results.json"
        if results_file.exists():
            with open(results_file, 'r') as f:
                data = json.load(f)
            # Reconstruct results
            for r in data['results']:
                config = TestConfiguration(**r['configuration'])
                result = TestResult(
                    configuration=config,
                    correlation=r['correlation'],
                    error_magnitude_mm=r['error_magnitude_mm'],
                    error_magnitude_pixels=r['error_magnitude_pixels'],
                    error_vector_mm=r['error_vector_mm'],
                    pix0_vector_c=r['pix0_vector_c'],
                    pix0_vector_pytorch=r['pix0_vector_pytorch'],
                    execution_time=r['execution_time'],
                    notes=r['notes']
                )
                framework.results.append(result)
            framework.generate_report()
            if args.plot:
                framework.plot_results()
        else:
            print(f"No results found in {args.output}")
    else:
        # Run tests
        if args.hypothesis:
            # Test specific hypothesis
            configs = [c for c in framework.create_test_configurations() 
                      if c.hypothesis_id == args.hypothesis]
            if not configs:
                print(f"No tests defined for hypothesis {args.hypothesis}")
                return
        else:
            configs = None
        
        framework.run_all_tests(configs)
        framework.generate_report()
        
        if args.plot:
            framework.plot_results()

if __name__ == "__main__":
    main()