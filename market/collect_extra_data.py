"""
Thu thập dữ liệu bổ sung: hàng hoá, tỷ giá, vàng, trái phiếu, quỹ mở.
Output: market_cache/extra_data.json
"""

import csv
import io
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / "market_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

GITHUB_BASE = "https://raw.githubusercontent.com/dmanh-ai/vnstock/main/data"

# ============================================================================
# COMMODITY DEFINITIONS (OHLCV without dates - rows are chronological)
# ============================================================================
COMMODITIES = {
    "oil_crude":     {"file": "commodity/oil_crude.csv",     "name": "Dầu thô WTI",   "unit": "USD/thùng", "group": "Năng lượng"},
    "gas_natural":   {"file": "commodity/gas_natural.csv",   "name": "Khí tự nhiên",   "unit": "USD/MMBtu", "group": "Năng lượng"},
    "gold_global":   {"file": "commodity/gold_global.csv",   "name": "Vàng thế giới",  "unit": "USD/oz",    "group": "Kim loại quý"},
    "iron_ore":      {"file": "commodity/iron_ore.csv",      "name": "Quặng sắt",      "unit": "USD/tấn",   "group": "Kim loại"},
    "steel_hrc":     {"file": "commodity/steel_hrc.csv",     "name": "Thép HRC",       "unit": "USD/tấn",   "group": "Kim loại"},
    "corn":          {"file": "commodity/corn.csv",          "name": "Ngô",            "unit": "USc/bushel","group": "Nông sản"},
    "soybean":       {"file": "commodity/soybean.csv",       "name": "Đậu nành",       "unit": "USc/bushel","group": "Nông sản"},
    "sugar":         {"file": "commodity/sugar.csv",         "name": "Đường",          "unit": "USc/lb",    "group": "Nông sản"},
    "fertilizer_ure":{"file": "commodity/fertilizer_ure.csv","name": "Phân Urê",       "unit": "USD/tấn",   "group": "Nông sản"},
}

# FX pairs to collect (OHLC with dates)
FX_PAIRS = {
    "USDVND": "USD/VND",
    "EURUSD": "EUR/USD",
    "USDJPY": "USD/JPY",
    "GBPUSD": "GBP/USD",
    "USDCNY": "USD/CNY",
    "USDKRW": "USD/KRW",
    "AUDUSD": "AUD/USD",
    "USDSGD": "USD/SGD",
}


# ============================================================================
# HELPERS
# ============================================================================

def fetch_text(url, timeout=30):
    """Fetch text content from URL."""
    try:
        req = Request(url, headers={"User-Agent": "DashboardBot/1.0"})
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except HTTPError as e:
        if e.code == 404:
            log.warning(f"  404 Not Found: {url}")
        else:
            log.warning(f"  HTTP {e.code}: {url}")
        return None
    except Exception as e:
        log.warning(f"  Error fetching {url}: {e}")
        return None


def parse_csv(text):
    """Parse CSV text to list of dicts."""
    if not text:
        return []
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


def safe_float(val):
    """Convert value to float, handling commas and edge cases."""
    if val is None:
        return None
    s = str(val).strip().replace(",", "").replace('"', '')
    if not s or s == "-":
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def pct_change(current, previous):
    """Calculate percentage change."""
    if current is None or previous is None or previous == 0:
        return None
    return round((current / previous - 1) * 100, 2)


# ============================================================================
# STEP 1: COMMODITIES (OHLCV without dates)
# ============================================================================

def collect_commodities():
    """Collect commodity OHLCV data. Compute change vs T-1 and T-20."""
    log.info("STEP 1: Collecting commodity data...")
    results = []

    for key, meta in COMMODITIES.items():
        url = f"{GITHUB_BASE}/{meta['file']}"
        text = fetch_text(url)
        if not text:
            continue

        rows = parse_csv(text)
        if len(rows) < 2:
            log.warning(f"  {key}: insufficient data ({len(rows)} rows)")
            continue

        # Last row = latest
        latest = safe_float(rows[-1].get("close"))
        prev = safe_float(rows[-2].get("close")) if len(rows) >= 2 else None
        prev_20 = safe_float(rows[-21].get("close")) if len(rows) >= 21 else None

        if latest is None:
            continue

        item = {
            "key": key,
            "name": meta["name"],
            "unit": meta["unit"],
            "group": meta["group"],
            "close": latest,
            "change_1d": pct_change(latest, prev),
            "change_20d": pct_change(latest, prev_20),
        }
        results.append(item)
        log.info(f"  {meta['name']}: {latest} {meta['unit']} ({item['change_1d']:+.2f}% 1D)" if item["change_1d"] is not None else f"  {meta['name']}: {latest}")

    return results


