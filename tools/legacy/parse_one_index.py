#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PARSER CHUẨN - Tái sử dụng cho các báo cáo khác
Parse chỉ số từ file text và tạo JavaScript object với format chuẩn
"""

import re
from pathlib import Path

def parse_index_from_txt(filepath, index_code, index_name, start_line, end_line=None):
    """
    Parse chỉ số từ file text baocao_full.txt

    Args:
        filepath: Đường dẫn đến file text
        index_code: Mã chỉ số (ví dụ: vn30, vn100)
        index_name: Tên chỉ số đầy đủ (ví dụ: VN30 - RỒNG VÀNG)
        start_line: Dòng bắt đầu
        end_line: Dòng kết thúc (optional)

    Returns:
        JavaScript object string với format chuẩn
    """

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Extract content
    if end_line:
        content_lines = lines[start_line-1:end_line]
    else:
        content_lines = lines[start_line-1:]

    content = ''.join(content_lines)

    # Find sections - look for headers
    sections = []

    # Pattern để tìm section headers (đầu dòng, in hoa, có dấu . ở cuối)
    section_pattern = r'^([A-ZÀ-ỸẲỨỪỰẦÂĂĐÊÔƠÙỨỰỲỴỶỨỪẤẮẰỰÝỴ]+.*[^a-zA-Z0-9]\n)'

    # Tìm tất cả sections
    section_titles = []
    for i, line in enumerate(content_lines):
        if re.match(section_pattern, line.strip()):
            section_titles.append((i+start_line, line.strip()))

    print(f"📊 Tìm thấy {len(section_titles)} sections tiềm năng")

    # Tạo sections object với icons mapping
    icon_map = {
        'THÔNG TIN CHUNG': '📊',
        'GIÁ & THAY ĐỔI': '📊',
        'TỔNG QUAN': '📊',
        'XU HƯỚNG GIÁ': '📈',
        'XU HƯỚNG KHỐI LƯỢNG': '📊',
        'KẾT HỢP XU HƯỚNG GIÁ & KHỐI LƯỢNG': '💹',
        'KẾT HỢP XU HƯỚNG GIÁ VÀ KHỐI LƯỢNG': '💹',
        'CUNG-CẦU': '⚖️',
        'CUNG - CẦU': '⚖️',
        'MỨC GIÁ QUAN TRỌNG': '🎯',
        'MỨC GIÁ QUAN TRỌNG': '🎯',
        'BIẾN ĐỘNG GIÁ': '📉',
        'MÔ HÌNH GIÁ - MÔ HÌNH NẾN': '🕯️',
        'MÔ HÌNH GIÁ': '🕯️',
        'MÔ HÌNH NẾN': '🕯️',
        'MARKET BREADTH': '👥',
        'TÂM LÝ THỊ TRƯỜNG': '👥',
        'MARKET BREADTH & TÂM LÝ THỊ TRƯỜNG': '👥',
        'LỊCH SỬ & XU HƯỚNG BREADTH': '📜',
        'RỦI RO': '⚠️',
        'KHUYẾN NGHỊ VỊ THẾ': '🎯',
        'GIÁ MỤC TIÊU': '🎯',
        'KỊCH BẢN WHAT-IF': '🎲',
    }

    # Parse từng section
    for i, (line_num, title) in enumerate(section_titles):
        # Lấy icon
        icon = icon_map.get(title, '📊')

        # Lấy content (đến section tiếp theo hoặc hết)
        if i < len(section_titles) - 1:
            next_line = section_titles[i+1][0]
            section_content_lines = content_lines[
                (line_num - start_line + 1):(section_titles[i+1][0] - start_line)
            ]
        else:
            section_content_lines = content_lines[(line_num - start_line + 1):]

        section_content = ''.join(section_content_lines).strip()

        # Format content thành HTML
        html_content = format_content_to_html(section_content, title)

        sections.append({
            'icon': icon,
            'title': title,
            'content': html_content
        })

    # Tạo JavaScript object string
    js_object = generate_js_object(index_code, index_name, sections)

    return js_object


def format_content_to_html(content, section_title):
    """
    Format plain text content thành HTML
    """
    # Đơn giản hóa - wrap content trong div
    paragraphs = content.split('\n\n')

    html_parts = []
    for para in paragraphs:
        para = para.strip()
        if para:
            # Convert bold text
            para = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', para)
            # Add paragraph tags
            html_parts.append(f'<p>{para}</p>')

    html_content = '<div class="info-box">\n    ' + '\n    '.join(html_parts) + '\n</div>'

    return f'`{html_content}`'


def generate_js_object(index_code, index_name, sections):
    """
    Tạo JavaScript object string
    """

    # Determine if this has alert section (KHUYẾN NGHỊ VỊ THẾ)
    has_alert = any('KHUYẾN NGHỊ' in s['title'] for s in sections)

    sections_js = []
    for s in sections:
        section_str = f'''            {{
                icon: "{s['icon']}",
                title: `{s['title']}`,
                content: {s['content']}'''

        # Add alert flag if applicable
        if 'alert' in s or s['title'] == 'KHUYẾN NGHỊ VỊ THẾ':
            section_str += ',\n                alert: true'

        section_str += '\n            },'
        sections_js.append(section_str)

    js_object = f'''    {index_code}: {{
        title: `{index_name} - PHÂN TÍCH ĐẦY ĐỦ 100%`,
        sections: [
{chr(10).join(sections_js)[:-1]}  # Remove trailing comma
        ]
    }}'''

    return js_object


def main():
    """
    Main function để test parser
    """
    project_root = Path(__file__).resolve().parents[2]
    filepath = str(project_root / 'baocao_full.txt')

    # Test với VN30
    print("🔧 Testing parser với VN30...\n")

    vn30_js = parse_index_from_txt(
        filepath=filepath,
        index_code='vn30',
        index_name='VN30',
        start_line=224,
        end_line=395
    )

    print("\n✅ Parser test hoàn thành!")
    print(f"📊 Output length: {len(vn30_js)} chars")


if __name__ == '__main__':
    main()
