
from flask import Flask, request
from telegram import Bot
import requests
import numpy as np

app = Flask(__name__)
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
bot = Bot(token=TOKEN)

def get_coin_id(symbol):
    url = "https://api.coingecko.com/api/v3/coins/list"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    data = r.json()
    symbol = symbol.lower()
    for coin in data:
        if coin["symbol"] == symbol:
            return coin["id"]
    return None

def get_price_history(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": "max"}
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return None
    prices = [p[1] for p in r.json().get("prices", [])]
    return prices

def forecast(prices):
    mean = round(np.mean(prices), 2)
    std = round(np.std(prices) * 1.5, 2)
    low = round(mean - std, 2)
    high = round(mean + std, 2)
    return mean, low, high, len(prices)

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    msg = data.get("message", {})
    text = msg.get("text", "")
    chat_id = msg.get("chat", {}).get("id")

    if not text.startswith("!"):
        return "ignored"

    symbol = text[1:].strip().upper()
    coin_id = get_coin_id(symbol)

    if not coin_id:
        bot.send_message(chat_id=chat_id, text="❌ Coin bulunamadı.")
        return "ok"

    prices = get_price_history(coin_id)
    if not prices or len(prices) < 10:
        bot.send_message(chat_id=chat_id, text="❌ Veri yetersiz.")
        return "ok"

    mean, low, high, count = forecast(prices)
    msg_text = f"📊 {symbol} Tahmini Kapanış: ${mean}\n🔄 Aralık: ${low} – ${high}\n📈 {count} günlük veriye dayalı"
    bot.send_message(chat_id=chat_id, text=msg_text)
    return "ok"

@app.route("/")
def home():
    return "Bot aktif!"

if __name__ == "__main__":
    app.run()
