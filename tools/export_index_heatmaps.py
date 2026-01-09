#!/usr/bin/env python3
"""
Export stock heatmap snapshots used by UI GLM dashboards (V3/V3 Pro).

Outputs:
- UI GLM/index_heatmap_data.js   -> window.UI_GLM_INDEX_HEATMAPS
- UI GLM/vnindex_heatmap_data.js -> window.UI_GLM_VNINDEX_HEATMAP

Sources:
- market_cache/all_stocks_historical.pkl (per-symbol OHLCV + returns)
- market_cache/hose_monthly/latest.sqlite (index constituents)
- UI GLM/ui_glm_meta.json (optional: as-of pinning)

Notes:
- "VNINDEX heatmap" in the dashboard is actually a HOSE-wide heatmap (top gainers/losers),
  matching the original UI's semantics.
"""

from __future__ import annotations

import json
import math
import os
import pickle
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd  # type: ignore


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ALL_STOCKS_PKL = REPO_ROOT / "market_cache" / "all_stocks_historical.pkl"
DEFAULT_MONTHLY_DB = REPO_ROOT / "market_cache" / "hose_monthly" / "latest.sqlite"
DEFAULT_UI_META_JSON = REPO_ROOT / "UI GLM" / "ui_glm_meta.json"
DEFAULT_INDEX_HEATMAP_OUT_JS = REPO_ROOT / "UI GLM" / "index_heatmap_data.js"
DEFAULT_VNINDEX_HEATMAP_OUT_JS = REPO_ROOT / "UI GLM" / "vnindex_heatmap_data.js"


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
        return int(v)
    except Exception:
        return None


def _to_iso_date(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, str):
        s = v[:10]
        try:
            datetime.strptime(s, "%Y-%m-%d")
            return s
        except Exception:
            return None
    try:
        if hasattr(v, "to_pydatetime"):
            dt = v.to_pydatetime()
            if isinstance(dt, datetime):
                return dt.date().isoformat()
    except Exception:
        pass
    try:
        return v.date().isoformat()
    except Exception:
        return None


