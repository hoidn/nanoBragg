#!/usr/bin/env python3
"""
Check the scaling applied in SMV files vs float binary files.
"""

import numpy as np
import sys
sys.path.append('scripts')
from smv_parser import parse_smv_image

def main():
    """Check the scaling difference."""
    print("🔍 Checking scaling difference between floatimage.bin and intimage.img")

    # Read raw float data
    if os.path.exists("floatimage.bin"):
        float_data = np.fromfile("floatimage.bin", dtype=np.float32).reshape(64, 64)
        print(f"floatimage.bin max: {float_data.max():.6e}")
        print(f"floatimage.bin at [34,34]: {float_data[34,34]:.6e}")
        print(f"floatimage.bin at [33,33]: {float_data[33,33]:.6e}")
        print(f"floatimage.bin at [32,32]: {float_data[32,32]:.6e}")

    # Read SMV integer data
    if os.path.exists("intimage.img"):
        smv_data, header = parse_smv_image("intimage.img")
        print(f"\nintimage.img max: {smv_data.max():.6e}")
        print(f"intimage.img at [34,34]: {smv_data[34,34]:.6e}")
        print(f"intimage.img at [33,33]: {smv_data[33,33]:.6e}")
        print(f"intimage.img at [32,32]: {smv_data[32,32]:.6e}")

        print(f"\nSMV header: {header}")

        # Calculate scale factor
        if os.path.exists("floatimage.bin"):
            scale_factor = smv_data[32,32] / float_data[32,32]
            print(f"\nScale factor (SMV/float): {scale_factor:.2e}")

if __name__ == "__main__":
    import os
    main()