import discord
from discord import app_commands
import requests
import mplfinance as mpf
import pandas as pd
import matplotlib.pyplot as plt
import io
import os

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1383877923911503896  # your server ID

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        await self.wait_until_ready()
        await self.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f'Bot is live as {self.user}')

client = MyClient()

@client.tree.command(name="price", description="Get the price chart of a coin", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(coin="The coin name (e.g., pepe, eth, doge)")
async def price_command(interaction: discord.Interaction, coin: str):
    await interaction.response.defer()

    url = f"https://api.coingecko.com/api/v3/coins/{coin.lower()}/market_chart?vs_currency=usd&days=1"
    res = requests.get(url)

    if res.status_code != 200:
        await interaction.followup.send("Coin not found.")
        return

    data = res.json()
    prices = pd.DataFrame(data["prices"], columns=["Timestamp", "Price"])
    prices["Timestamp"] = pd.to_datetime(prices["Timestamp"], unit="ms")
    prices.set_index("Timestamp", inplace=True)

    ohlc = prices["Price"].resample("5min").ohlc()
    ohlc.dropna(inplace=True)

    mpf.plot(
        ohlc,
        type="candle",
        mav=(9, 21),
        style="binance",
        title=f"{coin.upper()} / USD - 1D Chart",
        ylabel="Price",
        savefig="chart.png"
    )

    file = discord.File("chart.png", filename="chart.png")
    await interaction.followup.send(f"{coin.upper()} price chart:", file=file)

client.run(TOKEN)
