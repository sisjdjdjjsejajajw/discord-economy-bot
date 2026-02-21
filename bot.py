import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import time
import random

TOKEN = os.getenv("TOKEN")

CHAT_CHANNEL_ID = 1474519935857328286
ADMIN_CHANNEL_ID = 1474519935857328286
ROLE_BONUS_ID = 1474519934351442047

MIN_WITHDRAW = 100
MIN_BET = 15

# Тестовая награда
MESSAGE_REWARD = 3
COOLDOWN = 10
MIN_LENGTH = 3

DATA_FILE = "data.json"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ---------------- DATA ----------------

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
else:
    data = {"users": {}}


def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ---------------- MESSAGE FARM ----------------

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
            "last_time": 0,
            "transactions": []
        }

    user = data["users"][user_id]
    now = time.time()

    if now - user["last_time"] < COOLDOWN:
        return

    user["last_time"] = now
    user["messages"] += 1

    # TEST MODE → 1 сообщение = 3 Robux
    if user["messages"] == 1:
        user["balance"] += MESSAGE_REWARD

    save_data()
    await bot.process_commands(message)


# ---------------- TRANSACTIONS ----------------

@tree.command(name="transfer", description="Перевести Robux")
async def transfer(interaction: discord.Interaction, member: discord.Member, amount: int):

    sender = str(interaction.user.id)
    receiver = str(member.id)

    if amount <= 0:
        await interaction.response.send_message("Сумма должна быть > 0", ephemeral=True)
        return

    if sender not in data["users"] or data["users"][sender]["balance"] < amount:
        await interaction.response.send_message("Недостаточно Robux", ephemeral=True)
        return

    if receiver not in data["users"]:
        data["users"][receiver] = {"messages": 0, "balance": 0, "last_time": 0, "transactions": []}

    data["users"][sender]["balance"] -= amount
    data["users"][receiver]["balance"] += amount

    data["users"][sender]["transactions"].append(
        f"Sent {amount} to {member.name}"
    )

    save_data()

    await interaction.response.send_message(
        f"Переведено {amount} Robux → {member.mention}",
        ephemeral=True
    )


# ---------------- BALANCE ----------------

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
        await interaction.response.send_message("Нет данных", ephemeral=True)
        return

    user = data["users"][user_id]

    bar = progress_bar(user["balance"])

    await interaction.response.send_message(
        f"💰 Robux: {user['balance']}\n[{bar}]",
        ephemeral=True
    )


# ---------------- MISSIONS ----------------

@tree.command(name="missions", description="Миссии")
async def missions(interaction: discord.Interaction):

    user_id = str(interaction.user.id)

    if user_id not in data["users"]:
        await interaction.response.send_message("Нет данных", ephemeral=True)
        return

    user = data["users"][user_id]

    # Тест миссия
    goal = 1
    reward = 3

    progress = min(user["messages"], goal)

    text = f"Миссия: {progress}/{goal}\nНаграда: {reward} Robux"

    if progress >= goal:
        text += "\nМожно получить награду!"

    await interaction.response.send_message(text, ephemeral=True)


# ---------------- ROULETTE ----------------

@tree.command(name="roulette", description="Рулетка")
async def roulette(interaction: discord.Interaction, bet: int):

    user_id = str(interaction.user.id)

    if bet < MIN_BET:
        await interaction.response.send_message(
            f"Минимальная ставка {MIN_BET}",
            ephemeral=True
        )
        return

    if user_id not in data["users"] or data["users"][user_id]["balance"] < bet:
        await interaction.response.send_message("Нет Robux", ephemeral=True)
        return

    data["users"][user_id]["balance"] -= bet

    # Шансы
    roll = random.random()

    reward = 0

    if roll < 0.0001:
        reward = 100
    elif roll < 0.10:
        reward = 20
    elif roll < 0.46:
        reward = 10
    elif roll < 0.51 and ROLE_BONUS_ID != 0:
        reward = "ROLE"

    if reward == "ROLE":
        member = interaction.user
        role = interaction.guild.get_role(ROLE_BONUS_ID)

        if role:
            await member.add_roles(role)

        result_text = "Вы выиграли роль!"
    else:
        data["users"][user_id]["balance"] += reward + bet
        result_text = f"Вы выиграли {reward} Robux!"

    save_data()

    await interaction.response.send_message(result_text, ephemeral=True)


bot.run(TOKEN)
