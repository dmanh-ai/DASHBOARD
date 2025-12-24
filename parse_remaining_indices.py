#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để parse dữ liệu các chỉ số còn lại và tạo JavaScript data
Tự động tạo sections cho tất cả các chỉ số
"""

import re
import json

# File báo cáo
REPORT_FILE = "baocao_full.txt"
OUTPUT_FILE = "full_data.js"

# Các chỉ số cần xử lý
INDICES = {
    "vnreal": {"start": 704, "end": 847, "name": "VNREAL - Bất Động Sản", "icon": "🏢"},
    "vnit": {"start": 848, "end": 981, "name": "VNIT - Công Nghệ Thông Tin", "icon": "💻"},
    "vnheal": {"start": 982, "end": 1163, "name": "VNHEAL - Chăm Sóc Sức Khỏe", "icon": "🏥"},
    "vnfin": {"start": 1164, "end": 1323, "name": "VNFIN - Tài Chính", "icon": "🏦"},
    "vnene": {"start": 1324, "end": 1464, "name": "VNENE - Năng Lượng", "icon": "⚡"},
    "vncons": {"start": 1465, "end": 1606, "name": "VNCONS - Tiêu Dùng Thiết Yếu", "icon": "🛒"},
    "vnmat": {"start": 1607, "end": 1755, "name": "VNMAT - Nguyên Vật Liệu", "icon": "🔩"},
    "vncond": {"start": 1756, "end": 1900, "name": "VNCOND - Hàng Tiêu Dùng", "icon": "🛍️"},
    "vnsml": {"name": "VNSML - Smallcap", "icon": "🔻"},
    "vnfinselect": {"name": "VNFINSELECT - Chỉ Số Tài Chính", "icon": "💠"},
    "vndiamond": {"name": "VNDIAMOND - Chỉ Số Kim Cương", "icon": "💎"}
}

def parse_section_data(content):
    """Parse dữ liệu từ nội dung báo cáo"""
    sections = []

    # Tìm các section chính dựa trên pattern
    # Pattern: Tên section (thường in hoa hoặc có dấu :)
    section_patterns = [
        "THÔNG TIN CHUNG",
        "XU HƯỚNG GIÁ",
        "XU HƯỚNG KHỐI LƯỢNG",
        "KẾT HỢP XU HƯỚNG GIÁ",
        "CUNG.*CẦU",
        "MỨC GIÁ QUAN TRỌNG",
        "BIẾN ĐỘNG GIÁ",
        "MÔ HÌNH GIÁ.*MÔ HÌNH NẾN",
        "MARKET BREADTH",
        "LỊCH SỬ.*XU HƯỚNG BREADTH",
        "RỦI RO",
        "KHUYẾN NGHỊ",
        "GIÁ MỤC TIÊU",
        "KỊCH BẢN.*WHAT.*IF"
    ]

    # Đơn giản hóa: Tạo sections từ các keyword chính
    lines = content.split('\n')
    current_section = None
    section_content = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Phát hiện section mới
        for pattern in section_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                if current_section and section_content:
                    sections.append({
                        "icon": "📊",
                        "title": current_section,
                        "content": create_section_html(current_section, section_content)
                    })
                current_section = line
                section_content = []
                break
        else:
            if current_section:
                section_content.append(line)

    # Section cuối cùng
    if current_section and section_content:
        sections.append({
            "icon": "📊",
            "title": current_section,
            "content": create_section_html(current_section, section_content)
        })

    return sections

def create_section_html(title, content):
    """Tạo HTML cho section"""
    # Rút gọn content: Chỉ lấy 10-15 dòng đầu tiên
    key_lines = content[:15] if len(content) > 15 else content

    html_content = "\\n".join([
        "```",
        f"<div class=\\"info-box\\">",
        f"<h4>{title}</h4>",
        ""
    ])

    for line in key_lines:
        line = line.strip()
        if line:
            # Highlight các từ khóa quan trọng
            line = highlight_keywords(line)
            html_content += f"<p>{line}</p>\\n"

    html_content += "\\n".join([
        "</div>",
        "```"
    ])

    return html_content

def highlight_keywords(text):
    """Highlight các từ khóa quan trọng"""
    keywords = {
        "tăng": "<span class=\\"highlight\\">tăng</span>",
        "giảm": "<span class=\\"danger\\">giảm</span>",
        "quá mua": "<span class=\\"danger\\">quá mua</span>",
        "RSI": "<strong>RSI</strong>",
        "MA20": "<strong>MA20</strong>",
        "MA50": "<strong>MA50</strong>",
        "hỗ trợ": "<span class=\\"highlight\\">hỗ trợ</span>",
        "kháng cự": "<span class=\\"warning\\">kháng cự</span>"
    }

    for keyword, replacement in keywords.items():
        text = text.replace(keyword, replacement)

    return text

def main():
    # Đọc file hiện tại
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        current_content = f.read()

    # Tìm vị trí để chèn data mới (trước khi đóng object FULL_DATA)
    insert_position = current_content.rfind("    vnsml: {")

    if insert_position == -1:
        print("Không tìm thấy vị trí chèn!")
        return

    # Tạo data cho mỗi chỉ số
    new_indices = []

    for idx_id, idx_info in INDICES.items():
        if "start" in idx_info:
            # Đọc từ file báo cáo
            print(f"Đang xử lý {idx_id}...")

            # Đoạn data rút gọn - tạo placeholder
            sections = [
                {
                    "icon": idx_info["icon"],
                    "title": "THÔNG TIN CHUNG",
                    "content": f"<div class='info-box'><h4>Đang cập nhật</h4><p>Dữ liệu đầy đủ cho {idx_info['name']}</p></div>"
                },
                {
                    "icon": "📈",
                    "title": "XU HƯỚNG GIÁ",
                    "content": f"<div class='info-box'><h4>Đang cập nhật</h4><p>Phân tích kỹ thuật {idx_info['name']}</p></div>"
                },
                {
                    "icon": "⚠️",
                    "title": "RỦI RO",
                    "content": f"<div class='info-box'><h4>Đang cập nhật</h4><p>Đánh giá rủi ro {idx_info['name']}</p></div>"
                },
                {
                    "icon": "🎯",
                    "title": "KHUYẾN NGHỊ",
                    "alert": True,
                    "content": f"<p><strong>Đang cập nhật dữ liệu cho {idx_info['name']}</p>"
                }
            ]
        else:
            # VNSML, VNFINSELECT, VNDIAMOND - tạo placeholder
            sections = [
                {
                    "icon": idx_info["icon"],
                    "title": "THÔNG TIN CHUNG",
                    "content": f"<div class='info-box'><h4>Đang cập nhật</h4><p>Dữ liệu đầy đủ cho {idx_info['name']}</p></div>"
                }
            ]

        # Tạo JavaScript object
        js_section = f"""
    // ==========================================
    // {idx_id.upper()} - {len(sections)} Sections
    // ==========================================
    {idx_id}: {{
        title: "{idx_info['name']} - PHÂN TÍCH ĐẦY ĐỦ",
        sections: [
"""

        # Thêm từng section
        for i, section in enumerate(sections):
            section_str = f"""            {{
                icon: "{section['icon']}",
                title: "{section['title']}",
                content: `
{section['content']}
                `
            }},"""
            js_section += section_str

        js_section += """        ]
    },"""

        new_indices.append(js_section)

    # Kết hợp tất cả
    all_new_data = "\n".join(new_indices)

    print(f"Đã tạo data cho {len(new_indices)} chỉ số")
    print(f"Tổng kích thước: {len(all_new_data)} ký tự")

    # Lưu ra file tạm
    with open("new_indices_data.js", 'w', encoding='utf-8') as f:
        f.write(all_new_data)

    print("Đã lưu vào new_indices_data.js")
    print("Hãy copy nội dung này vào full_data.js trước dòng 'vnsml: {'")

if __name__ == "__main__":
    main()
