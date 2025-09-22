# Import Path Guide for nanoBragg PyTorch Implementation

## Summary

The nanoBragg PyTorch implementation uses the package name `nanobrag_torch`, not `nanoBragg`. This guide provides the correct import patterns and explains common issues.

## Correct Import Patterns

### 1. For Development (using src/ path)
When running code from the repository root during development:

```python
# Core models
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.simulator import Simulator

# Configuration classes
from src.nanobrag_torch.config import (
    DetectorConfig, CrystalConfig, BeamConfig,
    DetectorConvention, DetectorPivot
)

# Utilities
from src.nanobrag_torch.utils.geometry import rotation_matrix_from_angles
from src.nanobrag_torch.utils.physics import bragg_angle, energy_to_wavelength
from src.nanobrag_torch.utils.noise import add_poisson_noise

# I/O functions
from src.nanobrag_torch.io.hkl import load_hkl_file
from src.nanobrag_torch.io.smv import read_smv_image, write_smv_image
```

### 2. For Installed Package (after pip install -e .)
When the package is installed in development mode:

```python
# Core models
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.simulator import Simulator

# Configuration classes
from nanobrag_torch.config import (
    DetectorConfig, CrystalConfig, BeamConfig,
    DetectorConvention, DetectorPivot
)

# Utilities
from nanobrag_torch.utils.geometry import rotation_matrix_from_angles
from nanobrag_torch.utils.physics import bragg_angle, energy_to_wavelength
from nanobrag_torch.utils.noise import add_poisson_noise

# I/O functions
from nanobrag_torch.io.hkl import load_hkl_file
from nanobrag_torch.io.smv import read_smv_image, write_smv_image
```

## Common Mistakes

### ❌ Incorrect Import Patterns

These import patterns will **NOT** work:

```python
# Wrong package name
from nanoBragg.detector import Detector
from nanoBragg.components.detector import Detector
from nanoBragg.models.detector import Detector
import nanoBragg

# Non-existent components path
from nanobrag_torch.components.detector import Detector
```

### ⚠️ Error Messages

If you see this error:
```
ImportError: No module named 'nanoBragg'
```

You are trying to import from `nanoBragg` instead of `nanobrag_torch`. Change your import to use the correct package name.

## Package Structure

The actual package structure is:

```
nanobrag_torch/
├── __init__.py
├── config.py                 # Configuration dataclasses
├── simulator.py             # Main simulation class
├── models/
│   ├── __init__.py
│   ├── detector.py          # Detector geometry
│   └── crystal.py           # Crystal structure
├── utils/
│   ├── __init__.py
│   ├── geometry.py          # Geometric utilities
│   ├── physics.py           # Physical constants
│   └── noise.py             # Noise generation
└── io/
    ├── __init__.py
    ├── hkl.py               # HKL file handling
    ├── smv.py               # SMV image format
    └── source.py            # Beam source utilities
```

## Installation Check

To verify your installation and imports work:

```python
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'  # Required for PyTorch

# Test basic import
import nanobrag_torch
print(f"nanobrag_torch version: {nanobrag_torch.__version__}")

# Test core components
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.config import DetectorConfig

# Create a simple detector to verify everything works
detector = Detector(DetectorConfig())
print("Import test successful!")
```

## Best Practices

1. **Always set the environment variable** before importing PyTorch-based code:
   ```python
   import os
   os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
   ```

2. **Use explicit imports** for clarity:
   ```python
   # Good
   from nanobrag_torch.config import DetectorConfig, DetectorConvention

   # Less clear
   from nanobrag_torch.config import *
   ```

3. **Check package installation**:
   ```bash
   pip list | grep nanobrag
   # Should show: nanobrag-torch    0.1.0    /path/to/nanoBragg
   ```

4. **For development work**, use the src/ path imports to avoid installation issues.

## Troubleshooting

### Issue: `No module named 'nanoBragg'`
**Solution**: Replace `nanoBragg` with `nanobrag_torch` in your imports.

### Issue: `No module named 'nanobrag_torch'`
**Solutions**:
1. Install the package: `pip install -e .` from the repository root
2. Use src/ path imports: `from src.nanobrag_torch.models.detector import Detector`
3. Add src/ to Python path: `sys.path.insert(0, 'src')`

### Issue: `OMP: Error #15: Initializing libomp.dylib`
**Solution**: Set the environment variable:
```python
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
```

## Testing Your Imports

Run this verification script to test all common import patterns:

```python
#!/usr/bin/env python3
"""Import verification script for nanoBragg PyTorch implementation."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

def test_imports():
    """Test all critical import patterns."""
    test_cases = [
        # Package-level imports (after pip install -e .)
        "import nanobrag_torch",
        "from nanobrag_torch.models.detector import Detector",
        "from nanobrag_torch.models.crystal import Crystal",
        "from nanobrag_torch.config import DetectorConfig, CrystalConfig, BeamConfig",

        # Development imports (using src/ path)
        "from src.nanobrag_torch.models.detector import Detector",
        "from src.nanobrag_torch.config import DetectorConfig",
    ]

    results = {"passed": 0, "failed": 0}

    for test_import in test_cases:
        try:
            exec(test_import)
            print(f"✓ {test_import}")
            results["passed"] += 1
        except ImportError as e:
            print(f"✗ {test_import} - {e}")
            results["failed"] += 1

    print(f"\nResults: {results['passed']} passed, {results['failed']} failed")
    return results["failed"] == 0

if __name__ == "__main__":
    success = test_imports()
    exit(0 if success else 1)
```

Save this as `verify_imports.py` and run it to check your setup.