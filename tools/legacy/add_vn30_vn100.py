#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add VN30 and VN100 to full_data.js
"""

import re

def parse_index_from_txt(filepath, start_line, end_line, index_name, title_prefix):
    """Parse index data from baocao_full.txt"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Extract lines for this index
    content_lines = lines[start_line-1:end_line]
    content = ''.join(content_lines)

    # Find sections by looking for section headers
    # Sections are typically on lines like "Xu Hướng Giá", "Xu Hướng Khối Lượng", etc.
    sections = []

    # Common section patterns to look for
    section_patterns = [
        ('📊', 'THÔNG TIN CHUNG'),
        ('📈', 'XU HƯỚNG GIÁ'),
        ('📊', 'XU HƯỚNG KHỐI LƯỢNG'),
        ('💹', 'KẾT HỢP XU HƯỚNG GIÁ & KHỐI LƯỢNG'),
        ('⚖️', 'CUNG-CẦU'),
        ('🎯', 'MỨC GIÁ QUAN TRỌNG'),
        ('📉', 'BIẾN ĐỘNG GIÁ'),
        ('🕯️', 'MÔ HÌNH GIÁ - MÔ HÌNH NẾN'),
        ('👥', 'MARKET BREADTH & TÂM LÝ THỊ TRƯỜNG'),
        ('📜', 'LỊCH SỬ & XU HƯỚNG BREADTH'),
        ('⚠️', 'RỦI RO'),
        ('🎯', 'KHUYẾN NGHỊ VỊ THẾ'),
        ('🎯', 'GIÁ MỤC TIÊU'),
        ('🎲', 'KỊCH BẢN WHAT-IF'),
    ]

    # For now, create a simplified version with main sections
    # Parse the content and extract key information

    # Extract key-value pairs and create HTML content
    html_content = f"""<div class='info-box'><h4>Phân tích chi tiết {index_name.upper()}</h4><p>Được lấy từ báo cáo gốc (lines {start_line}-{end_line}).</p></div>"""

    # Try to find common sections
    current_pos = 0
    section_count = 0

    # Add basic info section
    sections.append({
        'icon': '📊',
        'title': 'THÔNG TIN CHUNG',
        'content': f"<div class='info-box'>{html_content}</div>".replace('html_content', f"<p>{content[:500]}...</p>")
    })

    # Add more sections based on content patterns
    if 'Xu Hướng Giá' in content:
        sections.append({
            'icon': '📈',
            'title': 'XU HƯỚNG GIÁ',
            'content': f"<div class='info-box'><p>{content[:800]}</p></div>"
        })
        section_count += 1

    if 'Xu Hướng Khối Lượng' in content:
        sections.append({
            'icon': '📊',
            'title': 'XU HƯỚNG KHỐI LƯỢNG',
            'content': f"<div class='info-box'><p>{content[800:1600]}</p></div>"
        })
        section_count += 1

    # For now, create placeholder sections that will be filled with actual content
    for i, (icon, title) in enumerate(section_patterns):
        if i >= len(sections):
            sections.append({
                'icon': icon,
                'title': title,
                'content': f"<div class='info-box'><p>Dữ liệu đang được cập nhật từ báo cáo gốc...</p></div>"
            })

    return sections[:13]  # Limit to 13 sections for now

print("Script ready to parse VN30 and VN100")
print("This will add these indices to full_data.js")
