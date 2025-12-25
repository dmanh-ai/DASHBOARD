#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PARSER MODELS - Data structures & Error handling cho parser
Task 1.2: Hybrid error model (exceptions nội bộ + structured result public API)
"""

from dataclasses import dataclass, field
from typing import Literal, Optional, List, Dict, Any

# Type aliases
Status = Literal["success", "error"]


# ============================================================================
# EXCEPTION CLASSES (Internal use)
# ============================================================================

class ParserError(Exception):
    """
    Base exception cho parser errors
    Dùng nội bộ trong parser functions
    """
    def __init__(self, message: str, debug_context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.debug_context = debug_context or {}

    def to_error_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for structured error reporting"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "debug": self.debug_context
        }


class IndexHeaderNotFound(ParserError):
    """Không tìm thấy header cho index trong content"""
    def __init__(self, index_code: str, index_name: str, debug_context: Optional[Dict[str, Any]] = None):
        message = f"Không tìm thấy header cho index {index_code} ({index_name})"
        super().__init__(message, debug_context)
        self.index_code = index_code
        self.index_name = index_name


class NoSectionsFound(ParserError):
    """Không tìm thấy section nào cho index"""
    def __init__(self, index_code: str, index_name: str, debug_context: Optional[Dict[str, Any]] = None):
        message = f"Không tìm thấy section nào cho index {index_code} ({index_name})"
        super().__init__(message, debug_context)
        self.index_code = index_code
        self.index_name = index_name


class InvalidBoundaries(ParserError):
    """Boundary detection thất bại"""
    def __init__(self, index_code: str, reason: str, debug_context: Optional[Dict[str, Any]] = None):
        message = f"Boundary detection thất bại cho {index_code}: {reason}"
        super().__init__(message, debug_context)
        self.index_code = index_code
        self.reason = reason


# ============================================================================
# DATA STRUCTURES (Public API)
# ============================================================================

@dataclass
class Section:
    """Một section trong index"""
    icon: str
    title: str
    content: str  # HTML string
    alert: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for rendering"""
        result = {
            "icon": self.icon,
            "title": self.title,
            "content": self.content
        }
        if self.alert:
            result["alert"] = True
        return result


@dataclass
class ParsedIndex:
    """Kết quả parse thành công cho một index"""
    key: str  # "vn30", "vnindex", etc.
    title: str
    sections: List[Section]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for rendering"""
        return {
            "key": self.key,
            "title": self.title,
            "sections": [s.to_dict() for s in self.sections]
        }


@dataclass
class ParseError:
    """Error information trong structured result"""
    error_type: str  # "IndexHeaderNotFound" | "NoSectionsFound" | ...
    message: str
    debug: Optional[Dict[str, Any]] = None


@dataclass
class ParsedResult:
    """
    Structured result cho public API
    Trả về từ parse_index() và parse_overview()
    """
    status: Status
    data: Optional[ParsedIndex] = None
    error: Optional[ParseError] = None
    raw_js: Optional[str] = None  # For backward compatibility during transition

    def is_success(self) -> bool:
        """Check if parsing succeeded"""
        return self.status == "success" and self.data is not None

    def get_error_summary(self) -> str:
        """Get error summary for logging"""
        if self.is_success():
            return "Success"
        elif self.error:
            return f"{self.error.error_type}: {self.error.message}"
        else:
            return "Unknown error"


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def success_result(data: ParsedIndex, raw_js: Optional[str] = None) -> ParsedResult:
    """Create success result"""
    return ParsedResult(
        status="success",
        data=data,
        raw_js=raw_js
    )


def error_result_from_exception(exc: ParserError) -> ParsedResult:
    """Create error result from exception"""
    return ParsedResult(
        status="error",
        error=ParseError(
            error_type=exc.__class__.__name__,
            message=exc.message,
            debug=exc.debug_context
        )
    )


def error_result_manual(error_type: str, message: str, debug: Optional[Dict[str, Any]] = None) -> ParsedResult:
    """Create error result manually"""
    return ParsedResult(
        status="error",
        error=ParseError(
            error_type=error_type,
            message=message,
            debug=debug
        )
    )
