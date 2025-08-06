#!/usr/bin/env python3
"""Test the regex fix to see if it was actually needed."""

import re

# Sample content that might appear in a checklist markdown file
test_content = """
## Phase 2 Checklist

### Task 1: Update configuration
- [ ] Update `src/nanobrag_torch/config.py` with new parameters
- [ ] Modify `src/nanobrag_torch/models/detector.py` to use new config

### Task 2: Add tests
- [ ] Create `tests/test_new_feature.py`
- [ ] Update `tests/test_integration.py`

Some other text with paths like src/utils.py but not in backticks.
"""

print("Test content:")
print(test_content)
print("\n" + "="*60 + "\n")

# Original regex (with triple backslashes)
original_regex = r'\\\`([a-zA-Z0-9/._-]+)\\\`'
print(f"Original regex: {original_regex}")
print("Raw string representation:", repr(original_regex))

try:
    original_files = re.findall(original_regex, test_content)
    print(f"Files found with original regex: {original_files}")
except Exception as e:
    print(f"Error with original regex: {e}")

print("\n" + "-"*40 + "\n")

# Fixed regex (with single backslash)
fixed_regex = r'\`([a-zA-Z0-9/._-]+)\`'
print(f"Fixed regex: {fixed_regex}")
print("Raw string representation:", repr(fixed_regex))

try:
    fixed_files = re.findall(fixed_regex, test_content)
    print(f"Files found with fixed regex: {fixed_files}")
except Exception as e:
    print(f"Error with fixed regex: {e}")

print("\n" + "="*60 + "\n")

# Also test with the exact escaping that would happen in the shell command
print("Testing what actually happens in the shell command:")

# Simulate the Python code as it would be executed from bash
code_original = """
import re
content = '''%s'''
files = re.findall(r'\\\`([a-zA-Z0-9/._-]+)\\\`', content)
print("Original regex result:", files)
""" % test_content

code_fixed = """
import re
content = '''%s'''
files = re.findall(r'\`([a-zA-Z0-9/._-]+)\`', content)
print("Fixed regex result:", files)
""" % test_content

print("Executing original version:")
exec(code_original)

print("\nExecuting fixed version:")
exec(code_fixed)