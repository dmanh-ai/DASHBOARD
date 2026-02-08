"""
Tính Technical Indicators từ OHLCV data.
Không cần ta-lib, chỉ dùng thuần Python.
"""

import math


def sma(closes, period):
    """Simple Moving Average."""
    if len(closes) < period:
        return None
    return round(sum(closes[-period:]) / period, 2)


def ema(closes, period):
    """Exponential Moving Average."""
    if len(closes) < period:
        return None
    k = 2 / (period + 1)
    ema_val = sum(closes[:period]) / period
    for c in closes[period:]:
        ema_val = c * k + ema_val * (1 - k)
    return round(ema_val, 2)


def rsi(closes, period=14):
    """Relative Strength Index."""
    if len(closes) < period + 1:
        return None
    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - 100 / (1 + rs), 2)


def macd(closes, fast=12, slow=26, signal=9):
    """MACD (line, signal, histogram)."""
    if len(closes) < slow + signal:
        return None, None, None
    fast_ema = _ema_series(closes, fast)
    slow_ema = _ema_series(closes, slow)

    macd_line = [f - s for f, s in zip(fast_ema[slow - fast:], slow_ema)]
    if len(macd_line) < signal:
        return None, None, None

    signal_line = _ema_series(macd_line, signal)
    histogram = macd_line[-1] - signal_line[-1]

    return round(macd_line[-1], 2), round(signal_line[-1], 2), round(histogram, 2)


def bollinger_bands(closes, period=20, std_dev=2):
    """Bollinger Bands (upper, middle, lower)."""
    if len(closes) < period:
        return None, None, None
    middle = sum(closes[-period:]) / period
    variance = sum((c - middle) ** 2 for c in closes[-period:]) / period
    std = math.sqrt(variance)
    upper = round(middle + std_dev * std, 2)
    lower = round(middle - std_dev * std, 2)
    return upper, round(middle, 2), lower


def obv(closes, volumes):
    """On-Balance Volume."""
    if len(closes) < 2 or len(volumes) < 2:
        return 0
    obv_val = 0
    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            obv_val += volumes[i]
        elif closes[i] < closes[i - 1]:
            obv_val -= volumes[i]
    return obv_val


def adx(highs, lows, closes, period=14):
    """Average Directional Index (simplified)."""
    if len(closes) < period * 2:
        return None
    plus_dm = []
    minus_dm = []
    tr_list = []

    for i in range(1, len(closes)):
        high_diff = highs[i] - highs[i - 1]
        low_diff = lows[i - 1] - lows[i]
        plus_dm.append(max(high_diff, 0) if high_diff > low_diff else 0)
        minus_dm.append(max(low_diff, 0) if low_diff > high_diff else 0)
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        tr_list.append(tr)

    if len(tr_list) < period:
        return None

    atr = sum(tr_list[:period]) / period
    plus_di = sum(plus_dm[:period]) / period
    minus_di = sum(minus_dm[:period]) / period

    for i in range(period, len(tr_list)):
        atr = (atr * (period - 1) + tr_list[i]) / period
        plus_di = (plus_di * (period - 1) + plus_dm[i]) / period
        minus_di = (minus_di * (period - 1) + minus_dm[i]) / period

    if atr == 0:
        return 0
    plus_di_pct = plus_di / atr * 100
    minus_di_pct = minus_di / atr * 100

    di_sum = plus_di_pct + minus_di_pct
    if di_sum == 0:
        return 0
    dx = abs(plus_di_pct - minus_di_pct) / di_sum * 100
    return round(dx, 2)


def volume_ma(volumes, period=20):
    """Volume Moving Average."""
    if len(volumes) < period:
        return None
    return round(sum(volumes[-period:]) / period, 0)


def _ema_series(values, period):
    """Tính EMA cho toàn bộ series."""
    k = 2 / (period + 1)
    result = [sum(values[:period]) / period]
    for val in values[period:]:
        result.append(val * k + result[-1] * (1 - k))
    return result


def pct_above_ma(bars, ma_period):
    """Tính % CP đóng cửa trên MA(n) - dùng cho breadth."""
    if len(bars) < ma_period:
        return None
    closes = [b["c"] for b in bars]
    ma_val = sum(closes[-ma_period:]) / ma_period
    current = closes[-1]
    return 1 if current > ma_val else 0


def compute_all_indicators(bars):
    """Tính tất cả indicators từ OHLCV bars.

    Args:
        bars: list of {"d", "o", "h", "l", "c", "v"}

    Returns:
        dict chứa tất cả indicators
    """
    closes = [b["c"] for b in bars]
    highs = [b["h"] for b in bars]
    lows = [b["l"] for b in bars]
    volumes = [b["v"] for b in bars]

    macd_line, macd_signal, macd_hist = macd(closes)
    bb_upper, bb_middle, bb_lower = bollinger_bands(closes)

    latest = bars[-1] if bars else {}
    prev = bars[-2] if len(bars) > 1 else latest

    change = latest.get("c", 0) - prev.get("c", 0)
    change_pct = (change / prev["c"] * 100) if prev.get("c") else 0

    return {
        "latest_close": latest.get("c"),
        "latest_volume": latest.get("v"),
        "latest_date": latest.get("d"),
        "change": round(change, 2),
        "change_pct": round(change_pct, 2),
        # Moving Averages
        "ma5": sma(closes, 5),
        "ma10": sma(closes, 10),
        "ma20": sma(closes, 20),
        "ma50": sma(closes, 50),
        "ma100": sma(closes, 100),
        "ma200": sma(closes, 200),
        "ema12": ema(closes, 12),
        "ema26": ema(closes, 26),
        # RSI
        "rsi14": rsi(closes, 14),
        # MACD
        "macd_line": macd_line,
        "macd_signal": macd_signal,
        "macd_histogram": macd_hist,
        # Bollinger Bands
        "bb_upper": bb_upper,
        "bb_middle": bb_middle,
        "bb_lower": bb_lower,
        # Volume
        "obv": obv(closes, volumes),
        "volume_ma20": volume_ma(volumes, 20),
        # ADX
        "adx14": adx(highs, lows, closes, 14),
        # Position vs MAs
        "above_ma5": closes[-1] > sma(closes, 5) if sma(closes, 5) else None,
        "above_ma20": closes[-1] > sma(closes, 20) if sma(closes, 20) else None,
        "above_ma50": closes[-1] > sma(closes, 50) if sma(closes, 50) else None,
        "above_ma200": closes[-1] > sma(closes, 200) if sma(closes, 200) else None,
    }
