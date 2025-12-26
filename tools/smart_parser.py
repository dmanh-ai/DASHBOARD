#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMART PARSER - Parser thông minh, tolerantes với thay đổi
Có thể xử lý nhiều format khác nhau của file Word

Phase 1: Hybrid error model - Internal exceptions + Structured public API
Phase 1.3: Normalize input text for robustness
Phase 1.5: Safe JS rendering with json.dumps
Phase 2: O(N) algorithms for index + section tokenization
Phase 3: Architecture - Parser logic separated from Renderer
"""

import re
import unicodedata
import json
from typing import List, Dict, Any, Optional
from parser_models import (
    ParserError, IndexHeaderNotFound, NoSectionsFound,
    ParsedResult, ParsedIndex, Section,
    success_result, error_result_from_exception, error_result_manual
)

# Import renderer for JS generation (Phase 3: Separation of concerns)
from renderer import js_str, render_index, render_overview


# ============================================================================
# TASK 1.3: TEXT NORMALIZATION
# ============================================================================

def normalize_text(text: str) -> str:
    """
    Normalize text cho robust parsing

    Args:
        text: Raw input text

    Returns:
        Normalized text
    """
    # 1. Strip BOM if present
    if text.startswith('\ufeff'):
        text = text[1:]

    # 2. Unicode normalization (NFC - composed form)
    text = unicodedata.normalize('NFC', text)

    # 3. Normalize newlines
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # 4. Replace weird Unicode whitespace/newlines
    # U+2028 = LINE SEPARATOR, U+2029 = PARAGRAPH SEPARATOR
    text = text.replace('\u2028', '\n').replace('\u2029', '\n')

    # 5. (Optional) Replace other weird whitespace
    # U+00A0 = non-breaking space, U+2000-U+200A = various spaces
    # Keep them for now as they might be intentional in content

    return text


# ============================================================================
# TASK 2.1: UNION REGEX FOR INDEX BOUNDARY DETECTION (O(N))
# ============================================================================

# All index codes in the system
ALL_INDEX_CODES = [
    'VNINDEX', 'VN30', 'VN100', 'VNMIDCAP', 'VNREAL',
    'VNIT', 'VNHEAL', 'VNFIN', 'VNENE', 'VNCONS',
    'VNMAT', 'VNCOND', 'VNSML', 'VNFINSELECT', 'VNDIAMOND'
]

INDEX_NAMES = ALL_INDEX_CODES  # Legacy compatibility


# ============================================================================
# TASK 2.2: O(N) SECTION TOKENIZER (FIX #1)
# ============================================================================

# Section definitions: (regex_key, icon, title)
# FIX: Use stricter patterns with line anchors to avoid false matches
_SECTION_DEFINITIONS = [
    ('^XU\\s+HƯỚNG\\s+GIÁ$', '📈', 'XU HƯỚNG GIÁ'),
    ('^XU\\s+HƯỚNG\\s+KHỐI\\s+LƯỢNG$', '📊', 'XU HƯỚNG KHỐI LƯỢNG'),
    ('^KẾT\\s+HỢP\\s+XU\\s+HƯỚNG\\s+GIÁ\\s+VÀ\\s+KHỐI\\s+LƯỢNG$', '💹', 'KẾT HỢP XU HƯỚNG GIÁ VÀ KHỐI LƯỢNG'),
    ('^CUNG(?:\\s*\\-|\\s+\\-\\s+)CẦU$', '⚖️', 'CUNG-CẦU'),
    ('^MỨC\\s+GIÁ\\s+QUAN\\s+TRỌNG$', '🎯', 'MỨC GIÁ QUAN TRỌNG'),
    ('^BIẾN\\s+ĐỘNG\\s+GIÁ$', '📉', 'BIẾN ĐỘNG GIÁ'),
    ('^MÔ\\s+HÌNH\\s+GIÁ(?:\\s+\\-|\\s+\\-\\s+)MÔ\\s+HÌNH\\s+NẾN$', '🕯️', 'MÔ HÌNH GIÁ - MÔ HÌNH NẾN'),
    ('^MARKET\\s+BREADTH(?:\\s+\\&|\\s+\\&\\s+)TÂM\\s+LÝ\\s+THỊ\\s+TRƯỜNG$', '👥', 'MARKET BREADTH & TÂM LÝ THỊ TRƯỜNG'),
    ('^LỊCH\\s+SỬ(?:\\s+\\&|\\s+\\&\\s+)XU\\s+HƯỚNG\\s+BREADTH$', '📜', 'LỊCH SỬ & XU HƯỚNG BREADTH'),
    ('^RỦI\\s+RO$', '⚠️', 'RỦI RO'),
    ('^KHUYẾN\\s+NGHỊ\\s+VỊ\\s+THẾ$', '🎯', 'KHUYẾN NGHỊ VỊ THẾ'),
    ('^GIÁ\\s+MỤC\\s+TIÊU$', '🎯', 'GIÁ MỤC TIÊU'),
    ('^KỊCH\\s+BẢN\\s+WHAT(?:\\s+\\-|\\s+\\-\\s+)IF$|^WHAT\\s+IF$', '🎲', 'KỊCH BẢN WHAT-IF'),
    ('^THÔNG\\s+TIN\\s+CHUNG$', '📊', 'THÔNG TIN CHUNG'),
    ('^TỔNG\\s+QUAN$', '📊', 'THÔNG TIN CHUNG'),
]


def _build_section_union_pattern() -> re.Pattern:
    """
    Build union regex pattern for all section headers (O(N) tokenization)

    FIX: Added $ anchor to avoid false matches in sentences

    Returns compiled pattern with named groups for each section type
    """
    # Build pattern with named groups
    #
    # NOTE: DOCX->TXT can introduce numbering/bullets before section headers.
    # To avoid brittle parsing, we accept optional prefixes like:
    # - "1. ", "1) ", "A) ", "- ", "• "
    # and optional trailing ":".
    prefix = r'(?:\s*(?:\d+\.\s*|\d+\)\s*|[A-Z]\)\s*|[-•]\s*))?'
    suffix = r'(?:\s*[:：])?'

    pattern_parts = []
    for i, (regex_key, _, _) in enumerate(_SECTION_DEFINITIONS):
        group_name = f'sec{i}'
        # Remove ^ and $ from pattern_key since we'll add them ourselves
        clean_pattern = regex_key.strip('^$')
        pattern_parts.append(rf'(?P<{group_name}>{prefix}{clean_pattern}{suffix})')

    # Join with | (OR) and wrap with anchors
    full_pattern = r'^\s*(' + '|'.join(pattern_parts) + r')\s*$'

    return re.compile(full_pattern, re.MULTILINE | re.IGNORECASE)


# Precompile section pattern once
_SECTION_UNION_PATTERN = _build_section_union_pattern()


def _get_section_info_by_match(match: re.Match) -> tuple:
    """
    Determine section info (icon, title) from match

    Args:
        match: Regex match object

    Returns:
        (icon, title) tuple
    """
    for i, (_, icon, title) in enumerate(_SECTION_DEFINITIONS):
        group_name = f'sec{i}'
        if match.group(group_name):
            return icon, title
    return None, None


def _parse_sections_from_content_optimized(index_content: str, index_code: str) -> List[Section]:
    """
    Parse sections từ index content - O(N) version

    Args:
        index_content: Nội dung của index
        index_code: Code của index (cho debug)

    Returns:
        List of Section objects

    Raises:
        NoSectionsFound: Nếu không tìm thấy section nào
    """
    # Find all section headers in O(N) with union regex
    matches = list(_SECTION_UNION_PATTERN.finditer(index_content))

    if not matches:
        raise NoSectionsFound(index_code, f"No sections found in content")

    sections = []

    # Process each match
    for i, match in enumerate(matches):
        icon, title = _get_section_info_by_match(match)
        if not icon or not title:
            continue

        # Determine section boundaries
        section_start = match.end()

        # End = start of next section, or end of content
        if i + 1 < len(matches):
            section_end = matches[i + 1].start()
        else:
            section_end = len(index_content)

        # Extract section content
        section_content = index_content[section_start:section_end].strip()

        if not section_content:
            continue

        # Format thành HTML
        html_content = format_content_smart(section_content)

        # Special handling: Tách "Kịch Bản What-if" nếu có trong content
        split_marker = 'Kịch Bản "What-if"'
        if split_marker in html_content:
            # Tách content tại marker
            parts = html_content.split(split_marker, 1)

            # Section gốc: Title cũ (phần đầu)
            section = Section(
                icon=icon,
                title=f'`{title}`',
                content=parts[0].strip(),
                alert=('KHUYẾN NGHỊ' in title)
            )
            sections.append(section)

            # Xử lý phần sau (cần loại bỏ PHẦN III nếu có)
            remaining_content = parts[1].strip()

            # Kiểm tra xem có "PHẦN III" trong phần sau không - đây là marker kết thúc, KHÔNG phải section riêng
            phan3_match = re.search(r'PHẦN\s+III\s*:', remaining_content)
            if phan3_match:
                # Cắt bỏ PHẦN III và phần sau nó (đây là bắt đầu section tiếp theo, không thuộc VNINDEX)
                whatif_content = remaining_content[:phan3_match.start()].strip()

                # Section Kịch Bản What-if (chỉ lấy phần trước PHẦN III)
                whatif_section = Section(
                    icon='🟡',
                    title='`Kịch Bản What-if`',
                    content=split_marker + whatif_content,
                    alert=False
                )
                sections.append(whatif_section)
            else:
                # Không có PHẦN III, lấy toàn bộ phần sau
                whatif_section = Section(
                    icon='🟡',
                    title='`Kịch Bản What-if`',
                    content=split_marker + remaining_content,
                    alert=False
                )
                sections.append(whatif_section)

            continue  # Skip normal processing

        # Normal processing
        section = Section(
            icon=icon,
            title=f'`{title}`',
            content=html_content,
            alert=('KHUYẾN NGHỊ' in title)
        )
        sections.append(section)

    if not sections:
        raise NoSectionsFound(index_code, f"No valid sections found")

    return sections


# ============================================================================
# TASK 2.1 (CONTINUED): INDEX HEADER BOUNDARY DETECTION
# ============================================================================

def _build_union_header_pattern() -> re.Pattern:
    """
    Build union regex pattern for all index header variants

    Returns compiled pattern that matches all index headers in 1 pass

    Pattern matches:
    - PHẦN II: PHÂN TÍCH CHỈ SỐ VNINDEX
    - 1. Chỉ số VN30 ...
    - PHÂN TÍCH CHỈ SỐ VN30
    - 1. VNREAL - Bất động sản  (industry format - PHẢI có dấu -)
    - 1. VNREAL  (bare code - KHÔNG có dấu -)
    """
    # Escape all codes for regex
    CODE_ALT = "|".join(map(re.escape, ALL_INDEX_CODES))

    # Build union pattern với named groups
    # FIX: Đảo thứ tự - industry_code PHẢI có dấu - hoặc :
    # bare_code KHÔNG được có dấu - hoặc :
    pattern = rf"""
        ^
        (?:
          PHẦN\s+[IVXLC]+\s*:\s*[^\n]*?\b(?P<part_code>{CODE_ALT})\b
          |\s*\d+\.\s*Chỉ\s*số\s+(?P<chiso_code>{CODE_ALT})\b
          |\s*PHÂN\s*TÍCH\s*CHỈ\s*SỐ\s+(?P<phan_tich_code>{CODE_ALT})\b
          |\s*\d+\.\s*(?P<industry_code>{CODE_ALT})\b\s+(?:-|—|:)
          |\s*\d+\.\s*(?P<bare_code>{CODE_ALT})\b\s*(?![-|—|:])
        )
    """

    return re.compile(pattern, re.MULTILINE | re.IGNORECASE | re.VERBOSE)


# Precompile pattern once (module level)
_UNION_HEADER_PATTERN = _build_union_header_pattern()


def _find_all_index_boundaries_1pass(content: str) -> dict[str, tuple[int, int]]:
    """
    Find all index boundaries in 1 pass O(N)

    Args:
        content: Full document content

    Returns:
        dict mapping index_code -> (start_pos, end_pos)

    Raises:
        ParserError: If boundary detection fails
    """
    # Header type priority (higher = better)
    # FIX: Ưu tiên format đầy đủ "CODE - NAME" (trong PHẦN IV)
    # hơn là bare CODE (trong PHẦN I overview)
    PRIORITY = {
        'part_code': 4,      # PHẦN II: ... VNINDEX (highest)
        'chiso_code': 3,     # 1. Chỉ số VN30 ...
        'phan_tich_code': 3, # PHÂN TÍCH CHỈ SỐ VN30
        'industry_code': 2,  # 1. VNREAL - ... (PHẦN IV analysis)
        'bare_code': 1,      # 1. VNREAL (PHẦN I overview - lowest priority)
    }

    matches = []

    # Find all matches in 1 pass
    for match in _UNION_HEADER_PATTERN.finditer(content):
        # Determine which group matched
        code = None
        group_name = None
        for gn in ['part_code', 'chiso_code', 'phan_tich_code', 'industry_code', 'bare_code']:
            group_value = match.group(gn)
            if group_value:
                code = group_value.upper()  # Normalize to uppercase
                group_name = gn
                break

        if code and group_name:
            matches.append({
                'code': code,
                'start': match.start(),
                'end': match.end(),
                'line': match.group(0),
                'priority': PRIORITY[group_name]
            })

    # Sort by position
    matches.sort(key=lambda m: m['start'])

    # For each code, select the match with HIGHEST priority
    # (i.e., prefer "PHẦN II: VNINDEX" over "2. VNINDEX")
    best_matches = {}
    for match in matches:
        code = match['code']
        if code not in best_matches or match['priority'] > best_matches[code]['priority']:
            best_matches[code] = match

    # Calculate boundaries: end = start của match tiếp theo, hoặc hết file
    boundaries = {}
    sorted_codes = sorted(best_matches.keys(), key=lambda c: best_matches[c]['start'])

    for i, code in enumerate(sorted_codes):
        start = best_matches[code]['end']  # Content starts AFTER header
        if i + 1 < len(sorted_codes):
            next_code = sorted_codes[i + 1]
            end = best_matches[next_code]['start']  # Content ends BEFORE next header
        else:
            end = len(content)

        boundaries[code] = (start, end)

    return boundaries


# ============================================================================
# LEGACY HELPER FUNCTIONS (kept for backward compatibility during transition)
# ============================================================================

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


# ============================================================================
# TASK 1.2: NEW INTERNAL API (with structured error handling)
# ============================================================================


def _parse_index_internal(content: str, index_name: str, index_code: str) -> ParsedIndex:
    """
    Internal parser - raises exceptions on error

    Args:
        content: Full document content
        index_name: Tên index (ví dụ: "VN30")
        index_code: Code cho index (ví dụ: "vn30")

    Returns:
        ParsedIndex object

    Raises:
        IndexHeaderNotFound: Nếu không tìm thấy header
        NoSectionsFound: Nếu không tìm thấy sections
    """
    # TASK 2.1: Use 1-pass boundary detection
    boundaries = _find_all_index_boundaries_1pass(content)

    # Normalize index_code to uppercase for lookup (boundaries uses uppercase)
    code_upper = index_code.upper()

    # Check if requested index exists
    if code_upper not in boundaries:
        available = list(boundaries.keys())
        raise IndexHeaderNotFound(
            index_code=index_code,
            index_name=index_name,
            debug_context={"available_indices": available}
        )

    # Get boundaries for this index
    start_pos, end_pos = boundaries[code_upper]

    # Extract nội dung index
    index_content = content[start_pos:end_pos]

    # Parse sections using O(N) tokenizer (TASK 2.2)
    sections = _parse_sections_from_content_optimized(index_content, index_code)

    # Return ParsedIndex
    return ParsedIndex(
        key=index_code,
        title=index_name,
        sections=sections
    )


def parse_index(content: str, index_name: str, index_code: str) -> ParsedResult:
    """
    Public API - Parse index với structured result

    Args:
        content: Full document content (string)
        index_name: Tên index (ví dụ: "VN30")
        index_code: Code cho index (ví dụ: "vn30")

    Returns:
        ParsedResult with status="success" or status="error"
    """
    try:
        # TASK 1.3: Normalize content before parsing
        normalized_content = normalize_text(content)
        parsed_index = _parse_index_internal(normalized_content, index_name, index_code)
        # Phase 3: Use renderer module for JS generation
        raw_js = render_index(parsed_index)
        return success_result(parsed_index, raw_js)
    except ParserError as e:
        return error_result_from_exception(e)


def _parse_overview_internal(content: str) -> ParsedIndex:
    """
    Internal overview parser - raises exceptions on error

    Args:
        content: Full document content

    Returns:
        ParsedIndex object

    Raises:
        NoSectionsFound: Nếu không tìm thấy sections
    """
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

        section = Section(
            icon=icon,
            title=f'`{title}`',
            content=format_content_smart(section_content)
        )
        sections.append(section)

    if not sections:
        raise NoSectionsFound("overview", "overview", debug_context={"content_length": len(overview_content)})

    return ParsedIndex(
        key="overview",
        title="TỔNG QUAN THỊ TRƯỜNG",
        sections=sections
    )


def parse_overview(content: str) -> ParsedResult:
    """
    Public API - Parse overview với structured result

    Args:
        content: Full document content (string)

    Returns:
        ParsedResult with status="success" or status="error"
    """
    try:
        # TASK 1.3: Normalize content before parsing
        normalized_content = normalize_text(content)
        parsed_index = _parse_overview_internal(normalized_content)
        # Phase 3: Use renderer module for JS generation
        raw_js = render_overview(parsed_index)
        return success_result(parsed_index, raw_js)
    except ParserError as e:
        return error_result_from_exception(e)


# ============================================================================
# OLD API (Backward compatibility - will be deprecated)
# ============================================================================

def parse_index_from_content(content, index_name, index_code):
    """
    Parser thông minh từ content string - tự động detect sections

    Args:
        content: Nội dung file text (string)
        index_name: Tên index (ví dụ: "VN30")
        index_code: Code cho index (ví dụ: "vn30")

    Returns:
        JavaScript object string
    """
    # Content đã được đọc từ ngoài, không cần open file nữa

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


def parse_smart(filepath, index_name, index_code):
    """
    Parser thông minh - backward compatibility wrapper

    Args:
        filepath: Đường dẫn file text
        index_name: Tên index (ví dụ: "VN30")
        index_code: Code cho index (ví dụ: "vn30")

    Returns:
        JavaScript object string
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return parse_index_from_content(content, index_name, index_code)

