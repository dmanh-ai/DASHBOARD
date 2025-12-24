#!/usr/bin/env python3
"""
PHÂN TÍCH 100% COVERAGE CỦA BÁO CÁO WORD
=========================================
Script này phân tích toàn bộ file text từ Word và:
1. Liệt kê TẤT CẢ các phần/chỉ số/section
2. Đảm bảo không sót mục nào
3. Tạo cấu trúc data hoàn chỉnh
"""

import re
import json
from pathlib import Path

# Đọc file
project_root = Path(__file__).resolve().parents[2]
file_path = project_root / "baocao_full.txt"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

# Phân tích cấu trúc
structure = {
    "parts": [],
    "indices": {},
    "industries": {},
    "total_lines": len(lines)
}

# Tìm các PHẦN
part_pattern = r'^PHẦN ([IVX]+):\s*(.+)$'
for i, line in enumerate(lines):
    match = re.match(part_pattern, line)
    if match:
        part_num = match.group(1)
        part_name = match.group(2)
        structure["parts"].append({
            "line": i + 1,
            "part": part_num,
            "name": part_name
        })

# Tìm các chỉ số trong PHẦN III
index_pattern = r'^[0-9]+\. Chỉ số\s+(VN[A-Z0-9]+)'
current_index = None

for i, line in enumerate(lines):
    match = re.match(index_pattern, line)
    if match:
        current_index = match.group(1)
        structure["indices"][current_index] = {
            "start_line": i + 1,
            "sections": []
        }

# Tìm các ngành trong PHẦN IV
industry_pattern = r'^[0-9]+\. (VN[A-Z]+) - (.+)$'
for i, line in enumerate(lines):
    match = re.match(industry_pattern, line)
    if match:
        ind_code = match.group(1)
        ind_name = match.group(2)
        structure["industries"][ind_code] = {
            "start_line": i + 1,
            "name": ind_name,
            "sections": []
        }

# Tìm các chỉ số khác trong PHẦN V
other_pattern = r'^[0-9]+\. Chỉ số\s+(VN[A-Z0-9]+)'
in_part_v = False
for i, line in enumerate(lines):
    if "PHẦN V" in line or "PHẦN V:" in line:
        in_part_v = True
    elif "PHẦN" in line and in_part_v:
        in_part_v = False

    if in_part_v:
        match = re.match(other_pattern, line)
        if match:
            idx = match.group(1)
            if idx not in structure["indices"]:
                structure["indices"][idx] = {
                    "start_line": i + 1,
                    "sections": []
                }

# In kết quả phân tích
print("=" * 80)
print("PHÂN TÍCH 100% COVERAGE - BÁO CÁO THỊ TRƯỜNG")
print("=" * 80)
print(f"\nTổng số dòng: {structure['total_lines']}")
print(f"\nCác PHẦN ({len(structure['parts'])}):")
for part in structure["parts"]:
    print(f"  PHẦN {part['part']}: {part['name']} (dòng {part['line']})")

print(f"\n" + "=" * 80)
print(f"CÁC CHỈ SỐ THÀNH PHẦN & KHÁC ({len(structure['indices'])}):")
print("=" * 80)
for idx, info in structure["indices"].items():
    print(f"  ✓ {idx} (bắt đầu dòng {info['start_line']})")

print(f"\n" + "=" * 80)
print(f"CÁC CHỈ SỐ NGÀNH ({len(structure['industries'])}):")
print("=" * 80)
for ind, info in structure["industries"].items():
    print(f"  ✓ {ind} - {info['name']} (bắt đầu dòng {info['start_line']})")

# Tổng kết
total_items = len(structure["indices"]) + len(structure["industries"])
print(f"\n" + "=" * 80)
print(f"TỔNG KẾT:")
print("=" * 80)
print(f"  • Tổng số PHẦN: {len(structure['parts'])}")
print(f"  • Chỉ số thành phần & khác: {len(structure['indices'])}")
print(f"  • Chỉ số ngành: {len(structure['industries'])}")
print(f"  • TỔNG CỘNG: {total_items} chỉ số")

print(f"\n" + "=" * 80)
print("CẤU TRÚC DATA CẦN TẠO:")
print("=" * 80)
print("""
const FULL_DATA = {
""")

# In ra cấu trúc VNINDEX (đã có)
print("    vnindex: { ... },  // ✓ ĐÃ CÓ 100%")

# In ra các chỉ số thành phần
print("\n    // CHỈ SỐ THÀNH PHẦN (PHẦN III)")
for idx in ["vn30", "vn100", "vnmidcap"]:
    if idx in structure["indices"]:
        print(f"    {idx}: {{ ... }},  // ⏳ Cần thêm")

print("\n    // CHỈ SỐ NGÀNH (PHẦN IV)")
for ind in structure["industries"]:
    print(f"    {ind.lower()}: {{ ... }},  // ⏳ Cần thêm")

print("\n    // CHỈ SỐ KHÁC (PHẦN V)")
for idx in ["vnsml", "vnfinselect", "vndiamond"]:
    if idx in structure["indices"]:
        print(f"    {idx}: {{ ... }},  // ⏳ Cần thêm")

print("""
};

CHECKLIST COVERAGE:
""")

checklist = [
    ("PHẦN I: Tổng quan thị trường", "overview", True),
    ("PHẦN II: VNINDEX", "vnindex", True),
    ("PHẦN III-a: VN30", "vn30", False),
    ("PHẦN III-b: VN100", "vn100", False),
    ("PHẦN III-c: VNMIDCAP", "vnmidcap", False),
    ("PHẦN IV-a: VNREAL", "vnreal", False),
    ("PHẦN IV-b: VNIT", "vnit", False),
    ("PHẦN IV-c: VNHEAL", "vnheal", False),
    ("PHẦN IV-d: VNFIN", "vnfin", False),
    ("PHẦN IV-e: VNENE", "vnene", False),
    ("PHẦN IV-f: VNCONS", "vncons", False),
    ("PHẦN IV-g: VNMAT", "vnmat", False),
    ("PHẦN IV-h: VNCOND", "vncond", False),
    ("PHẦN V-a: VNSML", "vnsml", False),
    ("PHẦN V-b: VNFINSELECT", "vnfinselect", False),
    ("PHẦN V-c: VNDIAMOND", "vndiamond", False),
]

done_count = 0
for name, key, done in checklist:
    status = "✅" if done else "⏳"
    print(f"  {status} {name:40} → {key}")
    if done:
        done_count += 1

print(f"\nProgress: {done_count}/{len(checklist)} ({done_count*100//len(checklist)}%)")
print("\n" + "=" * 80)
