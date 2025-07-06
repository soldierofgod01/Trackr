import discord
from discord import app_commands
import requests
import matplotlib.pyplot as plt
import pandas as pd
import mplfinance as mpf
from io import BytesIO
import datetime
import os

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        print(f"Bot is live as {self.user}")
        # Force sync to your server using its ID
        await self.tree.sync(guild=discord.Object(id=1383877923911503896))

client = MyClient()

@client.tree.command(name="price", description="Get price chart of a coin", guild=discord.Object(id=1383877923911503896))
@app_commands.describe(coin="The coin ID (like pepe, floki, eth)")
async def price(interaction: discord.Interaction, coin: str):
    await interaction.response.defer()
    r = requests.get(f"https://api.coingecko.com/api/v3/coins/{coin.lower()}/market_chart",
                     params={"vs_currency": "usd", "days": 1, "interval": "hourly"})
    if r.status_code != 200:
        return await interaction.followup.send("❌ Invalid coin or error.")
    data = r.json()
    df = pd.DataFrame(data['prices'], columns=['ts','price'])
    df['ts'] = pd.to_datetime(df['ts'], unit='ms')
    df.set_index('ts', inplace=True)
    df['EMA6'] = df.price.ewm(span=6).mean()
    df['EMA12'] = df.price.ewm(span=12).mean()
    df['EMA20'] = df.price.ewm(span=20).mean()
    ohlc = df.price.resample('1H').ohlc().dropna()
    apds = [mpf.make_addplot(df['EMA6'], color='green'),
            mpf.make_addplot(df['EMA12'], color='orange'),
            mpf.make_addplot(df['EMA20'], color='red')]
    buf = BytesIO()
    mpf.plot(ohlc, type='candle', style='binance', addplot=apds, savefig=buf)
    buf.seek(0)
    info = requests.get("https://api.coingecko.com/api/v3/coins/markets",
                        params={"vs_currency":"usd","ids":coin.lower()}).json()[0]
    embed = discord.Embed(
        title=f"{info['name']} — ${info['current_price']:.8f}",
        description=(
            f"📊 24h High: ${info['high_24h']:.8f} | Low: ${info['low_24h']:.8f}\n"
            f"💰 Market Cap: ${info['market_cap']:,}\n"
            f"🔁 Volume: ${info['total_volume']:,}"
        ), color=0x1ABC9C)
    embed.set_footer(text=f"Powered by CoinGecko • {datetime.datetime.utcnow():%Y-%m-%d %H:%M} UTC")
    embed.set_image(url="attachment://chart.png")
    await interaction.followup.send(embed=embed, file=discord.File(buf, "chart.png"))

client.run(os.getenv("DISCORD_BOT_TOKEN"))
