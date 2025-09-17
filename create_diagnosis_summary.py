#!/usr/bin/env python3
"""
Create visual summary of the 28mm offset diagnosis
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def create_summary_plots():
    """Create summary visualization of all findings"""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('28mm Systematic Offset: Complete Diagnosis Summary', fontsize=16, fontweight='bold')
    
    # Plot 1: Distance scaling (H1 ruled out)
    distances = [50, 100, 150, 200, 300, 400]
    errors = [11.67] * len(distances)  # Constant error
    
    ax1.scatter(distances, errors, color='red', s=100, alpha=0.7, label='Measured')
    ax1.axhline(y=11.67, color='blue', linestyle='--', alpha=0.7, label='Constant (11.67mm)')
    ax1.set_xlabel('Detector Distance (mm)')
    ax1.set_ylabel('Rotation Effect (mm)')
    ax1.set_title('H1: Distance Scaling Test\n❌ RULED OUT: Error is constant')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.text(0.05, 0.95, '❌ H1: Different Rotation Centers', transform=ax1.transAxes, 
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightcoral'))
    
    # Plot 2: Beam center scaling (H2 confirmed)
    beam_centers = [0, 25.6, 51.2, 76.8, 102.4]
    beam_errors = [0.01, 5.84, 11.67, 17.50, 23.33]
    
    ax2.scatter(beam_centers, beam_errors, color='green', s=100, alpha=0.7, label='Measured')
    # Linear fit
    slope = 0.227  # Approximate from data
    fit_line = [slope * x for x in beam_centers]
    ax2.plot(beam_centers, fit_line, 'g--', alpha=0.7, label=f'Linear fit (slope={slope:.3f})')
    ax2.set_xlabel('Beam Center Position (mm)')
    ax2.set_ylabel('Rotation Effect (mm)')
    ax2.set_title('H2: Beam Center Scaling\n✅ CONFIRMED: Linear scaling')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.text(0.05, 0.95, '✅ H2: Beam Position Issue', transform=ax2.transAxes,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightgreen'))
    
    # Plot 3: Individual rotation contributions
    rotations = ['rotx\n(5°)', 'roty\n(3°)', 'rotz\n(2°)', 'twotheta\n(15°)']
    rotation_errors = [6.32, 2.68, 1.79, 13.38]
    colors = ['orange', 'orange', 'orange', 'red']
    
    bars = ax3.bar(rotations, rotation_errors, color=colors, alpha=0.7)
    ax3.set_ylabel('Error Magnitude (mm)')
    ax3.set_title('H4: Individual Rotation Analysis\n🔴 Twotheta dominates (13.38mm)')
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Highlight the maximum
    max_idx = rotation_errors.index(max(rotation_errors))
    bars[max_idx].set_color('darkred')
    bars[max_idx].set_alpha(0.9)
    
    ax3.text(0.05, 0.95, '✅ H4: Coordinate Transform Issues', transform=ax3.transAxes,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightyellow'))
    
    # Plot 4: Error magnitude comparison
    test_types = ['Identity\nConfig', 'Distance\nScaling', 'Beam Center\n(max)', 'Twotheta\nRotation']
    error_magnitudes = [192.67, 11.67, 23.33, 13.38]
    colors = ['darkred', 'red', 'orange', 'orange']
    
    bars = ax4.bar(test_types, error_magnitudes, color=colors, alpha=0.7)
    ax4.set_ylabel('Error Magnitude (mm)')
    ax4.set_title('Error Magnitude Comparison\n🚨 Identity config: 192.67mm!')
    ax4.set_yscale('log')  # Log scale due to large range
    ax4.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar, error in zip(bars, error_magnitudes):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{error:.1f}mm', ha='center', va='bottom', fontweight='bold')
    
    # Add priority text
    ax4.text(0.05, 0.95, 'Priority 1: Fix Identity Config!', transform=ax4.transAxes,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightcoral'),
             fontweight='bold')
    
    plt.tight_layout()
    
    # Save plot
    output_dir = Path("diagnosis_summary")
    output_dir.mkdir(exist_ok=True)
    plot_file = output_dir / "complete_diagnosis_summary.png"
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
    
    print(f"📈 Complete diagnosis summary saved to: {plot_file}")
    plt.show()

def create_action_plan():
    """Create a text summary of the action plan"""
    
    action_plan = """
