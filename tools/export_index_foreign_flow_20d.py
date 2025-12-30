#!/usr/bin/env python3
"""
Export "foreign investor flow" aggregates for UI GLM (20 trading sessions).

This deliberately does NOT parse Word reports. It reads the canonical VCI daily facts
database + monthly HOSE constituents database, so UI GLM stays stable even when Word
wording changes.

Sources:
- market_cache/vci_trading_daily/latest.sqlite (table: vci_trading_daily_facts)
- market_cache/hose_monthly/latest.sqlite (table: constituents)

Output:
- UI GLM/index_foreign_flow_20d.js -> window.UI_GLM_INDEX_FOREIGN_FLOW_20D
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VCI_DB = REPO_ROOT / "market_cache" / "vci_trading_daily" / "latest.sqlite"
DEFAULT_MONTHLY_DB = REPO_ROOT / "market_cache" / "hose_monthly" / "latest.sqlite"
DEFAULT_OUT_JS = REPO_ROOT / "UI GLM" / "index_foreign_flow_20d.js"


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


def _load_constituents(monthly_db_path: Path, index_name: str) -> List[str]:
    idx = _canonicalize_index_for_db(index_name)
    conn = _open_ro_sqlite(monthly_db_path)
    try:
        rows = conn.execute(
            "SELECT code FROM constituents WHERE index_name = ? ORDER BY code",
            (idx,),
        ).fetchall()
    finally:
        conn.close()
    return [str(r[0]).strip().upper() for r in rows if r and r[0]]


def _load_list_dates(monthly_db_path: Path, codes: List[str]) -> Dict[str, Optional[str]]:
    """
    Return {CODE -> list_date(YYYY-MM-DD) or None}.

    Notes:
    - monthly DB is a current snapshot; list_date is used only to avoid requiring facts
      for dates before a symbol was listed (strict mode).
    """
    codes_u = [str(c or "").strip().upper() for c in (codes or []) if str(c or "").strip()]
    if not codes_u:
        return {}

    conn = _open_ro_sqlite(monthly_db_path)
    try:
        placeholders = ",".join(["?"] * len(codes_u))
        rows = conn.execute(
            f"SELECT code, list_date FROM companies WHERE UPPER(code) IN ({placeholders})",
            tuple(codes_u),
        ).fetchall()
    finally:
        conn.close()

    out: Dict[str, Optional[str]] = {c: None for c in codes_u}
    for r in rows:
        code = str(r[0]).strip().upper() if r and r[0] else ""
        if not code:
            continue
        d = str(r[1])[:10] if r and r[1] else None
        out[code] = d or None
    return out


def _fetch_last_trading_dates(vci_db_path: Path, days: int, *, min_symbols_per_day: int) -> List[str]:
    """
    Pick the last N trading dates that have sufficient coverage in the VCI facts DB.

    Rationale:
    - The DB may be partially updated (e.g. only a few symbols have the latest date).
    - Using DISTINCT(trading_date) would incorrectly "advance" as-of even when coverage is tiny.
    """
    conn = _open_ro_sqlite(vci_db_path)
    try:
        rows = conn.execute(
            """
            SELECT trading_date
            FROM vci_trading_daily_facts
            WHERE UPPER(source) = UPPER('VCI') AND resolution = '1D'
            GROUP BY trading_date
            HAVING COUNT(DISTINCT symbol) >= ?
            ORDER BY trading_date DESC
            LIMIT ?
            """,
            (int(min_symbols_per_day), int(days)),
        ).fetchall()
    finally:
        conn.close()

    ds = [str(r[0])[:10] for r in rows if r and r[0]]
    ds = list(reversed(ds))
    if not ds:
        raise RuntimeError(
            f"No trading dates found with min_symbols_per_day={min_symbols_per_day} "
            f"in DB={vci_db_path}"
        )
    return ds


FactsRow = Dict[str, Optional[float]]


def _load_facts_for_dates(vci_db_path: Path, dates: List[str]) -> Dict[str, Dict[str, FactsRow]]:
    if not dates:
        return {}

    out: Dict[str, Dict[str, FactsRow]] = {d: {} for d in dates}
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from vci_shared_db import get_facts_by_date_symbol  # type: ignore

    facts_map = get_facts_by_date_symbol(
        dates,
        columns=[
            "fr_buy_value_total",
            "fr_sell_value_total",
            "fr_net_value_total",
            "fr_buy_volume_total",
            "fr_sell_volume_total",
            "fr_net_volume_total",
        ],
        db_path=vci_db_path,
        strict=True,
    )
    for d in dates:
        day = facts_map.get(d, {})
        for sym, payload in day.items():
            out[d][sym] = {
                "fr_buy_value_total": payload.get("fr_buy_value_total"),
                "fr_sell_value_total": payload.get("fr_sell_value_total"),
                "fr_net_value_total": payload.get("fr_net_value_total"),
                "fr_buy_volume_total": payload.get("fr_buy_volume_total"),
                "fr_sell_volume_total": payload.get("fr_sell_volume_total"),
                "fr_net_volume_total": payload.get("fr_net_volume_total"),
            }
    return out


def _sum_optional(values: List[Optional[float]]) -> float:
    s = 0.0
    for v in values:
        if v is None:
            continue
        try:
            s += float(v)
        except Exception:
            continue
    return float(s)


def _safe_float(v: Any) -> Optional[float]:
    try:
        x = float(v)
        return x
    except Exception:
        return None


def _compute_index_aggregates(
    index_name: str,
    codes: List[str],
    dates: List[str],
    facts: Dict[str, Dict[str, FactsRow]],
    list_dates: Dict[str, Optional[str]],
    top_n: int = 10,
    *,
    strict: bool,
    min_coverage_pct: float,
) -> Dict[str, Any]:
    available_any: set[str] = set()
    for d in dates:
        day_map = facts.get(d, {})
        if day_map:
            available_any.update(day_map.keys())

    by_day: List[Dict[str, Any]] = []
    for d in dates:
        day_map = facts.get(d, {})
        eligible = [c for c in codes if not list_dates.get(c) or str(list_dates.get(c)) <= d]
        universe_all = len(eligible)
        eligible_supported = [c for c in eligible if c in available_any]
        unsupported = [c for c in eligible if c not in available_any]

        universe = len(eligible_supported)
        present = [c for c in eligible_supported if c in day_map]
        coverage = len(present)
        coverage_pct = (100.0 * coverage / universe) if universe > 0 else 0.0
        missing = [c for c in eligible_supported if c not in day_map]

        if strict and missing:
            sample = ",".join(missing[:10])
            raise RuntimeError(
                f"Missing VCI facts for index={index_name} date={d}: missing={len(missing)}/{len(eligible_supported)} "
                f"(unsupported={len(unsupported)}/{universe_all}, sample={sample}{'...' if len(missing) > 10 else ''})."
            )

        buy_val = _sum_optional([day_map[c].get("fr_buy_value_total") for c in present])
        sell_val = _sum_optional([day_map[c].get("fr_sell_value_total") for c in present])
        net_val = _sum_optional([day_map[c].get("fr_net_value_total") for c in present])
        buy_vol = _sum_optional([day_map[c].get("fr_buy_volume_total") for c in present])
        sell_vol = _sum_optional([day_map[c].get("fr_sell_volume_total") for c in present])
        net_vol = _sum_optional([day_map[c].get("fr_net_volume_total") for c in present])

        by_day.append(
            {
                "date": d,
                "universe": universe,
                "coverage": coverage,
                "coverage_pct": coverage_pct,
                "unsupported": len(unsupported),
                "missing": len(missing),
                "fr_buy_value_total": buy_val,
                "fr_sell_value_total": sell_val,
                "fr_net_value_total": net_val,
                "fr_buy_volume_total": buy_vol,
                "fr_sell_volume_total": sell_vol,
                "fr_net_volume_total": net_vol,
            }
        )

    current_date = dates[-1] if dates else ""
    # Choose an "effective asof" date: latest day with acceptable coverage.
    # If none, fall back to the latest date we have (still export, but dashboard can show low coverage).
    effective_idx = None
    for i in range(len(by_day) - 1, -1, -1):
        try:
            pct = float(by_day[i].get("coverage_pct") or 0.0)
        except Exception:
            pct = 0.0
        if pct >= float(min_coverage_pct):
            effective_idx = i
            break

    current = by_day[effective_idx] if (by_day and effective_idx is not None) else (by_day[-1] if by_day else None)
    current_date = str(current.get("date")) if isinstance(current, dict) and current.get("date") else current_date

    top_buy: List[Dict[str, Any]] = []
    top_sell: List[Dict[str, Any]] = []
    if current_date:
        day_map = facts.get(current_date, {})
        rows: List[Tuple[str, float, float, float, float, float, float]] = []
        eligible = [c for c in codes if not list_dates.get(c) or str(list_dates.get(c)) <= current_date]
        eligible = [c for c in eligible if c in day_map]
        for c in eligible:
            r = day_map.get(c)
            if not r:
                continue
            buy_v = _safe_float(r.get("fr_buy_value_total")) or 0.0
            sell_v = _safe_float(r.get("fr_sell_value_total")) or 0.0
            net_v = _safe_float(r.get("fr_net_value_total"))
            if net_v is None:
                net_v = buy_v - sell_v
            buy_q = _safe_float(r.get("fr_buy_volume_total")) or 0.0
            sell_q = _safe_float(r.get("fr_sell_volume_total")) or 0.0
            net_q = _safe_float(r.get("fr_net_volume_total"))
            if net_q is None:
                net_q = buy_q - sell_q
            rows.append((c, float(net_v), float(buy_v), float(sell_v), float(net_q), float(buy_q), float(sell_q)))

        rows_sorted = sorted(rows, key=lambda x: x[1], reverse=True)
        top_buy_rows = [r for r in rows_sorted if r[1] > 0][: int(top_n)]
        top_sell_rows = [r for r in reversed(rows_sorted) if r[1] < 0][: int(top_n)]

        top_buy = [
            {
                "symbol": sym,
                "fr_net_value_total": net_v,
                "fr_buy_value_total": buy_v,
                "fr_sell_value_total": sell_v,
                "fr_net_volume_total": net_q,
                "fr_buy_volume_total": buy_q,
                "fr_sell_volume_total": sell_q,
            }
            for sym, net_v, buy_v, sell_v, net_q, buy_q, sell_q in top_buy_rows
        ]
        top_sell = [
            {
                "symbol": sym,
                "fr_net_value_total": net_v,
                "fr_buy_value_total": buy_v,
                "fr_sell_value_total": sell_v,
                "fr_net_volume_total": net_q,
                "fr_buy_volume_total": buy_q,
                "fr_sell_volume_total": sell_q,
            }
            for sym, net_v, buy_v, sell_v, net_q, buy_q, sell_q in top_sell_rows
        ]

    return {
        "name": index_name,
        "asof": current_date,
        "days": len(dates),
        "current": current,
        "by_day_20d": by_day,
        "top_n": int(top_n),
        "top_net_buy": top_buy,
        "top_net_sell": top_sell,
    }


def main() -> None:
    vci_db_path = Path(os.environ.get("UI_GLM_VCI_DAILY_DB", str(DEFAULT_VCI_DB)))
    monthly_db_path = Path(os.environ.get("UI_GLM_MONTHLY_DB", str(DEFAULT_MONTHLY_DB)))
    out_js = Path(os.environ.get("UI_GLM_INDEX_FOREIGN_FLOW_OUT_JS", str(DEFAULT_OUT_JS)))
    days = int(os.environ.get("UI_GLM_INDEX_FOREIGN_FLOW_DAYS", "20"))
    strict = (os.environ.get("UI_GLM_INDEX_FOREIGN_FLOW_STRICT", "0").strip().lower() in {"1", "true", "yes", "on"})
    min_symbols_per_day = int(os.environ.get("UI_GLM_VCI_MIN_SYMBOLS_PER_DAY", "250"))
    min_coverage_pct = float(os.environ.get("UI_GLM_INDEX_FOREIGN_FLOW_MIN_COVERAGE_PCT", "98"))

    if not vci_db_path.exists():
        raise SystemExit(f"Missing source: {vci_db_path}")
    if not monthly_db_path.exists():
        raise SystemExit(f"Missing source: {monthly_db_path}")

    dates = _fetch_last_trading_dates(vci_db_path, days=days, min_symbols_per_day=min_symbols_per_day)
    facts = _load_facts_for_dates(vci_db_path, dates)
    indices_out: Dict[str, Any] = {}
    for idx_u, key in INDEX_KEY_MAP.items():
        codes = _load_constituents(monthly_db_path, idx_u)
        if not codes:
            raise RuntimeError(f"No constituents found in monthly DB for index={idx_u}")

        list_dates = _load_list_dates(monthly_db_path, codes)
        indices_out[key] = _compute_index_aggregates(
            idx_u,
            codes=codes,
            dates=dates,
            facts=facts,
            list_dates=list_dates,
            top_n=10,
            strict=strict,
            min_coverage_pct=min_coverage_pct,
        )

    asof = indices_out.get("vnindex", {}).get("asof") or dates[-1]
    payload: Dict[str, Any] = {
        "asof": asof,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "days": len(dates),
        "indices": indices_out,
        "notes": {
            "fields": {
                "fr_buy_value_total": "Tổng giá trị mua của NĐT nước ngoài (mua khớp + mua thỏa thuận).",
                "fr_sell_value_total": "Tổng giá trị bán của NĐT nước ngoài (bán khớp + bán thỏa thuận).",
                "fr_net_value_total": "Mua ròng theo giá trị (= mua_total - bán_total).",
                "fr_buy_volume_total": "Tổng khối lượng mua của NĐT nước ngoài.",
                "fr_sell_volume_total": "Tổng khối lượng bán của NĐT nước ngoài.",
                "fr_net_volume_total": "Mua ròng theo khối lượng (= mua_total - bán_total).",
            },
            "aggregation": (
                "Index aggregates are sum over available constituents from HOSE monthly DB. "
                f"strict={bool(strict)}; min_symbols_per_day={int(min_symbols_per_day)}; "
                f"min_coverage_pct={float(min_coverage_pct)}. "
                "Fields universe/coverage/coverage_pct/unsupported/missing are included per day."
            ),
            "top10": "Top lists are computed per-index on the latest day in the 20D window, ranked by fr_net_value_total.",
            "source": "market_cache/vci_trading_daily/latest.sqlite + market_cache/hose_monthly/latest.sqlite",
        },
    }

    out_js.parent.mkdir(parents=True, exist_ok=True)
    out_js.write_text(
        "// AUTO-GENERATED from market_cache/vci_trading_daily/latest.sqlite + market_cache/hose_monthly/latest.sqlite\n"
        "// Foreign investor flow (20D) by index for UI GLM\n"
        f"window.UI_GLM_INDEX_FOREIGN_FLOW_20D = {json.dumps(payload, ensure_ascii=False, separators=(',', ':'))};\n",
        encoding="utf-8",
    )
    print(f"Wrote: {out_js} (asof={payload['asof']})")


if __name__ == "__main__":
    main()
