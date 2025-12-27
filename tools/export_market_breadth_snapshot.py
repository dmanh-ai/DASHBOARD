#!/usr/bin/env python3
"""
Export 1-day market breadth snapshot for UI GLM (static).

Source:
- market_cache/all_stocks_historical.pkl (stocks_data[*].latest.{returns,volume,time})
- market_cache/VNINDEX_ad_history.pkl (items: [{date, ad}, ...]) for McClellan oscillator

Output:
- UI GLM/market_breadth_snapshot.js => window.UI_GLM_MARKET_BREADTH_SNAPSHOT
"""

from __future__ import annotations

import json
import math
import os
import pickle
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ALL_STOCKS_PKL = REPO_ROOT / "market_cache" / "all_stocks_historical.pkl"
DEFAULT_AD_HISTORY_PKL = REPO_ROOT / "market_cache" / "VNINDEX_ad_history.pkl"
DEFAULT_OUT_JS = REPO_ROOT / "UI GLM" / "market_breadth_snapshot.js"


def _safe_float(v: Any) -> Optional[float]:
    try:
        x = float(v)
        if math.isfinite(x):
            return x
    except Exception:
        return None
    return None


def _safe_int(v: Any) -> Optional[int]:
    try:
        x = int(v)
        return x
    except Exception:
        return None


def _to_iso_date(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, str):
        # Accept "YYYY-MM-DD"
        try:
            datetime.strptime(v[:10], "%Y-%m-%d")
            return v[:10]
        except Exception:
            return None
    if isinstance(v, date) and not isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, datetime):
        return v.date().isoformat()
    # pandas Timestamp prints as datetime-like and supports .to_pydatetime()
    try:
        if hasattr(v, "to_pydatetime"):
            dt = v.to_pydatetime()
            if isinstance(dt, datetime):
                return dt.date().isoformat()
    except Exception:
        pass
    return None


def _ema(values: List[float], period: int) -> List[float]:
    if not values:
        return []
    alpha = 2.0 / (period + 1.0)
    out: List[float] = []
    prev = values[0]
    out.append(prev)
    for x in values[1:]:
        prev = alpha * x + (1.0 - alpha) * prev
        out.append(prev)
    return out


def _compute_mcclellan_from_ad_history(ad_items: List[Dict[str, Any]]) -> Tuple[Optional[float], str, Optional[str]]:
    vals: List[float] = []
    last_date: Optional[str] = None
    for it in ad_items or []:
        ad = _safe_float(it.get("ad"))
        if ad is None:
            continue
        vals.append(ad)
        last_date = _to_iso_date(it.get("date")) or last_date

    if not vals:
        return None, "N/A", last_date

    ema19 = _ema(vals, 19)
    ema39 = _ema(vals, 39)
    mcc = ema19[-1] - ema39[-1]
    return float(mcc), "EMA(19)-EMA(39)", last_date


def load_all_stocks_snapshot(path: Path) -> Dict[str, Any]:
    with open(path, "rb") as f:
        obj = pickle.load(f)
    if not isinstance(obj, dict) or "stocks_data" not in obj:
        raise RuntimeError("Unexpected all_stocks_historical.pkl format")
    return obj


def compute_market_breadth_from_stocks(stocks_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    adv = dec = unchanged = 0
    adv_vol = dec_vol = 0.0
    total_vol = 0.0
    asof: Optional[str] = None

    for sym, payload in (stocks_data or {}).items():
        latest = payload.get("latest") if isinstance(payload, dict) else None
        if not isinstance(latest, dict):
            continue

        r = _safe_float(latest.get("returns"))
        v = _safe_float(latest.get("volume")) or 0.0
        t = _to_iso_date(latest.get("time"))
        if t:
            asof = t

        if r is None:
            continue

        total_vol += v
        if r > 0:
            adv += 1
            adv_vol += v
        elif r < 0:
            dec += 1
            dec_vol += v
        else:
            unchanged += 1

    total = adv + dec + unchanged
    vol_ratio = (adv_vol / dec_vol) if dec_vol > 0 else 1.0
    trin: Optional[float] = None
    if adv > 0 and dec > 0 and adv_vol > 0 and dec_vol > 0:
        trin = (adv / dec) / (adv_vol / dec_vol)

    return (
        {
            "total_stocks": total,
            "advancing": adv,
            "declining": dec,
            "unchanged": unchanged,
            "advance_volume": adv_vol,
            "decline_volume": dec_vol,
            "total_volume": total_vol,
            "trin": trin,
            "volume_ratio": vol_ratio,
        },
        asof,
    )


def main() -> None:
    all_stocks_path = Path(os.environ.get("UI_GLM_ALL_STOCKS_PKL", str(DEFAULT_ALL_STOCKS_PKL)))
    ad_history_path = Path(os.environ.get("UI_GLM_AD_HISTORY_PKL", str(DEFAULT_AD_HISTORY_PKL)))
    out_js = Path(os.environ.get("UI_GLM_BREADTH_OUT_JS", str(DEFAULT_OUT_JS)))

    if not all_stocks_path.exists():
        raise SystemExit(f"Missing source: {all_stocks_path}")

    all_obj = load_all_stocks_snapshot(all_stocks_path)
    stocks_data = all_obj.get("stocks_data") or {}
    if not isinstance(stocks_data, dict):
        raise SystemExit("Invalid stocks_data in all_stocks_historical.pkl")

    breadth, asof = compute_market_breadth_from_stocks(stocks_data)

    mcc_value: Optional[float] = None
    mcc_type = "N/A"
    mcc_asof: Optional[str] = None
    if ad_history_path.exists():
        try:
            ad_obj = pickle.load(open(ad_history_path, "rb"))
            items = ad_obj.get("items") if isinstance(ad_obj, dict) else None
            if isinstance(items, list):
                mcc_value, mcc_type, mcc_asof = _compute_mcclellan_from_ad_history(items)
        except Exception:
            mcc_value = None

    # Ensure numeric McClellan to avoid N/A: fallback to net A-D (still data-derived).
    if mcc_value is None:
        mcc_value = float((breadth.get("advancing") or 0) - (breadth.get("declining") or 0))
        mcc_type = "Net A-D (fallback)"
        mcc_asof = asof

    payload = {
        "asof": asof or mcc_asof or "",
        "universe": "HOSE (stocks_data)",
        "advancing": breadth["advancing"],
        "declining": breadth["declining"],
        "unchanged": breadth["unchanged"],
        "total_stocks": breadth["total_stocks"],
        "advance_volume": breadth["advance_volume"],
        "decline_volume": breadth["decline_volume"],
        "total_volume": breadth["total_volume"],
        "trin": breadth["trin"],
        "volume_ratio": breadth["volume_ratio"],
        "mcclellan": mcc_value,
        "mcclellan_type": mcc_type,
    }

    out_js.parent.mkdir(parents=True, exist_ok=True)
    out_js.write_text(
        "// AUTO-GENERATED from market_cache/all_stocks_historical.pkl (+ VNINDEX_ad_history.pkl)\n"
        "// Market breadth snapshot (1 day) for DASHBOARD_V3.html\n"
        f"window.UI_GLM_MARKET_BREADTH_SNAPSHOT = {json.dumps(payload, ensure_ascii=False)};\n",
        encoding="utf-8",
    )

    print(f"Wrote: {out_js}")


if __name__ == '__main__':
    main()

