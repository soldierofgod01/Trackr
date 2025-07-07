import discord
from discord.ext import commands
from discord import app_commands
import os
import requests
import pandas as pd
import mplfinance as mpf
from io import BytesIO

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1383877923911503896

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"✅ Synced {len(synced)} commands to your server.")
    except Exception as e:
        print(f"❌ Sync failed: {e}")

@bot.tree.command(name="ping", description="Test if the bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

@bot.tree.command(name="price", description="Get candlestick chart for any coin")
@app_commands.describe(symbol="Coin symbol (e.g. btc, eth, pepe)")
async def price(interaction: discord.Interaction, symbol: str):
    await interaction.response.defer(thinking=True)
    print("🔁 Step 1: Command received")

    try:
        coin_list = requests.get("https://api.coingecko.com/api/v3/coins/list").json()
        coin_id = next((coin["id"] for coin in coin_list if coin["symbol"] == symbol.lower()), None)
        print(f"🔁 Step 2: CoinGecko ID = {coin_id}")

        if not coin_id:
            await interaction.followup.send(f"❌ Couldn't find coin `{symbol}`.", ephemeral=True)
            return

        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": "7", "interval": "hourly"}
        res = requests.get(url, params=params)
        prices = res.json().get("prices", [])
        print(f"🔁 Step 3: Fetched {len(prices)} prices")

        if not prices:
            await interaction.followup.send("❌ No price data available.", ephemeral=True)
            return

        import matplotlib
        matplotlib.use('Agg')

        df = pd.DataFrame(prices, columns=["Timestamp", "Price"])
        df["Date"] = pd.to_datetime(df["Timestamp"], unit="ms")
        df.set_index("Date", inplace=True)
        df["Open"] = df["Price"]
        df["High"] = df["Price"]
        df["Low"] = df["Price"]
        df["Close"] = df["Price"]
        df = df[["Open", "High", "Low", "Close"]]

        buf = BytesIO()
        mpf.plot(df, type="candle", style="charles", title=f"{symbol.upper()} (7D)", savefig=buf)
        buf.seek(0)
        print("✅ Step 4: Chart generated")

        file = discord.File(buf, filename=f"{symbol}_chart.png")
        await interaction.followup.send(file=file)

    except Exception as e:
        import traceback
        print("❌ Error:\n", traceback.format_exc())
        await interaction.followup.send("❌ Something went wrong.", ephemeral=True)

bot.run(TOKEN)
