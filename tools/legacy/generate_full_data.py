#!/usr/bin/env python3
"""
Parse baocao_full.txt and create complete full_data.js with all stock indices.
Uses backticks for all content strings to avoid quote escaping issues.
"""

import re
from pathlib import Path
import sys

def read_file(filepath):
    """Read file content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.readlines()
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def find_index_starts(lines):
    """Find all index start positions."""
    indices = {}
    for i, line in enumerate(lines):
        # Match patterns like "1. Chỉ số VN30" or "2. VN100" or "1. VNIT - Công nghệ"
        match = re.search(r'^(\d+)\.\s+(Chỉ\s+)?(VN\w+)(?:\s*-)?', line)
        if match:
            num = match.group(1)
            index_name = match.group(3).strip()
            # Skip VNINDEX as it's already processed
            if index_name != 'VNINDEX':
                indices[index_name] = i
                print(f"Found {index_name} at line {i+1}")
    return indices

def parse_index_content(lines, start_line, index_name):
    """Parse content for a specific index."""
    # Simple placeholder - returns basic structure
    # In production, you'd parse the actual content here
    return f"""
    {{
        icon: "📊",
        title: `PHÂN TÍCH {index_name}`,
        content: `
            <div class="info-box">
                <h4>Dữ liệu cho {index_name}</h4>
                <p>Nội dung phân tích cho {index_name} sẽ được thêm vào đây.</p>
                <p>Dữ liệu được lấy từ baocao_full.txt</p>
            </div>
        `
    }}
"""

def generate_full_js():
    """Generate the complete full_data.js file."""
    project_root = Path(__file__).resolve().parents[2]
    input_file = str(project_root / 'baocao_full.txt')
    output_file = str(project_root / 'full_data.js')

    lines = read_file(input_file)
    if not lines:
        return

    print(f"Read {len(lines)} lines from {input_file}")

    # Find all indices
    indices = find_index_starts(lines)
    print(f"\nFound {len(indices)} indices to process")

    # Read existing vnindex_data.js to get VNINDEX structure
    vnindex_file = str(project_root / 'vnindex_data.js')
    try:
        with open(vnindex_file, 'r', encoding='utf-8') as f:
            vnindex_content = f.read()
            # Extract just the vnindex object
            match = re.search(r'vnindex:\s*{([^}]+sections:\s*\[[^\]]+\]\s*\])', vnindex_content, re.DOTALL)
            if match:
                vnindex_section = match.group(0)
            else:
                vnindex_section = "// Could not parse vnindex"
    except:
        vnindex_section = "// Error reading vnindex_data.js"

    print("\nGenerating full_data.js...")
    print(f"Output: {output_file}")
    print("Note: This is a placeholder script. Manual parsing is needed for complete data.")

if __name__ == "__main__":
    generate_full_js()