def _load_ui_meta_asof(meta_json: Path) -> Optional[str]:
    if not meta_json.exists():
        return None
    try:
        obj = json.loads(meta_json.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None
    asof = obj.get("asof_iso")
    if isinstance(asof, str) and len(asof) >= 10:
        return asof[:10]
    return None


def _infer_asof_from_all_stocks(all_obj: Dict[str, Any]) -> Optional[str]:
    # Prefer explicit field if present.
    d = _to_iso_date(all_obj.get("asof_date"))
    if d:
        return d

    stocks = all_obj.get("stocks_data")
    if not isinstance(stocks, dict) or not stocks:
        return None

    # Try a few common symbols first to avoid iterating the whole dict.
    for sym in ("VCB", "ACB", "AAA"):
        payload = stocks.get(sym)
        latest = payload.get("latest") if isinstance(payload, dict) else None
        d = _to_iso_date(latest.get("time")) if isinstance(latest, dict) else None
        if d:
            return d

    # Fallback: scan until we find one.
    for payload in stocks.values():
        latest = payload.get("latest") if isinstance(payload, dict) else None
        d = _to_iso_date(latest.get("time")) if isinstance(latest, dict) else None
        if d:
            return d
    return None


def _pick_row_asof(payload: Dict[str, Any], asof: str) -> Optional[Dict[str, Any]]:
    """
    Return last available row with time <= asof (best-effort).
    """
    df = payload.get("data")
    if isinstance(df, pd.DataFrame) and not df.empty and "time" in df.columns:
        try:
            t_asof = pd.Timestamp(asof)
            df2 = df.loc[df["time"] <= t_asof]
            if df2 is not None and not df2.empty:
                row = df2.tail(1).to_dict("records")[0]
                return dict(row) if isinstance(row, dict) else None
        except Exception:
            pass

    latest = payload.get("latest")
    if isinstance(latest, dict):
        return latest
    return None


def _build_point(symbol: str, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    close = _safe_float(row.get("close"))
    volume = _safe_float(row.get("volume"))
    if close is None or volume is None:
        return None

    r = _safe_float(row.get("returns"))
    if r is None:
        r = _safe_float(row.get("price_change"))
    if r is None:
        return None

    # UI expects change_pct as a % number (not ratio).
    change_pct = round(r * 100.0, 4)
    vol_i = int(round(volume))
    value = close * float(vol_i)

    return {
        "symbol": symbol,
        "price": round(close, 2),
        "volume": vol_i,
        "value": value,
        "change_pct": change_pct,
    }


def _load_constituents(monthly_db: Path) -> Dict[str, List[str]]:
    con = sqlite3.connect(str(monthly_db))
    try:
        rows = con.execute("SELECT index_name, code FROM constituents").fetchall()
    finally:
        con.close()

    out: Dict[str, List[str]] = {}
    for idx, code in rows:
        if not idx or not code:
            continue
        idx_name = str(idx).strip().upper()
        sym = str(code).strip().upper()
        if not idx_name or not sym:
            continue
        out.setdefault(idx_name, []).append(sym)
    # stable unique
    for k, v in list(out.items()):
        uniq = []
        seen = set()
        for s in v:
            if s in seen:
                continue
            seen.add(s)
            uniq.append(s)
        out[k] = uniq
    return out


def _compute_heatmap_for_symbols(
    symbols: Iterable[str],
    *,
    stocks_data: Dict[str, Any],
    asof: str,
    top_k: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int, int, int]:
    points: List[Dict[str, Any]] = []
    count_pos = 0
    count_neg = 0
    count_total = 0

    for sym in symbols:
        payload = stocks_data.get(sym)
        if not isinstance(payload, dict):
            continue
        row = _pick_row_asof(payload, asof)
        if not isinstance(row, dict):
            continue
        p = _build_point(sym, row)
        if not p:
            continue

        # Count includes only symbols we can compute.
        count_total += 1
        if p["change_pct"] > 0:
            count_pos += 1
        elif p["change_pct"] < 0:
            count_neg += 1

        points.append(p)

    gainers_all = [p for p in points if p.get("change_pct") is not None and float(p["change_pct"]) > 0]
    losers_all = [p for p in points if p.get("change_pct") is not None and float(p["change_pct"]) < 0]

    gainers_all.sort(key=lambda x: float(x["change_pct"]), reverse=True)
    losers_all.sort(key=lambda x: float(x["change_pct"]))

    gainers = gainers_all[: int(top_k)]
    losers = losers_all[: int(top_k)]
    return gainers, losers, count_total, count_pos, count_neg


def main() -> None:
    all_stocks_path = Path(os.environ.get("UI_GLM_ALL_STOCKS_PKL", str(DEFAULT_ALL_STOCKS_PKL)))
    monthly_db = Path(os.environ.get("UI_GLM_MONTHLY_DB", str(DEFAULT_MONTHLY_DB)))
    meta_json = Path(os.environ.get("UI_GLM_META_JSON", str(DEFAULT_UI_META_JSON)))

    out_index_js = Path(os.environ.get("UI_GLM_INDEX_HEATMAP_OUT_JS", str(DEFAULT_INDEX_HEATMAP_OUT_JS)))
    out_vnindex_js = Path(os.environ.get("UI_GLM_VNINDEX_HEATMAP_OUT_JS", str(DEFAULT_VNINDEX_HEATMAP_OUT_JS)))

    top_k = int((os.environ.get("UI_GLM_HEATMAP_TOP_K") or "30").strip() or "30")
    vnindex_universe = (os.environ.get("UI_GLM_VNINDEX_UNIVERSE") or "HOSE").strip().upper()

    if not all_stocks_path.exists():
        raise SystemExit(f"Missing source: {all_stocks_path}")
    if not monthly_db.exists():
        raise SystemExit(f"Missing source: {monthly_db}")

    all_obj = pickle.load(open(all_stocks_path, "rb"))
    if not isinstance(all_obj, dict):
        raise SystemExit("Invalid all_stocks_historical.pkl (not a dict)")
    stocks_data = all_obj.get("stocks_data") or {}
    if not isinstance(stocks_data, dict) or not stocks_data:
        raise SystemExit("Invalid all_stocks_historical.pkl: stocks_data missing/empty")

    asof = (os.environ.get("UI_GLM_ASOF") or "").strip()
    if not asof:
        asof = _load_ui_meta_asof(meta_json) or ""
    if not asof:
        asof = _infer_asof_from_all_stocks(all_obj) or ""
    if not asof:
        raise SystemExit("Cannot infer as-of date for heatmaps (set UI_GLM_ASOF)")

    constituents = _load_constituents(monthly_db)

    # 1) VNINDEX heatmap (HOSE-wide snapshot)
    vnindex_syms = constituents.get(vnindex_universe, [])
    gainers, losers, _, _, _ = _compute_heatmap_for_symbols(
        vnindex_syms,
        stocks_data=stocks_data,
        asof=asof,
        top_k=top_k,
    )
    out_vnindex_js.parent.mkdir(parents=True, exist_ok=True)
    out_vnindex_js.write_text(
        "// AUTO-GENERATED snapshot for UI GLM (VNINDEX constituents)\n"
        "// Used by `DASHBOARD_V3.html` to render VNINDEX gainers/losers heatmaps under `TỔNG QUAN THỊ TRƯỜNG`.\n"
        f"window.UI_GLM_VNINDEX_HEATMAP = {json.dumps({'date': asof, 'gainers': gainers, 'losers': losers}, ensure_ascii=False)};\n",
        encoding="utf-8",
    )

    # 2) Index heatmaps (per-index snapshot)
    indices_out: Dict[str, Any] = {}
    for idx_name, syms in constituents.items():
        if idx_name == vnindex_universe:
            continue
        g, l, cnt, cnt_pos, cnt_neg = _compute_heatmap_for_symbols(
            syms,
            stocks_data=stocks_data,
            asof=asof,
            top_k=top_k,
        )
        if cnt <= 0:
            continue
        indices_out[idx_name] = {
            "gainers": g,
            "losers": l,
            "count": cnt,
            "count_pos": cnt_pos,
            "count_neg": cnt_neg,
        }

    out_index_js.parent.mkdir(parents=True, exist_ok=True)
    out_index_js.write_text(
        "// AUTO-GENERATED from market_cache/hose_monthly/latest.sqlite + market_cache/all_stocks_historical.pkl\n"
        "// Heatmap snapshots (top gainers/losers) for indices used in DASHBOARD_V3.html\n"
        f"window.UI_GLM_INDEX_HEATMAPS = {json.dumps({'asof': asof, 'indices': indices_out}, ensure_ascii=False)};\n",
        encoding="utf-8",
    )

    print(f"Wrote: {out_vnindex_js}")
    print(f"Wrote: {out_index_js}")


if __name__ == "__main__":
    main()

