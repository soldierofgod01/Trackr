import discord
from discord.ext import commands
from discord import app_commands
import os
import requests
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime, timedelta

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Sync failed: {e}")

@bot.tree.command(name="price", description="Show candlestick chart of any coin (e.g. /price pepe)")
@app_commands.describe(symbol="Coin symbol like btc, eth, pepe")
async def price(interaction: discord.Interaction, symbol: str):
    await interaction.response.defer()

    coin_list = requests.get("https://api.coingecko.com/api/v3/coins/list").json()
    coin_id = None
    symbol = symbol.lower()

    for coin in coin_list:
        if coin["symbol"] == symbol:
            coin_id = coin["id"]
            break

    if not coin_id:
        await interaction.followup.send(f"❌ Couldn't find coin with symbol `{symbol}`")
        return

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7&interval=hourly"
    data = requests.get(url).json()

    if "prices" not in data:
        await interaction.followup.send("❌ Failed to fetch price data.")
        return

    df = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)

    df["open"] = df["price"].shift(1)
    df["high"] = df["price"].rolling(2).max()
    df["low"] = df["price"].rolling(2).min()
    df["close"] = df["price"]
    df = df.dropna()
    df = df[["open", "high", "low", "close"]]

    df["EMA20"] = df["close"].ewm(span=20).mean()
    df["EMA50"] = df["close"].ewm(span=50).mean()

    fig, ax = mpf.plot(
        df,
        type="candle",
        style="yahoo",
        mav=(20, 50),
        volume=False,
        returnfig=True,
        title=f"{symbol.upper()} Price - 7D Hourly",
    )

    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    file = discord.File(buf, filename="chart.png")
    await interaction.followup.send(file=file)

bot.run(TOKEN)
