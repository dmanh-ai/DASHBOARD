"""
Thu thập dữ liệu chứng khoán VN từ vnstock.
Output: JSON files trong market_cache/
"""

import json
import os
import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# Thêm parent vào path để import config
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import INDICES, HISTORY_DAYS, FOREIGN_FLOW_DAYS, HEATMAP_TOP_K

# ============================================================================
# PATHS
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / "market_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def save_json(data, filename):
    """Lưu data ra JSON file."""
    path = CACHE_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, default=str)
    log.info(f"Saved: {path} ({path.stat().st_size:,} bytes)")


# ============================================================================
# VNSTOCK INITIALIZATION
# ============================================================================

def init_vnstock():
    """Khởi tạo vnstock, trả về object chính."""
    try:
        from vnstock import Vnstock
        vs = Vnstock()
        log.info("vnstock initialized OK")
        return vs
    except ImportError:
        log.error("vnstock chưa cài. Chạy: pip install vnstock")
        sys.exit(1)
    except Exception as e:
        log.error(f"vnstock init failed: {e}")
        sys.exit(1)


# ============================================================================
# 1. THU THẬP INDEX OHLCV
# ============================================================================

def collect_index_ohlcv(vs):
    """Lấy OHLCV cho tất cả 15 chỉ số."""
    log.info("=" * 60)
    log.info("STEP 1: Thu thập Index OHLCV...")

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=HISTORY_DAYS + 50)).strftime("%Y-%m-%d")

    results = {}
    for key, (vnstock_code, display_name) in INDICES.items():
        try:
            log.info(f"  Fetching {display_name} ({vnstock_code})...")
            stock = vs.stock(symbol=vnstock_code, source="VCI")
            df = stock.quote.history(
                start=start_date, end=end_date,
                interval="1D", type="index"
            )

            if df is None or df.empty:
                log.warning(f"  No data for {display_name}")
                continue

            # Chuẩn hóa tên cột
            df.columns = [c.lower().strip() for c in df.columns]

            # Tìm cột time/date
            time_col = next((c for c in df.columns if c in ("time", "date", "trading_date")), None)
            if time_col is None:
                log.warning(f"  No time column found for {display_name}, cols: {list(df.columns)}")
                continue

            bars = []
            for _, row in df.iterrows():
                bars.append({
                    "d": str(row[time_col])[:10],
                    "o": round(float(row.get("open", 0)), 2),
                    "h": round(float(row.get("high", 0)), 2),
                    "l": round(float(row.get("low", 0)), 2),
                    "c": round(float(row.get("close", 0)), 2),
                    "v": int(row.get("volume", 0)),
                })

            results[key] = {
                "name": display_name,
                "bars": bars,
            }
            log.info(f"  OK: {display_name} → {len(bars)} bars")
            time.sleep(0.3)  # Rate limit

        except Exception as e:
            log.error(f"  FAILED {display_name}: {e}")
            continue

    if results:
        asof = max(r["bars"][-1]["d"] for r in results.values() if r["bars"])
        save_json({"asof": asof, "indices": results}, "index_ohlcv.json")
    else:
        log.error("No index OHLCV data collected!")

    return results


# ============================================================================
# 2. THU THẬP INDEX CONSTITUENTS
# ============================================================================

def collect_constituents(vs):
    """Lấy danh sách CP thành phần cho mỗi chỉ số."""
    log.info("=" * 60)
    log.info("STEP 2: Thu thập Index Constituents...")

    results = {}
    stock = vs.stock(symbol="VCB", source="VCI")

    for key, (vnstock_code, display_name) in INDICES.items():
        try:
            log.info(f"  Fetching constituents: {display_name}...")
            symbols = stock.listing.symbols_by_group(vnstock_code)

            if symbols is None:
                log.warning(f"  No constituents for {display_name}")
                continue

            # symbols có thể là list hoặc DataFrame
            if hasattr(symbols, "tolist"):
                symbol_list = symbols.tolist()
            elif hasattr(symbols, "values"):
                # DataFrame - lấy cột đầu tiên
                symbol_list = symbols.iloc[:, 0].tolist()
            else:
                symbol_list = list(symbols)

            results[key] = {
                "name": display_name,
                "symbols": symbol_list,
                "count": len(symbol_list),
            }
            log.info(f"  OK: {display_name} → {len(symbol_list)} stocks")
            time.sleep(0.2)

        except Exception as e:
            log.error(f"  FAILED {display_name}: {e}")
            continue

    save_json(results, "constituents.json")
    return results


