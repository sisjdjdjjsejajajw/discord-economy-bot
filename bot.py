import discord
from discord.ext import commands
import json
import random
import datetime
import time
import os

# ===================== НАСТРОЙКИ =====================
TOKEN = ""
CHAT_CHANNEL_ID = 1474519935857328286  # ID канала для фарма
ADMIN_CHANNEL_ID = 1474519935857328286  # канал для заявок на вывод (можно тот же)

MIN_WITHDRAW = 100
MESSAGE_REWARD = 4
COOLDOWN = 10
MIN_LENGTH = 3
# =====================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"

# ---------- Загрузка данных ----------
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
else:
    data = {
        "users": {},
        "daily_missions": {},
        "last_reset": ""
    }

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ---------- Ежедневные миссии ----------
MISSION_POOL = [
    {"goal": 100, "reward": 5},
    {"goal": 200, "reward": 10},
    {"goal": 300, "reward": 15},
    {"goal": 400, "reward": 20}
]

def reset_daily_missions():
    today = str(datetime.date.today())
    data["daily_missions"] = {
        "date": today,
        "missions": random.sample(MISSION_POOL, 2)
    }

    for user in data["users"]:
        data["users"][user]["daily_progress"] = 0
        data["users"][user]["daily_claimed"] = [False, False]

    data["last_reset"] = today
    save_data()

def check_daily_reset():
    today = str(datetime.date.today())
    if data["last_reset"] != today:
        reset_daily_missions()

# ---------- События ----------
@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user}")
    check_daily_reset()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id != CHAT_CHANNEL_ID:
        return

    if len(message.content.strip()) < MIN_LENGTH:
        return

    check_daily_reset()

    user_id = str(message.author.id)

    if user_id not in data["users"]:
        data["users"][user_id] = {
            "messages": 0,
            "balance": 0,
            "last_message_time": 0,
            "daily_progress": 0,
            "daily_claimed": [False, False],
            "test_given": False  # флаг для теста
        }

    user = data["users"][user_id]
    now = time.time()

    if now - user["last_message_time"] < COOLDOWN:
        return

    user["last_message_time"] = now
    user["messages"] += 1
    user["daily_progress"] += 1

    # ---------- Тест: начисляем за 1 сообщение ----------
    if user["messages"] >= 1 and not user.get("test_given", False):
        user["balance"] += MESSAGE_REWARD
        user["test_given"] = True
        await message.channel.send(
            f"{message.author.mention} получил {MESSAGE_REWARD} Robux (тест)!"
        )

    save_data()
    await bot.process_commands(message)

# ---------- Команды ----------
@bot.command()
async def balance(ctx):
    user_id = str(ctx.author.id)
    if user_id not in data["users"]:
        await ctx.send("У тебя нет данных.")
        return

    user = data["users"][user_id]
    await ctx.send(
        f"📊 Сообщений: {user['messages']}\n"
        f"💰 Robux: {user['balance']}"
    )

@bot.command()
async def missions(ctx):
    check_daily_reset()
    missions = data["daily_missions"]["missions"]
    user_id = str(ctx.author.id)

    if user_id not in data["users"]:
        await ctx.send("Нет данных.")
        return

    user = data["users"][user_id]
    progress = user["daily_progress"]

    text = ""
    for i, m in enumerate(missions):
        status = "✅ Получено" if user["daily_claimed"][i] else ""
        text += f"Миссия {i+1}: {progress}/{m['goal']} → {m['reward']} Robux {status}\n"

    await ctx.send(text)

@bot.command()
async def claim(ctx, mission_number: int):
    check_daily_reset()
    user_id = str(ctx.author.id)

    if mission_number not in [1, 2]:
        await ctx.send("Номер миссии 1 или 2.")
        return

    user = data["users"].get(user_id)
    if not user:
        return

    index = mission_number - 1
    mission = data["daily_missions"]["missions"][index]

    if user["daily_claimed"][index]:
        await ctx.send("Ты уже получил награду.")
        return

    if user["daily_progress"] >= mission["goal"]:
        user["balance"] += mission["reward"]
        user["daily_claimed"][index] = True
        save_data()
        await ctx.send(f"Награда получена! +{mission['reward']} Robux")
    else:
        await ctx.send("Миссия не выполнена.")

@bot.command()
async def transfer(ctx, member: discord.Member, amount: int):
    sender_id = str(ctx.author.id)
    receiver_id = str(member.id)

    if amount <= 0:
        await ctx.send("Сумма должна быть больше 0.")
        return

    if sender_id == receiver_id:
        await ctx.send("Нельзя переводить себе.")
        return

    if sender_id not in data["users"] or data["users"][sender_id]["balance"] < amount:
        await ctx.send("Недостаточно средств.")
        return

    if receiver_id not in data["users"]:
        data["users"][receiver_id] = {
            "messages": 0,
            "balance": 0,
            "last_message_time": 0,
            "daily_progress": 0,
            "daily_claimed": [False, False],
            "test_given": False
        }

    data["users"][sender_id]["balance"] -= amount
    data["users"][receiver_id]["balance"] += amount
    save_data()

    await ctx.send(f"Переведено {amount} Robux пользователю {member.mention}")

@bot.command()
async def withdraw(ctx):
    user_id = str(ctx.author.id)

    if user_id not in data["users"]:
        return

    user = data["users"][user_id]

    if user["balance"] < MIN_WITHDRAW:
        await ctx.send(f"Минимум для вывода: {MIN_WITHDRAW} Robux")
        return

    user["balance"] -= MIN_WITHDRAW
    save_data()

    admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
    if admin_channel:
        await admin_channel.send(
            f"Заявка на вывод от {ctx.author.mention} — {MIN_WITHDRAW} Robux"
        )

    await ctx.send("Заявка отправлена администратору.")

bot.run(TOKEN)