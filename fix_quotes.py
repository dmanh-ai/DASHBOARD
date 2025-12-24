#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix quote escaping issues in data files
"""

import re

def fix_quotes_in_file(filepath):
    """Fix nested quotes in JavaScript file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix pattern: title: "text with "quotes" inside"
    # Change to: title: 'text with "quotes" inside'
    # Or escape inner quotes

    # Pattern 1: title: "..." with nested quotes
    def fix_title(match):
        indent = match.group(1)
        title_content = match.group(2)
        # Escape any double quotes inside the title
        escaped = title_content.replace('"', '\\"')
        return f'{indent}title: "{escaped}",'

    # Pattern to match title lines
    pattern = r'(\s+)title:\s*"([^"]*(?:"[^"]*)*)"(?:,)?\s*$'

    fixed_content = re.sub(pattern, fix_title, content, flags=re.MULTILINE)

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(fixed_content)

    print(f"✅ Fixed quotes in {filepath}")

# Fix all three data files
print("🔧 Fixing quotes in data files...\n")

try:
    fix_quotes_in_file('vnindex_data.js')
except Exception as e:
    print(f"⚠️  vnindex_data.js: {e}")

try:
    fix_quotes_in_file('full_data_remaining.js')
except Exception as e:
    print(f"⚠️  full_data_remaining.js: {e}")

try:
    fix_quotes_in_file('full_data_special.js')
except Exception as e:
    print(f"⚠️  full_data_special.js: {e}")

print("\n✅ Done! Now recombine the files.")
