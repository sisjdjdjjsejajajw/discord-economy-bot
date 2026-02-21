import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import time

TOKEN = os.getenv("TOKEN")

CHAT_CHANNEL_ID = 1474519935857328286
ADMIN_CHANNEL_ID = 1474519935857328286

MIN_WITHDRAW = 100
MESSAGE_REWARD = 4
COOLDOWN = 10
MIN_LENGTH = 3

DATA_FILE = "data.json"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ---------- DATA ----------
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
else:
    data = {"users": {}}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ---------- MESSAGE FARM ----------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id != CHAT_CHANNEL_ID:
        return

    if len(message.content.strip()) < MIN_LENGTH:
        return

    user_id = str(message.author.id)

    if user_id not in data["users"]:
        data["users"][user_id] = {
            "messages": 0,
            "balance": 0,
            "last_time": 0
        }

    user = data["users"][user_id]

    now = time.time()

    if now - user["last_time"] < COOLDOWN:
        return

    user["last_time"] = now
    user["messages"] += 1

    # TEST REWARD (1 message = reward once)
    if user["messages"] == 1:
        user["balance"] += MESSAGE_REWARD
        await message.channel.send(
            f"{message.author.mention} получил {MESSAGE_REWARD} Robux!"
        )

    save_data()
    await bot.process_commands(message)

# ---------- SLASH COMMANDS ----------

@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user}")
    await tree.sync()

def progress_bar(balance):
    max_balance = 100
    length = 10

    filled = int(balance / max_balance * length)
    empty = length - filled

    return "🟩" * filled + "🟥" * empty

@tree.command(name="balance", description="Баланс")
async def balance(interaction: discord.Interaction):
    user_id = str(interaction.user.id)

    if user_id not in data["users"]:
        await interaction.response.send_message(
            "Нет данных", ephemeral=True
        )
        return

    user = data["users"][user_id]

    bar = progress_bar(user["balance"])

    await interaction.response.send_message(
        f"💰 Robux: {user['balance']}\n[{bar}]",
        ephemeral=True
    )

@tree.command(name="withdraw", description="Вывод Robux")
async def withdraw(interaction: discord.Interaction):
    user_id = str(interaction.user.id)

    if user_id not in data["users"]:
        return

    user = data["users"][user_id]

    if user["balance"] < MIN_WITHDRAW:
        await interaction.response.send_message(
            f"Минимум вывода {MIN_WITHDRAW}",
            ephemeral=True
        )
        return

    user["balance"] -= MIN_WITHDRAW
    save_data()

    admin = bot.get_channel(ADMIN_CHANNEL_ID)

    if admin:
        await admin.send(
            f"Вывод заявки от {interaction.user.mention}"
        )

    await interaction.response.send_message(
        "Заявка отправлена",
        ephemeral=True
    )

bot.run(TOKEN)