# ============================================================================
# STEP 2: EXCHANGE RATES (from exchange_rates.csv)
# ============================================================================

def collect_exchange_rates():
    """Collect Vietcombank exchange rates."""
    log.info("STEP 2: Collecting exchange rates...")
    url = f"{GITHUB_BASE}/exchange_rates.csv"
    text = fetch_text(url)
    if not text:
        return []

    rows = parse_csv(text)
    if not rows:
        return []

    # Group by date
    by_date = {}
    for row in rows:
        d = row.get("date", "")
        if d not in by_date:
            by_date[d] = []
        by_date[d].append(row)

    dates = sorted(by_date.keys())
    if not dates:
        return []

    latest_date = dates[-1]
    prev_date = dates[-2] if len(dates) >= 2 else None

    # Build previous day lookup
    prev_lookup = {}
    if prev_date:
        for row in by_date[prev_date]:
            code = row.get("currency_code", "")
            prev_lookup[code] = safe_float(row.get("sell"))

    results = []
    for row in by_date[latest_date]:
        code = row.get("currency_code", "")
        name = row.get("currency_name", "")
        buy_cash = safe_float(row.get("buy_cash"))
        buy_transfer = safe_float(row.get("buy_transfer"))
        sell = safe_float(row.get("sell"))

        if sell is None:
            continue

        prev_sell = prev_lookup.get(code)
        change_1d = pct_change(sell, prev_sell)

        results.append({
            "code": code,
            "name": name,
            "buy_cash": buy_cash,
            "buy_transfer": buy_transfer,
            "sell": sell,
            "change_1d": change_1d,
            "date": latest_date,
        })

    log.info(f"  {len(results)} currencies collected for {latest_date}")
    return results


# ============================================================================
# STEP 3: FX OHLC (historical for change_20d)
# ============================================================================

def collect_fx():
    """Collect FX OHLC data for historical change calculations."""
    log.info("STEP 3: Collecting FX historical data...")
    results = []

    for pair, label in FX_PAIRS.items():
        url = f"{GITHUB_BASE}/fx/{pair}.csv"
        text = fetch_text(url)
        if not text:
            continue

        rows = parse_csv(text)
        if len(rows) < 2:
            continue

        latest = safe_float(rows[-1].get("close"))
        prev = safe_float(rows[-2].get("close")) if len(rows) >= 2 else None
        prev_20 = safe_float(rows[-21].get("close")) if len(rows) >= 21 else None
        latest_date = rows[-1].get("time", "")[:10] if rows[-1].get("time") else ""

        if latest is None:
            continue

        results.append({
            "pair": pair,
            "label": label,
            "close": latest,
            "change_1d": pct_change(latest, prev),
            "change_20d": pct_change(latest, prev_20),
            "date": latest_date,
        })
        log.info(f"  {label}: {latest}")

    return results


# ============================================================================
# STEP 4: GOLD PRICES (VN domestic)
# ============================================================================

def collect_gold():
    """Collect Vietnamese gold prices (SJC) from all branches."""
    log.info("STEP 4: Collecting gold prices...")
    url = f"{GITHUB_BASE}/gold_prices.csv"
    text = fetch_text(url)
    if not text:
        return []

    rows = parse_csv(text)
    if not rows:
        return []

    # Group by date
    by_date = {}
    for row in rows:
        d = row.get("date", "")
        if d not in by_date:
            by_date[d] = []
        by_date[d].append(row)

    dates = sorted(by_date.keys())
    if not dates:
        return []

    latest_date = dates[-1]
    prev_date = dates[-2] if len(dates) >= 2 else None

    # Build prev lookup by branch
    prev_lookup = {}
    if prev_date:
        for row in by_date[prev_date]:
            branch = row.get("branch", "")
            prev_lookup[branch] = safe_float(row.get("sell_price"))

    results = []
    for row in by_date[latest_date]:
        branch = row.get("branch", "")
        name = row.get("name", "")
        buy = safe_float(row.get("buy_price"))
        sell = safe_float(row.get("sell_price"))

        if sell is None:
            continue

        prev_sell = prev_lookup.get(branch)
        change_1d = pct_change(sell, prev_sell)

        results.append({
            "name": name,
            "branch": branch,
            "buy": buy,
            "sell": sell,
            "change_1d": change_1d,
            "date": latest_date,
        })

    log.info(f"  {len(results)} gold prices for {latest_date}")
    return results


# ============================================================================
# STEP 5: BONDS
# ============================================================================

def collect_bonds():
    """Collect bond metadata."""
    log.info("STEP 5: Collecting bond data...")
    url = f"{GITHUB_BASE}/metadata/corporate_bonds.csv"
    text = fetch_text(url)
    if not text:
        return []
    rows = parse_csv(text)
    log.info(f"  {len(rows)} bond records")
    return rows


