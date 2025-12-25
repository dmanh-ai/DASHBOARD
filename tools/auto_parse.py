#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTO PARSER - Tự động parse tất cả indices từ file text mới
Sử dụng khi có file Word mới cần convert sang dashboard
"""

import sys
from pathlib import Path

from smart_parser import parse_overview, parse_index
from parser_models import ParsedResult

def parse_all_indices(input_txt, output_js='full_data_new.js'):
    """
    Parse tất cả indices (overview + 15 chỉ số) từ file text
    """

    # Danh sách tất cả indices cần parse
    indices = [
        ('OVERVIEW', 'overview'),
        ('VNINDEX', 'vnindex'),
        ('VN30', 'vn30'),
        ('VN100', 'vn100'),
        ('VNMIDCAP', 'vnmidcap'),
        ('VNREAL', 'vnreal'),
        ('VNIT', 'vnit'),
        ('VNHEAL', 'vnheal'),
        ('VNFIN', 'vnfin'),
        ('VNENE', 'vnene'),
        ('VNCONS', 'vncons'),
        ('VNMAT', 'vnmat'),
        ('VNCOND', 'vncond'),
        ('VNSML', 'vnsml'),
        ('VNFINSELECT', 'vnfinselect'),
        ('VNDIAMOND', 'vndiamond')
    ]

    print(f"🚀 Starting parse from: {input_txt}")
    print(f"📝 Output to: {output_js}")
    print("-" * 60)

    # ✅ TASK 1.1: Đọc file 1 lần duy nhất
    print(f"📖 Reading file: {input_txt}")
    with open(input_txt, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"   ✓ Loaded {len(content)} characters")

    # Mở file output
    with open(output_js, 'w', encoding='utf-8') as f:
        # Write header
        f.write("// AUTO GENERATED - " + input_txt + "\n")
        f.write("const FULL_DATA = {\n")

        success_count = 0
        failed_indices = []
        error_summary = {}  # error_type -> count
        total = len(indices)

        # Parse từng index
        for i, (index_name, index_code) in enumerate(indices, 1):
            try:
                print(f"[{i}/{total}] Processing {index_name}...", end=" ")

                # TASK 1.2: Sử dụng structured result API
                result: ParsedResult
                if index_code == "overview":
                    result = parse_overview(content)
                else:
                    result = parse_index(content, index_name, index_code)

                # Check result status
                if result.is_success():
                    # Write JS output
                    f.write(result.raw_js + ",\n")
                    print("✅ DONE")
                    success_count += 1
                else:
                    # Structured error handling
                    error_type = result.error.error_type if result.error else "Unknown"
                    error_msg = result.error.message if result.error else "No error info"
                    print(f"❌ FAILED: {error_type}")
                    failed_indices.append(index_name)

                    # Collect error statistics
                    error_summary[error_type] = error_summary.get(error_type, 0) + 1

            except Exception as e:
                print(f"❌ UNEXPECTED ERROR: {e}")
                failed_indices.append(index_name)
                error_summary["UnexpectedError"] = error_summary.get("UnexpectedError", 0) + 1

        # Close FULL_DATA object
        f.write("};\n")

    # Print summary
    print("-" * 60)
    print(f"📊 SUMMARY:")
    print(f"   ✅ Success: {success_count}/{total} items")
    print(f"   ❌ Failed: {len(failed_indices)}/{total} items")

    if failed_indices:
        print(f"\n❌ Failed indices:")
        for idx in failed_indices:
            print(f"   - {idx}")

        # TASK 1.2: Show error statistics
        if error_summary:
            print(f"\n📋 Error breakdown:")
            for error_type, count in sorted(error_summary.items(), key=lambda x: -x[1]):
                print(f"   • {error_type}: {count}")
    else:
        print(f"\n🎉 ALL INDICES PARSED SUCCESSFULLY!")

    print(f"\n📝 Output file: {output_js}")
    print(f"\n🔍 Next steps:")
    print(f"   1. node --check {output_js}")
    print(f"   2. If OK: cp {output_js} full_data.js")
    print(f"   3. Open index.html (or ELEGANT_CHRISTMAS.html) to verify")

    return success_count == len(indices)


if __name__ == '__main__':
    import os

    # Default paths
    project_root = Path(__file__).resolve().parents[1]
    default_output = str(project_root / "full_data_new.js")

    # Prefer `reports/txt/baocao_full.txt` to keep repo root clean; fallback to root for compatibility.
    preferred_input = project_root / "reports" / "txt" / "baocao_full.txt"
    legacy_input = project_root / "baocao_full.txt"
    default_input = str(preferred_input if preferred_input.exists() else legacy_input)

    # Get input from command line or use default
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = default_input

    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = default_output

    # Check input file exists
    if not os.path.exists(input_file):
        print(f"❌ ERROR: File not found: {input_file}")
        print(f"\nUsage: python auto_parse.py [input_file.txt] [output_file.js]")
        print(f"\nExample:")
        print(f"   python auto_parse.py baocao_new.txt full_data_new.js")
        sys.exit(1)

    # Run parser
    success = parse_all_indices(input_file, output_file)

    sys.exit(0 if success else 1)
