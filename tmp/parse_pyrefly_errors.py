#!/usr/bin/env python3
"""Parse pyrefly errors into a structured JSON task list."""
import json
import re

def parse_pyrefly_errors(log_file):
    """Parse pyrefly error log into structured JSON format."""
    errors = []
    
    with open(log_file, 'r') as f:
        content = f.read()
    
    # Regular expression to match error entries
    error_pattern = r'ERROR (.+?) \[(.+?)\]\s+-->\s+(.+?):(\d+):(\d+)'
    
    for match in re.finditer(error_pattern, content):
        error_message = match.group(1).strip()
        error_code = match.group(2).strip()
        file_path = match.group(3).strip()
        line_number = int(match.group(4))
        col_number = int(match.group(5))
        
        error_entry = {
            "file_path": file_path,
            "line_number": line_number,
            "column_number": col_number,
            "error_code": error_code,
            "error_message": error_message
        }
        errors.append(error_entry)
    
    return errors

if __name__ == "__main__":
    errors = parse_pyrefly_errors("./tmp/pyrefly_errors.log")
    
    # Save to JSON file
    with open("./tmp/pyrefly_tasks.json", "w") as f:
        json.dump(errors, f, indent=2)
    
    print(f"✅ Parsed {len(errors)} errors into ./tmp/pyrefly_tasks.json")
    
    # Print summary
    print("\nError Summary:")
    error_counts = {}
    for error in errors:
        code = error["error_code"]
        error_counts[code] = error_counts.get(code, 0) + 1
    
    for code, count in sorted(error_counts.items()):
        print(f"  {code}: {count} errors")