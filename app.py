from flask import Flask, request
from telegram import Bot
import requests
import numpy as np

app = Flask(__name__)

# === TELEGRAM AYARI ===
BOT_TOKEN = "7994060842:AAE3sKL4-nII9rvELnAvyX-jNgFyEGwBHOQ"
bot = Bot(token=BOT_TOKEN)

# === Binance'ten fiyat verisi çek ===
def get_price_history_binance(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1d&limit=100"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    data = response.json()
    return [float(candle[4]) for candle in data]  # Kapanış fiyatı

# === Tahmin ve varyans hesapla ===
def forecast(prices):
    mean = round(np.mean(prices[-5:]), 2)  # Son 5 gün ortalaması
    std = round(np.std(prices[-5:]), 2)
    return mean, round(mean - std, 2), round(mean + std, 2), len(prices)

# === Telegram Webhook ===
@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    chat_id = data["message"]["chat"]["id"]
    text = data["message"]["text"].strip().upper()

    if not text.startswith("!"):
        return "OK"

    symbol = text[1:]  # !BTC -> BTC
    prices = get_price_history_binance(symbol)
    if not prices or len(prices) < 10:
        bot.send_message(chat_id=chat_id, text="❌ Fiyat verisi alınamadı ya da yetersiz.")
        return "OK"

    mean, low, high, days = forecast(prices)
    msg = f"📈 {symbol} Tahmini Kapanış: ${mean}\n"
    msg += f"📊 Fiyat Aralığı: ${low} - ${high}\n"
    msg += f"📅 {days} günlük Binance verisiyle hesaplandı"

    bot.send_message(chat_id=chat_id, text=msg)
    return "ok"

@app.route("/")
def home():
    return "Coin Forecast Bot Aktif!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
