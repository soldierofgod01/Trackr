import discord
from discord.ext import commands
from discord import app_commands
import os

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
client = commands.Bot(command_prefix="!", intents=intents)

@client.event
async def on_ready():
    await client.tree.sync()
    print(f"Bot is live as {client.user}")

@client.tree.command(name="hello", description="Say hello")
async def hello_command(interaction: discord.Interaction):
    await interaction.response.send_message("Wassup! 🫡")

client.run(TOKEN)
