#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated parser to extract full technical analysis for all remaining indices
Reads baocao_full.txt and generates JavaScript data structure
"""

import re

# File paths
REPORT_FILE = "baocao_full.txt"
OUTPUT_FILE = "full_data_remaining.js"

# Index configurations with line ranges
INDICES = {
    "vnit": {"start": 848, "end": 980, "name": "VNIT - CÔNG NGHỆ THÔNG TIN", "icon": "💻"},
    "vnheal": {"start": 982, "end": 1163, "name": "VNHEAL - CHĂM SÓC SỨC KHỎE", "icon": "🏥"},
    "vnfin": {"start": 1164, "end": 1323, "name": "VNFIN - TÀI CHÍNH", "icon": "🏦"},
    "vnene": {"start": 1324, "end": 1464, "name": "VNENE - NĂNG LƯỢNG", "icon": "⚡"},
    "vncons": {"start": 1465, "end": 1606, "name": "VNCONS - TIÊU DÙNG THIẾT YẾU", "icon": "🛒"},
    "vnmat": {"start": 1607, "end": 1755, "name": "VNMAT - NGUYÊN VẬT LIỆU", "icon": "🔩"},
    "vncond": {"start": 1756, "end": 1900, "name": "VNCOND - HÀNG TIÊU DÙNG", "icon": "🛍️"},
}

def read_section(filename, start_line, end_line):
    """Read a specific section from the report file"""
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        # Convert to 0-based indexing and extract
        section_text = ''.join(lines[start_line-1:end_line])
    return section_text

def parse_index_data(content, index_name):
    """Parse index data and extract sections"""
    sections = []

    # Define section patterns with their icons
    section_patterns = [
        ("THÔNG TIN CHUNG", "📊"),
        ("XU HƯỚNG GIÁ", "📈"),
        ("XU HƯỚNG KHỐI LƯỢNG", "📊"),
        ("KẾT HỢP XU HƯỚNG GIÁ.*KHỐI LƯỢNG", "🔄"),
        ("CUNG.*CẦU", "⚖️"),
        ("MỨC GIÁ QUAN TRỌNG", "📍"),
        ("BIẾN ĐỘNG GIÁ", "📉"),
        ("MÔ HÌNH GIÁ.*MÔ HÌNH NẾN", "🕯️"),
        ("MARKET BREADTH.*TÂM LÝ", "📊"),
        ("LỊCH SỬ.*XU HƯỚNG BREADTH", "📜"),
        ("RỦI RO", "⚠️"),
        ("KHUYẾN NGHỊ.*VỊ THẾ", "🎯"),
        ("GIÁ MỤC TIÊU", "🎯"),
        ("KỊCH BẢN.*WHAT.*IF", "🔮"),
    ]

    # Split content into sections based on headers
    lines = content.split('\n')
    current_section = None
    current_icon = None
    section_content = []

    for line in lines:
        line_stripped = line.strip()

        # Check if this line matches a section header
        matched = False
        for pattern, icon in section_patterns:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                # Save previous section if exists
                if current_section and section_content:
                    sections.append({
                        "icon": current_icon,
                        "title": current_section,
                        "content": create_section_content(current_section, section_content)
                    })

                # Start new section
                current_section = line_stripped
                current_icon = icon
                section_content = []
                matched = True
                break

        if not matched and current_section:
            # Add line to current section content if it's not empty
            if line_stripped and not line_stripped.startswith('─'):
                section_content.append(line_stripped)

    # Don't forget the last section
    if current_section and section_content:
        sections.append({
            "icon": current_icon,
            "title": current_section,
            "content": create_section_content(current_section, section_content)
        })

    return sections

def create_section_content(title, content_lines):
    """Create HTML content for a section"""
    # Take first 15-20 lines to keep content manageable
    key_lines = content_lines[:20] if len(content_lines) > 20 else content_lines

    html_parts = []
    for line in key_lines:
        if line:
            # Format the line with HTML
            formatted = format_line(line)
            html_parts.append(f"<p>{formatted}</p>")

    # Wrap in info-box
    return f"<div class='info-box'>{''.join(html_parts)}</div>"

def format_line(text):
    """Format text with highlighting for key terms"""
    # Highlight key terms
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

    # Add each section
    for i, section in enumerate(sections):
        is_alert = "KHUYẾN NGHỊ" in section['title'].upper()
        alert_str = ",\n                alert: true" if is_alert else ""

        js_code += f"""            {{
                icon: "{section['icon']}",
                title: "{section['title']}",
                content: `
{section['content']}
                `{alert_str}
            }}"""

        # Add comma if not last section
        if i < len(sections) - 1:
            js_code += ","

        js_code += "\n"

    js_code += "        ]\n    },\n"

    return js_code

def main():
    print("🚀 Starting automated parser for all remaining indices...\n")

    all_js_code = ""
    total_sections = 0

    for idx_id, idx_info in INDICES.items():
        print(f"📊 Processing {idx_id.upper()} (lines {idx_info['start']}-{idx_info['end']})...")

        # Read the section from report
        content = read_section(REPORT_FILE, idx_info['start'], idx_info['end'])

        # Parse the data
        sections = parse_index_data(content, idx_id)

        if sections:
            print(f"   ✅ Found {len(sections)} sections")
            total_sections += len(sections)

            # Generate JavaScript
            js_code = generate_javascript(idx_id, idx_info, sections)
            all_js_code += js_code
        else:
            print(f"   ⚠️  No sections found, using placeholder")

        print()

    print(f"📈 Total: {len(INDICES)} indices, {total_sections} sections\n")

    # Save to file
    output_file = OUTPUT_FILE
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(all_js_code)

    print(f"✅ Saved to {output_file}")
    print(f"\n📝 To add this data to full_data.js:")
    print(f"1. Open {output_file}")
    print(f"2. Copy the content")
    print(f"3. Paste into full_data.js after the VNREAL section")

if __name__ == "__main__":
    main()
