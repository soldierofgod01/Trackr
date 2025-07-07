import discord
from discord.ext import commands
from discord import app_commands
import os
import requests
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
TOKEN = os.getenv("trackr")  # Make sure your Render secret key is set to 'trackr'
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

@bot.tree.command(name="price", description="Get price and stats of any coin")
@app_commands.describe(symbol="Coin symbol like 'pepe', 'btc', 'eth'")
async def price(interaction: discord.Interaction, symbol: str):
    await interaction.response.defer(thinking=True)

    try:
        # Get coin ID from symbol
        coin_list = requests.get("https://api.coingecko.com/api/v3/coins/list").json()
        coin_id = next((coin["id"] for coin in coin_list if coin["symbol"] == symbol.lower()), None)

        if not coin_id:
            await interaction.followup.send(f"❌ Coin `{symbol}` not found.")
            return

        # Fetch market data
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        res = requests.get(url)
        if res.status_code != 200:
            await interaction.followup.send("❌ Failed to fetch data from API.")
            return

        data = res.json()
        market_data = data.get("market_data", {})
        name = data.get("name", symbol.upper())
        current_price = market_data.get("current_price", {}).get("usd", "N/A")
        market_cap = market_data.get("market_cap", {}).get("usd", "N/A")
        volume = market_data.get("total_volume", {}).get("usd", "N/A")
        high = market_data.get("high_24h", {}).get("usd", "N/A")
        low = market_data.get("low_24h", {}).get("usd", "N/A")

        msg = (
            f"💰 **{name} Stats (USD)**\n"
            f"> **Price:** ${current_price:,}\n"
            f"> **Market Cap:** ${market_cap:,}\n"
            f"> **24h Volume:** ${volume:,}\n"
            f"> **24h High:** ${high:,}\n"
            f"> **24h Low:** ${low:,}"
        )
        await interaction.followup.send(msg)

    except Exception as e:
        print(f"❌ Error: {e}")
        await interaction.followup.send("❌ Something went wrong while fetching data.")

bot.run(TOKEN)
