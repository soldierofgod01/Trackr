import discord
from discord.ext import commands
from discord import app_commands
import os
import requests

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

@bot.tree.command(name="ping", description="Test if the bot works")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong! Bot is alive.")

@bot.tree.command(name="price", description="Get live price of any coin (e.g. /price sol)")
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

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    response = requests.get(url).json()
    price = response[coin_id]["usd"]

    await interaction.followup.send(f"💰 **{symbol.upper()}** is currently **${price}**")

@bot.tree.command(name="info", description="Get live info on any coin (e.g. /info sol)")
@app_commands.describe(symbol="Coin symbol like btc, eth, pepe")
async def info(interaction: discord.Interaction, symbol: str):
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

    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={coin_id}"
    data = requests.get(url).json()

    if not data:
        await interaction.followup.send("❌ Failed to fetch coin info.")
        return

    coin = data[0]
    name = coin["name"]
    price = coin["current_price"]
    market_cap = coin["market_cap"]
    volume = coin["total_volume"]
    high_24h = coin["high_24h"]
    low_24h = coin["low_24h"]
    change_24h = coin["price_change_percentage_24h"]

    response = (
        f"📊 **{name.upper()} ({symbol.upper()})**\n"
        f"Price: ${price:,.2f}\n"
        f"Market Cap: ${market_cap:,.0f}\n"
        f"24h Volume: ${volume:,.0f}\n"
        f"24h High: ${high_24h:,.2f}\n"
        f"24h Low: ${low_24h:,.2f}\n"
        f"24h Change: {change_24h:+.2f}%"
    )

    await interaction.followup.send(response)

@bot.tree.command(name="gainers", description="Top 5 crypto gainers in the last 24h")
async def gainers(interaction: discord.Interaction):
    await interaction.response.defer()
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "percent_change_24h_desc", "per_page": 5, "page": 1}
    data = requests.get(url, params=params).json()

    msg = "**🚀 Top 5 Gainers (24h):**\n"
    for coin in data:
        msg += f"• {coin['name']} ({coin['symbol'].upper()}): {coin['price_change_percentage_24h']:.2f}%\n"

    await interaction.followup.send(msg)

@bot.tree.command(name="trending", description="Top 7 trending coins searched on CoinGecko")
async def trending(interaction: discord.Interaction):
    await interaction.response.defer()
    url = "https://api.coingecko.com/api/v3/search/trending"
    data = requests.get(url).json()

    msg = "**📈 Trending Coins:**\n"
    for i, coin in enumerate(data["coins"], start=1):
        item = coin["item"]
        msg += f"{i}. {item['name']} ({item['symbol'].upper()})\n"

    await interaction.followup.send(msg)

bot.run(TOKEN)
