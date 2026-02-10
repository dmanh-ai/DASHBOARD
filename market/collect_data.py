"""
Thu thập dữ liệu chứng khoán VN từ repo dmanh-ai/data.
Đọc CSV files có sẵn tại: github.com/dmanh-ai/data/data/indices/
Indicators (SMA, RSI, MACD, BB) đã được tính sẵn trong CSV.
Output: JSON files trong market_cache/
"""

import csv
import io
import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import INDICES, AVAILABLE_CSV, PRICE_SCALE, GITHUB_DATA_URL

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / "market_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# DATA SOURCE: GitHub repo dmanh-ai/data
# ============================================================================

GITHUB_RAW_BASE = GITHUB_DATA_URL


def save_json(data, filename):
    """Lưu data ra JSON file."""
    path = CACHE_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, default=str)
    log.info(f"Saved: {path} ({path.stat().st_size:,} bytes)")


# ============================================================================
# FETCH CSV FROM GITHUB
# ============================================================================

def fetch_csv(filename, max_retries=3):
    """Tải CSV từ GitHub raw, trả về list of dicts."""
    url = f"{GITHUB_RAW_BASE}/{filename}"
    log.info(f"  Fetching: {url}")

    for attempt in range(max_retries):
        try:
            req = Request(url, headers={"User-Agent": "DASHBOARD-Pipeline/1.0"})
            with urlopen(req, timeout=30) as resp:
                text = resp.read().decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text))
            rows = list(reader)
            log.info(f"  OK: {filename} → {len(rows)} rows")
            return rows
        except URLError as e:
            log.warning(f"  Attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(2 ** (attempt + 1))
        except Exception as e:
            log.error(f"  Error parsing {filename}: {e}")
            return []

    log.error(f"  FAILED to fetch {filename} after {max_retries} attempts")
    return []


def parse_float(val, scale=1.0):
    """Parse float an toàn, trả về None nếu rỗng."""
    if val is None or str(val).strip() == "":
        return None
    try:
        return round(float(val) * scale, 2)
    except (ValueError, TypeError):
        return None


def parse_int(val):
    """Parse int an toàn."""
    if val is None or str(val).strip() == "":
        return 0
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


# ============================================================================
# 1. THU THẬP INDEX OHLCV + INDICATORS TỪ CSV
# ============================================================================

def collect_index_data():
    """Lấy OHLCV + indicators từ CSV files trên GitHub."""
    log.info("=" * 60)
    log.info("STEP 1: Thu thập Index OHLCV + Indicators từ GitHub...")

    results = {}

    for dashboard_key, csv_file in AVAILABLE_CSV.items():

        rows = fetch_csv(csv_file)
        if not rows:
            continue

        # Auto-detect price scale: nếu close cuối < 10 → data bị scale 1/1000
        last_close_raw = None
        for r in reversed(rows):
            try:
                v = float(r.get("close", "0"))
                if v > 0:
                    last_close_raw = v
                    break
            except (ValueError, TypeError):
                pass
        scale = PRICE_SCALE if (last_close_raw and last_close_raw < 10) else 1.0
        if scale != 1.0:
            log.info(f"  {csv_file}: auto-detected price scale ×{scale}")

        bars = []
        indicators_latest = {}

        for row in rows:
            date_str = str(row.get("time", ""))[:10]
            if not date_str:
                continue

            bar = {
                "d": date_str,
                "o": parse_float(row.get("open"), scale),
                "h": parse_float(row.get("high"), scale),
                "l": parse_float(row.get("low"), scale),
                "c": parse_float(row.get("close"), scale),
                "v": parse_int(row.get("volume")),
            }

            # Skip rows với giá = 0 hoặc None
            if not bar["c"] or bar["c"] == 0:
                continue

            bars.append(bar)

            # Lưu indicators từ row cuối cùng (latest)
            indicators_latest = {
                "sma_20": parse_float(row.get("sma_20"), scale),
                "sma_50": parse_float(row.get("sma_50"), scale),
                "sma_200": parse_float(row.get("sma_200"), scale),
                "rsi_14": parse_float(row.get("rsi_14")),  # RSI không scale
                "macd": parse_float(row.get("macd"), scale),
                "macd_signal": parse_float(row.get("macd_signal"), scale),
                "macd_hist": parse_float(row.get("macd_hist"), scale),
                "bb_upper": parse_float(row.get("bb_upper"), scale),
                "bb_lower": parse_float(row.get("bb_lower"), scale),
                "daily_return": parse_float(row.get("daily_return")),  # % không scale
                "volatility_20d": parse_float(row.get("volatility_20d")),
            }

        if not bars:
            continue

        latest = bars[-1]
        prev = bars[-2] if len(bars) > 1 else latest
        change = (latest["c"] or 0) - (prev["c"] or 0)
        change_pct = (change / prev["c"] * 100) if prev.get("c") else 0

        display_name = INDICES.get(dashboard_key, (csv_file, csv_file))[1]

        results[dashboard_key] = {
            "name": display_name,
            "bars": bars,
            "indicators": indicators_latest,
            "latest": {
                "date": latest["d"],
                "close": latest["c"],
                "volume": latest["v"],
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
            },
        }
        log.info(f"  {display_name}: {len(bars)} bars, latest={latest['d']} close={latest['c']}")

    if results:
        asof = max(r["latest"]["date"] for r in results.values())
        save_json({"asof": asof, "indices": results}, "index_ohlcv.json")
    else:
        log.error("No index data collected!")

    return results


# ============================================================================
# 2. TÍNH THÊM INDICATORS CHO GENERATE_REPORT
# ============================================================================

def enrich_indicators(index_data):
    """Bổ sung thêm indicators mà CSV chưa có (MA5, MA10, MA100, ADX, OBV...)."""
    log.info("=" * 60)
    log.info("STEP 2: Tính bổ sung indicators...")

    from indicators import compute_all_indicators

    for key, data in index_data.items():
        bars = data.get("bars", [])
        if len(bars) < 20:
            continue

        computed = compute_all_indicators(bars)

        # Merge: giữ indicators từ CSV (chính xác hơn), bổ sung các cái mới
        csv_ind = data.get("indicators", {})
        merged = {
            # Từ CSV (chính xác, đã tính trên toàn bộ history)
            "sma_20": csv_ind.get("sma_20") or computed.get("ma20"),
            "sma_50": csv_ind.get("sma_50") or computed.get("ma50"),
            "sma_200": csv_ind.get("sma_200") or computed.get("ma200"),
            "rsi_14": csv_ind.get("rsi_14") or computed.get("rsi14"),
            "macd": csv_ind.get("macd") or computed.get("macd_line"),
            "macd_signal": csv_ind.get("macd_signal") or computed.get("macd_signal"),
            "macd_hist": csv_ind.get("macd_hist") or computed.get("macd_histogram"),
            "bb_upper": csv_ind.get("bb_upper") or computed.get("bb_upper"),
            "bb_lower": csv_ind.get("bb_lower") or computed.get("bb_lower"),
            "daily_return": csv_ind.get("daily_return") or computed.get("change_pct"),
            "volatility_20d": csv_ind.get("volatility_20d"),
            # Bổ sung từ compute (CSV không có)
            "ma5": computed.get("ma5"),
            "ma10": computed.get("ma10"),
            "ma100": computed.get("ma100"),
            "ema12": computed.get("ema12"),
            "ema26": computed.get("ema26"),
            "bb_middle": computed.get("bb_middle"),
            "obv": computed.get("obv"),
            "volume_ma20": computed.get("volume_ma20"),
            "adx14": computed.get("adx14"),
            # Position flags
            "above_ma20": computed.get("above_ma20"),
            "above_ma50": computed.get("above_ma50"),
            "above_ma200": computed.get("above_ma200"),
        }

        data["indicators"] = merged
        log.info(f"  Enriched: {data['name']}")

    save_json(
        {"asof": max(d["latest"]["date"] for d in index_data.values()), "indices": index_data},
        "index_ohlcv.json",
    )
    return index_data


# ============================================================================
# 3. TẠO BREADTH ĐƠN GIẢN TỪ INDEX DATA
# ============================================================================

def compute_breadth_from_indices(index_data):
    """Tính breadth đơn giản từ các chỉ số."""
    log.info("=" * 60)
    log.info("STEP 3: Tính Market Breadth...")

    advancing = 0
    declining = 0
    unchanged = 0

    for key, data in index_data.items():
        change_pct = data["latest"].get("change_pct", 0)
        if change_pct > 0:
            advancing += 1
        elif change_pct < 0:
            declining += 1
        else:
            unchanged += 1

    breadth = {
        "asof": datetime.now().strftime("%Y-%m-%d"),
        "advancing": advancing,
        "declining": declining,
        "unchanged": unchanged,
        "total_stocks": advancing + declining + unchanged,
        "net_ad": advancing - declining,
        "source": "index-level (simplified)",
    }

    save_json(breadth, "breadth_snapshot.json")
    log.info(f"  Breadth: +{advancing} / -{declining} / ={unchanged}")
    return breadth


# ============================================================================
# MAIN
# ============================================================================

def main():
    log.info("=" * 60)
    log.info("DATA COLLECTION STARTED (source: dmanh-ai/data)")
    log.info("=" * 60)

    # Step 1: Fetch index OHLCV + indicators from CSV
    index_data = collect_index_data()

    if not index_data:
        log.error("No data collected! Check network or GitHub repo.")
        sys.exit(1)

    # Step 2: Enrich with additional indicators
    index_data = enrich_indicators(index_data)

    # Step 3: Breadth from indices
    compute_breadth_from_indices(index_data)

    log.info("=" * 60)
    log.info(f"DATA COLLECTION COMPLETED! Indices: {list(index_data.keys())}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
