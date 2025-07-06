import discord
from discord.ext import commands
from discord import app_commands
import os
import requests
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from io import BytesIO

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

@bot.tree.command(name="price", description="Get candlestick chart with EMAs for any coin")
@app_commands.describe(symbol="Coin symbol (e.g. btc, eth, pepe)")
async def price(interaction: discord.Interaction, symbol: str):
    await interaction.response.defer()

    # 1. Find coin ID from symbol
    coin_list = requests.get("https://api.coingecko.com/api/v3/coins/list").json()
    coin_id = next((coin["id"] for coin in coin_list if coin["symbol"] == symbol.lower()), None)

    if not coin_id:
        await interaction.followup.send(f"❌ Couldn't find coin with symbol `{symbol}`.")
        return

    # 2. Get market chart data
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": "7", "interval": "hourly"}
    res = requests.get(url, params=params)

    if res.status_code != 200:
        await interaction.followup.send("❌ Failed to fetch price data.")
        return

    prices = res.json().get("prices", [])
    if not prices:
        await interaction.followup.send("❌ No price data available.")
        return

    # 3. Convert to DataFrame
    df = pd.DataFrame(prices, columns=["Timestamp", "Price"])
    df["Date"] = pd.to_datetime(df["Timestamp"], unit="ms")
    df.set_index("Date", inplace=True)

    # Fake OHLC (using close only)
    df["Open"] = df["Price"]
    df["High"] = df["Price"]
    df["Low"] = df["Price"]
    df["Close"] = df["Price"]

    df = df[["Open", "High", "Low", "Close"]]

    # 4. Plot chart with EMAs
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()

    apds = [
        mpf.make_addplot(df["EMA20"], color="orange"),
        mpf.make_addplot(df["EMA50"], color="blue")
    ]

    buf = BytesIO()
    mpf.plot(df, type="candle", addplot=apds, style="yahoo", title=f"{symbol.upper()} Price (7D)", savefig=buf)
    buf.seek(0)

    # 5. Send as Discord file
    file = discord.File(fp=buf, filename=f"{symbol}_chart.png")
    await interaction.followup.send(file=file)

bot.run(TOKEN)
