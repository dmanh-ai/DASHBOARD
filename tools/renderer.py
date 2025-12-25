#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RENDERER - JS Generation from Parsed Data
Separates rendering logic from parsing logic
"""

import json
from typing import List

from parser_models import ParsedIndex


def js_str(s: str) -> str:
    """
    Escape string for JavaScript using json.dumps
    This prevents syntax errors from backticks, ${}, etc.

    Args:
        s: String to escape

    Returns:
        Escaped string with quotes (e.g., "'content'")
    """
    return json.dumps(s, ensure_ascii=False)


def render_index(parsed: ParsedIndex) -> str:
    """
    Render ParsedIndex to JavaScript object string

    Args:
        parsed: ParsedIndex object with key, title, sections

    Returns:
        JavaScript object string
    """
    sections_js = []
    for s in parsed.sections:
        # Use js_str for ALL user-generated strings
        # Section titles are hardcoded constants, but escape for consistency
        section_str = f"""            {{
                icon: {js_str(s.icon)},
                title: {js_str(s.title)},
                content: {js_str(s.content)}"""

        if s.alert:
            section_str += ',\n                alert: true'

        section_str += '\n            },'
        sections_js.append(section_str)

    # Use js_str for title
    js_object = f'''    {parsed.key}: {{
        title: {js_str(f"{parsed.title} - PHÂN TÍCH ĐẦY ĐỦ 100%")},
        sections: [
{chr(10).join(sections_js)[:-1]}
        ]
    }}'''

    return js_object


def render_overview(parsed: ParsedIndex) -> str:
    """
    Render ParsedIndex (overview) to JavaScript object string

    Args:
        parsed: ParsedIndex object for overview

    Returns:
        JavaScript object string
    """
    sections_js = []
    for s in parsed.sections:
        # Use js_str for ALL strings for consistency
        sections_js.append(f"""            {{
                icon: {js_str(s.icon)},
                title: {js_str(s.title)},
                content: {js_str(s.content)}
            }},""")

    return f"""    overview: {{
        title: {js_str("📊 BÁO CÁO TỔNG HỢP THỊ TRƯỜNG")},
        sections: [
{chr(10).join(sections_js)[:-1]}
        ]
    }}"""


def render_all_indices(indices_data: List[ParsedIndex], overview_data: ParsedIndex) -> str:
    """
    Render all indices + overview to complete JS file content

    Args:
        indices_data: List of ParsedIndex objects for each index
        overview_data: ParsedIndex object for overview

    Returns:
        Complete JS file content as string
    """
    js_parts = []

    # Add overview first
    js_parts.append(render_overview(overview_data))

    # Add all indices
    for index_data in indices_data:
        js_parts.append(render_index(index_data))

    # Wrap in FULL_DATA object
    full_content = "const FULL_DATA = {\n" + ",\n".join(js_parts) + "\n};"

    return full_content
