"""
Lưu snapshot dữ liệu hàng ngày vào history_data.json.
Mỗi ngày giao dịch append 1 record mới, tích lũy theo thời gian.
Dùng để phân tích xu hướng dài hạn trên dashboard.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / "market_cache"
HISTORY_FILE = PROJECT_ROOT / "history_data.json"
MAX_HISTORY_DAYS = 365  # Giữ tối đa 1 năm


def load_json(filename):
    path = CACHE_DIR / filename
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_float(v):
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def build_daily_snapshot():
    """Trích xuất metrics quan trọng từ cache hôm nay."""
    index_ohlcv = load_json("index_ohlcv.json")
    breadth = load_json("breadth_snapshot.json")
    foreign = load_json("foreign_data.json")
    commodities = load_json("commodities_data.json")
    portfolio = load_json("portfolio_data.json")

    asof = index_ohlcv.get("asof", datetime.now().strftime("%Y-%m-%d"))

    # 1. Index prices (all 15)
    indices = {}
    for key, idx_data in index_ohlcv.get("indices", {}).items():
        latest = idx_data.get("latest", {})
        indicators = idx_data.get("indicators", {})
        if latest.get("close") is not None:
            indices[key] = {
                "close": latest["close"],
                "change_pct": latest.get("change_pct"),
                "rsi14": indicators.get("rsi_14") or indicators.get("rsi14"),
                "above_ma20": indicators.get("above_ma20"),
                "volume": latest.get("volume"),
            }

    # 2. Breadth
    breadth_snap = {}
    if breadth:
        breadth_snap = {
            "advancing": breadth.get("advancing"),
            "declining": breadth.get("declining"),
            "unchanged": breadth.get("unchanged"),
            "total": breadth.get("total_stocks"),
            "trin": breadth.get("trin"),
            "mcclellan": breadth.get("mcclellan"),
        }

    # 3. Foreign flow
    foreign_snap = {}
    if foreign and foreign.get("flow"):
        for ex, fl in foreign["flow"].items():
            foreign_snap[ex] = {
                "net": fl.get("net_value"),
                "buy": fl.get("buy_value"),
                "sell": fl.get("sell_value"),
            }

    # 4. Commodities (key items)
    comm_snap = {}
    wc = commodities.get("world_commodities", [])
    for c in wc:
        key = c.get("key") or c.get("name", "").lower().replace(" ", "_")
        if key and c.get("close") is not None:
            comm_snap[key] = {
                "close": c["close"],
                "change_pct": c.get("change_pct"),
            }
    # Gold VN
    gold_list = commodities.get("gold", [])
    if gold_list:
        g = gold_list[0]
        comm_snap["gold_vn"] = {
            "buy": g.get("buy"),
            "sell": g.get("sell"),
        }
    # USD/VND
    fx_rates = commodities.get("exchange_rates", [])
    for r in fx_rates:
        if (r.get("code") or "").upper() == "USD":
            comm_snap["usd_vnd"] = {"sell": r.get("sell")}
            break

    # 5. Portfolio snapshot
    portfolio_snap = {}
    holdings = portfolio.get("holdings", [])
    if holdings:
        total_value = 0
        total_cost = 0
        items = []
        for h in holdings:
            symbol = h.get("symbol", "")
            qty = h.get("quantity", 0)
            avg = h.get("avg_price", 0)
            # Current price not always in portfolio_data, use what's available
            current = h.get("current_price") or h.get("market_price") or avg
            cost = qty * avg
            value = qty * current
            total_cost += cost
            total_value += value
            items.append({
                "symbol": symbol,
                "qty": qty,
                "avg": avg,
                "current": current,
                "pnl_pct": round((current / avg - 1) * 100, 2) if avg > 0 else 0,
            })
        portfolio_snap = {
            "total_value": total_value,
            "total_cost": total_cost,
            "pnl_pct": round((total_value / total_cost - 1) * 100, 2) if total_cost > 0 else 0,
            "holdings": items,
            "equity_ratio": portfolio.get("equity_ratio"),
            "margin_ratio": portfolio.get("margin_ratio"),
        }

    return {
        "date": asof,
        "ts": datetime.now().isoformat(),
        "indices": indices,
        "breadth": breadth_snap,
        "foreign": foreign_snap,
        "commodities": comm_snap,
        "portfolio": portfolio_snap,
    }


def load_history():
    """Load lịch sử hiện có."""
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def save_history(records):
    """Lưu lịch sử ra file."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, default=str)
    log.info(f"History saved: {HISTORY_FILE} ({len(records)} records, {HISTORY_FILE.stat().st_size:,} bytes)")


def main():
    log.info("=" * 60)
    log.info("ARCHIVING DAILY SNAPSHOT...")
    log.info("=" * 60)

    snapshot = build_daily_snapshot()
    today = snapshot["date"]

    if not snapshot.get("indices"):
        log.warning("No index data available, skipping archive")
        return

    # Load existing history
    history = load_history()
    existing_dates = {r.get("date") for r in history}

    if today in existing_dates:
        # Update existing record for today
        history = [r for r in history if r.get("date") != today]
        log.info(f"Updating existing record for {today}")

    history.append(snapshot)

    # Sort by date
    history.sort(key=lambda r: r.get("date", ""))

    # Trim to max history
    if len(history) > MAX_HISTORY_DAYS:
        history = history[-MAX_HISTORY_DAYS:]
        log.info(f"Trimmed to {MAX_HISTORY_DAYS} records")

    save_history(history)

    log.info(f"Snapshot for {today}: {len(snapshot.get('indices', {}))} indices, "
             f"breadth: {snapshot.get('breadth', {}).get('advancing', 'N/A')} up / "
             f"{snapshot.get('breadth', {}).get('declining', 'N/A')} down")
    log.info("=" * 60)
    log.info("ARCHIVE COMPLETE!")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
