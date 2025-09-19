#!/usr/bin/env python3
"""
Script to extract section 0 and final section file lists from gemini response files
and generate XML files with the contents of those files.

Usage:
    python extract_file_sections.py <input_file> [--min-score <score>]
    
Example:
    python extract_file_sections.py tmp/geminictx_run_1755109315/gemini-pass1-response.txt
    python extract_file_sections.py tmp/geminictx_run_1755109315/gemini-pass1-response.txt --min-score 5.0
"""

import os
import sys
import re
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

def extract_section_0_files(content, min_score=None):
    """Extract file paths and scores from Section 0: File List"""
    files_with_scores = []
    lines = content.split('\n')
    
    in_section_0 = False
    current_file = None
    
    for i, line in enumerate(lines):
        if line.strip() == "### Section 0: File List":
            in_section_0 = True
            continue
        
        if in_section_0:
            # Check if we've reached another section
            if line.strip().startswith("### Section ") and "Section 0" not in line:
                break
                
            # Extract file path
            file_match = re.match(r'^\s*FILE:\s*(.+)', line)
            if file_match:
                current_file = file_match.group(1).strip()
                continue
                
            # Extract score
            score_match = re.match(r'^\s*SCORE:\s*(.+)', line)
            if score_match and current_file:
                try:
                    score = float(score_match.group(1).strip())
                    if min_score is None or score >= min_score:
                        files_with_scores.append((current_file, score))
                except ValueError:
                    pass
                current_file = None
    
    return files_with_scores

def extract_final_section_files(content, min_score=None):
    """Extract file paths and scores from final section (Curated File List)"""
    files_with_scores = []
    lines = content.split('\n')
    
    # Find the last section that contains "Curated File List"
    section_start = -1
    for i, line in enumerate(lines):
        if "Curated File List" in line and line.strip().startswith("### Section"):
            section_start = i
    
    if section_start == -1:
        # Fallback: look for any final section with files
        for i in range(len(lines) - 1, -1, -1):
            if line.strip().startswith("### Section"):
                section_start = i
                break
    
    if section_start != -1:
        current_file = None
        for i in range(section_start + 1, len(lines)):
            line = lines[i]
            
            # Extract file path
            file_match = re.match(r'^\s*FILE:\s*(.+)', line)
            if file_match:
                current_file = file_match.group(1).strip()
                continue
                
            # Extract score
            score_match = re.match(r'^\s*SCORE:\s*(.+)', line)
            if score_match and current_file:
                try:
                    score = float(score_match.group(1).strip())
                    if min_score is None or score >= min_score:
                        files_with_scores.append((current_file, score))
                except ValueError:
                    pass
                current_file = None
    
    return files_with_scores

def read_file_contents(file_path, base_dir):
    """Read contents of a file, handling relative paths"""
    try:
        # Try absolute path first
        if os.path.isabs(file_path):
            full_path = file_path
        else:
            # Try relative to base directory
            full_path = os.path.join(base_dir, file_path)
        
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        else:
            return f"ERROR: File not found: {file_path}"
    except Exception as e:
        return f"ERROR reading {file_path}: {str(e)}"

def create_xml_file(files_with_scores, base_dir, output_path, root_name="files"):
    """Create XML file with file contents and scores"""
    root = ET.Element(root_name)
    
    for file_path, score in files_with_scores:
        file_elem = ET.SubElement(root, "file")
        file_elem.set("path", file_path)
        file_elem.set("score", str(score))
        
        content = read_file_contents(file_path, base_dir)
        file_elem.text = content
    
    # Pretty print the XML
    xml_str = ET.tostring(root, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ")
    
    # Remove extra blank lines
    pretty_xml = '\n'.join(line for line in pretty_xml.split('\n') if line.strip())
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    print(f"Created {output_path} with {len(files_with_scores)} files")

def main():
    parser = argparse.ArgumentParser(description="Extract file sections from gemini response files")
    parser.add_argument("input_file", help="Path to the input gemini response file")
    parser.add_argument("--min-score", type=float, default=None, 
                        help="Minimum score threshold for including files (default: include all)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found")
        sys.exit(1)
    
    # Read input file
    with open(args.input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract file lists with scores
    section_0_files = extract_section_0_files(content, args.min_score)
    final_section_files = extract_final_section_files(content, args.min_score)
    
    if args.min_score:
        print(f"Using minimum score threshold: {args.min_score}")
    print(f"Found {len(section_0_files)} files in Section 0")
    print(f"Found {len(final_section_files)} files in final section")
    
    # Determine base directory (parent of input file)
    base_dir = os.path.dirname(os.path.abspath(args.input_file))
    project_root = Path(base_dir).parent.parent  # Go up to project root
    
    # Generate output file names based on input file
    input_basename = os.path.splitext(os.path.basename(args.input_file))[0]
    output_dir = os.path.dirname(args.input_file)
    
    # Add score threshold to filename if specified
    suffix = f"_minscore{args.min_score}" if args.min_score else ""
    section_0_xml = os.path.join(output_dir, f"{input_basename}_section0_files{suffix}.xml")
    final_section_xml = os.path.join(output_dir, f"{input_basename}_final_section_files{suffix}.xml")
    
    # Create XML files
    create_xml_file(section_0_files, str(project_root), section_0_xml, "section_0_files")
    create_xml_file(final_section_files, str(project_root), final_section_xml, "final_section_files")
    
    print("\nFile lists:")
    print("\nSection 0 files (with scores):")
    for f, score in section_0_files[:5]:  # Show first 5
        print(f"  - {f} (score: {score})")
    if len(section_0_files) > 5:
        print(f"  ... and {len(section_0_files) - 5} more")
    
    print("\nFinal section files (with scores):")
    for f, score in final_section_files[:5]:  # Show first 5
        print(f"  - {f} (score: {score})")
    if len(final_section_files) > 5:
        print(f"  ... and {len(final_section_files) - 5} more")

if __name__ == "__main__":
    main()