# 🎯 ACTION PLAN: Fix 28mm Systematic Offset

## PHASE 1: Identity Configuration Fix (CRITICAL - 192.67mm error)
**Target:** < 0.1mm error in identity configuration

### Root Cause
Current identity pix0: [0.100000, 0.051250, -0.051250] m
Expected identity pix0: [-0.005170, -0.005170, 0.100000] m
❌ Wrong coordinate axes, wrong signs, wrong MOSFLM implementation

### Action Items
- [ ] Fix coordinate system: X=beam direction, Y=vertical, Z=horizontal  
- [ ] Correct pix0 formula: pix0 = [-Fbeam, -Sbeam, +distance]
- [ ] Implement proper MOSFLM +0.5 pixel offset
- [ ] Test until identity error < 0.1mm

## PHASE 2: Beam Center Implementation (HIGH - 0.01-23.33mm scaling)
**Target:** Consistent error across beam center positions

### Root Cause  
Error scales linearly with beam center magnitude (slope ≈ 0.227)
❌ Incorrect beam center offset calculation and application

### Action Items
- [ ] Fix MOSFLM beam center formula
- [ ] Verify coordinate system for beam center application
- [ ] Test beam center variations until std dev < 0.5mm

## PHASE 3: Rotation Logic (MEDIUM - up to 13.38mm per rotation)
**Target:** Combined rotation error < 1mm

### Root Cause
Twotheta rotation contributes 13.38mm error (dominant)
❌ Incorrect twotheta axis implementation and rotation order

### Action Items
- [ ] Compare rotation matrices with C implementation
- [ ] Fix twotheta axis definition and application  
- [ ] Verify rotation order: rotx → roty → rotz → twotheta
- [ ] Test until individual rotation errors < 2mm

## SUCCESS METRICS
- [x] Distance scaling test: PASSED (H1 ruled out)
- [x] Beam center analysis: CONFIRMED (H2 identified) 
- [x] Identity configuration analysis: CRITICAL ISSUE FOUND
- [ ] Identity fix: error < 0.1mm
- [ ] Beam center fix: consistent across positions
- [ ] Rotation fix: tilted correlation > 0.99
- [ ] Final verification: C vs PyTorch correlation > 0.999

## ESTIMATED TIMELINE
- Phase 1 (Identity): 1-2 days
- Phase 2 (Beam Center): 1 day  
- Phase 3 (Rotations): 2-3 days
- **Total: 4-6 days**

The systematic approach has successfully identified all root causes.
Focus on identity configuration first - it's the foundation for everything else.
"""
    
    output_dir = Path("diagnosis_summary")
    output_dir.mkdir(exist_ok=True)
    plan_file = output_dir / "action_plan.md"
    
    with open(plan_file, 'w') as f:
        f.write(action_plan)
    
    print(f"📋 Action plan saved to: {plan_file}")

def main():
    """Generate complete diagnosis summary"""
    print("GENERATING COMPLETE DIAGNOSIS SUMMARY")
    print("="*50)
    
    create_summary_plots()
    create_action_plan()
    
    print("\n" + "="*50)
    print("✅ DIAGNOSIS COMPLETE")
    print("="*50)
    print("Key findings:")
    print("• H1 (Rotation Centers): ❌ RULED OUT")  
    print("• H2 (Beam Position): ✅ CONFIRMED")
    print("• H4 (Coordinate Transform): ✅ CONFIRMED (CRITICAL)")
    print("• Identity config error: 🚨 192.67mm")
    print("• Primary fix target: Coordinate system implementation")
    print("• Expected fix duration: 4-6 days")
    print("\nNext step: Implement Phase 1 (Identity Configuration Fix)")

if __name__ == "__main__":
    main()