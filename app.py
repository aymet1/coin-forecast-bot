from flask import Flask, request
from telegram import Bot
import requests
import datetime
import numpy as np

app = Flask(__name__)

# === TELEGRAM AYARI ===
BOT_TOKEN = "TELEGRAM_BOT_TOKENINI_YAZ"
bot = Bot(token=BOT_TOKEN)

# === CoinMarketCap verisi çek ===
def get_historical_prices(symbol, days=7):
    try:
        end_date = datetime.datetime.utcnow()
        start_date = end_date - datetime.timedelta(days=days)
        url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/historical"
        parameters = {
            "symbol": symbol.upper(),
            "convert": "USD",
            "time_start": start_date.strftime("%Y-%m-%d"),
            "time_end": end_date.strftime("%Y-%m-%d"),
        }
        headers = {
            "Accept": "application/json",
            "X-CMC_PRO_API_KEY": "385f0b74-ba78-4451-8956-234722f5465e"
        }

        response = requests.get(url, headers=headers, params=parameters)
        data = response.json()

        if "data" not in data or "quotes" not in data["data"]:
            return []

        prices = [quote["quote"]["USD"]["close"] for quote in data["data"]["quotes"]]
        return prices

    except Exception as e:
        print("Hata:", e)
        return []

# === Tahmin Hesapla ===
def forecast(prices):
    if len(prices) < 5:
        return None
    mean = round(np.mean(prices), 2)
    std = round(np.std(prices) * 1.5, 2)
    return mean, round(mean - std, 2), round(mean + std, 2), len(prices)

# === Webhook ===
@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    chat_id = data["message"]["chat"]["id"]
    text = data["message"]["text"].strip().upper()

    if not text.startswith("!"):
        return "OK"

    symbol = text[1:]
    prices = get_historical_prices(symbol)

    if not prices or len(prices) < 5:
        bot.send_message(chat_id=chat_id, text="❌ Fiyat verisi alınamadı veya coin bulunamadı.")
        return "OK"

    result = forecast(prices)
    if not result:
        bot.send_message(chat_id=chat_id, text="❌ Tahmin yapılamadı. Veri yetersiz.")
        return "OK"

    mean, low, high, count = result
    msg = f"📈 *{symbol}* Tahmini Kapanış: ${mean}\n📊 Fiyat Aralığı: ${low} - ${high}\n📅 {count} günlük veriyle hesaplandı."
    bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")

    return "OK"

@app.route("/")
def home():
    return "Coin Forecast Bot Aktif!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
