# Quick Start: Configuration Consistency Validation

## For Developers Who Just Want It Working

### 30-Second Setup

```bash
# 1. Run this right now to check if you have the problem
grep "convention selected" your_last_c_output.log

# If it says "custom convention selected" but you expected MOSFLM, you have the bug!

# 2. Quick fix for most cases
# In your test script, remove any of these parameters:
# -twotheta_axis, -fdet_vector, -sdet_vector, -odet_vector

# 3. After this initiative is implemented, just run:
python scripts/validate_config_consistency.py
# It will tell you exactly what's wrong and how to fix it
```

## The Problem in One Picture

```
What You Think Is Happening:
PyTorch (MOSFLM) ←→ C (MOSFLM) ✅

What's Actually Happening:
PyTorch (MOSFLM) ←→ C (CUSTOM) ❌
                      ↑
                      Your test added -twotheta_axis!
```

## The One Test That Reveals Everything

```python
# Run this Python snippet to see if you're affected:
import subprocess

# Test 1: C without explicit parameters
result1 = subprocess.run(
    ["./nanoBragg", "-twotheta", "15"],
    capture_output=True, text=True
)

# Test 2: C with explicit default parameter  
result2 = subprocess.run(
    ["./nanoBragg", "-twotheta", "15", "-twotheta_axis", "0", "0", "-1"],
    capture_output=True, text=True
)

# Check if they're different (they shouldn't be but ARE!)
if "mosflm" in result1.stderr and "custom" in result2.stderr:
    print("🚨 YOU HAVE THE BUG! Explicit defaults change behavior!")
else:
    print("✅ Your system is consistent")
```

## What This Initiative Will Give You

### Before (Current State)
- 🔴 4-8 hours debugging configuration mismatches
- 🔴 No idea why correlation is 0.04 instead of 0.99
- 🔴 Test infrastructure secretly sabotaging you
- 🔴 Hidden convention switches

### After (With This Initiative)
- ✅ 30 seconds to detect and fix configuration issues
- ✅ Clear message: "MODE MISMATCH: C=CUSTOM, PyTorch=MOSFLM"
- ✅ Exact fix: "Remove -twotheta_axis from your command"
- ✅ Prevented from happening in the first place

## For Test Writers

### The Golden Rule
**Never pass default parameters explicitly** unless you're testing that specific behavior.

```bash
# BAD - Forces CUSTOM convention
./nanoBragg -twotheta 15 -twotheta_axis 0 0 -1

# GOOD - Uses MOSFLM convention
./nanoBragg -twotheta 15
```

### The New Validation Flow

```python
# Your test script after initiative implementation
def run_test():
    # 1. Configuration is automatically validated
    config = create_config()
    
    # 2. Pre-flight check catches mismatches
    preflight_check(config)  # Throws clear error if mismatch
    
    # 3. Run with confidence
    run_simulation(config)
```

## For Debuggers

### New Debugging Order

1. **FIRST**: Run configuration validation
   ```bash
   python scripts/validate_config_consistency.py
   ```

2. **ONLY IF VALIDATION PASSES**: Check your implementation
   
3. **NEVER**: Spend hours debugging before checking configuration

### The Decision Tree

```
Correlation < 0.5?
    ↓
Run validate_config_consistency.py
    ↓
Says "MODE MISMATCH"? → Fix configuration (5 min)
    ↓
Says "OK"? → Check test infrastructure (10 min)
    ↓
Still broken? → NOW debug your code
```

## FAQ

**Q: Why does adding `-twotheta_axis 0 0 -1` (the default!) change behavior?**  
A: The C code switches to CUSTOM convention based on parameter PRESENCE, not VALUE. This is a bug.

**Q: How did this take months to find?**  
A: The test infrastructure was adding this parameter, changing C's behavior silently.

**Q: Will this initiative fix the C code?**  
A: No, we're adding detection and prevention. Fixing C would break compatibility.

**Q: What if I WANT CUSTOM convention?**  
A: That's fine! The validation will ensure both C and PyTorch use the same convention.

## Getting Started with Development

If you want to help implement this initiative:

1. Read the [full initiative plan](README.md)
2. Check the [implementation checklist](implementation_checklist.md)
3. Start with Week 1 tasks (highest impact, easiest implementation)
4. Test your changes with the known problematic case

## The One-Liner That Would Have Saved Months

```python
assert c_mode == pytorch_mode, f"Mode mismatch: C={c_mode}, Py={pytorch_mode}"
```

This initiative ensures this check happens automatically, every time, with clear fixes.

---

**Remember**: 90% of "correlation issues" are configuration mismatches, not code bugs. Check configuration first, always.