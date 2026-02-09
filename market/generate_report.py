"""
Dùng Claude API để viết báo cáo phân tích thị trường.
Output: reports/txt/BaoCao_YYYYMMDD_HHMMSS.txt
"""

import json
import os
import sys
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    INDICES, PART_ORDER, INDEX_SECTIONS, OVERVIEW_SECTIONS,
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
    # Load stock snapshot for real breadth data
    stock_snapshot = load_json("stock_snapshot.json")
    stock_breadth = stock_snapshot.get("breadth", {}) if stock_snapshot else {}

    # Prefer stock-level breadth if available, fallback to index-level
    if stock_breadth and stock_breadth.get("total_stocks", 0) > 50:
        breadth = stock_breadth
    else:
        breadth = load_json("breadth_snapshot.json")

    return {
        "index_ohlcv": load_json("index_ohlcv.json"),
        "breadth": breadth,
        "stock_snapshot": stock_snapshot or {},
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
            summaries[key] = {
                "name": s["index_name"],
                "close": s["latest"]["close"],
                "change_pct": s["latest"]["change_pct"],
                "rsi14": ind.get("rsi_14") or ind.get("rsi14"),
                "above_ma20": ind.get("above_ma20"),
            }

    breadth = data["breadth"]

    # Stock impact data (which stocks drive VNINDEX)
    stock_snapshot = data.get("stock_snapshot", {})
    index_impact = stock_snapshot.get("index_impact", {})

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
        "index_impact": index_impact,
        "top_gainers": stock_snapshot.get("gainers", [])[:10],
        "top_losers": stock_snapshot.get("losers", [])[:10],
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
- KHÔNG viết lại tiêu đề section.
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

    # Build index impact description (stock contributions to VNINDEX)
    impact = summary.get('index_impact', {})
    impact_text = ""
    pos_list = impact.get('positive', [])
    neg_list = impact.get('negative', [])
    if pos_list or neg_list:
        lines = ["CỔ PHIẾU TÁC ĐỘNG ĐẾN VNINDEX:"]
        if neg_list:
            neg_items = [f"  {s['symbol']} ({s['change_pct']:+.2f}%, đóng góp {s['impact']:+.3f})" for s in neg_list[:5]]
            lines.append("- Kéo xuống: " + ", ".join(neg_items))
        if pos_list:
            pos_items = [f"  {s['symbol']} ({s['change_pct']:+.2f}%, đóng góp {s['impact']:+.3f})" for s in pos_list[:5]]
            lines.append("- Nâng đỡ: " + ", ".join(pos_items))
        impact_text = "\n".join(lines)

    # Build top movers description
    top_gainers = summary.get('top_gainers', [])
    top_losers = summary.get('top_losers', [])
    movers_text = ""
    if top_gainers or top_losers:
        lines = ["TOP CỔ PHIẾU BIẾN ĐỘNG:"]
        if top_gainers:
            g_items = [f"{s['symbol']} ({s['change_pct']:+.2f}%)" for s in top_gainers[:5]]
            lines.append(f"- Tăng mạnh nhất: {', '.join(g_items)}")
        if top_losers:
            l_items = [f"{s['symbol']} ({s['change_pct']:+.2f}%)" for s in top_losers[:5]]
            lines.append(f"- Giảm mạnh nhất: {', '.join(l_items)}")
        movers_text = "\n".join(lines)

    extra_data = ""
    if impact_text:
        extra_data += f"\n{impact_text}\n"
    if movers_text:
        extra_data += f"\n{movers_text}\n"

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

    # Volume ratio
    vol_ratio = b.get('volume_ratio')
    vol_text = ""
    if vol_ratio is not None:
        vol_text = f"\n- Volume ratio (tăng/giảm): {vol_ratio:.2f}" if isinstance(vol_ratio, float) else f"\n- Volume ratio: {vol_ratio}"

    return f"""Dựa trên dữ liệu thị trường ngày {summary['date']}, viết phân tích tổng quan.

DỮ LIỆU:
{breadth_text}{vol_text}
{extra_data}{ma20_text}

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
NẾU CÓ dữ liệu cổ phiếu tác động, đề cập cụ thể tên mã cổ phiếu kéo xuống/nâng đỡ VNINDEX với % thay đổi và điểm đóng góp.
Ví dụ: "VCB (-4.83%, đóng góp -0.211), HPG (-2.72%, đóng góp -0.102)..."
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

5. XẾP HẠNG

6. PHÂN TÍCH NGÀNH

7. NHẬN ĐỊNH"""


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

Viết ĐÚNG 14 phần, mỗi phần bắt đầu bằng tiêu đề IN HOA trên dòng riêng.
MỖI PHẦN BẮT BUỘC theo cấu trúc sau:

Kết luận ngắn: [1 câu tóm tắt nhận định chính]

Dẫn chứng & Ý nghĩa:
1. [Tiêu đề dẫn chứng]: [Giải thích chi tiết với số liệu cụ thể từ data, ví dụ giá, MA, RSI...]
2. [Tiêu đề dẫn chứng]: [Giải thích chi tiết]
3. [Tiêu đề dẫn chứng]: [Giải thích chi tiết]

Hành động gợi ý: [Khuyến nghị cụ thể với mức giá rõ ràng]

Điều kiện khiến kết luận sai: [Kịch bản invalidation cụ thể với mức giá]

RIÊNG phần XU HƯỚNG GIÁ, mục "Dẫn chứng & Ý nghĩa" phải chia thành:
- Ngắn hạn (1-5 phiên): [phân tích MA5, MA10, momentum ngắn]
- Trung hạn (10-20 phiên): [phân tích MA20, momentum trung]
- Dài hạn (>50 phiên): [phân tích MA50, MA200]

14 PHẦN CẦN VIẾT:

XU HƯỚNG GIÁ

XU HƯỚNG KHỐI LƯỢNG

KẾT HỢP XU HƯỚNG GIÁ VÀ KHỐI LƯỢNG

CUNG-CẦU

MỨC GIÁ QUAN TRỌNG

BIẾN ĐỘNG GIÁ

MÔ HÌNH GIÁ - MÔ HÌNH NẾN

MARKET BREADTH & TÂM LÝ THỊ TRƯỜNG

LỊCH SỬ & XU HƯỚNG BREADTH

RỦI RO

KHUYẾN NGHỊ VỊ THẾ

GIÁ MỤC TIÊU

KỊCH BẢN WHAT-IF

THÔNG TIN CHUNG"""


# ============================================================================
# CLAUDE API CALL
# ============================================================================

def call_claude(prompt, max_retries=3):
    """Gọi Claude API với retry."""
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
            log.warning(f"Claude API attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** (attempt + 1))
            else:
                log.error(f"Claude API failed after {max_retries} attempts")
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

    # Phần II trở đi: Các chỉ số
    part_num = 2
    for key in PART_ORDER[1:]:  # Skip "overview"
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

    # Generate all parts concurrently (overview + 15 indices)
    index_texts = {}
    overview_text = ""

    def _gen_overview():
        return ("overview", generate_overview(data))

    def _gen_index(k):
        return (k, generate_index(k, data))

    max_workers = min(5, len(PART_ORDER))
    log.info(f"Generating report with {max_workers} concurrent workers...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        futures.append(executor.submit(_gen_overview))
        for key in PART_ORDER[1:]:
            futures.append(executor.submit(_gen_index, key))

        for future in as_completed(futures):
            key, text = future.result()
            if key == "overview":
                overview_text = text or ""
                log.info("  OVERVIEW done")
            elif text:
                index_texts[key] = text
                log.info(f"  {INDICES[key][1]} done")

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
    log.info(f"Indices generated: {len(index_texts)}/15")

    # Cũng lưu path ra stdout để script khác đọc được
    print(f"REPORT_PATH={output_path}")

    log.info("=" * 60)
    log.info("REPORT GENERATION COMPLETED!")
    log.info("=" * 60)

    return str(output_path)


if __name__ == "__main__":
    main()