# ============================================================================
# 3. THU THẬP GIÁ TẤT CẢ CP (cho heatmap + breadth)
# ============================================================================

def collect_all_stocks(vs, constituents):
    """Lấy giá gần nhất cho tất cả CP trong các chỉ số."""
    log.info("=" * 60)
    log.info("STEP 3: Thu thập giá tất cả CP...")

    # Gom tất cả symbols unique
    all_symbols = set()
    for data in constituents.values():
        all_symbols.update(data.get("symbols", []))

    log.info(f"  Total unique symbols: {len(all_symbols)}")

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=HISTORY_DAYS + 50)).strftime("%Y-%m-%d")

    results = {}
    failed = []
    total = len(all_symbols)

    for i, symbol in enumerate(sorted(all_symbols), 1):
        try:
            if i % 50 == 0:
                log.info(f"  Progress: {i}/{total}")

            stock = vs.stock(symbol=symbol, source="VCI")
            df = stock.quote.history(start=start_date, end=end_date, interval="1D")

            if df is None or df.empty:
                failed.append(symbol)
                continue

            df.columns = [c.lower().strip() for c in df.columns]
            time_col = next((c for c in df.columns if c in ("time", "date", "trading_date")), None)
            if time_col is None:
                failed.append(symbol)
                continue

            # Lấy tất cả bars (cho indicators) và latest
            bars = []
            for _, row in df.iterrows():
                bars.append({
                    "d": str(row[time_col])[:10],
                    "o": round(float(row.get("open", 0)), 2),
                    "h": round(float(row.get("high", 0)), 2),
                    "l": round(float(row.get("low", 0)), 2),
                    "c": round(float(row.get("close", 0)), 2),
                    "v": int(row.get("volume", 0)),
                })

            if bars:
                latest = bars[-1]
                prev = bars[-2] if len(bars) > 1 else latest
                change = latest["c"] - prev["c"]
                change_pct = (change / prev["c"] * 100) if prev["c"] else 0

                results[symbol] = {
                    "bars": bars,
                    "latest": {
                        "date": latest["d"],
                        "close": latest["c"],
                        "volume": latest["v"],
                        "change": round(change, 2),
                        "change_pct": round(change_pct, 2),
                    }
                }

            time.sleep(0.1)  # Rate limit

        except Exception as e:
            failed.append(symbol)
            continue

    log.info(f"  Collected: {len(results)}/{total} stocks, failed: {len(failed)}")
    if failed:
        log.warning(f"  Failed symbols: {failed[:20]}{'...' if len(failed) > 20 else ''}")

    save_json({"asof": end_date, "stocks": results}, "all_stocks.json")
    return results


# ============================================================================
# 4. THU THẬP FOREIGN FLOW (dòng tiền ngoại)
# ============================================================================

def collect_foreign_flow(vs, constituents):
    """Lấy dòng tiền ngoại cho CP trong các chỉ số chính."""
    log.info("=" * 60)
    log.info("STEP 4: Thu thập Foreign Flow...")

    # Chỉ lấy cho các chỉ số chính (VNINDEX, VN30) để tiết kiệm API calls
    key_indices = ["vnindex", "vn30", "vn100"]
    all_symbols = set()
    for key in key_indices:
        if key in constituents:
            all_symbols.update(constituents[key].get("symbols", []))

    log.info(f"  Fetching foreign flow for {len(all_symbols)} stocks...")

    results = {}
    for i, symbol in enumerate(sorted(all_symbols), 1):
        try:
            if i % 50 == 0:
                log.info(f"  Progress: {i}/{len(all_symbols)}")

            from vnstock import Trading
            trading = Trading(source="VCI", symbol=symbol)
            df = trading.foreign_trade(symbol=symbol)

            if df is None or df.empty:
                continue

            df.columns = [c.lower().strip() for c in df.columns]

            # Lấy 20 ngày gần nhất
            records = []
            for _, row in df.tail(FOREIGN_FLOW_DAYS).iterrows():
                date_col = next((c for c in df.columns if "date" in c or "time" in c), df.columns[0])
                rec = {"date": str(row[date_col])[:10]}
                for col in df.columns:
                    if "buy" in col or "sell" in col or "net" in col:
                        rec[col] = float(row[col]) if not (hasattr(row[col], "__float__") and row[col] != row[col]) else 0
                records.append(rec)

            if records:
                results[symbol] = records

            time.sleep(0.15)

        except Exception as e:
            continue

    log.info(f"  Collected foreign flow: {len(results)} stocks")
    save_json({"asof": datetime.now().strftime("%Y-%m-%d"), "stocks": results}, "foreign_flow.json")
    return results


