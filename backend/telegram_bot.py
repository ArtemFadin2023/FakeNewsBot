import requests
import re
import time
import uuid
import os 

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InlineQueryResultArticle,
    InputTextMessageContent
)
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    filters,
    ContextTypes
)

TOKEN = "8745359881:AAGpHHpswwtJdsiiR-sPWhS-fYXL11C3Pp4"
BASE_URL = os.getenv("BASE_URL")
API_URL = f"{BASE_URL}/analyze"
WEB_URL = "https://your-app.onrender.com"

ADMIN_ID = 6533759527

user_last_time = {}

# =========================
# 🔥 АНТИСПАМ
# =========================
def is_spam(user_id):
    now = time.time()
    last = user_last_time.get(user_id, 0)
    user_last_time[user_id] = now
    return (now - last) < 1.5

# =========================
# 🔥 ФИЛЬТР
# =========================
def is_gibberish(text):
    if len(text) < 5:
        return True
    if not re.search(r"[а-яА-Яa-zA-Z]", text):
        return True
    letters = len(re.findall(r"[а-яА-Яa-zA-Z]", text))
    return letters / len(text) < 0.4

# =========================
# 🔒 ADMIN CHECK
# =========================
def is_admin(update):
    try:
        res = requests.get(f"{BASE_URL}/admins", timeout=5)
        admins = res.json()
        return update.effective_user.id == ADMIN_ID or str(update.effective_user.id) in admins
    except:
        return update.effective_user.id == ADMIN_ID

# =========================
# 📱 UI
# =========================
keyboard = [
    ["🧠 Проверить новость"],
    ["📊 Статус", "📈 График"],
    ["📸 Арсен", "🔒 Админ"]
]

markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# =========================
# 🚀 START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Fake News AI\n\nВыбери действие 👇", reply_markup=markup)

# =========================
# 🔒 ADMIN PANEL
# =========================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("❌ Нет доступа")
        return

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Открыть админку", url=f"{WEB_URL}/admin?pass=2703")]
    ])

    await update.message.reply_text(
        "🔒 Админ панель\n\n"
        "/users — список пользователей\n"
        "/addadmin ID — выдать админа\n"
        "/graph — статистика",
        reply_markup=kb
    )

# =========================
# 👥 USERS
# =========================
async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return

    res = requests.get(f"{BASE_URL}/users").json()

    for u in res:
        uid = u["id"]
        username = u.get("username")
        banned = u.get("banned", False)

        text = f"👤 ID: {uid}\n"
        if username:
            text += f"Username: @{username}\n"

        text += f"Статус: {'🚫 Бан' if banned else '✅ Активен'}"

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "✅ Разбан" if banned else "🚫 Бан",
                callback_data=f"{'unban' if banned else 'ban'}_{uid}"
            )]
        ])

        await update.message.reply_text(text, reply_markup=kb)

# =========================
# 🔁 BAN / UNBAN
# =========================
async def handle_admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(update):
        return

    uid = query.data.split("_")[1]  # 🔥 строка, не int

    if query.data.startswith("ban"):
        requests.post(f"{BASE_URL}/ban", json={
            "user_id": uid,
            "admin_id": ADMIN_ID
        })

        await query.edit_message_text(f"👤 ID: {uid}\nСтатус: 🚫 Бан")

    else:
        requests.post(f"{BASE_URL}/unban", json={
            "user_id": uid,
            "admin_id": ADMIN_ID
        })

        await query.edit_message_text(f"👤 ID: {uid}\nСтатус: ✅ Активен")

# =========================
# 👑 ADD ADMIN
# =========================
async def add_admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        target = context.args[0]

        requests.post(f"{BASE_URL}/add_admin", json={
            "user_id": target
        })

        await update.message.reply_text(f"✅ {target} теперь админ")
    except:
        await update.message.reply_text("❌ Пример: /addadmin 123456")

# =========================
# 📊 STATUS
# =========================
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        requests.get(BASE_URL, timeout=3)
        await update.message.reply_text("🟢 Сервер работает")
    except:
        await update.message.reply_text("🔴 Сервер оффлайн")

# =========================
# 📈 GRAPH
# =========================
async def graph(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return

    res = requests.get(f"{BASE_URL}/stats").json()

    await update.message.reply_text(
        f"📊\nФейк: {res['fake']}\nПравда: {res['real']}"
    )

# =========================
# 📸 АРСЕН
# =========================
async def arsen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("arsen.jpg", "rb") as photo:
            await update.message.reply_photo(photo)
    except:
        await update.message.reply_text("❌ Нет фото")

# =========================
# 🚀 INLINE (НОРМАЛЬНЫЙ)
# =========================
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query

    if not query or len(query) < 5:
        return

    try:
        res = requests.post(API_URL, json={"text": query}, timeout=4)
        text = res.json().get("result", "Ошибка")
    except:
        text = "⚠️ Ошибка"

    await update.inline_query.answer([
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="🧠 Проверить новость",
            description=query[:50],
            input_message_content=InputTextMessageContent(text)
        )
    ], cache_time=1)

# =========================
# 💬 MESSAGE
# =========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    text = update.message.text

    if not text:
        return

    # 🔥 КНОПКИ (СТРОГО)
    if text == "🧠 Проверить новость":
        await update.message.reply_text("✍️ Отправь текст")
        return

    if text == "📊 Статус":
        await status(update, context)
        return

    if text == "📈 График":
        await graph(update, context)
        return

    if text == "📸 Арсен":
        await arsen(update, context)
        return

    if text == "🔒 Админ":
        await admin_panel(update, context)
        return

    # =========================
    # 🔥 АНАЛИЗ
    # =========================
    if not is_admin(update) and is_spam(user_id):
        await update.message.reply_text("⚠️ Не спамь")
        return

    if is_gibberish(text):
        await update.message.reply_text("🤨 Отправь нормальный текст")
        return

    try:
        res = requests.post(API_URL, json={
            "text": text,
            "user_id": user_id,
            "username": username
        }, timeout=10)

        result = res.json().get("result", "Ошибка")

        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👍 Правда", callback_data="real"),
                InlineKeyboardButton("👎 Фейк", callback_data="fake")
            ]
        ])

        await update.message.reply_text(result, reply_markup=kb)

    except:
        await update.message.reply_text("⚠️ Сервер долго отвечает")

# =========================
# 🚀 RUN
# =========================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("users", users))
app.add_handler(CommandHandler("addadmin", add_admin_cmd))
app.add_handler(CommandHandler("graph", graph))

app.add_handler(CallbackQueryHandler(handle_admin_actions, pattern="^(ban_|unban_)"))
app.add_handler(InlineQueryHandler(inline_query))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🤖 BOT STARTED")

app.run_polling()