"""
Dùng Claude API để viết báo cáo phân tích thị trường.
Output: reports/txt/BaoCao_YYYYMMDD_HHMMSS.txt
"""

import json
import os
import sys
import logging
import time
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    INDICES, PART_ORDER, REPORT_INDICES, INDEX_SECTIONS, OVERVIEW_SECTIONS,
    CLAUDE_MODEL, CLAUDE_MAX_TOKENS,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / "market_cache"
REPORTS_DIR = PROJECT_ROOT / "reports" / "txt"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# LOAD CACHED DATA
# ============================================================================

def load_json(filename):
    path = CACHE_DIR / filename
    if not path.exists():
        log.warning(f"Cache file not found: {path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_data():
    """Load tất cả data đã thu thập."""
    return {
        "index_ohlcv": load_json("index_ohlcv.json"),
        "breadth": load_json("breadth_snapshot.json"),
        "bondlab": load_json("bondlab_data.json"),
        "stock_snapshot": load_json("stock_snapshot.json"),
        "foreign": load_json("foreign_data.json"),
        "commodities": load_json("commodities_data.json"),
    }


# ============================================================================
# PREPARE DATA SUMMARIES FOR CLAUDE
# ============================================================================

def prepare_index_summary(key, data):
    """Chuẩn bị tóm tắt data cho 1 chỉ số để gửi Claude.
    Dùng indicators đã tính sẵn từ CSV (collect_data.py lưu trong index_ohlcv.json).
    """
    index_data = data["index_ohlcv"].get("indices", {}).get(key, {})
    bars = index_data.get("bars", [])

    if not bars:
        return None

    # Indicators đã được enrich sẵn bởi collect_data.py
    indicators = index_data.get("indicators", {})
    latest_info = index_data.get("latest", {})
    recent_bars = bars[-20:]

    return {
        "index_name": INDICES[key][1],
        "latest": {
            "date": latest_info.get("date", bars[-1]["d"]),
            "close": latest_info.get("close", bars[-1]["c"]),
            "change": latest_info.get("change", 0),
            "change_pct": latest_info.get("change_pct", 0),
        },
        "indicators": indicators,
        "recent_20_bars": [
            {"d": b["d"], "c": b["c"], "v": b["v"]} for b in recent_bars
        ],
    }


def prepare_overview_summary(data):
    """Chuẩn bị tóm tắt tổng quan cho overview."""
    summaries = {}
    for key in PART_ORDER[1:]:  # Skip "overview"
        s = prepare_index_summary(key, data)
        if s:
            ind = s["indicators"]
            # Compute 20-day performance from recent bars
            bars_20 = s.get("recent_20_bars", [])
            perf_20d = None
            if len(bars_20) >= 2:
                first_c = bars_20[0].get("c", 0)
                last_c = bars_20[-1].get("c", 0)
                if first_c and first_c > 0:
                    perf_20d = round((last_c / first_c - 1) * 100, 2)
            summaries[key] = {
                "name": s["index_name"],
                "close": s["latest"]["close"],
                "change_pct": s["latest"]["change_pct"],
                "perf_20d": perf_20d,
                "rsi14": ind.get("rsi_14") or ind.get("rsi14"),
                "above_ma20": ind.get("above_ma20"),
            }

    breadth = data["breadth"]

    # Pre-compute MA20 status for money flow analysis
    above_ma20 = []
    below_ma20 = []
    for key, s in summaries.items():
        if s.get("above_ma20") is True:
            above_ma20.append(s["name"])
        elif s.get("above_ma20") is False:
            below_ma20.append(s["name"])

    return {
        "date": data["index_ohlcv"].get("asof", ""),
        "indices_summary": summaries,
        "breadth": breadth,
        "above_ma20": above_ma20,
        "below_ma20": below_ma20,
    }


# ============================================================================
# CLAUDE API PROMPTS
# ============================================================================

SYSTEM_PROMPT = """Bạn là chuyên gia phân tích kỹ thuật chứng khoán Việt Nam hàng đầu.
Viết phân tích bằng tiếng Việt, chuyên nghiệp, chi tiết với dẫn chứng số liệu cụ thể.

QUY TẮC FORMAT BẮT BUỘC cho mỗi section phân tích chỉ số:
- Bắt đầu bằng "Kết luận ngắn:" (1 câu tóm tắt rõ ràng)
- Tiếp theo "Dẫn chứng & Ý nghĩa:" (đánh số 1, 2, 3... mỗi điểm có tiêu đề và giải thích chi tiết với số liệu cụ thể)
- Tiếp theo "Hành động gợi ý:" (khuyến nghị cụ thể với mức giá)
- Kết thúc bằng "Điều kiện khiến kết luận sai:" (kịch bản invalidation)

QUY TẮC VIẾT:
- Dùng số liệu CỤ THỂ từ data (giá, MA, RSI, volume...)
- KHÔNG dùng markdown formatting (**, ##, -, •). Viết plain text.
- Mỗi phần BẮT BUỘC bắt đầu bằng TIÊU ĐỀ SECTION trên 1 dòng riêng biệt (ví dụ: XU HƯỚNG GIÁ, rồi xuống dòng mới viết nội dung)
- Dùng dấu phẩy phân cách hàng nghìn: 1,856 (không phải 1.856)
- Dùng T-0 (hôm nay), T-1, T-2... cho các phiên trước
- Gọi MA là "đường xu hướng X phiên" khi giải thích"""


def build_overview_prompt(summary):
    """Prompt cho phần Overview."""
    b = summary['breadth']
    adv = b.get('advancing', 0)
    dec = b.get('declining', 0)
    unch = b.get('unchanged', 0)
    total = b.get('total_stocks', adv + dec + unch)
    trin = b.get('trin')
    mcclellan = b.get('mcclellan')

    # Build breadth description
    breadth_lines = [f"- Breadth: Tăng {adv}, Giảm {dec}, Đứng {unch} (tổng {total} cổ phiếu)"]
    if trin is not None:
        breadth_lines.append(f"- TRIN (Arms Index): {trin:.2f}" if isinstance(trin, float) else f"- TRIN: {trin}")
    if mcclellan is not None:
        mcc_type = b.get('mcclellan_type', 'Net A-D')
        breadth_lines.append(f"- McClellan Oscillator: {mcclellan:.2f} ({mcc_type})" if isinstance(mcclellan, float) else f"- McClellan: {mcclellan}")
    breadth_text = "\n".join(breadth_lines)

    # MA20 status summary
    above_ma20 = summary.get('above_ma20', [])
    below_ma20 = summary.get('below_ma20', [])
    total_indices = len(above_ma20) + len(below_ma20)
    ma20_text = ""
    if total_indices > 0:
        ma20_text = f"\nTRẠNG THÁI MA20:\n"
        ma20_text += f"- {len(below_ma20)} trong {total_indices} chỉ số dưới MA20"
        if above_ma20:
            ma20_text += f"\n- Còn trên MA20: {', '.join(above_ma20)}"
        if below_ma20:
            ma20_text += f"\n- Đã phá vỡ MA20: {', '.join(below_ma20)}"

    return f"""Dựa trên dữ liệu thị trường ngày {summary['date']}, viết phân tích tổng quan.

DỮ LIỆU:
{breadth_text}
{ma20_text}

CÁC CHỈ SỐ:
{json.dumps(summary['indices_summary'], ensure_ascii=False, indent=2)}

Viết ĐÚNG 7 phần theo thứ tự, mỗi phần bắt đầu bằng số thứ tự.
Mỗi phần viết 3-5 câu phân tích trực tiếp, DẪN CHỨNG SỐ LIỆU cụ thể từ data.
KHÔNG dùng format "Kết luận ngắn:" cho overview. Viết dạng đoạn văn tự nhiên.

HƯỚNG DẪN CHO TỪNG PHẦN:

1. TỔNG QUAN THỊ TRƯỜNG
Phân tích bức tranh chung: breadth, volume, xu hướng chính. Kết thúc bằng "Hành động:" với khuyến nghị cụ thể.

2. PHÂN TÍCH MỐI QUAN HỆ
Phân tích mối quan hệ giữa các nhóm vốn hóa (largecap/midcap/smallcap) qua VN100, VN30, VNMIDCAP, VNSML.
So sánh mức thay đổi giữa các nhóm, nhóm nào mạnh/yếu hơn, phân kỳ hay đồng thuận.
Kết thúc bằng "Ý nghĩa:" đánh giá ý nghĩa của mối quan hệ này.
Sau đó viết 1 dòng cảnh báo bắt đầu bằng "Điều kiện khiến kết luận sai:" mô tả khi nào nhận định sẽ thay đổi.

3. DÒNG TIỀN & XU HƯỚNG
Phân tích dòng tiền và xu hướng dựa trên DỮ LIỆU CỤ THỂ:
- Volume ratio tăng/giảm và ý nghĩa (nghiêng về bên mua hay bên bán)
- Đếm cụ thể bao nhiêu trong bao nhiêu chỉ số đã phá vỡ MA20, gọi tên những chỉ số còn trên MA20
- Nhận xét về thanh khoản: tập trung bán tháo hay mua vào
- Nhận định xu hướng downtrend/uptrend dựa trên cấu trúc đáy cao/đáy thấp hơn
- Áp lực bán lan tỏa từ nhóm nào sang nhóm nào
Viết dạng đoạn văn tự nhiên, KHÔNG dùng box đặc biệt. Có thể dùng 1 bullet point cho điểm nhấn.

4. HỘI TỤ KỸ THUẬT
Tập trung vào VNINDEX và VN30, phân tích CHI TIẾT các chỉ báo kỹ thuật:
- Đánh giá trạng thái quá bán/quá mua: nêu RSI CỤ THỂ của VNINDEX và VN30 (ví dụ: "RSI VNINDEX ở mức 18.2, VN30 chỉ 16.4 - vùng quá bán sâu")
- Xu hướng giảm/tăng: so sánh giá VNINDEX với đường xu hướng 20 phiên (MA20) và 50 phiên (MA50), nêu MỨC GIÁ CỤ THỂ (ví dụ: "dưới MA20 tại 1,846 và MA50 tại 1,783")
- Độ mạnh xu hướng (ADX): nêu giá trị ADX và đánh giá mạnh/yếu/trung bình
- Các mức giá quan trọng: hỗ trợ chính kế tiếp, kháng cự gần, vùng POC nếu có
- Kết thúc bằng "Ý nghĩa:" với khuyến nghị giao dịch cụ thể (có mức giá cắt lỗ)
- Sau box Ý nghĩa, thêm 1 câu tổng kết xu hướng giao dịch nên theo (sideway/short/long).

5. XẾP HẠNG
Xếp hạng dựa trên HIỆU SUẤT 20 NGÀY (perf_20d) và mức độ chịu đựng trong phiên.
Mở đầu bằng 1 câu tổng quan: nhóm nào mạnh nhất, nhóm nào yếu nhất xét 20 ngày.
Sau đó viết DANH SÁCH ĐÁNH SỐ (1, 2, 3, 4...) xếp hạng từ mạnh đến yếu, mỗi mục gồm:
- Số thứ tự. TÊN CHỈ SỐ (Tên ngành tiếng Việt): mô tả hiệu suất 20 ngày (%), % thay đổi phiên, RSI, nhận xét.
Ví dụ:
"1. VNENE (Năng lượng) Dẫn đầu với mức tăng 20 ngày +17.35%, bất chấp thị trường giảm mạnh."
"2. VNHEAL (Chăm sóc sức khỏe) Hiệu suất 20 ngày +7.1%, RSI 78.5 cảnh báo quá mua dài hạn."
Chọn 4-6 chỉ số đáng chú ý nhất (mạnh nhất + yếu nhất), KHÔNG cần liệt kê hết 14.
KHÔNG dùng box đặc biệt.

6. PHÂN TÍCH NGÀNH
Mở đầu 1 câu tổng quan về sự phân hóa ngành.
Sau đó chia thành 2 nhóm:

"Top 3 ngành mạnh (so với VNINDEX 20D):"
Danh sách đánh số 1, 2, 3. Mỗi mục: Tên ngành tiếng Việt (MÃ CHỈ SỐ) + điểm cộng so với VNINDEX 20D + % tăng 20 ngày + nhận xét ngắn.
Ví dụ: "1. Năng lượng (VNENE) +23.4 điểm cộng, tăng 17.35%. Động lượng tăng mạnh nhất thị trường."
Tính điểm cộng/trừ = perf_20d của ngành - perf_20d của VNINDEX.

"Top 3 ngành yếu (so với VNINDEX 20D):"
Danh sách đánh số 1, 2, 3. Mỗi mục: Tên ngành (MÃ) + điểm trừ + % giảm + nhận xét.

Tiếp theo viết 1 đoạn "Cơ hội:" nhận xét cơ hội đầu tư từ các ngành mạnh và ngành quá bán.
Nếu có ngành nào đáng lo ngại (ví dụ VNFIN khối lượng bán tăng vọt), viết 1 dòng bắt đầu bằng "Rủi ro:" hoặc "Cảnh báo rủi ro:" cảnh báo.
Cuối cùng viết "Snapshot các ngành khác:" liệt kê ngắn các ngành còn lại, mỗi dòng: TÊN (MÃ): Giảm/Tăng X%/ngày, tăng/giảm Y%/20 ngày.

7. NHẬN ĐỊNH
Phần này có CẤU TRÚC CỐ ĐỊNH, viết ĐÚNG theo thứ tự sau:

"Top 3 quan sát quan trọng:"
Danh sách đánh số 1), 2), 3) - mỗi quan sát 1-2 câu tóm tắt điểm nhấn quan trọng nhất từ toàn bộ phân tích.
Ví dụ: "1) Áp lực bán lan rộng cực độ: Số mã giảm áp đảo 4.5 lần số mã tăng, thanh khoản bán chiếm 85%."

"Cảnh báo"
Tiếp theo viết "Rủi ro:" liệt kê 2-3 rủi ro chính với số liệu cụ thể (mức hỗ trợ, % volume...).

"Mức quan trọng cần theo dõi:"
Liệt kê các yếu tố cần theo dõi: mã trụ đang kìm hãm chỉ số, chỉ báo độ rộng A/D cần cải thiện.

"Đề xuất định vị danh mục:"
Khuyến nghị cụ thể: tỷ trọng (underweight/overweight), phòng thủ hay tấn công, ngành nào nên ưu tiên, ngành nào tránh, điểm cắt lỗ.

"3-METRIC LEADERSHIP (vs VNINDEX):"
Viết dạng bullet list:
- Nhịp dẫn dắt: nhóm nào đang dẫn dắt thị trường
- Vượt trội 20 phiên (so với VNINDEX): liệt kê các chỉ số outperform với điểm cộng
- Tụt hậu 20 phiên (so với VNINDEX): liệt kê các chỉ số underperform với điểm trừ
- Đồng thuận 5 & 20 phiên: liệt kê chỉ số có xu hướng nhất quán cả 5 và 20 phiên"""


def build_index_prompt(summary):
    """Prompt cho phân tích 1 chỉ số."""
    ind = summary["indicators"]
    ma5 = ind.get("ma5")
    ma10 = ind.get("ma10")
    ma20 = ind.get("sma_20") or ind.get("ma20")
    ma50 = ind.get("sma_50") or ind.get("ma50")
    ma200 = ind.get("sma_200") or ind.get("ma200")
    rsi = ind.get("rsi_14") or ind.get("rsi14")
    macd_l = ind.get("macd") or ind.get("macd_line")
    macd_s = ind.get("macd_signal")
    macd_h = ind.get("macd_hist") or ind.get("macd_histogram")
    bb_u = ind.get("bb_upper")
    bb_m = ind.get("bb_middle")
    bb_l = ind.get("bb_lower")
    adx_val = ind.get("adx14")
    obv_val = ind.get("obv")
    vol_ma = ind.get("volume_ma20")
    above_20 = ind.get("above_ma20")
    above_50 = ind.get("above_ma50")
    volatility = ind.get("volatility_20d")
    daily_ret = ind.get("daily_return")

    return f"""Phân tích kỹ thuật chỉ số {summary['index_name']} ngày {summary['latest']['date']}.

DỮ LIỆU:
- Giá đóng cửa: {summary['latest']['close']} ({summary['latest']['change_pct']:+.2f}%)
- MA5={ma5}, MA10={ma10}, MA20={ma20}, MA50={ma50}, MA200={ma200}
- RSI(14)={rsi}
- MACD: Line={macd_l}, Signal={macd_s}, Hist={macd_h}
- Bollinger: Upper={bb_u}, Middle={bb_m}, Lower={bb_l}
- ADX(14)={adx_val}
- OBV={obv_val}, Volume MA20={vol_ma}
- Volatility 20D={volatility}, Daily Return={daily_ret}%
- Vị trí: {'Trên' if above_20 else 'Dưới'} MA20, {'Trên' if above_50 else 'Dưới'} MA50

GIÁ 20 PHIÊN GẦN NHẤT:
{json.dumps(summary['recent_20_bars'], ensure_ascii=False)}

Viết ĐÚNG 10 phần, mỗi phần bắt đầu bằng tiêu đề IN HOA trên dòng riêng.
MỖI PHẦN BẮT BUỘC theo cấu trúc sau:

Kết luận ngắn: [1 câu tóm tắt nhận định chính]

Dẫn chứng & Ý nghĩa:
1. [Tiêu đề dẫn chứng]: [Giải thích chi tiết với số liệu cụ thể từ data, ví dụ giá, MA, RSI...]
2. [Tiêu đề dẫn chứng]: [Giải thích chi tiết]
3. [Tiêu đề dẫn chứng]: [Giải thích chi tiết]

Hành động gợi ý: [Khuyến nghị cụ thể với mức giá rõ ràng]

Điều kiện khiến kết luận sai: [Kịch bản invalidation cụ thể với mức giá]

RIÊNG phần XU HƯỚNG GIÁ, viết ĐÚNG format sau (KHÔNG dùng "Dẫn chứng & Ý nghĩa", KHÔNG dùng "Hành động gợi ý"):

Kết luận ngắn: [1 câu tổng kết xu hướng ngắn/trung/dài hạn]

Dẫn chứng từ dữ liệu:
- Ngắn hạn (1 - 5 phiên): Giá ([close]) nằm dưới/trên tất cả các đường MA ngắn (đường xu hướng 5 phiên= [MA5], đường xu hướng 20 phiên= [MA20]).
  Đoạn tiếp: Momentum 5 phiên âm/dương sâu ([%]), tín hiệu hướng phần (5 phiên) ở mức [RSI] (quá bán/mua cực độ) cho thấy [nhận xét].
- Trung hạn (10 - 20 phiên): Giá nằm dưới/trên đường xu hướng 20 phiên ([MA20]) và đã giảm/tăng [X%] trong 20 phiên, độ mạnh xu hướng (20 phiên) ở mức [ADX] cho thấy xu hướng [nhận xét sức mạnh].
- Dài hạn (> 50 phiên): Giá vẫn nằm trên/dưới đường xu hướng 50 phiên ([MA50]) và đường xu hướng 100 phiên ([MA100]). Momentum 50 và 100 phiên vẫn dương/âm (lần lượt [X] và [Y]), xác nhận xu hướng [nhận xét].

Kiểm tra Divergence & Alignment:
Tín hiệu hướng phần Divergence: [Giá và RSI có divergence không? Cả giá và tín hiệu hướng phần ngắn/trung hạn đang đồng hành hay phân kỳ?]
Độ mạnh xu hướng Alignment: độ mạnh xu hướng (5 phiên) ở mức [ADX_5] kết hợp với giá [tăng/giảm] mạnh, cho thấy [đánh giá độ tin cậy xu hướng].
Độ mạnh xu hướng (20 phiên) ([ADX_20]) đang [tăng/giảm] → báo hiệu xu hướng [đang thiết lập/suy yếu].

Ý nghĩa: Hành động: [khuyến nghị giao dịch ngắn gọn 1 câu, ví dụ "Lực bán chiếm ưu thế tuyệt đối."]
[2-3 câu bổ sung: có nên mua/bán không, chờ tín hiệu gì]

Điều kiện khiến kết luận sai: [kịch bản invalidation với mức giá cụ thể từ MA, ví dụ "Giá phục hồi mạnh, đóng cửa vượt lên và giữ được trên vùng đường xu hướng 5 phiên ([MA5]) với khối lượng lớn."]

GHI CHÚ THUẬT NGỮ cho XU HƯỚNG GIÁ:
- Gọi RSI là "tín hiệu hướng phần"
- Gọi ADX là "độ mạnh xu hướng"
- Gọi MA là "đường xu hướng X phiên"
- Gọi Momentum là "Momentum X phiên"
- KHÔNG viết tắt RSI, ADX, MA trong phần XU HƯỚNG GIÁ

RIÊNG phần XU HƯỚNG KHỐI LƯỢNG, viết ĐÚNG format sau (KHÔNG dùng "Dẫn chứng & Ý nghĩa", KHÔNG dùng "Hành động gợi ý"):

Kết luận ngắn: [1 câu tổng kết xu hướng khối lượng và ý nghĩa, ví dụ "Khối lượng có xu hướng tăng trong các phiên giảm điểm mạnh gần đây, cho thấy áp lực bán mạnh. Khối lượng nền trung và dài hạn vẫn ở mức cao."]

Dẫn chứng từ dữ liệu:
- Ngắn hạn: Khối lượng phiên hiện tại (T-0: ~ [volume] CP) so với VMA10 (~ [volume_ma10] CP). Nêu cụ thể các phiên có khối lượng đột biến (T-7, T-4, T-2...) với mức khối lượng.
- Trung & Dài hạn: VMA20 (~ [volume_ma20] CP) so với VMA50 (~ [volume_ma50] CP), nhận xét khối lượng giao dịch 20 phiên gần đây so với mức trung bình 50 phiên, đồng hành hay đi ngược với xu hướng giá.

Ý nghĩa: Hành động: [1 câu nhận xét ý nghĩa của khối lượng: phân phối/tích lũy/bán tháo, củng cố hay mâu thuẫn xu hướng giá]

Điều kiện khiến kết luận sai: [kịch bản invalidation, ví dụ "Khối lượng sụt giảm mạnh trong khi giá vẫn tiếp tục lao dốc, có thể báo hiệu lực bán đã cạn kiệt."]

RIÊNG phần KẾT HỢP XU HƯỚNG GIÁ VÀ KHỐI LƯỢNG, viết ĐÚNG format sau:

Kết luận ngắn: [1 câu tổng kết mức đồng thuận giữa giá và khối lượng, ví dụ "Giá và khối lượng đồng thuận cao trong việc xác nhận xu hướng giảm mạnh ở ngắn và trung hạn."]

Dẫn chứng từ dữ liệu:
Ngắn/Trung hạn: [Phân tích mẫu hình giá-khối lượng: "khối lượng tăng khi giá giảm/tăng" điển hình, xác nhận xu hướng có sức mạnh hay không]
Kiểm tra Momentum Cascade: Momentum 20 phiên ([X]) có mức độ âm/dương sâu hơn hay nông hơn Momentum 5 phiên ([Y]).
[Đoạn giải thích: động lực giảm/tăng trung hạn so với ngắn hạn, tín hiệu xu hướng có chiều sâu hay đang suy yếu]

Ý nghĩa: Hành động: [1 câu đánh giá ý nghĩa của sự đồng thuận/phân kỳ]
[1-2 câu chiến lược: bảo vệ vốn/tấn công, mua vào/chờ đợi]

Điều kiện khiến kết luận sai: [kịch bản phá vỡ đồng thuận với mức khối lượng cụ thể, ví dụ "Giá đảo chiều tăng với khối lượng cực lớn (> 1.5 tỷ CP), tạo ra mẫu hình khối lượng tăng khi giá tăng"]

RIÊNG phần CUNG-CẦU, viết ĐÚNG format sau:

Kết luận ngắn: [1 câu về cán cân cung-cầu và vùng giá, ví dụ "Cung (áp lực bán) đang áp đảo ở vùng giá hiện tại. Cầu mạnh chỉ có thể xuất hiện ở các vùng hỗ trợ dài hạn phía dưới."]

Dẫn chứng từ dữ liệu (Volume Profile & giá bình quân theo khối lượng):
Vùng CUNG (Áp lực bán mạnh): Point of Control (POC) tại [giá] - vùng giá có nhiều thanh khoản nhất, [nhận xét kháng cự]. Giá hiện tại nằm sâu dưới/trên VWAP20 ([giá]), cho thấy bên [bán/mua] chiếm ưu thế áp đảo.
Vùng CẦU (Áp lực mua tiềm năng): Vùng giá từ [X] đến [Y] (quanh đường xu hướng 50 phiên và VWAP5). [nhận xét vùng lực mua phòng thủ].
CMF20 ([giá trị]) xác nhận dòng tiền đang [chảy vào/ra khỏi] thị trường trong ngắn hạn.

Ý nghĩa: Hành động: [1 câu ngắn gọn, ví dụ "Bên bán đang kiểm soát hoàn toàn."]
[2-3 câu: đợt hồi phục gặp áp lực ở đâu, vùng nào người mua nên cân nhắc, điều kiện tích lũy]

Điều kiện khiến kết luận sai: [kịch bản giá vượt VWAP20 và POC]

RIÊNG phần MỨC GIÁ QUAN TRỌNG, viết ĐÚNG format sau:

Kết luận ngắn: Hỗ trợ gần: [range]. Kháng cự gần: [range], sau đó là [range].

Dẫn chứng và
Độ tin cậy:
HỖ TRỢ (Bên Mua Cần Giữ):
[range] (Cao): [giải thích: đáy phiên, Bollinger Band dưới, Donchian]. Mất vùng này → [hệ quả].
~ [range] (Trung bình - Cao): [giải thích: vùng tập trung MA50, VWAP5, đáy gần đây]. Hỗ trợ động quan trọng.
[mức giá] (Trung bình): [giải thích: MA100, Keltner Band dưới]. Hỗ trợ xa hơn.

KHÁNG CỰ (Bên Bán Cần Giữ):
[range] (Cao): [giải thích: MA5, MA10]. Thách thức đầu tiên cho phục hồi.
[range] (Trung bình): [giải thích: BB5 trên, đỉnh gần đây].
[range] (Rất cao): [giải thích: MA20, VWAP20] - kháng cự chính xu hướng trung hạn.
[range] (Rất cao): [giải thích: POC, High Volume Node (HVN)]. "Bức tường" kháng cự mạnh nhất.

Ý nghĩa: Hành động: [1 câu nhận định đường đi ít kháng cự nhất]
[2-3 câu: theo dõi phản ứng giá ở đâu, điều kiện xu hướng giảm kết thúc]

Điều kiện khiến kết luận sai: [kịch bản phá vỡ mức kháng cự quan trọng]

RIÊNG phần BIẾN ĐỘNG GIÁ, viết ĐÚNG format sau:

Kết luận ngắn: [1 câu tổng kết biến động ngắn/trung hạn và có squeeze hay không, ví dụ "Biến động (volatility) ngắn hạn ở mức cao, trung hạn ở mức trung bình. Không có tín hiệu squeeze."]

Dẫn chứng từ dữ liệu:
- Ngắn hạn: biên độ dao động (5 phiên) ([X]) và biên độ dao động (10 phiên) ([Y]) cho thấy biến động [cao/thấp]. Khoảng giá trong phiên (H-L) thường trên/dưới [X] điểm.
- Trung/Dài hạn: biên độ dao động (20 phiên) ([X]) và biên độ dao động (50 phiên) ([Y]) [ổn định/tăng/giảm] ở mức [cao/trung bình/thấp] (~[X]% so với giá).
Độ rộng Bollinger 20 (Width= [X]%) cho thấy biến động [không ở trạng thái thắt chặt/đang thắt chặt].

Kiểm tra
TTM Squeeze: Dữ liệu ghi rõ "[CÓ/KHÔNG] (BB20 [rộng/hẹp] hơn KC20)".
Cụ thể, dải Bollinger 20 ([range]) [rộng/hẹp] hơn dải Keltner 20 ([range]).
[Giải thích: biến động thực tế vs trung bình, có "nén chặt" (squeeze) hay không]
[Nhận xét trạng thái: biến động mở rộng/thu hẹp]

Ý nghĩa: Hành động: [1 câu về ý nghĩa squeeze/không squeeze cho giao dịch]
[1-2 câu bổ sung: quản lý vốn, rủi ro biến động]

Điều kiện khiến kết luận sai: [kịch bản BB20 thu hẹp/mở rộng so với KC20]

RIÊNG phần RỦI RO, viết ĐÚNG format sau (KHÔNG dùng "Kết luận ngắn:" box):

[1-2 đoạn văn mở đầu đánh giá tổng quan rủi ro: rủi ro cao/trung bình/thấp ở ngắn hạn, trung hạn, dài hạn. Dòng tiền đã xác nhận hay chưa.]

- Trung hạn (10 - 20 phiên): Rủi ro [cao/trung bình/thấp].
  [Đoạn giải thích: giá vs MA20, ADX tăng/giảm, breadth percentile, tâm lý (X mã tăng vs Y mã giảm)]
- Dài hạn (40 - 60 phiên): Rủi ro [cao/trung bình/thấp].
  [Đoạn giải thích: giá vs MA50, MA200, cấu trúc xu hướng tăng dài hạn còn/mất]

Điều kiện thất bại chính (khiến rủi ro tăng cao hơn dự kiến):
1. [Điều kiện giá: đóng cửa dưới/trên mức X (đáy/đỉnh & Band Bollinger)] → hệ quả.
2. [Điều kiện breadth: số mã tăng không vượt X, cán cân cung/cầu, tỷ lệ khối lượng tăng/giảm]
3. [Điều kiện drivers: mã trụ tiếp tục giảm/tăng, không có driver mới hấp thụ thanh khoản]

Ý nghĩa: Hành động: [1 câu chiến lược vốn, ví dụ "Ưu tiên bảo toàn vốn trong ngắn hạn. Chỉ xem xét gia tăng rủi ro khi có sự đồng thuận cải thiện giữa giá và breadth."]

RIÊNG phần KHUYẾN NGHỊ VỊ THẾ, viết ĐÚNG format sau (KHÔNG dùng "Kết luận ngắn:" box):

[1 câu mở đầu nêu plan chính: "TẠM ĐỨNG NGOÀI" hoặc "GIỮ VỊ THẾ HIỆN TẠI MÀ KHÔNG BỔ SUNG" hoặc "TÌM ĐIỂM MUA THỬ" cho khung ngắn và trung hạn. Mức độ tự tin: CAO/TRUNG BÌNH/THẤP ([X]/10).]

Dẫn chứng cho hành động [chờ đợi/mua/bán]:
[Đoạn 1: Áp lực bán/mua trong phiên]
[Đoạn 2: Breadth - nêu % mã tăng, tỷ lệ, breadth percentile, cần chờ số mã tăng phục hồi trên [X] như tín hiệu ổn định]
[Đoạn 3: Cung-Cầu - giá vs VWAP20 và POC, đợt hồi về MA5/MA10 gặp áp lực chốt lời]

Điều kiện để thay đổi khuyến nghị (chuyển sang "[plan mới]"):
1. [Điều kiện giá: hình thành đáy/đỉnh rõ ràng tại vùng [X]-[Y] (có nến phản ứng hoặc sideways tích lũy) VÀ đồng thời]
2. [Điều kiện breadth: cán cân cung/cầu [X], tỷ lệ khối lượng tăng/giảm > [X] trong ít nhất 1 phiên]

RIÊNG phần GIÁ MỤC TIÊU, viết ĐÚNG format sau (KHÔNG dùng "Kết luận ngắn:" box):

[1 câu mở đầu: tập trung vào các vùng giá then chốt để ra quyết định vào/lệnh hoặc cắt lỗ, thay vì một con số cố định.]

- Kịch bản GIẢM (Khả năng cao ngắn hạn):
Mục tiêu 1 (Hỗ trợ gần): [range]. [Giải thích: vùng đáy, MA50, VWAP5]
Hành động: [1 câu: quan sát phản ứng mua tại đây]
Mục tiêu 2 (Hỗ trợ trung hạn): ~ [giá]. [Giải thích: MA100, hỗ trợ xa]
Hành động: [1 câu: điều kiện mua thử với khối lượng nhỏ]

- Kịch bản TĂNG (Cần điều kiện cải thiện):
Mục tiêu 1 (Kháng cự gần): [range]. [Giải thích: MA5, MA10]. Mọi đợt phục hồi đầu tiên đều khó vượt qua.
Hành động: [1 câu: vùng chốt lời cho người mua]
Mục tiêu 2 (Kháng cự then chốt): [range]. [Giải thích: MA20, VWAP20]. Vượt và giữ trên vùng này = tín hiệu xu hướng giảm có thể kết thúc.
Hành động: [1 câu: theo dõi khối lượng và breadth]

RIÊNG phần KỊCH BẢN WHAT-IF, viết ĐÚNG format sau (KHÔNG dùng "Kết luận ngắn:" box):

Kịch Bản "What-if"
[1 câu mở đầu: thống nhất 3 kịch bản chính với xác suất ước lượng dựa trên hiện trạng.]

1. Kịch bản Tích Cực ([mô tả ngắn]) - Xác suất [X-Y]%
- Diễn biến: [Giá giữ vững, bật mạnh từ vùng [X]-[Y], đóng cửa trên [Z] với khối lượng lớn. Breadth cải thiện nhanh (cán cân cung/cầu, số mã tăng). Drivers ổn định.]
Hành động: [khuyến nghị cụ thể với mức giá vào lệnh, stoploss]

2. Kịch bản Trung Tính ([mô tả ngắn]) - Xác suất [X-Y]%
- Diễn biến: [Giá dao động biên độ hẹp quanh vùng [X]-[Y] trong [N] phiên tới. Biến động giảm, khối lượng giảm dần. Breadth thoát cực đoan nhưng chưa mạnh.]
Hành động: [khuyến nghị: quan sát, đứng ngoài, chờ breakout với khối lượng tăng]

3. Kịch bản Tiêu Cực ([mô tả ngắn]) - Xác suất [X-Y]%
- Diễn biến: [Giá phá vỡ hỗ trợ [X], kiểm tra vùng [Y]. Breadth tiếp tục yếu (số mã tăng < [Z]). Các driver chính tiếp tục giảm.]
Hành động: [khuyến nghị: không mua đón đáy, cắt lỗ nếu đang giữ, điều kiện mua lại khi có tín hiệu tích lũy]

3-METRIC LEADERSHIP (vs VNINDEX):
- Nhịp dẫn dắt: [nhóm nào đang dẫn dắt hay chưa có nhóm nổi trội]
- Vượt trội 20 phiên (so với VNINDEX): [liệt kê chỉ số outperform với % vượt trội]
- Tụt hậu 20 phiên (so với VNINDEX): [liệt kê chỉ số underperform với % tụt hậu]
- Đồng thuận 5 & 20 phiên: [liệt kê chỉ số có xu hướng nhất quán cả 5 và 20 phiên]
- Ghi chú: dùng để chọn "nhóm dẫn dắt / tụt hậu", tránh kết luận chỉ dựa 1 phiên.

10 PHẦN CẦN VIẾT:

XU HƯỚNG GIÁ

XU HƯỚNG KHỐI LƯỢNG

KẾT HỢP XU HƯỚNG GIÁ VÀ KHỐI LƯỢNG

CUNG-CẦU

MỨC GIÁ QUAN TRỌNG

BIẾN ĐỘNG GIÁ

RỦI RO

KHUYẾN NGHỊ VỊ THẾ

GIÁ MỤC TIÊU

KỊCH BẢN WHAT-IF"""


# ============================================================================
# CLAUDE API CALL
# ============================================================================

def call_claude(prompt, max_retries=5):
    """Gọi Claude API với retry và rate limit handling."""
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        log.error("ANTHROPIC_API_KEY not set!")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = "rate" in err_str or "429" in err_str or "overloaded" in err_str
            if is_rate_limit:
                wait = min(2 ** (attempt + 2), 60)  # 4, 8, 16, 32, 60
                log.warning(f"Rate limited (attempt {attempt + 1}/{max_retries}), waiting {wait}s...")
            else:
                wait = 2 ** (attempt + 1)  # 2, 4, 8, 16, 32
                log.warning(f"API error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(wait)
            else:
                log.error(f"Claude API failed after {max_retries} attempts: {e}")
                return None


# ============================================================================
# BONDLAB AI ANALYSIS
# ============================================================================

BONDLAB_SYSTEM_PROMPT = """Bạn là chuyên gia phân tích thị trường trái phiếu và lãi suất Việt Nam.
Viết phân tích bằng tiếng Việt, chuyên nghiệp, chi tiết với dẫn chứng số liệu cụ thể.

QUY TẮC VIẾT:
- Dùng số liệu CỤ THỂ từ data (lãi suất, bps thay đổi, spread, xác suất...)
- KHÔNG dùng markdown formatting (**, ##, -, •). Viết plain text.
- Dùng dấu phẩy phân cách hàng nghìn: 1,856 (không phải 1.856)
- Viết dạng đoạn văn tự nhiên, mạch lạc, chuyên sâu."""


def build_bondlab_prompt(bondlab_data):
    """Prompt cho phần BondLab AI analysis."""
    asof = bondlab_data.get("asof", "")

    return f"""Dựa trên dữ liệu trái phiếu và liên ngân hàng ngày {asof}, viết phân tích diễn giải toàn diện.

DỮ LIỆU:
{json.dumps(bondlab_data, ensure_ascii=False, indent=2)}

Viết phân tích theo CẤU TRÚC sau (viết liền mạch, KHÔNG đánh số phần):

TÓM TẮT
1-2 câu tổng kết tình hình lãi suất và thanh khoản liên ngân hàng hôm nay.

MÔI TRƯỜNG LÃI SUẤT
Phân tích lãi suất TPCP các kỳ hạn (2Y, 5Y, 10Y), so sánh thay đổi bps.
Đánh giá spread 10Y-2Y và ý nghĩa: đường cong yield đang dốc lên/phẳng/đảo ngược.
So sánh với lãi suất huy động và cho vay.

ODDS (XÁC SUẤT PHIÊN KẾ TIẾP)
Phân tích odds tăng/giảm/đi ngang cho interbank và TPCP.
Nhận xét kỳ vọng thay đổi (E[Δ]) có ý nghĩa gì.
Mức độ tin cậy của dự báo.

XU HƯỚNG 20 PHIÊN
Nhận xét xu hướng lãi suất 20 phiên gần nhất (nếu có dữ liệu).
So sánh với xu hướng ngắn hạn (5 phiên).

YIELD CURVE
Phân tích hình dạng đường cong yield: normal/flat/inverted.
So sánh spread giữa các kỳ hạn. Ý nghĩa cho kinh tế và thị trường cổ phiếu.

INTERBANK & THANH KHOẢN
Phân tích lãi suất liên ngân hàng ON, 1W, 1M, 3M.
Đánh giá thanh khoản hệ thống: dồi dào hay căng thẳng.
Tác động đến thị trường cổ phiếu.

STRESS & ALERTS
Nhận xét các cảnh báo (alerts) nếu có.
Đánh giá mức stress của thị trường trái phiếu.
Kênh truyền dẫn từ bond sang equity.

WATCHLIST NGÀY MAI
2-3 yếu tố quan trọng cần theo dõi phiên kế tiếp.
Kịch bản lãi suất có thể ảnh hưởng thị trường cổ phiếu."""


def generate_bondlab_analysis(data):
    """Tạo phân tích AI cho BondLab."""
    bondlab = data.get("bondlab", {})
    if not bondlab:
        log.warning("No bondlab data, skipping AI analysis")
        return None

    log.info("Generating BONDLAB analysis...")
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        log.warning("No API key, skipping bondlab analysis")
        return None

    client = anthropic.Anthropic(api_key=api_key)
    prompt = build_bondlab_prompt(bondlab)

    for attempt in range(3):
        try:
            message = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                system=BONDLAB_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            text = message.content[0].text
            log.info("  BONDLAB analysis done")
            return text
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = "rate" in err_str or "429" in err_str or "overloaded" in err_str
            wait = min(2 ** (attempt + 2), 30) if is_rate_limit else 2 ** (attempt + 1)
            log.warning(f"  BondLab API attempt {attempt + 1}/3: {e}")
            if attempt < 2:
                time.sleep(wait)

    log.error("  BONDLAB analysis failed after 3 attempts")
    return None


# ============================================================================
# RESEARCHLAB AI MEMO
# ============================================================================

RESEARCHLAB_SYSTEM_PROMPT = """Bạn là chuyên gia nghiên cứu vĩ mô và liên thị trường (cross-asset) Việt Nam.
Nhiệm vụ: viết Research Memo tổng hợp mối quan hệ giữa thị trường trái phiếu, lãi suất và thị trường cổ phiếu.

QUY TẮC FORMAT BẮT BUỘC:
- Output PHẢI là JSON hợp lệ với 5 key: summary, alerts, evidence, market_context, watchlist
- Mỗi key là một array of strings, mỗi string là 1 bullet point
- KHÔNG dùng markdown. Viết plain text tiếng Việt.
- Dùng số liệu CỤ THỂ từ data.
- Mỗi phần 2-4 bullet points."""


def build_researchlab_prompt(data):
    """Prompt cho ResearchLab memo dựa trên tất cả data đã thu thập."""
    # Tóm tắt index performance
    indices = data.get("index_ohlcv", {}).get("indices", {})
    index_summary = {}
    for key, idx in indices.items():
        latest = idx.get("latest", {})
        bars = idx.get("bars", [])
        perf_5d = None
        if len(bars) >= 6:
            c5 = bars[-6].get("c", 0)
            c0 = bars[-1].get("c", 0)
            if c5 and c5 > 0:
                perf_5d = round((c0 / c5 - 1) * 100, 2)
        perf_20d = None
        if len(bars) >= 21:
            c20 = bars[-21].get("c", 0)
            c0 = bars[-1].get("c", 0)
            if c20 and c20 > 0:
                perf_20d = round((c0 / c20 - 1) * 100, 2)
        index_summary[key] = {
            "name": idx.get("name", key),
            "close": latest.get("close"),
            "change_pct": latest.get("change_pct"),
            "perf_5d": perf_5d,
            "perf_20d": perf_20d,
        }

    # Breadth
    breadth = data.get("breadth", {})

    # BondLab
    bondlab = data.get("bondlab", {})
    # Remove analysis text to keep prompt focused on numbers
    bondlab_clean = {k: v for k, v in bondlab.items() if k != "analysis"}

    # Foreign flow
    foreign = data.get("foreign", {})
    foreign_summary = {}
    if foreign.get("flow"):
        for ex, fl in foreign["flow"].items():
            foreign_summary[ex] = {
                "net_value": fl.get("net_value"),
                "buy_value": fl.get("buy_value"),
                "sell_value": fl.get("sell_value"),
            }

    asof = data.get("index_ohlcv", {}).get("asof", "")

    return f"""Dựa trên DỮ LIỆU THỊ TRƯỜNG ngày {asof}, viết Research Memo phân tích mối quan hệ liên thị trường.

DỮ LIỆU CHỈ SỐ CỔ PHIẾU (15 chỉ số):
{json.dumps(index_summary, ensure_ascii=False, indent=2)}

BREADTH:
{json.dumps(breadth, ensure_ascii=False, indent=2)}

DỮ LIỆU TRÁI PHIẾU & LIÊN NGÂN HÀNG (BondLab):
{json.dumps(bondlab_clean, ensure_ascii=False, indent=2)}

GIAO DỊCH NƯỚC NGOÀI:
{json.dumps(foreign_summary, ensure_ascii=False, indent=2)}

Trả về JSON hợp lệ với cấu trúc:
{{
  "summary": [
    "Bullet 1: tổng quan xu hướng cổ phiếu gần đây (dùng perf_5d)",
    "Bullet 2: tổng quan lãi suất TPCP và đường cong yield (spread 10y-2y)",
    "Bullet 3: mức stress trái phiếu và áp lực chính"
  ],
  "alerts": [
    "Bullet: cảnh báo truyền dẫn giá (price transmission) từ trái phiếu sang cổ phiếu - liệt kê chỉ số bị ảnh hưởng",
    "Bullet: tín hiệu lead-lag giữa đường cong yield và lợi nhuận cổ phiếu",
    "Bullet: truyền dẫn khối lượng (volume transmission) - trạng thái ok/caution/warn"
  ],
  "evidence": [
    "Bullet: phân tích VAR/Granger - tác động cú sốc từ đường cong lợi suất đến giá cổ phiếu, p-value, mức tác động",
    "Bullet: mối đồng pha (coherence) giữa đường cong và lợi nhuận cổ phiếu, độ trễ",
    "Bullet: chỉ số stress trái phiếu trung bình, so với mức lịch sử, thành phần đóng góp"
  ],
  "market_context": [
    "Bullet: bối cảnh đường cong yield cao trong môi trường lãi suất hiện tại, kỳ vọng chính sách",
    "Bullet: môi trường risk-on/risk-off dựa trên stress trái phiếu + xu hướng cổ phiếu",
    "Bullet: khả năng khuếch đại cú sốc từ thị trường vốn"
  ],
  "watchlist": [
    "Bullet: điều kiện stress trái phiếu + đường cong → rủi ro cho nhóm nhạy cảm lãi suất",
    "Bullet: nếu coherence mạnh hơn → tín hiệu truyền dẫn rủi ro sâu hơn",
    "Bullet: thanh khoản cổ phiếu + stress thanh khoản trái phiếu → khả năng điều chỉnh mạnh"
  ]
}}

CHỈ trả về JSON, KHÔNG có text nào khác trước hoặc sau JSON."""


def generate_researchlab_memo(data):
    """Tạo ResearchLab memo bằng AI dựa trên tất cả data đã thu thập."""
    log.info("Generating RESEARCHLAB memo...")
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        log.warning("No API key, skipping researchlab memo")
        return None

    client = anthropic.Anthropic(api_key=api_key)
    prompt = build_researchlab_prompt(data)

    for attempt in range(3):
        try:
            message = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                system=RESEARCHLAB_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            text = message.content[0].text.strip()

            # Extract JSON from response (handle possible markdown wrapping)
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3].strip()

            memo = json.loads(text)
            log.info("  RESEARCHLAB memo done")
            return memo
        except json.JSONDecodeError as e:
            log.warning(f"  ResearchLab JSON parse error (attempt {attempt + 1}/3): {e}")
            if attempt < 2:
                time.sleep(4)
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = "rate" in err_str or "429" in err_str or "overloaded" in err_str
            wait = min(2 ** (attempt + 2), 30) if is_rate_limit else 2 ** (attempt + 1)
            log.warning(f"  ResearchLab API attempt {attempt + 1}/3: {e}")
            if attempt < 2:
                time.sleep(wait)

    log.error("  RESEARCHLAB memo failed after 3 attempts")
    return None


# ============================================================================
# COMMODITIES AI RECOMMENDATION
# ============================================================================

COMMODITIES_SYSTEM_PROMPT = """Bạn là chuyên gia phân tích hàng hoá thế giới và tác động đến thị trường Việt Nam.
Viết khuyến nghị bằng tiếng Việt, chuyên nghiệp, ngắn gọn, có dẫn chứng số liệu cụ thể.

QUY TẮC:
- KHÔNG dùng markdown formatting (**, ##). Viết plain text.
- Dùng số liệu CỤ THỂ từ data hàng hoá (giá, % thay đổi, đơn vị).
- Tập trung phân tích xu hướng hàng hoá (dầu, thép, sắt, vàng, nông sản...) và tác động kinh tế.
- Viết thực tế, tập trung vào tác động lên nền kinh tế và thị trường cổ phiếu VN."""


def build_commodities_prompt(data):
    """Prompt cho khuyến nghị hàng hoá dựa trên dữ liệu commodity thực tế."""
    commodities = data.get("commodities", {})

    # Tóm tắt world_commodities cho prompt
    world_comm = commodities.get("world_commodities", [])
    comm_summary = []
    for c in world_comm:
        name = c.get("name", "")
        close = c.get("close")
        change_pct = c.get("change_pct")
        unit = c.get("unit", "")
        if close is not None:
            pct_str = f"{change_pct:+.2f}%" if change_pct is not None else "N/A"
            comm_summary.append(f"- {name}: {close} {unit} ({pct_str})")

    comm_text = "\n".join(comm_summary) if comm_summary else "Không có dữ liệu"

    # Gold VN summary
    gold = commodities.get("gold", [])
    gold_text = ""
    if gold:
        gold_lines = []
        for g in gold[:5]:
            name = g.get("name", "")
            buy = g.get("buy")
            sell = g.get("sell")
            if buy and sell:
                gold_lines.append(f"- {name}: Mua {buy:,.0f} / Bán {sell:,.0f} VND")
        gold_text = "\n".join(gold_lines)

    # Exchange rates summary
    fx = commodities.get("exchange_rates", [])
    fx_text = ""
    if fx:
        fx_lines = []
        for r in fx[:5]:
            code = r.get("code", "")
            sell = r.get("sell")
            if sell:
                fx_lines.append(f"- {code}: Bán {sell:,.0f} VND")
        fx_text = "\n".join(fx_lines)

    asof = commodities.get("asof", data.get("index_ohlcv", {}).get("asof", ""))

    return f"""Dựa trên dữ liệu hàng hoá thế giới ngày {asof}, viết KHUYẾN NGHỊ ngắn gọn.

HÀNG HOÁ THẾ GIỚI (giá mới nhất):
{comm_text}

GIÁ VÀNG VIỆT NAM:
{gold_text or "Không có dữ liệu"}

TỶ GIÁ:
{fx_text or "Không có dữ liệu"}

Viết khuyến nghị theo cấu trúc:

TỔNG QUAN HÀNG HOÁ
3-4 câu tổng kết xu hướng hàng hoá thế giới: nhóm năng lượng (dầu thô, khí tự nhiên), nhóm kim loại (thép, sắt, than cốc), nhóm nông sản (đậu nành, ngô, đường), vàng. Nêu giá và % thay đổi cụ thể.

TÁC ĐỘNG LÊN KINH TẾ & CỔ PHIẾU VIỆT NAM
3-4 câu phân tích tác động của giá hàng hoá lên:
- Nhóm năng lượng (dầu khí, điện): giá dầu thô tăng/giảm ảnh hưởng thế nào
- Nhóm vật liệu xây dựng (thép, xi măng): giá thép, sắt, than cốc tác động gì
- Nhóm phân bón, nông nghiệp: giá phân Urê, đậu nành, ngô ảnh hưởng đầu vào
- Nhóm tài chính: tỷ giá, giá vàng → dòng vốn ngoại

KHUYẾN NGHỊ
3-4 câu khuyến nghị cụ thể dựa trên xu hướng hàng hoá:
- Nhóm nào hưởng lợi từ giá hàng hoá hiện tại
- Nhóm nào chịu áp lực chi phí đầu vào tăng
- Mức giá hàng hoá nào cần theo dõi (dầu > X USD/thùng, thép > Y USD/tấn, vàng > Z USD/oz)

CẢNH BÁO
1-2 câu cảnh báo rủi ro: biến động dầu/vàng bất ngờ, áp lực tỷ giá, rủi ro supply chain."""


def generate_commodities_recommendation(data):
    """Tạo khuyến nghị AI cho hàng hoá."""
    commodities = data.get("commodities", {})
    if not commodities:
        log.warning("No commodities data, skipping AI recommendation")
        return None

    log.info("Generating COMMODITIES recommendation...")
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        log.warning("No API key, skipping commodities recommendation")
        return None

    client = anthropic.Anthropic(api_key=api_key)
    prompt = build_commodities_prompt(data)

    for attempt in range(3):
        try:
            message = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=2048,
                system=COMMODITIES_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            text = message.content[0].text
            log.info("  COMMODITIES recommendation done")
            return text
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = "rate" in err_str or "429" in err_str or "overloaded" in err_str
            wait = min(2 ** (attempt + 2), 30) if is_rate_limit else 2 ** (attempt + 1)
            log.warning(f"  Commodities API attempt {attempt + 1}/3: {e}")
            if attempt < 2:
                time.sleep(wait)

    log.error("  COMMODITIES recommendation failed after 3 attempts")
    return None


# ============================================================================
# GENERATE FULL REPORT
# ============================================================================

def generate_overview(data):
    """Tạo phần Overview."""
    log.info("Generating OVERVIEW...")
    summary = prepare_overview_summary(data)
    text = call_claude(build_overview_prompt(summary))
    if not text:
        return ""
    return text


def generate_index(key, data):
    """Tạo phân tích cho 1 chỉ số."""
    display_name = INDICES[key][1]
    log.info(f"Generating {display_name}...")

    summary = prepare_index_summary(key, data)
    if not summary:
        log.warning(f"No data for {display_name}, skipping")
        return ""

    text = call_claude(build_index_prompt(summary))
    if not text:
        return ""
    return text


def assemble_report(overview_text, index_texts):
    """Ghép tất cả thành 1 file báo cáo đúng format parser."""

    lines = []
    # Phần I: Overview
    lines.append("PHẦN I: TỔNG QUAN THỊ TRƯỜNG")
    lines.append("")
    lines.append(overview_text)
    lines.append("")
    lines.append("")

    # Phần II trở đi: Các chỉ số (chỉ REPORT_INDICES)
    part_num = 2
    for key in REPORT_INDICES:
        if key not in index_texts or not index_texts[key]:
            continue

        display_name = INDICES[key][1]

        # Header theo format parser mong đợi
        if key == "vnindex":
            lines.append(f"PHẦN {_roman(part_num)}: PHÂN TÍCH CHỈ SỐ {display_name}")
        else:
            lines.append(f"{part_num - 1}. Chỉ số {display_name}")

        lines.append("")
        lines.append(index_texts[key])
        lines.append("")
        lines.append("")
        part_num += 1

    return "\n".join(lines)


def _roman(n):
    """Chuyển số sang La Mã (đơn giản)."""
    vals = [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    result = ""
    for val, numeral in vals:
        while n >= val:
            result += numeral
            n -= val
    return result


# ============================================================================
# MAIN
# ============================================================================

def main():
    log.info("=" * 60)
    log.info("REPORT GENERATION STARTED")
    log.info("=" * 60)

    # Load data
    data = load_all_data()
    if not data["index_ohlcv"]:
        log.error("No index OHLCV data found. Run collect_data.py first!")
        sys.exit(1)

    # Log available indices
    available = list(data["index_ohlcv"].get("indices", {}).keys())
    log.info(f"Data available for {len(available)} indices: {available}")

    # Generate REPORT_INDICES SEQUENTIALLY to avoid API rate limiting.
    # With 5 calls (overview + 4 indices) at ~30s each, total ~3 minutes.
    index_texts = {}

    # 1) Generate overview
    overview_text = generate_overview(data)
    if overview_text:
        log.info("  OVERVIEW done")
    else:
        log.warning("  OVERVIEW failed!")

    # 2) Generate each index with delay between calls
    for i, key in enumerate(REPORT_INDICES, 1):
        time.sleep(2)  # Rate limit delay between API calls
        text = generate_index(key, data)
        if text:
            index_texts[key] = text
            log.info(f"  [{i}/{len(REPORT_INDICES)}] {INDICES[key][1]} done")
        else:
            log.warning(f"  [{i}/{len(REPORT_INDICES)}] {INDICES[key][1]} FAILED")

    # 3) Generate BondLab AI analysis (save to bondlab_data.json)
    time.sleep(2)
    bondlab_text = generate_bondlab_analysis(data)
    if bondlab_text:
        bondlab_cache = CACHE_DIR / "bondlab_data.json"
        if bondlab_cache.exists():
            with open(bondlab_cache, "r", encoding="utf-8") as f:
                bondlab_json = json.load(f)
            bondlab_json["analysis"] = bondlab_text
            with open(bondlab_cache, "w", encoding="utf-8") as f:
                json.dump(bondlab_json, f, ensure_ascii=False, default=str)
            log.info("  BondLab analysis saved to bondlab_data.json")
        else:
            log.warning("  bondlab_data.json not found, cannot save analysis")

    # 4) Generate ResearchLab memo (save to researchlab_data.json)
    time.sleep(2)
    rl_memo = generate_researchlab_memo(data)
    if rl_memo:
        asof = data["index_ohlcv"].get("asof", "")
        rl_data = {
            "asof": asof,
            "summary": rl_memo.get("summary", []),
            "alerts": rl_memo.get("alerts", []),
            "evidence": rl_memo.get("evidence", []),
            "market_context": rl_memo.get("market_context", []),
            "watchlist": rl_memo.get("watchlist", []),
        }
        rl_path = CACHE_DIR / "researchlab_data.json"
        with open(rl_path, "w", encoding="utf-8") as f:
            json.dump(rl_data, f, ensure_ascii=False, default=str)
        log.info(f"  ResearchLab memo saved to {rl_path}")

    # 5) Generate Commodities AI recommendation (save to commodities_data.json)
    time.sleep(2)
    comm_text = generate_commodities_recommendation(data)
    if comm_text:
        comm_cache = CACHE_DIR / "commodities_data.json"
        if comm_cache.exists():
            with open(comm_cache, "r", encoding="utf-8") as f:
                comm_json = json.load(f)
            comm_json["recommendation"] = comm_text
            with open(comm_cache, "w", encoding="utf-8") as f:
                json.dump(comm_json, f, ensure_ascii=False, default=str)
            log.info("  Commodities recommendation saved to commodities_data.json")
        else:
            log.warning("  commodities_data.json not found, cannot save recommendation")

    # Assemble report
    full_report = assemble_report(overview_text, index_texts)

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"BaoCao_{timestamp}.txt"
    output_path = REPORTS_DIR / filename

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_report)

    log.info(f"Report saved: {output_path}")
    log.info(f"Report size: {output_path.stat().st_size:,} bytes")
    log.info(f"Indices generated: {len(index_texts)}/{len(REPORT_INDICES)}")

    # Cũng lưu path ra stdout để script khác đọc được
    print(f"REPORT_PATH={output_path}")

    log.info("=" * 60)
    log.info("REPORT GENERATION COMPLETED!")
    log.info("=" * 60)

    return str(output_path)


if __name__ == "__main__":
    main()
