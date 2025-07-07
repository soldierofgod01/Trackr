import os
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp

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

@bot.tree.command(name="ping", description="Check bot status", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

@bot.tree.command(name="price", description="Get current coin price", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(symbol="Enter the coin ID (e.g., bitcoin, ethereum)")
async def price(interaction: discord.Interaction, symbol: str):
    await interaction.response.defer()
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await interaction.followup.send(f"❌ API Error: {resp.status}")
                    return

                data = await resp.json()
                price = data.get(symbol.lower(), {}).get("usd")

                if price is None:
                    await interaction.followup.send("❌ Coin not found. Please check the ID.")
                else:
                    await interaction.followup.send(f"💰 **{symbol.title()}**: ${price}")
    except Exception as e:
        await interaction.followup.send("⚠️ Something went wrong while fetching the price.")
        print(f"Error in /price: {e}")

bot.run(TOKEN)
