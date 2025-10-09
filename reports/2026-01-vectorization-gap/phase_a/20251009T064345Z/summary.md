# Vectorization Loop Inventory Summary

**Generated:** 2025-10-09 06:43:57 UTC

## Overview

- Total loops found: 24
- Likely hot loops: 12
- Scan target: src/nanobrag_torch/

## Loops by Module

### src/nanobrag_torch/io/hkl.py

Loop count: 3

- Line 51: `for line in f`
  - Type: for
  - Hint: unknown iterable

- Line 110: `for (h, k, l, F) in reflections`
  - Type: for
  - Hint: unknown iterable

- Line 208: `while True`
  - Type: while
  - Hint: while loop (typically hard to vectorize)

### src/nanobrag_torch/io/mask.py

Loop count: 2

- Line 52: `for line in header_content.split(';')`
  - Type: for
  - Hint: unknown iterable

- Line 178: `for line in header_content.split(';')`
  - Type: for
  - Hint: unknown iterable

### src/nanobrag_torch/io/mosflm.py

Loop count: 2

- Line 59: `for line in f`
  - Type: for
  - Hint: unknown iterable

- Line 67: `for part in parts`
  - Type: for
  - Hint: unknown iterable

### src/nanobrag_torch/io/smv.py

Loop count: 2

- Line 46: `for line in header_content.split('\n')`
  - Type: for
  - Hint: unknown iterable

- Line 240: `for (key, value) in header.items()`
  - Type: for
  - Hint: dict iteration (usually small)

### src/nanobrag_torch/io/source.py

Loop count: 1

- Line 60: `for (line_num, line) in enumerate(f, 1)`
  - Type: for
  - Hint: enumerate (check underlying collection size)

### src/nanobrag_torch/models/crystal.py

Loop count: 4

- Line 180: `for (angle_name, angle) in [('alpha', self.cell_alpha), ('beta', self.cell_beta), ('gamma', self.cell_gamma)]`
  - Type: for
  - Hint: unknown iterable

- Line 187: `for (angle_name, angle) in [('alpha', self.cell_alpha), ('beta', self.cell_beta), ('gamma', self.cell_gamma)]`
  - Type: for
  - Hint: unknown iterable

- Line 762: `for angle in self.config.misset_deg`
  - Type: for
  - Hint: unknown iterable

- Line 1350: `for i in range(3)`
  - Type: for
  - Hint: range-based (likely hot if large N)

### src/nanobrag_torch/simulator.py

Loop count: 4

- Line 1469: `for i in range(4)`
  - Type: for
  - Hint: range-based (likely hot if large N)

- Line 1470: `for j in range(4)`
  - Type: for
  - Hint: range-based (likely hot if large N)

- Line 1471: `for k in range(4)`
  - Type: for
  - Hint: range-based (likely hot if large N)

- Line 1568: `for phi_tic in range(phi_steps)`
  - Type: for
  - Hint: range-based (likely hot if large N)

### src/nanobrag_torch/utils/c_random.py

Loop count: 1

- Line 100: `for j in range(self.NTAB + 7, -1, -1)`
  - Type: for
  - Hint: range-based (likely hot if large N)

### src/nanobrag_torch/utils/noise.py

Loop count: 1

- Line 171: `for i in range(n)`
  - Type: for
  - Hint: range-based (likely hot if large N)

### src/nanobrag_torch/utils/physics.py

Loop count: 4

- Line 393: `for j in range(4)`
  - Type: for
  - Hint: range-based (likely hot if large N)

- Line 439: `for j in range(4)`
  - Type: for
  - Hint: range-based (likely hot if large N)

- Line 543: `for j in range(4)`
  - Type: for
  - Hint: range-based (likely hot if large N)

- Line 594: `for j in range(4)`
  - Type: for
  - Hint: range-based (likely hot if large N)

## Hot Path Candidates

Loops likely to affect simulation performance:

### src/nanobrag_torch/models/crystal.py:180

```python
for (angle_name, angle) in [('alpha', self.cell_alpha), ('beta', self.cell_beta), ('gamma', self.cell_gamma)]
```

- **Type:** for
- **Iteration hint:** unknown iterable
- **Priority:** HIGH if in simulator/crystal hot path

### src/nanobrag_torch/models/crystal.py:187

```python
for (angle_name, angle) in [('alpha', self.cell_alpha), ('beta', self.cell_beta), ('gamma', self.cell_gamma)]
```

- **Type:** for
- **Iteration hint:** unknown iterable
- **Priority:** HIGH if in simulator/crystal hot path

### src/nanobrag_torch/models/crystal.py:762

```python
for angle in self.config.misset_deg
```

- **Type:** for
- **Iteration hint:** unknown iterable
- **Priority:** HIGH if in simulator/crystal hot path

### src/nanobrag_torch/models/crystal.py:1350

```python
for i in range(3)
```

- **Type:** for
- **Iteration hint:** range-based (likely hot if large N)
- **Priority:** HIGH if in simulator/crystal hot path

### src/nanobrag_torch/simulator.py:1469

```python
for i in range(4)
```

- **Type:** for
- **Iteration hint:** range-based (likely hot if large N)
- **Priority:** HIGH if in simulator/crystal hot path

### src/nanobrag_torch/simulator.py:1470

```python
for j in range(4)
```

- **Type:** for
- **Iteration hint:** range-based (likely hot if large N)
- **Priority:** HIGH if in simulator/crystal hot path

### src/nanobrag_torch/simulator.py:1471

```python
for k in range(4)
```

- **Type:** for
- **Iteration hint:** range-based (likely hot if large N)
- **Priority:** HIGH if in simulator/crystal hot path

### src/nanobrag_torch/simulator.py:1568

```python
for phi_tic in range(phi_steps)
```

- **Type:** for
- **Iteration hint:** range-based (likely hot if large N)
- **Priority:** HIGH if in simulator/crystal hot path

### src/nanobrag_torch/utils/physics.py:393

```python
for j in range(4)
```

- **Type:** for
- **Iteration hint:** range-based (likely hot if large N)
- **Priority:** HIGH if in simulator/crystal hot path

### src/nanobrag_torch/utils/physics.py:439

```python
for j in range(4)
```

- **Type:** for
- **Iteration hint:** range-based (likely hot if large N)
- **Priority:** HIGH if in simulator/crystal hot path

### src/nanobrag_torch/utils/physics.py:543

```python
for j in range(4)
```

- **Type:** for
- **Iteration hint:** range-based (likely hot if large N)
- **Priority:** HIGH if in simulator/crystal hot path

### src/nanobrag_torch/utils/physics.py:594

```python
for j in range(4)
```

- **Type:** for
- **Iteration hint:** range-based (likely hot if large N)
- **Priority:** HIGH if in simulator/crystal hot path

## Next Steps

1. Cross-reference with profiler traces (Phase B1)
2. Mark loops for vectorization or document why they're safe
3. Update fix_plan.md with findings
