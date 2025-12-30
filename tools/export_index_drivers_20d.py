#!/usr/bin/env python3
"""
Export "index drivers" (top kéo lên/kéo xuống + concentration_top10_pct) for UI GLM.

This deliberately does NOT parse Word reports. It reads the same canonical caches that
market uses (pickles + monthly DB), so UI GLM stays stable even when Word wording changes.

Sources:
- market_cache/all_stocks_historical.pkl (stocks_data[*].data: time/close)
- market_cache/hose_monthly/latest.sqlite (constituents + companies weights)

Output:
- UI GLM/index_drivers_20d.js -> window.UI_GLM_INDEX_DRIVERS_20D
"""

from __future__ import annotations

import json
import os
import pickle
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ALL_STOCKS_PKL = REPO_ROOT / "market_cache" / "all_stocks_historical.pkl"
DEFAULT_MONTHLY_DB = REPO_ROOT / "market_cache" / "hose_monthly" / "latest.sqlite"
DEFAULT_OUT_JS = REPO_ROOT / "UI GLM" / "index_drivers_20d.js"


INDEX_KEY_MAP: Dict[str, str] = {
    "VNINDEX": "vnindex",
    "VN30": "vn30",
    "VN100": "vn100",
    "VNMIDCAP": "vnmidcap",
    "VNSML": "vnsml",
    "VNDIAMOND": "vndiamond",
    "VNFINSELECT": "vnfinselect",
    "VNREAL": "vnreal",
    "VNMAT": "vnmat",
    "VNIT": "vnit",
    "VNHEAL": "vnheal",
    "VNFIN": "vnfin",
    "VNENE": "vnene",
    "VNCONS": "vncons",
    "VNCOND": "vncond",
}


def _open_ro_sqlite(path: Path) -> sqlite3.Connection:
    uri = f"file:{path.as_posix()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _canonicalize_index_for_db(index_name: str) -> str:
    n = (index_name or "").strip().upper()
    if n in {"VNINDEX", "VN-INDEX"}:
        return "HOSE"
    if n == "VNMIDCAP":
        return "VNMID"
    return n


def _load_constituents(db_path: Path, index_name: str) -> List[str]:
    idx = _canonicalize_index_for_db(index_name)
    conn = _open_ro_sqlite(db_path)
    try:
        rows = conn.execute(
            "SELECT code FROM constituents WHERE index_name = ? ORDER BY code",
            (idx,),
        ).fetchall()
    finally:
        conn.close()
    return [str(r[0]).strip().upper() for r in rows if r and r[0]]


def main() -> None:
    all_stocks_path = Path(os.environ.get("UI_GLM_ALL_STOCKS_PKL", str(DEFAULT_ALL_STOCKS_PKL)))
    monthly_db_path = Path(os.environ.get("UI_GLM_MONTHLY_DB", str(DEFAULT_MONTHLY_DB)))
    out_js = Path(os.environ.get("UI_GLM_INDEX_DRIVERS_OUT_JS", str(DEFAULT_OUT_JS)))

    if not all_stocks_path.exists():
        raise SystemExit(f"Missing source: {all_stocks_path}")
    if not monthly_db_path.exists():
        raise SystemExit(f"Missing source: {monthly_db_path}")

    # Import compute logic from market/src, so UI and market stay consistent.
    market_src = REPO_ROOT / "market" / "src"
    sys.path.insert(0, str(market_src))
    from index_drivers import compute_index_drivers_20d  # type: ignore

    obj = pickle.load(open(all_stocks_path, "rb"))
    stocks_data = obj.get("stocks_data") if isinstance(obj, dict) else None
    if not isinstance(stocks_data, dict):
        raise SystemExit("Invalid all_stocks_historical.pkl: stocks_data missing")

    indices_out: Dict[str, Any] = {}
    asof_max = ""
    errors: Dict[str, str] = {}

    for idx_u, key in INDEX_KEY_MAP.items():
        try:
            codes = _load_constituents(monthly_db_path, idx_u)
            # If monthly DB has no rows for this index, fall back to all stocks only for VNINDEX.
            if not codes and idx_u == "VNINDEX":
                subset = stocks_data
            else:
                subset = {c: stocks_data[c] for c in codes if c in stocks_data}

            top_n = 10 if idx_u in {"VNINDEX", "VN100"} else 5
            res = compute_index_drivers_20d(
                idx_u,
                subset,
                days=20,
                top_n=top_n,
                monthly_db_path=monthly_db_path,
            )
            if not res:
                raise RuntimeError("No drivers computed (insufficient coverage/data)")

            current = json.loads(res["drivers_current"])
            by_day = json.loads(res["drivers_by_day_20d"])
            asof = str(current.get("date") or "")
            if asof:
                asof_max = max(asof_max, asof)

            indices_out[key] = {
                "name": idx_u,
                "asof": asof,
                "top_n": top_n,
                "current": current,
                "by_day_20d": by_day,
                "definition": res.get("drivers_definition") or "",
            }
        except Exception as e:
            errors[idx_u] = str(e)
            indices_out[key] = {
                "name": idx_u,
                "asof": "",
                "top_n": (10 if idx_u in {"VNINDEX", "VN100"} else 5),
                "current": None,
                "by_day_20d": [],
                "definition": "",
                "error": str(e),
            }

    payload: Dict[str, Any] = {
        "asof": asof_max,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "indices": indices_out,
        "errors": errors,
        "notes": {
            "ranking": "top_up/top_down are ranked by contribution_pct (weight_pct * return_pct).",
            "concentration": "concentration_top10_pct = top10(|contribution|) / sum(|contribution|).",
            "source": "Computed from all_stocks_historical.pkl + hose_monthly latest.sqlite (companies weights).",
        },
    }

    out_js.parent.mkdir(parents=True, exist_ok=True)
    out_js.write_text(
        "// AUTO-GENERATED from market_cache/all_stocks_historical.pkl + market_cache/hose_monthly/latest.sqlite\n"
        "// Index drivers (20D) for UI GLM\n"
        f"window.UI_GLM_INDEX_DRIVERS_20D = {json.dumps(payload, ensure_ascii=False, separators=(',', ':'))};\n",
        encoding="utf-8",
    )
    print(f"Wrote: {out_js} (asof={payload['asof']})")


if __name__ == "__main__":
    main()

