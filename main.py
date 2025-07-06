import os import discord from discord import app_commands from discord.ext import commands import requests import pandas as pd import matplotlib.pyplot as plt import mplfinance as mpf from io import BytesIO from datetime import datetime, timezone

TOKEN = os.getenv("trackr") GUILD_ID = 1383877923911503896

intents = discord.Intents.default() bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event async def on_ready(): await bot.wait_until_ready() try: synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID)) print(f"Synced {len(synced)} command(s)") except Exception as e: print(f"Sync error: {e}") print(f"Bot is live as {bot.user}")

@bot.tree.command(name="ping", description="Check if bot is online", guild=discord.Object(id=GUILD_ID)) async def ping_command(interaction: discord.Interaction): await interaction.response.send_message("Pong!")

@bot.tree.command(name="price", description="Get candlestick chart of a coin", guild=discord.Object(id=GUILD_ID)) @app_commands.describe(symbol="Coin symbol (e.g. bitcoin, ethereum, pepe)") async def price_command(interaction: discord.Interaction, symbol: str): await interaction.response.defer() try: print("Fetching price data...") url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart?vs_currency=usd&days=1&interval=hourly" res = requests.get(url) if res.status_code != 200: raise ValueError("Coin not found or API issue.")

data = res.json()
    prices = data['prices']
    if not prices:
        raise ValueError("No price data returned.")

    print("Processing data into dataframe...")
    df = pd.DataFrame(prices, columns=['timestamp', 'price'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df['Open'] = df['price'].shift(1)
    df['High'] = df['price'].rolling(window=2).max()
    df['Low'] = df['price'].rolling(window=2).min()
    df['Close'] = df['price']
    ohlc = df[['Open', 'High', 'Low', 'Close']].dropna()

    print("Generating chart...")
    fig, ax = plt.subplots()
    mpf.plot(ohlc, type='candle', style='charles', ax=ax, ylabel='USD')
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    print("Sending chart to Discord...")
    file = discord.File(buf, filename="chart.png")
    embed = discord.Embed(title=f"{symbol.capitalize()} Price Chart", color=0x1ABC9C)
    embed.set_image(url="attachment://chart.png")
    embed.set_footer(text=f"Powered by CoinGecko • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    await interaction.followup.send(embed=embed, file=file)

except Exception as e:
    print(f"Price command error: {e}")
    await interaction.followup.send("❌ Failed to fetch price data.")

bot.run(TOKEN)
