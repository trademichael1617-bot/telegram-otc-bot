import pandas as pd
import numpy as np

# =========================
# SETTINGS (DO NOT CHANGE)
# =========================
SYMBOL = "EURUSD"
TIMEFRAME = "1m"

RSI_PERIOD = 7
RSI_OVERBOUGHT = 90
RSI_OVERSOLD = 10

BB_PERIOD = 25
BB_DEV = 2

CONSOLIDATION_LOOKBACK = 20
BB_WIDTH_THRESHOLD = 0.015  # controls consolidation sensitivity


# =========================
# INDICATOR FUNCTIONS
# =========================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def bollinger_bands(series, period, dev):
    sma = series.rolling(period).mean()
    std = series.rolling(period).std()
    upper = sma + (std * dev)
    lower = sma - (std * dev)
    return upper, lower, sma


def is_consolidating(close, upper_bb, lower_bb):
    """
    Returns True ONLY when market is ranging
    """
    bb_width = (upper_bb - lower_bb) / close
    recent_range = (
        close.rolling(CONSOLIDATION_LOOKBACK).max()
        - close.rolling(CONSOLIDATION_LOOKBACK).min()
    ) / close

    return (bb_width < BB_WIDTH_THRESHOLD) & (recent_range < BB_WIDTH_THRESHOLD)


# =========================
# STRATEGY LOGIC
# =========================
def analyze_market(df):
    """
    df MUST contain only EURUSD 1m CLOSE prices
    """

    df = df.copy()

    # LINE CHART LOGIC → CLOSE PRICE ONLY
    df["rsi"] = rsi(df["close"], RSI_PERIOD)
    df["upper_bb"], df["lower_bb"], df["mid_bb"] = bollinger_bands(
        df["close"], BB_PERIOD, BB_DEV
    )

    df["consolidating"] = is_consolidating(
        df["close"], df["upper_bb"], df["lower_bb"]
    )

    df["signal"] = "NONE"

    # BUY SIGNAL
    buy_condition = (
        (df["rsi"] <= RSI_OVERSOLD)
        & (df["close"] <= df["lower_bb"])
        & (df["consolidating"])
    )

    # SELL SIGNAL
    sell_condition = (
        (df["rsi"] >= RSI_OVERBOUGHT)
        & (df["close"] >= df["upper_bb"])
        & (df["consolidating"])
    )

    df.loc[buy_condition, "signal"] = "CALL"
    df.loc[sell_condition, "signal"] = "PUT"

    return df


# =========================
# EXAMPLE USAGE
# =========================
if __name__ == "__main__":
    # Example dataframe (replace with live price feed)
    # Data MUST be 1-minute EURUSD closes
    data = {
        "close": np.random.random(200) * 0.002 + 1.0800
    }

    df = pd.DataFrame(data)

    result = analyze_market(df)

    latest = result.iloc[-1]

    if latest["signal"] != "NONE":
        print(f"📢 {SYMBOL} SIGNAL → {latest['signal']}")
    else:
        print("⏸ No trade (Market not consolidating)")
