#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMART PARSER - Parser thông minh, tolerantes với thay đổi
Có thể xử lý nhiều format khác nhau của file Word
"""

import re

INDEX_NAMES = [
    'VNINDEX', 'VN30', 'VN100', 'VNMIDCAP', 'VNREAL',
    'VNIT', 'VNHEAL', 'VNFIN', 'VNENE', 'VNCONS',
    'VNMAT', 'VNCOND', 'VNSML', 'VNFINSELECT', 'VNDIAMOND'
]

def _find_index_header(content, index_name):
    patterns = [
        rf'^\s*PHẦN\s+[IVXLC]+\s*:\s*.*\b{re.escape(index_name)}\b.*$',
        rf'^\s*\d+\.\s*Chỉ\s*số\s+\b{re.escape(index_name)}\b.*$',
        rf'^\s*PHÂN\s*TÍCH\s*CHỈ\s*SỐ\s+\b{re.escape(index_name)}\b.*$',
        rf'^\s*\b{re.escape(index_name)}\b\s*$',
    ]

    best_match = None
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
        if match and (best_match is None or match.start() < best_match.start()):
            best_match = match

    return best_match

def _find_next_index_header_start(content, start_pos, current_index_name):
    index_alternation = "|".join(map(re.escape, INDEX_NAMES))
    next_header_pattern = (
        rf'^\s*PHẦN\s+[IVXLC]+\s*:\s*.*$'
        rf'|^\s*\d+\.\s*Chỉ\s*số\s+(?:{index_alternation})\b.*$'
        rf'|^\s*PHÂN\s*TÍCH\s*CHỈ\s*SỐ\s+(?:{index_alternation})\b.*$'
    )

    best = None
    for match in re.finditer(next_header_pattern, content[start_pos:], re.IGNORECASE | re.MULTILINE):
        text = match.group(0)
        if re.search(rf'\b{re.escape(current_index_name)}\b', text, re.IGNORECASE):
            continue
        absolute = start_pos + match.start()
        if best is None or absolute < best:
            best = absolute

    return best

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
    index_match = _find_index_header(content, index_name)

    if not index_match:
        return f"# LỖI: Không tìm thấy {index_name} trong file\n"

    # 2. Tìm vị trí bắt đầu (sau header index)
    start_pos = index_match.end()

    # 3. Tìm vị trí kết thúc (đầu index tiếp theo hoặc hết file)
    next_start = _find_next_index_header_start(content, start_pos, index_name)
    end_pos = next_start if next_start is not None else len(content)

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

def parse_overview_smart(filepath):
    """
    Parse phần TỔNG QUAN/OVERVIEW ở đầu báo cáo (trước VNINDEX).

    Returns:
        JavaScript object string (overview: {...})
    """

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Overview nằm trước phần phân tích VNINDEX (tránh match tên index trong phần "coverage" ở đầu)
    first_index_match = re.search(r'^\s*PHẦN\s+II\b.*$', content, re.IGNORECASE | re.MULTILINE)
    overview_content = content[:first_index_match.start()] if first_index_match else content

    overview_sections = [
        ('📊', 'TỔNG QUAN THỊ TRƯỜNG', r'^\s*\d+\.\s*TỔNG\s*QUAN\s*THỊ\s*TRƯỜNG\b.*$'),
        ('🔗', 'PHÂN TÍCH MỐI QUAN HỆ', r'^\s*\d+\.\s*PHÂN\s*TÍCH\s*MỐI\s*QUAN\s*HỆ\b.*$'),
        ('💰', 'DÒNG TIỀN & XU HƯỚNG', r'^\s*\d+\.\s*DÒNG\s*TIỀN\s*&\s*XU\s*HƯỚNG\b.*$'),
        ('🧩', 'HỘI TỤ KỸ THUẬT', r'^\s*\d+\.\s*HỘI\s*TỤ\s*KỸ\s*THUẬT\b.*$'),
        ('🏆', 'XẾP HẠNG', r'^\s*\d+\.\s*XẾP\s*HẠNG\b.*$'),
        ('🏭', 'PHÂN TÍCH NGÀNH', r'^\s*\d+\.\s*PHÂN\s*TÍCH\s*NGÀNH\b.*$'),
        ('📝', 'NHẬN ĐỊNH', r'^\s*\d+\.\s*NHẬN\s*ĐỊNH\b.*$'),
    ]

    sections = []
    for icon, title, pattern in overview_sections:
        match = re.search(pattern, overview_content, re.IGNORECASE | re.MULTILINE)
        if not match:
            continue

        start = match.end()

        # Find nearest next section header occurrence
        end = len(overview_content)
        for _, __, next_pattern in overview_sections:
            next_match = re.search(next_pattern, overview_content[start:], re.IGNORECASE | re.MULTILINE)
            if next_match:
                end = min(end, start + next_match.start())

        section_content = overview_content[start:end].strip()
        if not section_content:
            continue

        sections.append({
            'icon': icon,
            'title': f'`{title}`',
            'content': format_content_smart(section_content),
        })

    if not sections:
        return "# LỖI: Không tìm thấy section nào cho OVERVIEW\n"

    # Custom title để giống full_data.js hiện tại
    sections_js = []
    for s in sections:
        sections_js.append(f"""            {{
                icon: "{s['icon'].replace('`', '')}",
                title: {s['title']},
                content: {s['content']}
            }},""")

    return f"""    overview: {{
        title: `📊 BÁO CÁO TỔNG HỢP THỊ TRƯỜNG`,
        sections: [
{chr(10).join(sections_js)[:-1]}
        ]
    }}"""


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
    import sys

    filepath = sys.argv[1] if len(sys.argv) > 1 else 'baocao_full.txt'

    # Tự động parse VN30 - không cần hardcode line numbers!
    vn30_js = parse_smart(filepath, 'VN30', 'vn30')

    print("✅ Smart Parser Output:")
    print(vn30_js[:500] + "...")
