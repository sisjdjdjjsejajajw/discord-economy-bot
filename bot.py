import discord
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Бот запущен как {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.lower() == "ping":
        await message.channel.send("pong")

client.run(TOKEN)
