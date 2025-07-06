import discord
from discord.ext import commands
import requests
import matplotlib.pyplot as plt
import pandas as pd
import mplfinance as mpf
from io import BytesIO
import datetime
import os

bot = commands.Bot(command_prefix="/", intents=discord.Intents.default())

@bot.event
async def on_ready():
    print(f"Bot is live as {bot.user}")

@bot.command()
async def price(ctx, coin: str):
    await ctx.defer()
    r = requests.get(f"https://api.coingecko.com/api/v3/coins/{coin.lower()}/market_chart",
                     params={"vs_currency": "usd", "days": 1, "interval": "hourly"})
    if r.status_code != 200:
        return await ctx.reply("❌ Invalid coin or error.")
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
    await ctx.reply(embed=embed, file=discord.File(buf, "chart.png"))

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