# ============================================================================
# STEP 6: FUND DATA
# ============================================================================

def collect_funds():
    """Collect fund listings and holdings."""
    log.info("STEP 6: Collecting fund data...")
    result = {"listings": [], "holdings": []}

    # Fund listings (NAV, performance)
    url = f"{GITHUB_BASE}/funds/fund_listing.csv"
    text = fetch_text(url)
    if text:
        rows = parse_csv(text)
        for row in rows:
            result["listings"].append({
                "short_name": row.get("short_name", ""),
                "name": row.get("name", ""),
                "fund_type": row.get("fund_type", ""),
                "owner": row.get("fund_owner_name", ""),
                "nav": safe_float(row.get("nav")),
                "nav_change_1d": safe_float(row.get("nav_change_previous")),
                "nav_change_1m": safe_float(row.get("nav_change_1m")),
                "nav_change_3m": safe_float(row.get("nav_change_3m")),
                "nav_change_12m": safe_float(row.get("nav_change_12m")),
                "nav_change_ytd": safe_float(row.get("nav_change_last_year")),
                "nav_update": row.get("nav_update_at", ""),
                "fund_id": row.get("fund_id_fmarket", ""),
            })
        log.info(f"  {len(result['listings'])} fund listings")

    # Fund holdings (stock allocations)
    url = f"{GITHUB_BASE}/funds/fund_holdings.csv"
    text = fetch_text(url)
    if text:
        rows = parse_csv(text)
        for row in rows:
            pct = safe_float(row.get("net_asset_percent"))
            if pct is None:
                continue
            result["holdings"].append({
                "stock": row.get("stock_code", ""),
                "industry": row.get("industry", ""),
                "pct": pct,
                "type": row.get("type_asset", ""),
                "fund_id": row.get("fundId", ""),
                "fund_name": row.get("short_name", ""),
                "update_at": row.get("update_at", ""),
            })
        log.info(f"  {len(result['holdings'])} fund holding records")

    return result


# ============================================================================
# STEP 7: PORTFOLIO (load from config if exists)
# ============================================================================

def load_portfolio():
    """Load portfolio from market/portfolio.json if it exists."""
    log.info("STEP 7: Loading portfolio...")
    portfolio_path = Path(__file__).resolve().parent / "portfolio.json"
    if not portfolio_path.exists():
        log.info("  portfolio.json not found, skipping")
        return []

    try:
        with open(portfolio_path, "r", encoding="utf-8") as f:
            portfolio = json.load(f)

        # Enrich with current prices from stock data
        today = datetime.now().strftime("%Y-%m-%d")
        for pos in portfolio:
            buy_date = pos.get("buy_date", "")
            if buy_date:
                try:
                    bd = datetime.strptime(buy_date, "%Y-%m-%d")
                    delta = (datetime.now() - bd).days
                    pos["holding_days"] = delta
                except ValueError:
                    pos["holding_days"] = None

            # Calculate PnL
            buy_price = safe_float(pos.get("buy_price"))
            current_price = safe_float(pos.get("current_price"))
            quantity = safe_float(pos.get("quantity"))
            if buy_price and current_price:
                pos["pnl_pct"] = round((current_price / buy_price - 1) * 100, 2)
                if quantity:
                    pos["pnl_value"] = round((current_price - buy_price) * quantity)

            # TP/SL status
            tp = safe_float(pos.get("tp"))
            sl = safe_float(pos.get("sl"))
            if current_price and tp:
                pos["tp_distance_pct"] = round((tp / current_price - 1) * 100, 2)
            if current_price and sl:
                pos["sl_distance_pct"] = round((sl / current_price - 1) * 100, 2)

        log.info(f"  {len(portfolio)} positions loaded")
        return portfolio
    except Exception as e:
        log.warning(f"  Error loading portfolio: {e}")
        return []


# ============================================================================
# MAIN
# ============================================================================

def main():
    log.info("=" * 60)
    log.info("EXTRA DATA COLLECTION STARTED")
    log.info("=" * 60)

    result = {}

    # Commodities
    result["commodities"] = collect_commodities()

    # Exchange rates (Vietcombank)
    result["exchange_rates"] = collect_exchange_rates()

    # FX historical
    result["fx"] = collect_fx()

    # Gold VN
    result["gold"] = collect_gold()

    # Bonds
    result["bonds"] = collect_bonds()

    # Funds
    result["funds"] = collect_funds()

    # Portfolio
    result["portfolio"] = load_portfolio()

    # Save
    output_path = CACHE_DIR / "extra_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    log.info(f"Extra data saved: {output_path}")
    log.info("=" * 60)
    log.info("EXTRA DATA COLLECTION COMPLETED!")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
