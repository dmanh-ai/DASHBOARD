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
DEFAULT_INDEX_HEATMAP_JS = REPO_ROOT / "UI GLM" / "index_heatmap_data.js"
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


def _compute_mcclellan_series_from_ad_history(ad_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cleaned: List[Tuple[str, float]] = []
    for it in ad_items or []:
        d = _to_iso_date(it.get("date"))
        v = _safe_float(it.get("ad"))
        if not d or v is None:
            continue
        cleaned.append((d, v))

    if not cleaned:
        return []

    dates = [d for d, _ in cleaned]
    vals = [v for _, v in cleaned]
    ema19 = _ema(vals, 19)
    ema39 = _ema(vals, 39)
    out = []
    for i in range(len(cleaned)):
        out.append({"date": dates[i], "mcclellan": float(ema19[i] - ema39[i])})
    return out


def _pick_series_value_for_date(series: List[Dict[str, Any]], target: str) -> Optional[float]:
    if not series:
        return None
    # exact match first
    for it in series:
        if it.get("date") == target:
            return _safe_float(it.get("mcclellan"))
    # otherwise nearest previous
    prev = None
    for it in series:
        d = it.get("date")
        if not isinstance(d, str):
            continue
        if d <= target:
            prev = _safe_float(it.get("mcclellan"))
    return prev


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


def _infer_asof_from_index_heatmaps(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    s = path.read_text(encoding="utf-8", errors="ignore")
    # file format: window.UI_GLM_INDEX_HEATMAPS = {...};
    i = s.find("{")
    j = s.rfind("}")
    if i < 0 or j < 0 or j <= i:
        return None
    try:
        obj = json.loads(s[i : j + 1])
        asof = obj.get("asof")
        if isinstance(asof, str) and len(asof) >= 10:
            return asof[:10]
    except Exception:
        return None
    return None


def compute_market_breadth_from_stocks_for_date(
    stocks_data: Dict[str, Any], asof: str
) -> Dict[str, Any]:
    adv = dec = unchanged = 0
    adv_vol = dec_vol = total_vol = 0.0
    used = 0

    for _, payload in (stocks_data or {}).items():
        if not isinstance(payload, dict):
            continue
        df = payload.get("data")
        if df is None:
            continue
        try:
            # df is a pandas DataFrame with a 'time' column
            row = df.loc[df["time"].astype(str).str.startswith(asof)].tail(1)
            if row is None or row.empty:
                continue
            r = _safe_float(row["returns"].iloc[0])
            v = _safe_float(row["volume"].iloc[0]) or 0.0
            if r is None:
                continue
            used += 1
            total_vol += v
            if r > 0:
                adv += 1
                adv_vol += v
            elif r < 0:
                dec += 1
                dec_vol += v
            else:
                unchanged += 1
        except Exception:
            continue

    total = adv + dec + unchanged
    vol_ratio = (adv_vol / dec_vol) if dec_vol > 0 else 1.0
    trin = None
    if adv > 0 and dec > 0 and adv_vol > 0 and dec_vol > 0:
        trin = (adv / dec) / (adv_vol / dec_vol)

    return {
        "asof": asof,
        "total_stocks": total,
        "advancing": adv,
        "declining": dec,
        "unchanged": unchanged,
        "advance_volume": adv_vol,
        "decline_volume": dec_vol,
        "total_volume": total_vol,
        "trin": trin,
        "volume_ratio": vol_ratio,
        "coverage": used,
    }


def main() -> None:
    all_stocks_path = Path(os.environ.get("UI_GLM_ALL_STOCKS_PKL", str(DEFAULT_ALL_STOCKS_PKL)))
    ad_history_path = Path(os.environ.get("UI_GLM_AD_HISTORY_PKL", str(DEFAULT_AD_HISTORY_PKL)))
    heatmap_js_path = Path(os.environ.get("UI_GLM_INDEX_HEATMAP_JS", str(DEFAULT_INDEX_HEATMAP_JS)))
    out_js = Path(os.environ.get("UI_GLM_BREADTH_OUT_JS", str(DEFAULT_OUT_JS)))

    if not all_stocks_path.exists():
        raise SystemExit(f"Missing source: {all_stocks_path}")

    all_obj = load_all_stocks_snapshot(all_stocks_path)
    stocks_data = all_obj.get("stocks_data") or {}
    if not isinstance(stocks_data, dict):
        raise SystemExit("Invalid stocks_data in all_stocks_historical.pkl")

    target_asof = os.environ.get("UI_GLM_ASOF") or _infer_asof_from_index_heatmaps(heatmap_js_path)
    if target_asof:
        breadth = compute_market_breadth_from_stocks_for_date(stocks_data, target_asof)
        asof = target_asof
    else:
        breadth, asof = compute_market_breadth_from_stocks(stocks_data)

    mcc_value: Optional[float] = None
    mcc_type = "N/A"
    mcc_asof: Optional[str] = None
    if ad_history_path.exists():
        try:
            ad_obj = pickle.load(open(ad_history_path, "rb"))
            items = ad_obj.get("items") if isinstance(ad_obj, dict) else None
            if isinstance(items, list):
                series = _compute_mcclellan_series_from_ad_history(items)
                if asof:
                    mcc_value = _pick_series_value_for_date(series, asof)
                if mcc_value is None:
                    mcc_value, mcc_type, mcc_asof = _compute_mcclellan_from_ad_history(items)
                else:
                    mcc_type = "EMA(19)-EMA(39)"
                    mcc_asof = asof
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
        "advancing": breadth.get("advancing", 0),
        "declining": breadth.get("declining", 0),
        "unchanged": breadth.get("unchanged", 0),
        "total_stocks": breadth.get("total_stocks", 0),
        "advance_volume": breadth.get("advance_volume", 0.0),
        "decline_volume": breadth.get("decline_volume", 0.0),
        "total_volume": breadth.get("total_volume", 0.0),
        "trin": breadth.get("trin"),
        "volume_ratio": breadth.get("volume_ratio"),
        "coverage": breadth.get("coverage"),
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
