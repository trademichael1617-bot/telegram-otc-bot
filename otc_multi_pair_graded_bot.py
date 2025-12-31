import csv
import requests
from datetime import datetime

# ================== CONFIG ==================
PAIR = "EURUSD"
RSI_UPPER = 85
RSI_LOWER = 15
CONSOLIDATION_THRESHOLD = 0.0005

BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
# ============================================


# ================== TELEGRAM =================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=payload)
# ============================================


# ================== RSI ======================
def calculate_rsi(closes, period=14):
    gains, losses = [], []

    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        if change > 0:
            gains.append(change)
        else:
            losses.append(abs(change))

    if len(gains) < period:
        return 50  # neutral

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period if losses else 1

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))
# ============================================


# ============ CONSOLIDATION ==================
def is_consolidating(highs, lows, lookback=10):
    recent_high = max(highs[-lookback:])
    recent_low = min(lows[-lookback:])
    return (recent_high - recent_low) < CONSOLIDATION_THRESHOLD
# ============================================


# ============== PAYOUT =======================
def get_otc_payout(pair):
    with open("payouts.csv") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["pair"] == pair and row["market"] == "OTC":
                return int(row["payout"])
    return None
# ============================================


# ================== MAIN =====================
def run_bot():

    # ---- OTC WEEKEND GUARD ----
    weekday = datetime.now().weekday()  # 0=Mon ... 6=Sun
    if weekday < 5:
        print("Weekday detected — OTC disabled")
        return

    # ---- LOAD CANDLES ----
    closes, highs, lows = [], [], []

    with open("candles.csv") as file:
        reader = csv.DictReader(file)
        for row in reader:
            closes.append(float(row["close"]))
            highs.append(float(row["high"]))
            lows.append(float(row["low"]))

    if len(closes) < 15:
        print("Not enough candle data")
        return

    # ---- INDICATORS ----
    rsi = calculate_rsi(closes)
    consolidating = is_consolidating(highs, lows)

    # ---- PAYOUT RULE ----
    payout = get_otc_payout(PAIR)
    if payout is None:
        print("No OTC payout found")
        return

    if payout < 90 or payout > 92:
        print("OTC payout not in range")
        return

    if not consolidating:
        print("Market is trending — no trade")
        return

    # ---- SIGNAL RULE ----
    signal = None
    if rsi <= RSI_LOWER:
        signal = "BUY"
    elif rsi >= RSI_UPPER:
        signal = "SELL"

    if signal is None:
        print("RSI not in signal zone")
        return

    # ---- TELEGRAM ALERT ----
    message = f"""
📊 PO OTC SIGNAL
Pair: {PAIR} (OTC)
Signal: {signal}
RSI: {round(rsi, 2)}
Payout: {payout}%
Market: Consolidation
Time: {datetime.now()}
"""
    send_telegram(message)

    # ---- LOG SIGNAL ----
    with open("signals.csv", "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.now(),
            PAIR,
            "OTC",
            signal,
            round(rsi, 2),
            payout
        ])

    print("Signal sent successfully")


# ============== RUN ==========================
if __name__ == "__main__":
    run_bot()
