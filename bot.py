import discord
from discord.ext import commands
from discord import app_commands
import os
import sqlite3
import time

TOKEN = os.getenv("TOKEN")

CHAT_CHANNEL_ID = 1474519935857328286
ADMIN_CHANNEL_ID = 1474519935857328286

MESSAGE_REWARD = 3
COOLDOWN = 10

# DATABASE
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id TEXT PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    messages INTEGER DEFAULT 0,
    last_time REAL DEFAULT 0
)
""")

conn.commit()

# BOT
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# FARM
@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if message.channel.id != CHAT_CHANNEL_ID:
        return

    if len(message.content.strip()) < 3:
        return

    user_id = str(message.author.id)

    cursor.execute("""
    INSERT OR IGNORE INTO users(user_id, balance, messages, last_time)
    VALUES (?, 0, 0, 0)
    """, (user_id,))

    conn.commit()

    cursor.execute("""
    SELECT balance, messages, last_time FROM users WHERE user_id=?
    """, (user_id,))

    user = cursor.fetchone()

    if time.time() - user[2] < COOLDOWN:
        return

    cursor.execute("""
    UPDATE users
    SET balance = balance + ?,
        messages = messages + 1,
        last_time = ?
    WHERE user_id = ?
    """, (MESSAGE_REWARD, time.time(), user_id))

    conn.commit()

    await bot.process_commands(message)

# READY
@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user}")
    await tree.sync()

# BALANCE
@tree.command(name="balance", description="Баланс")
async def balance(interaction: discord.Interaction):

    user_id = str(interaction.user.id)

    cursor.execute("""
    SELECT balance FROM users WHERE user_id=?
    """, (user_id,))

    data = cursor.fetchone()

    if not data:
        await interaction.response.send_message(
            "Нет данных",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"💰 Robux: {data[0]}",
        ephemeral=True
    )

bot.run(TOKEN)
