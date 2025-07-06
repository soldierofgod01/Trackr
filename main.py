import os
import discord
from discord import app_commands
from discord.ext import commands
import requests

TOKEN = os.getenv("trackr")
GUILD_ID = 1383877923911503896

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    print(f"{bot.user} is online!")

@bot.tree.command(name="ping", description="Check if bot is online", guild=discord.Object(id=GUILD_ID))
async def ping_command(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@bot.tree.command(name="price", description="Get current price of a coin", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(symbol="Coin symbol (e.g. bitcoin, ethereum)")
async def price_command(interaction: discord.Interaction, symbol: str):
    await interaction.response.defer()
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        price = data.get(symbol, {}).get("usd")

        if price is None:
            raise ValueError("Coin not found or no price data.")

        await interaction.followup.send(f"💰 **{symbol.capitalize()}**: ${price:.2f}")
    except Exception as e:
        await interaction.followup.send("❌ Failed to fetch price data.")
        print(f"Error in /price command: {e}")

bot.run(TOKEN)
