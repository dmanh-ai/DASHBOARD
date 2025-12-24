#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMART PARSER - Parser thông minh, tolerantes với thay đổi
Có thể xử lý nhiều format khác nhau của file Word
"""

import re

def parse_smart(filepath, index_name, index_code):
    """
    Parser thông minh - tự động detect sections

    Args:
        filepath: Đường dẫn file text
        index_name: Tên index (ví dụ: "VN30")
        index_code: Code cho index (ví dụ: "vn30")

    Returns:
        JavaScript object string
    """

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. TỰ ĐỘNG TÌM VỊ TRÍ INDEX (không hardcode line numbers)
    index_pattern = rf'{index_name}[^a-zA-Z]'  # Tìm "VN30" hoặc "VN30 - RỒNG VÀNG"
    index_match = re.search(index_pattern, content)

    if not index_match:
        return f"# LỖI: Không tìm thấy {index_name} trong file\n"

    # 2. Tìm vị trí bắt đầu (sau header index)
    start_pos = index_match.end()

    # 3. Tìm vị trí kết thúc (đầu index tiếp theo hoặc hết file)
    # Tìm các index khác nhưVN100, VNMIDCAP, VNREAL, etc.
    other_indices = ['VNINDEX', 'VN30', 'VN100', 'VNMIDCAP', 'VNREAL',
                     'VNIT', 'VNHEAL', 'VNFIN', 'VNENE', 'VNCONS',
                     'VNMAT', 'VNCOND', 'VNSML', 'VNFINSELECT', 'VNDIAMOND']

    end_pos = len(content)
    for other_index in other_indices:
        if other_index != index_name:
            pattern = rf'{other_index}[^a-zA-Z]'
            match = re.search(pattern, content[start_pos:])
            if match:
                end_pos = start_pos + match.start()
                break

    # 4. Extract nội dung index
    index_content = content[start_pos:end_pos]

    # 5. TỰ ĐỘNG DETECT SECTIONS (flexible patterns)
    sections = []

    # Pattern FLEXIBLE - tolerates với spacing, format
    section_patterns = [
        (r'XU.*HƯỚNG.*GIÁ', '📈', 'XU HƯỚNG GIÁ'),
        (r'XU.*HƯỚNG.*KHỐI.*LƯỢNG', '📊', 'XU HƯỚNG KHỐI LƯỢNG'),
        (r'KẾT.*HỢP.*XU.*HƯỚNG', '💹', 'KẾT HỢP XU HƯỚNG GIÁ VÀ KHỐI LƯỢNG'),
        (r'CUNG.*CẦU|CUNG.*CẦU', '⚖️', 'CUNG-CẦU'),
        (r'MỨC.*GIÁ.*QUAN.*TRỌNG', '🎯', 'MỨC GIÁ QUAN TRỌNG'),
        (r'BIẾN.*ĐỘNG.*GIÁ', '📉', 'BIẾN ĐỘNG GIÁ'),
        (r'MÔ.*HÌNH.*GIÁ.*MÔ.*HÌNH.*NẾN', '🕯️', 'MÔ HÌNH GIÁ - MÔ HÌNH NẾN'),
        (r'MARKET.*BREADTH|TÂM.*LÝ.*THỊ.*TRƯỜNG', '👥', 'MARKET BREADTH & TÂM LÝ THỊ TRƯỜNG'),
        (r'LỊCH.*SỬ.*XU.*HƯỚNG.*BREADTH', '📜', 'LỊCH SỬ & XU HƯỚNG BREADTH'),
        (r'RỦI.*RO', '⚠️', 'RỦI RO'),
        (r'KHUYẾN.*NGHỊ.*VỊ.*THẾ', '🎯', 'KHUYẾN NGHỊ VỊ THẾ'),
        (r'GIÁ.*MỤC.*TIÊU', '🎯', 'GIÁ MỤC TIÊU'),
        (r'KỊCH.*BẢN.*WHAT.*IF|WHAT.*IF', '🎲', 'KỊCH BẢN WHAT-IF'),
        (r'THÔNG.*TIN.*CHUNG', '📊', 'THÔNG TIN CHUNG'),
        (r'TỔNG.*QUAN', '📊', 'THÔNG TIN CHUNG'),
    ]

    # Tìm tất cả sections
    for pattern, icon, title in section_patterns:
        match = re.search(pattern, index_content, re.IGNORECASE)
        if match:
            # Extract content từ đây đến section tiếp theo
            section_start = match.end()

            # Tìm section tiếp theo
            next_section_pos = len(index_content)
            for next_pattern, _, _ in section_patterns:
                next_match = re.search(next_pattern, index_content[section_start:], re.IGNORECASE)
                if next_match and next_match.start() < next_section_pos:
                    next_section_pos = next_match.start()

            # Extract content
            section_content = index_content[section_start:section_start + next_section_pos].strip()

            # Format thành HTML
            if section_content:
                html_content = format_content_smart(section_content)

                section_obj = {
                    'icon': icon,
                    'title': f'`{title}`',
                    'content': html_content
                }

                # Add alert flag cho KHUYẾN NGHỊ
                if 'KHUYẾN NGHỊ' in title:
                    section_obj['alert'] = True

                sections.append(section_obj)

    # 6. Generate JavaScript object
    return generate_js_object_smart(index_code, index_name, sections)


def format_content_smart(content):
    """
    Format content thành HTML với smart parsing
    Tolerates với nhiều format khác nhau
    """

    # Xử lý các dạng list khác nhau
    # 1. Bullet points: • or -
    content = re.sub(r'^[•\-]\s*', '<li>', content, flags=re.MULTILINE)

    # 2. Numbered lists: 1. 2. 3.
    content = re.sub(r'^\d+\.\s+', '<li>', content, flags=re.MULTILINE)

    # 3. Bold text: **text** or __text__
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)

    # 4. Wrap paragraphs
    paragraphs = re.split(r'\n\s*\n', content)
    html_parts = []

    for para in paragraphs:
        para = para.strip()
        if para:
            # Clean up extra whitespace
            para = re.sub(r'\s+', ' ', para)
            # Wrap in p tag if not already wrapped
            if not para.startswith('<'):
                para = f'<p>{para}</p>'
            html_parts.append(para)

    html_content = '\n                '.join(html_parts)
    return f"`<div class='info-box'>{html_content}</div>`"


def generate_js_object_smart(index_code, index_name, sections):
    """Generate JavaScript object với consistent format"""

    if not sections:
        return f"    # LỖI: Không tìm thấy sections nào cho {index_name}\n"

    sections_js = []
    for s in sections:
        section_str = f"""            {{
                icon: "{s['icon'].replace('`', '')}",
                title: {s['title']},
                content: {s['content']}"""

        if s.get('alert'):
            section_str += ',\n                alert: true'

        section_str += '\n            },'
        sections_js.append(section_str)

    js_object = f'''    {index_code}: {{
        title: `{index_name} - PHÂN TÍCH ĐẦY ĐỦ 100%`,
        sections: [
{chr(10).join(sections_js)[:-1]}
        ]
    }}'''

    return js_object


# Example usage
if __name__ == '__main__':
    filepath = '/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/UI GLM/baocao_full.txt'

    # Tự động parse VN30 - không cần hardcode line numbers!
    vn30_js = parse_smart(filepath, 'VN30', 'vn30')

    print("✅ Smart Parser Output:")
    print(vn30_js[:500] + "...")
