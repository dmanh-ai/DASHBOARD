#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rebuild full_data.js hoàn chỉnh từ đầu
"""

import re
import json

# Header
header = """// ==========================================
// DỮ LIỆU HOÀN CHỈNH CHO TẤT CẢ 16 CHỈ SỐ
// 100% Coverage - Phiên bản hoàn chỉnh
// Generated: 2024-12-24
// ==========================================

const FULL_DATA = {
"""

# Đọc các file data
files_to_read = {
    'vnindex_data.js': 'main',
    'full_data_remaining.js': 'industry',
    'full_data_special.js': 'special'
}

output = header + "\n"

# 1. Đọc vnindex_data.js để lấy VNINDEX, VN30, VN100, VNMIDCAP, VNREAL
try:
    with open('vnindex_data.js', 'r', encoding='utf-8') as f:
        main_content = f.read()

    # Extract FULL_DATA object
    match = re.search(r'const FULL_DATA\s*=\s*{(.+)};\s*$', main_content, re.DOTALL)
    if match:
        data_obj = match.group(1)
        # Add to output
        output += "    " + data_obj.strip() + "\n"
        print("✅ Added main indices from vnindex_data.js")
except Exception as e:
    print(f"⚠️  Error reading vnindex_data.js: {e}")

# 2. Đọc và thêm các ngành
try:
    with open('full_data_remaining.js', 'r', encoding='utf-8') as f:
        industry_data = f.read()

    output += """
    // ==========================================
    // 7 Chỉ Số Ngành - Full Data
    // ==========================================
"""
    output += "    " + industry_data.strip()
    print("✅ Added 7 industry indices")
except Exception as e:
    print(f"⚠️  Error reading industry data: {e}")

# 3. Đọc và thêm các chỉ số đặc biệt
try:
    with open('full_data_special.js', 'r', encoding='utf-8') as f:
        special_data = f.read()

    output += """
    // ==========================================
    // 3 Chỉ Số Đặc Biệt - Full Data
    // ==========================================
"""
    output += "    " + special_data.strip()
    print("✅ Added 3 special indices")
except Exception as e:
    print(f"⚠️  Error reading special data: {e}")

# Kết thúc
output += "\n};\n"

# Ghi ra file
output_file = 'full_data.js'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"\n✅ Đã tạo {output_file}")
print(f"📊 Kích thước: {len(output)} ký tự")

# Verify
indices = re.findall(r'(\w+):\s*{', output)
unique_indices = list(set(indices))
print(f"🎯 Số indices unique: {len(unique_indices)}")
print(f"📋 Danh sách: {', '.join(sorted(unique_indices))}")
