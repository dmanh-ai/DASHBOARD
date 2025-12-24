#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Combine all data files into a working full_data.js
"""

print("🔧 Combining data files into full_data.js\n")

# Read vnindex_data.js (has valid const FULL_DATA wrapper)
with open('vnindex_data.js', 'r', encoding='utf-8') as f:
    vnindex_content = f.read()

# Remove the closing brace and semicolon
if vnindex_content.rstrip().endswith('};'):
    vnindex_content = vnindex_content.rstrip()[:-2]

print(f"✅ Read vnindex_data.js: {len(vnindex_content)} chars")

# Read remaining data (industry indices)
with open('full_data_remaining.js', 'r', encoding='utf-8') as f:
    remaining = f.read().strip()

print(f"✅ Read full_data_remaining.js: {len(remaining)} chars")

# Read special data
with open('full_data_special.js', 'r', encoding='utf-8') as f:
    special = f.read().strip()

print(f"✅ Read full_data_special.js: {len(special)} chars")

# Combine all
output = vnindex_content + ',\n' + remaining + ',\n' + special + '\n};'

# Write to full_data.js
with open('full_data.js', 'w', encoding='utf-8') as f:
    f.write(output)

print(f"\n✅ Created full_data.js: {len(output)} chars")

# Count indices
import re
indices = re.findall(r'(\w+):\s*{', output)
unique_indices = list(set(indices))
print(f"📊 Found {len(unique_indices)} unique indices")
print(f"📋 {', '.join(sorted(unique_indices))}")
