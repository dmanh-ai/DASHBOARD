#!/usr/bin/env python3
"""
Export index OHLCV history from Market HOSE monthly sqlite DB into UI GLM JS payload.

Input table: `index_ohlcv_daily` in `market_cache/hose_monthly/latest.sqlite`
Output: `UI GLM/index_ohlcv.js` (window.UI_GLM_INDEX_OHLCV)
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple


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


def _repo_root() -> Path:
    # UI GLM/tools/* -> repo_root
    return Path(__file__).resolve().parents[2]


def _default_db_path() -> Path:
    return _repo_root() / "market_cache" / "hose_monthly" / "latest.sqlite"


def _default_out_path() -> Path:
    return _repo_root() / "UI GLM" / "index_ohlcv.js"


def export_index_ohlcv(db_path: Path, out_path: Path) -> Tuple[str, Dict[str, object]]:
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            """
            SELECT index_name, date, open, high, low, close, volume, source
            FROM index_ohlcv_daily
            ORDER BY index_name, date
            """
        ).fetchall()
        if not rows:
            raise RuntimeError("index_ohlcv_daily is empty (no rows). Run market/src/snapshot_index_ohlcv_db.py first.")

        meta_source = conn.execute(
            "SELECT value FROM meta WHERE key='index_ohlcv_source' LIMIT 1"
        ).fetchone()
        meta_updated = conn.execute(
            "SELECT value FROM meta WHERE key='index_ohlcv_updated_at' LIMIT 1"
        ).fetchone()

        asof = ""
        indices: Dict[str, Dict[str, object]] = {}

        for index_name, d, o, h, l, c, v, src in rows:
            idx_u = str(index_name or "").upper()
            key = INDEX_KEY_MAP.get(idx_u)
            if not key:
                continue

            asof = max(asof, str(d))
            idx_obj = indices.setdefault(
                key,
                {
                    "name": idx_u,
                    "method": str(src or "") or (str(meta_source[0]) if meta_source else ""),
                    "bars": [],
                },
            )
            idx_obj["bars"].append({"d": d, "o": o, "h": h, "l": l, "c": c, "v": v})

        payload: Dict[str, object] = {
            "asof": asof,
            "updated_at": str(meta_updated[0]) if meta_updated else "",
            "indices": indices,
        }

        out_path.parent.mkdir(parents=True, exist_ok=True)
        js = (
            "// AUTO-GENERATED from market_cache/hose_monthly/latest.sqlite:index_ohlcv_daily\n"
            "// Source: market/src/snapshot_index_ohlcv_db.py\n"
            f"window.UI_GLM_INDEX_OHLCV = {json.dumps(payload, ensure_ascii=False, separators=(',', ':'))};\n"
        )
        out_path.write_text(js, encoding="utf-8")
        return asof, payload
    finally:
        conn.close()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=str(_default_db_path()), help="Path to market sqlite DB (default: latest.sqlite)")
    p.add_argument("--out", default=str(_default_out_path()), help="Output JS path (default: UI GLM/index_ohlcv.js)")
    args = p.parse_args()

    asof, payload = export_index_ohlcv(Path(args.db), Path(args.out))
    print(f"✅ Exported {len(payload.get('indices', {}))} indices (asof={asof}) -> {args.out}")


if __name__ == "__main__":
    main()

