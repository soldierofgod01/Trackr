import discord from discord import app_commands from discord.ext import commands import os import requests import pandas as pd import matplotlib.pyplot as plt import mplfinance as mpf from io import BytesIO from datetime import datetime

TOKEN = os.getenv("trackr")  # Make sure your Render Secret is called 'trackr' GUILD_ID = 1383877923911503896  # Replace with your Discord server ID

intents = discord.Intents.default() bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event async def on_ready(): print(f"Bot is live as {bot.user}") try: synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID)) print(f"Synced {len(synced)} commands.") except Exception as e: print(f"Failed to sync commands: {e}")

@bot.tree.command(name="ping", description="Check bot latency.", guild=discord.Object(id=GUILD_ID)) async def ping(interaction: discord.Interaction): await interaction.response.send_message("🏓 Pong!")

@bot.tree.command(name="price", description="Get candlestick chart for any coin", guild=discord.Object(id=GUILD_ID)) @app_commands.describe(symbol="Coin symbol (e.g. btc, eth, pepe)") async def price(interaction: discord.Interaction, symbol: str): await interaction.response.defer(thinking=True)

try:
    coin_list = requests.get("https://api.coingecko.com/api/v3/coins/list").json()
    coin_id = next((c["id"] for c in coin_list if c["symbol"].lower() == symbol.lower()), None)

    if not coin_id:
        await interaction.followup.send(f"❌ Couldn't find a coin with symbol `{symbol}`.")
        return

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": "7", "interval": "hourly"}
    response = requests.get(url, params=params)

    if response.status_code != 200:
        await interaction.followup.send("❌ Failed to fetch price data from CoinGecko.")
        return

    prices = response.json().get("prices", [])
