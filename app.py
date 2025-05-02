from flask import Flask, request
from telegram import Bot
import requests
import datetime

app = Flask(__name__)

# === TELEGRAM BOT AYARI ===
BOT_TOKEN = "7994060842:AAE3sKL4-nII9rvELnAvyX-jNgFyEGwBHOQ"
CMC_API_KEY = "385f0b74-ba78-4451-8956-234722f5465e"
bot = Bot(token=BOT_TOKEN)

# === CoinMarketCap verisi çek ===
def get_historical_prices_cmc(symbol, convert="USD"):
    try:
        end_date = datetime.datetime.utcnow().date()
        start_date = end_date - datetime.timedelta(days=30)
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/historical'
        parameters = {
            'symbol': symbol.upper(),
            'convert': convert,
            'time_start': start_date.isoformat(),
            'time_end': end_date.isoformat(),
            'interval': 'daily'
        }
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': 385f0b74-ba78-4451-8956-234722f5465e ,
        }
        response = requests.get(url, headers=headers, params=parameters)
        data = response.json()
        if "data" not in data or "quotes" not in data["data"]:
            return []
        prices = [quote["quote"][convert]["close"] for quote in data["data"]["quotes"]]
        return prices
    except Exception as e:
        print("HATA:", e)
        return []

# === Tahmin Hesapla ===
def forecast(prices):
    import numpy as np
    if not prices or len(prices) < 5:
        return None
    mean = round(np.mean(prices[-5:]), 2)
    std = round(np.std(prices[-5:]), 2)
    return mean, round(mean - std, 2), round(mean + std, 2), len(prices)

# === Telegram Webhook ===
@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    msg = data.get("message", {})
    text = msg.get("text", "").strip().upper()
    chat_id = msg.get("chat", {}).get("id")

    if not text.startswith("!"):
        return "ignored"

    symbol = text[1:]
    prices = get_historical_prices_cmc(symbol)
    if not prices:
        bot.send_message(chat_id=chat_id, text="❌ Fiyat verisi alınamadı veya coin bulunamadı.")
        return "ok"

    result = forecast(prices)
    if not result:
        bot.send_message(chat_id=chat_id, text="⚠️ Tahmin hesaplanamadı. Yetersiz veri.")
        return "ok"

    mean, low, high, count = result
    msg_text = f"📉 {symbol} Tahmini Kapanış: ${mean}\n📊 Fiyat Aralığı: ${low} – ${high}\n📅 {count} günlük veriye dayalı tahmin"
    bot.send_message(chat_id=chat_id, text=msg_text)
    return "ok"

@app.route("/")
def home():
    return "Bot aktif!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