def parse_overview_from_content(content):
    """
    Parse phần TỔNG QUAN/OVERVIEW từ content string.

    Args:
        content: Nội dung file text (string)

    Returns:
        JavaScript object string (overview: {...})
    """
    # Content đã được đọc từ ngoài, không cần open file nữa

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


def parse_overview_smart(filepath):
    """
    Parse phần TỔNG QUAN/OVERVIEW ở đầu báo cáo - backward compatibility wrapper.

    Args:
        filepath: Đường dẫn file text

    Returns:
        JavaScript object string (overview: {...})
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return parse_overview_from_content(content)


def format_content_smart(content):
    """
    Format content thành HTML với smart parsing
    Tolerates với nhiều format khác nhau

    TASK 1.4: Generate valid HTML structure
    FIX #2: Return plain HTML (no backticks) for JS safety
    """
    lines = content.split('\n')
    html_parts = []
    in_bullet_list = False

    for line in lines:
        line = line.strip()
        if not line:
            if in_bullet_list:
                html_parts.append('</ul>')
                in_bullet_list = False
            continue

        # Detect bullet points
        if re.match(r'^[\s]*(•|[-*])\s+', line):
            if not in_bullet_list:
                html_parts.append('<ul>')
                in_bullet_list = True
            # Remove bullet marker, wrap in <li>
            clean_line = re.sub(r'^[\s]*(•|[-*])\s+', '', line)
            html_parts.append(f'<li>{clean_line}</li>')
        else:
            if in_bullet_list:
                html_parts.append('</ul>')
                in_bullet_list = False
            # Bold text: **text** or __text__
            line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
            line = re.sub(r'__(.*?)__', r'<strong>\1</strong>', line)
            html_parts.append(f'<p>{line}</p>')

    if in_bullet_list:
        html_parts.append('</ul>')

    html_content = '\n                '.join(html_parts)
    # FIX #2: Return plain HTML, NOT template literal
    return f"<div class='info-box'>{html_content}</div>"


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
