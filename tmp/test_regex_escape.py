#!/usr/bin/env python3
"""Test to understand the escaping behavior in shell commands."""

import re

# Let's see what Python actually receives when we use different escaping
print("Testing what Python receives from shell escaping:\n")

# Test 1: Raw string with triple backslashes
print("Test 1: r'\\\\\\`pattern\\\\\\`'")
pattern1 = r'\\\`([a-zA-Z0-9/._-]+)\\\`'
print(f"Pattern string: {repr(pattern1)}")
print(f"Length: {len(pattern1)}")
print(f"Characters: {[c for c in pattern1]}")
print()

# Test 2: Raw string with single backslashes
print("Test 2: r'\\`pattern\\`'")
pattern2 = r'\`([a-zA-Z0-9/._-]+)\`'
print(f"Pattern string: {repr(pattern2)}")
print(f"Length: {len(pattern2)}")
print(f"Characters: {[c for c in pattern2]}")
print()

# Test what these patterns actually match
test_string = "This is `a/test/path.py` in backticks"
print(f"\nTest string: {test_string}")
print(f"Pattern 1 matches: {re.findall(pattern1, test_string)}")
print(f"Pattern 2 matches: {re.findall(pattern2, test_string)}")

# Test with escaped backticks in the test string
test_string2 = "This is \\`another/test.py\\` with escaped backticks"
print(f"\nTest string 2: {test_string2}")
print(f"Pattern 1 matches: {re.findall(pattern1, test_string2)}")
print(f"Pattern 2 matches: {re.findall(pattern2, test_string2)}")