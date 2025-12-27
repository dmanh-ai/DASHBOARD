#!/usr/bin/env python3
"""
Export breadth history (multi-day) for UI GLM static dashboard.

Sources:
- market_cache/historical_breadth.pkl  -> breadth_history (int-indexed) with pct_above_ma* + A/D counts
- market_cache/all_stocks_historical.pkl -> use AAA.data['time'] to map int index -> ISO date
- UI GLM/index_heatmap_data.js -> infer report as-of date to align UI (optional)

Output:
- UI GLM/breadth_history.js -> window.UI_GLM_BREADTH_HISTORY
"""

from __future__ import annotations

import json
import math
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HIST_BREADTH_PKL = REPO_ROOT / "market_cache" / "historical_breadth.pkl"
DEFAULT_ALL_STOCKS_PKL = REPO_ROOT / "market_cache" / "all_stocks_historical.pkl"
DEFAULT_INDEX_HEATMAP_JS = REPO_ROOT / "UI GLM" / "index_heatmap_data.js"
DEFAULT_OUT_JS = REPO_ROOT / "UI GLM" / "breadth_history.js"


def _to_iso_date(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, str):
        if len(v) >= 10 and v[4] == "-" and v[7] == "-":
            return v[:10]
        return None
    # pandas Timestamp
    try:
        if hasattr(v, "to_pydatetime"):
            dt = v.to_pydatetime()
            return dt.date().isoformat()
    except Exception:
        pass
    try:
        # datetime/date
        return v.date().isoformat()
    except Exception:
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


