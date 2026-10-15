import numpy as np
import pandas as pd


def compute_indicators(ohlcv_rows: list[list[float]]) -> dict[str, float | None]:
    """
    Computes RSI(14), MACD(12,26,9), Bollinger Bands(20,2), ATR(14), and VWAP
    directly on Pandas/NumPy 2.x without pandas-ta dependency fragility.
    Input rows: [[timestamp_ms, open, high, low, close, volume], ...]
    """
    if len(ohlcv_rows) < 30:
        return {"error": None, "rsi_14": None, "macd": None, "vwap": None}

    df = pd.DataFrame(
        ohlcv_rows, columns=["timestamp", "open", "high", "low", "close", "volume"]
    ).astype(float)

    close = df["close"]
    high = df["high"]
    low = df["low"]
    vol = df["volume"]

    # 1. Wilder's RSI (14)
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))

    # 2. MACD (12, 26, 9)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist = macd_line - signal_line

    # 3. Bollinger Bands (20, 2)
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std(ddof=0)
    bb_upper = sma20 + 2.0 * std20
    bb_lower = sma20 - 2.0 * std20

    # 4. ATR (14)
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()

    # 5. Rolling Session VWAP
    typical_price = (high + low + close) / 3.0
    total_vol = vol.sum()
    vwap = float((typical_price * vol).sum() / total_vol) if total_vol > 0 else None

    def _safe_last(series: pd.Series) -> float | None:
        val = series.iloc[-1]
        return round(float(val), 6) if pd.notna(val) else None

    return {
        "rsi_14": _safe_last(rsi),
        "macd_line": _safe_last(macd_line),
        "macd_signal": _safe_last(signal_line),
        "macd_hist": _safe_last(macd_hist),
        "bb_upper_20_2": _safe_last(bb_upper),
        "bb_mid_20": _safe_last(sma20),
        "bb_lower_20_2": _safe_last(bb_lower),
        "atr_14": _safe_last(atr),
        "period_vwap": round(vwap, 6) if vwap is not None else None,
    }