# ============================================================================
# 5. TÍNH MARKET BREADTH
# ============================================================================

def compute_breadth(all_stocks):
    """Tính advance/decline từ dữ liệu CP."""
    log.info("=" * 60)
    log.info("STEP 5: Tính Market Breadth...")

    advancing = 0
    declining = 0
    unchanged = 0
    adv_volume = 0
    dec_volume = 0

    for symbol, data in all_stocks.items():
        latest = data.get("latest", {})
        change_pct = latest.get("change_pct", 0)
        volume = latest.get("volume", 0)

        if change_pct > 0:
            advancing += 1
            adv_volume += volume
        elif change_pct < 0:
            declining += 1
            dec_volume += volume
        else:
            unchanged += 1

    total = advancing + declining + unchanged
    trin = None
    if declining > 0 and dec_volume > 0:
        trin = round((advancing / declining) / (adv_volume / dec_volume), 4) if advancing > 0 else 0

    volume_ratio = round(adv_volume / dec_volume, 4) if dec_volume > 0 else 0
    net_ad = advancing - declining

    breadth = {
        "asof": datetime.now().strftime("%Y-%m-%d"),
        "advancing": advancing,
        "declining": declining,
        "unchanged": unchanged,
        "total_stocks": total,
        "advance_volume": adv_volume,
        "decline_volume": dec_volume,
        "total_volume": adv_volume + dec_volume,
        "trin": trin,
        "volume_ratio": volume_ratio,
        "net_ad": net_ad,
        "mcclellan": net_ad,  # Simplified - ideally need historical EMA
        "mcclellan_type": "Net A-D (simplified)",
    }

    save_json(breadth, "breadth_snapshot.json")
    log.info(f"  Breadth: +{advancing} / -{declining} / ={unchanged}")
    return breadth


# ============================================================================
# 6. TÍNH HEATMAP DATA
# ============================================================================

def compute_heatmaps(all_stocks, constituents):
    """Tính heatmap cho mỗi chỉ số."""
    log.info("=" * 60)
    log.info("STEP 6: Tính Heatmap Data...")

    heatmaps = {}
    for key, const_data in constituents.items():
        symbols = const_data.get("symbols", [])
        gainers = []
        losers = []

        for sym in symbols:
            if sym not in all_stocks:
                continue
            latest = all_stocks[sym]["latest"]
            point = {
                "symbol": sym,
                "price": latest["close"],
                "volume": latest["volume"],
                "value": round(latest["close"] * latest["volume"], 0),
                "change_pct": latest["change_pct"],
            }
            if latest["change_pct"] > 0:
                gainers.append(point)
            elif latest["change_pct"] < 0:
                losers.append(point)

        gainers.sort(key=lambda x: x["change_pct"], reverse=True)
        losers.sort(key=lambda x: x["change_pct"])

        heatmaps[key] = {
            "gainers": gainers[:HEATMAP_TOP_K],
            "losers": losers[:HEATMAP_TOP_K],
            "count": len(symbols),
            "count_pos": len(gainers),
            "count_neg": len(losers),
        }

    save_json({"asof": datetime.now().strftime("%Y-%m-%d"), "indices": heatmaps}, "heatmaps.json")
    log.info(f"  Heatmaps computed for {len(heatmaps)} indices")
    return heatmaps


# ============================================================================
# MAIN
# ============================================================================

def main():
    log.info("=" * 60)
    log.info("DATA COLLECTION STARTED")
    log.info("=" * 60)

    vs = init_vnstock()

    # Step 1: Index OHLCV
    index_ohlcv = collect_index_ohlcv(vs)

    # Step 2: Constituents
    constituents = collect_constituents(vs)

    # Step 3: All stocks
    all_stocks = collect_all_stocks(vs, constituents)

    # Step 4: Foreign flow
    collect_foreign_flow(vs, constituents)

    # Step 5: Market breadth
    compute_breadth(all_stocks)

    # Step 6: Heatmaps
    compute_heatmaps(all_stocks, constituents)

    log.info("=" * 60)
    log.info("DATA COLLECTION COMPLETED!")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
