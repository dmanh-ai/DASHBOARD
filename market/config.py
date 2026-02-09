"""
Cấu hình chỉ số và mapping cho pipeline tự động.
"""

# ============================================================================
# INDEX DEFINITIONS
# ============================================================================

# Map: key trong FULL_DATA → (code CSV file, tên hiển thị)
# 15 chỉ số có data từ repo dmanh-ai/vnstock
INDICES = {
    "vnindex":     ("VNINDEX",     "VNINDEX"),
    "vn30":        ("VN30",        "VN30"),
    "vn100":       ("VN100",       "VN100"),
    "vnmidcap":    ("VNMID",       "VNMIDCAP"),
    "vnsml":       ("VNSML",       "VNSML"),
    "vnreal":      ("VNREAL",      "VNREAL"),
    "vnit":        ("VNIT",        "VNIT"),
    "vnheal":      ("VNHEAL",      "VNHEAL"),
    "vnfin":       ("VNFIN",       "VNFIN"),
    "vnene":       ("VNENE",       "VNENE"),
    "vncons":      ("VNCONS",      "VNCONS"),
    "vnmat":       ("VNMAT",       "VNMAT"),
    "vncond":      ("VNCOND",      "VNCOND"),
    "vnfinselect": ("VNFINSELECT", "VNFINSELECT"),
    "vndiamond":   ("VNDIAMOND",   "VNDIAMOND"),
}

# CSV files có sẵn trên repo dmanh-ai/vnstock (data/indices/)
# Dashboard key → CSV filename
AVAILABLE_CSV = {
    "vnindex":     "VNINDEX.csv",
    "vn30":        "VN30.csv",
    "vn100":       "VN100.csv",
    "vnmidcap":    "VNMID.csv",
    "vnsml":       "VNSML.csv",
    "vnreal":      "VNREAL.csv",
    "vnit":        "VNIT.csv",
    "vnheal":      "VNHEAL.csv",
    "vnfin":       "VNFIN.csv",
    "vnene":       "VNENE.csv",
    "vncons":      "VNCONS.csv",
    "vnmat":       "VNMAT.csv",
    "vncond":      "VNCOND.csv",
    "vnfinselect": "VNFINSELECT.csv",
    "vndiamond":   "VNDIAMOND.csv",
}

# Giá trong CSV bị scale 1/1000
PRICE_SCALE = 1000.0

# GitHub raw URL cho data
GITHUB_DATA_URL = "https://raw.githubusercontent.com/dmanh-ai/vnstock/main/data/indices"

# Thứ tự phần trong báo cáo
# PART_ORDER: tất cả chỉ số (dùng cho overview - cần data tất cả để xếp hạng/phân tích ngành)
PART_ORDER = [
    "overview",
    "vnindex", "vn30", "vn100", "vnmidcap",
    "vnreal", "vnit", "vnheal", "vnfin",
    "vnene", "vncons", "vnmat", "vncond",
    "vnsml", "vnfinselect", "vndiamond",
]

# REPORT_INDICES: chỉ số được viết phân tích AI chi tiết (12 sections mỗi chỉ số)
REPORT_INDICES = ["vnindex", "vn30", "vn100", "vnmidcap"]

# 12 section titles cho mỗi chỉ số (phải khớp regex trong smart_parser.py)
INDEX_SECTIONS = [
    "XU HƯỚNG GIÁ",
    "XU HƯỚNG KHỐI LƯỢNG",
    "KẾT HỢP XU HƯỚNG GIÁ VÀ KHỐI LƯỢNG",
    "CUNG-CẦU",
    "MỨC GIÁ QUAN TRỌNG",
    "BIẾN ĐỘNG GIÁ",
    "MARKET BREADTH & TÂM LÝ THỊ TRƯỜNG",
    "RỦI RO",
    "KHUYẾN NGHỊ VỊ THẾ",
    "GIÁ MỤC TIÊU",
    "KỊCH BẢN WHAT-IF",
    "THÔNG TIN CHUNG",
]

# 7 section titles cho overview
OVERVIEW_SECTIONS = [
    "TỔNG QUAN THỊ TRƯỜNG",
    "PHÂN TÍCH MỐI QUAN HỆ",
    "DÒNG TIỀN & XU HƯỚNG",
    "HỘI TỤ KỸ THUẬT",
    "XẾP HẠNG",
    "PHÂN TÍCH NGÀNH",
    "NHẬN ĐỊNH",
]

# Số ngày lịch sử cần lấy
HISTORY_DAYS = 250
# Số ngày cho foreign flow
FOREIGN_FLOW_DAYS = 20
# Số CP top gainers/losers cho heatmap
HEATMAP_TOP_K = 30

# Claude model
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
CLAUDE_MAX_TOKENS = 8192
