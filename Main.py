import discord
from discord.ext import commands
from discord import app_commands
import os
import requests
import pandas as pd
import mplfinance as mpf

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot is live as {bot.user} and slash commands synced.")

@bot.tree.command(name="price", description="Get the price chart of a coin")
@app_commands.describe(coin="The coin name (e.g., pepe, eth, btc)")
async def price(interaction: discord.Interaction, coin: str):
    await interaction.response.defer()

    url = f"https://api.coingecko.com/api/v3/coins/{coin.lower()}/market_chart?vs_currency=usd&days=1"
    res = requests.get(url)

    if res.status_code != 200:
        await interaction.followup.send("❌ Coin not found.")
        return

    data = res.json()
    df = pd.DataFrame(data["prices"], columns=["Timestamp", "Price"])
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit="ms")
    df.set_index("Timestamp", inplace=True)

    ohlc = df["Price"].resample("5min").ohlc().dropna()

    mpf.plot(
        ohlc,
        type="candle",
        mav=(9, 21),
        style="binance",
        title=f"{coin.upper()} / USD - 1D Chart",
        ylabel="Price",
        savefig="chart.png"
    )

    await interaction.followup.send(file=discord.File("chart.png"))

bot.run(TOKEN)
