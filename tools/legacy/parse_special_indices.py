#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser for the 3 special indices: VNSML, VNFINSELECT, VNDIAMOND
"""

import re

# File paths
REPORT_FILE = "baocao_full.txt"
OUTPUT_FILE = "full_data_special.js"

# Special indices configurations
INDICES = {
    "vnsml": {"start": 1928, "end": 2075, "name": "VNSML - SMALLCAP", "icon": "🔻"},
    "vnfinselect": {"start": 2076, "end": 2221, "name": "VNFINSELECT - CHỈ SỐ TÀI CHÍNH", "icon": "💠"},
    "vndiamond": {"start": 2222, "end": 2373, "name": "VNDIAMOND - CHỈ SỐ KIM CƯƠNG", "icon": "💎"},
}

def read_section(filename, start_line, end_line):
    """Read a specific section from the report file"""
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        section_text = ''.join(lines[start_line-1:end_line])
    return section_text

def parse_index_data(content, index_name):
    """Parse index data and extract sections"""
    sections = []

    section_patterns = [
        ("THÔNG TIN CHUNG", "📊"),
        ("XU HƯỚNG GIÁ", "📈"),
        ("XU HƯỚNG KHỐI LƯỢNG", "📊"),
        ("KẾT HỢP.*GIÁ.*KHỐI LƯỢNG", "🔄"),
        ("CUNG.*CẦU", "⚖️"),
        ("MỨC GIÁ QUAN TRỌNG", "📍"),
        ("BIẾN ĐỘNG GIÁ", "📉"),
        ("MÔ HÌNH GIÁ.*NẾN", "🕯️"),
        ("MARKET BREADTH", "📊"),
        ("LỊCH SỬ.*BREADTH", "📜"),
        ("RỦI RO", "⚠️"),
        ("KHUYẾN NGHỊ", "🎯"),
        ("GIÁ MỤC TIÊU", "🎯"),
        ("KỊCH BẢN.*WHAT.*IF", "🔮"),
        ("TỔNG HỢP.*QUYẾT ĐỊNH", "📋"),
    ]

    lines = content.split('\n')
    current_section = None
    current_icon = None
    section_content = []

    for line in lines:
        line_stripped = line.strip()

        matched = False
        for pattern, icon in section_patterns:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                if current_section and section_content:
                    sections.append({
                        "icon": current_icon,
                        "title": current_section,
                        "content": create_section_content(current_section, section_content)
                    })

                current_section = line_stripped
                current_icon = icon
                section_content = []
                matched = True
                break

        if not matched and current_section:
            if line_stripped and not line_stripped.startswith('─'):
                section_content.append(line_stripped)

    if current_section and section_content:
        sections.append({
            "icon": current_icon,
            "title": current_section,
            "content": create_section_content(current_section, section_content)
        })

    return sections

def create_section_content(title, content_lines):
    """Create HTML content for a section"""
    key_lines = content_lines[:25] if len(content_lines) > 25 else content_lines

    html_parts = []
    for line in key_lines:
        if line:
            formatted = format_line(line)
            html_parts.append(f"<p>{formatted}</p>")

    return f"<div class='info-box'>{''.join(html_parts)}</div>"

def format_line(text):
    """Format text with highlighting"""
    highlights = {
        "tăng": "<span class='highlight'>tăng</span>",
        "giảm": "<span class='danger'>giảm</span>",
        "quá mua": "<span class='danger'>quá mua</span>",
        "quá bán": "<span class='highlight'>quá bán</span>",
        "rủi ro cao": "<span class='danger'>rủi ro cao</span>",
        "rủi ro thấp": "<span class='highlight'>rủi ro thấp</span>",
        "MA20": "<strong>MA20</strong>",
        "MA50": "<strong>MA50</strong>",
        "MA200": "<strong>MA200</strong>",
        "hỗ trợ": "<span class='highlight'>hỗ trợ</span>",
        "kháng cự": "<span class='warning'>kháng cự</span>",
        "mua": "<span class='highlight'>mua</span>",
        "bán": "<span class='danger'>bán</span>",
        "CMF": "<strong>CMF</strong>",
        "RSI": "<strong>RSI</strong>",
        "ADX": "<strong>ADX</strong>",
    }

    result = text
    for key, replacement in highlights.items():
        result = result.replace(key, replacement)

    return result

def generate_javascript(index_id, index_info, sections):
    """Generate JavaScript code for an index"""
    js_code = f"""    {index_id}: {{
        title: "{index_info['name']} - PHÂN TÍCH ĐẦY ĐỦ 100%",
        sections: [
"""

    for i, section in enumerate(sections):
        is_alert = "KHUYẾN NGHỊ" in section['title'].upper() or "QUYẾT ĐỊNH" in section['title'].upper()
        alert_str = ",\n                alert: true" if is_alert else ""

        js_code += f"""            {{
                icon: "{section['icon']}",
                title: "{section['title']}",
                content: `
{section['content']}
                `{alert_str}
            }}"""

        if i < len(sections) - 1:
            js_code += ","

        js_code += "\n"

    js_code += "        ]\n    },\n"

    return js_code

def main():
    print("🚀 Parsing 3 special indices: VNSML, VNFINSELECT, VNDIAMOND...\n")

    all_js_code = ""
    total_sections = 0

    for idx_id, idx_info in INDICES.items():
        print(f"📊 Processing {idx_id.upper()} (lines {idx_info['start']}-{idx_info['end']})...")

        content = read_section(REPORT_FILE, idx_info['start'], idx_info['end'])
        sections = parse_index_data(content, idx_id)

        if sections:
            print(f"   ✅ Found {len(sections)} sections")
            total_sections += len(sections)

            js_code = generate_javascript(idx_id, idx_info, sections)
            all_js_code += js_code
        else:
            print(f"   ⚠️  No sections found")

        print()

    print(f"📈 Total: {len(INDICES)} indices, {total_sections} sections\n")

    output_file = OUTPUT_FILE
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(all_js_code)

    print(f"✅ Saved to {output_file}")

if __name__ == "__main__":
    main()
