#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTO PARSER - Tự động parse tất cả indices từ file text mới
Sử dụng khi có file Word mới cần convert sang dashboard
"""

import sys
from smart_parser import parse_smart

def parse_all_indices(input_txt, output_js='full_data_new.js'):
    """
    Parse tất cả 16 indices từ file text
    """

    # Danh sách tất cả indices cần parse
    indices = [
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

    # Mở file output
    with open(output_js, 'w', encoding='utf-8') as f:
        # Write header
        f.write("// AUTO GENERATED - " + input_txt + "\n")
        f.write("const FULL_DATA = {\n")

        success_count = 0
        failed_indices = []

        # Parse từng index
        for i, (index_name, index_code) in enumerate(indices, 1):
            try:
                print(f"[{i}/16] Processing {index_name}...", end=" ")

                js_obj = parse_smart(input_txt, index_name, index_code)

                # Check if parse thành công
                if js_obj and not js_obj.startswith("# LỖI"):
                    # Validate: check có sections không
                    if "sections:" in js_obj and "title:" in js_obj:
                        f.write(js_obj + ",\n")
                        print("✅ DONE")
                        success_count += 1
                    else:
                        print("⚠️  WARNING: Invalid structure")
                        failed_indices.append(index_name)
                else:
                    print("❌ FAILED")
                    failed_indices.append(index_name)

            except Exception as e:
                print(f"❌ ERROR: {e}")
                failed_indices.append(index_name)

        # Close FULL_DATA object
        f.write("};\n")

    # Print summary
    print("-" * 60)
    print(f"📊 SUMMARY:")
    print(f"   ✅ Success: {success_count}/16 indices")
    print(f"   ❌ Failed: {len(failed_indices)}/16 indices")

    if failed_indices:
        print(f"\n❌ Failed indices:")
        for idx in failed_indices:
            print(f"   - {idx}")
    else:
        print(f"\n🎉 ALL INDICES PARSED SUCCESSFULLY!")

    print(f"\n📝 Output file: {output_js}")
    print(f"\n🔍 Next steps:")
    print(f"   1. node --check {output_js}")
    print(f"   2. Copy {output_js} → full_data.js")
    print(f"   3. Open COMPLETE.html to verify")

    return success_count == len(indices)


if __name__ == '__main__':
    import os

    # Default paths
    default_input = '/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/UI GLM/baocao_full.txt'
    default_output = '/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/UI GLM/full_data_new.js'

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