def _infer_asof_from_index_heatmaps(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    s = path.read_text(encoding="utf-8", errors="ignore")
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


def _percentile(values: List[float], x: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    # percent of values <= x
    le = 0
    for v in sorted_vals:
        if v <= x:
            le += 1
        else:
            break
    return 100.0 * le / len(sorted_vals)


def _pick_symbol_time_index(all_stocks_obj: Dict[str, Any], symbol: str = "AAA") -> List[str]:
    stocks_data = all_stocks_obj.get("stocks_data") or {}
    payload = stocks_data.get(symbol)
    if not isinstance(payload, dict):
        raise RuntimeError(f"Missing symbol {symbol} in all_stocks_historical.pkl")
    df = payload.get("data")
    if df is None:
        raise RuntimeError(f"Missing .data for {symbol}")
    try:
        times = df["time"].tolist()
    except Exception as e:
        raise RuntimeError(f"Unexpected data format for {symbol}: {e}")
    out: List[str] = []
    for t in times:
        d = _to_iso_date(t)
        out.append(d or "")
    return out


def main() -> None:
    hist_path = Path(os.environ.get("UI_GLM_HIST_BREADTH_PKL", str(DEFAULT_HIST_BREADTH_PKL)))
    all_stocks_path = Path(os.environ.get("UI_GLM_ALL_STOCKS_PKL", str(DEFAULT_ALL_STOCKS_PKL)))
    heatmap_js_path = Path(os.environ.get("UI_GLM_INDEX_HEATMAP_JS", str(DEFAULT_INDEX_HEATMAP_JS)))
    out_js = Path(os.environ.get("UI_GLM_BREADTH_HISTORY_OUT_JS", str(DEFAULT_OUT_JS)))

    if not hist_path.exists():
        raise SystemExit(f"Missing source: {hist_path}")
    if not all_stocks_path.exists():
        raise SystemExit(f"Missing source: {all_stocks_path}")

    hist_obj = pickle.load(open(hist_path, "rb"))
    breadth_history = hist_obj.get("breadth_history") if isinstance(hist_obj, dict) else None
    if not isinstance(breadth_history, dict):
        raise SystemExit("Invalid historical_breadth.pkl: breadth_history missing")

    all_obj = pickle.load(open(all_stocks_path, "rb"))
    if not isinstance(all_obj, dict):
        raise SystemExit("Invalid all_stocks_historical.pkl")
    time_index = _pick_symbol_time_index(all_obj, "AAA")

    # Determine as-of date aligned with report (optional).
    asof = os.environ.get("UI_GLM_ASOF") or _infer_asof_from_index_heatmaps(heatmap_js_path)

    # Build sorted series and map integer index -> date.
    keys = sorted(k for k in breadth_history.keys() if isinstance(k, int))
    series: List[Dict[str, Any]] = []
    for k in keys:
        if k < 0 or k >= len(time_index):
            continue
        d = time_index[k]
        if not d:
            continue
        if asof and d > asof:
            continue
        v = breadth_history.get(k) or {}
        if not isinstance(v, dict):
            continue
        rec = {
            "d": d,
            "adv": int(v.get("advancing", 0) or 0),
            "dec": int(v.get("declining", 0) or 0),
            "unch": int(v.get("unchanged", 0) or 0),
            "total": int(v.get("total_stocks", 0) or 0),
            "pct_ma5": float(v.get("pct_above_ma5", 0.0) or 0.0),
            "pct_ma10": float(v.get("pct_above_ma10", 0.0) or 0.0),
            "pct_ma20": float(v.get("pct_above_ma20", 0.0) or 0.0),
            "pct_ma50": float(v.get("pct_above_ma50", 0.0) or 0.0),
            "pct_ma100": float(v.get("pct_above_ma100", 0.0) or 0.0),
            "pct_ma200": float(v.get("pct_above_ma200", 0.0) or 0.0),
            "adv_pct": float(v.get("advance_percent", 0.0) or 0.0),
            "dec_pct": float(v.get("decline_percent", 0.0) or 0.0),
        }
        series.append(rec)

    if len(series) < 30:
        raise SystemExit(f"Not enough breadth history records: {len(series)}")

    # Compute derived series: net A-D, A-D line, McClellan.
    net = [float(r["adv"] - r["dec"]) for r in series]
    ad_line = []
    s = 0.0
    for x in net:
        s += x
        ad_line.append(s)

    ema19 = _ema(net, 19)
    ema39 = _ema(net, 39)
    mcc = [float(ema19[i] - ema39[i]) for i in range(len(series))]

    for i, r in enumerate(series):
        r["net_ad"] = float(net[i])
        r["ad_line"] = float(ad_line[i])
        r["mcc"] = float(mcc[i])

    # Summary anchored at latest record.
    last = series[-1]
    ma20_vals = [float(r["pct_ma20"]) for r in series if isinstance(r.get("pct_ma20"), (int, float))]
    pct_rank = _percentile(ma20_vals, float(last["pct_ma20"]))

    def _delta(idx_back: int) -> Optional[float]:
        if len(series) <= idx_back:
            return None
        return float(last["pct_ma20"]) - float(series[-1 - idx_back]["pct_ma20"])

    vs_1w = _delta(5)
    vs_1m = _delta(20)

    payload = {
        "asof": last["d"],
        "days": len(series),
        "series": series,
        "summary": {
            "pct_ma20": float(last["pct_ma20"]),
            "percentile_ma20": float(pct_rank),
            "vs_1w": vs_1w,
            "vs_1m": vs_1m,
            "current": {
                "pct_ma5": float(last["pct_ma5"]),
                "pct_ma20": float(last["pct_ma20"]),
                "pct_ma50": float(last["pct_ma50"]),
                "pct_ma200": float(last["pct_ma200"]),
            },
        },
        "notes": {
            "index_mapping": "breadth_history keys map to AAA.data row index (time).",
            "mcclellan": "Computed from net A-D: EMA19 - EMA39.",
        },
    }

    out_js.parent.mkdir(parents=True, exist_ok=True)
    out_js.write_text(
        "// AUTO-GENERATED from market_cache/historical_breadth.pkl (+ all_stocks_historical.pkl)\n"
        "// Breadth history for DASHBOARD_V3.html\n"
        f"window.UI_GLM_BREADTH_HISTORY = {json.dumps(payload, ensure_ascii=False)};\n",
        encoding="utf-8",
    )
    print(f"Wrote: {out_js} (days={payload['days']}, asof={payload['asof']})")


if __name__ == "__main__":
    main()

