from flask import Flask, request, jsonify, render_template
from factcheck import build_answer

import json
import re
import os
from difflib import SequenceMatcher

print("🔥 APP START")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))

ADMIN_ID = 6533759527
ADMIN_PASSWORD = "2703"

HISTORY_FILE = os.path.join(BASE_DIR, "chat_history.json")
NEWS_FILE = os.path.join(BASE_DIR, "news_db.json")
USERS_FILE = os.path.join(BASE_DIR, "users.json")
ADMINS_FILE = os.path.join(BASE_DIR, "admins.json")


# =========================
# 💾 JSON
# =========================
def load_json(file):
    if not os.path.exists(file):
        return []
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# =========================
# 👑 ADMINS
# =========================
def load_admins():
    return [str(a) for a in load_json(ADMINS_FILE)]

def is_admin(user_id):
    return str(user_id) == str(ADMIN_ID) or str(user_id) in load_admins()

def add_admin(user_id):
    if not user_id:
        return

    admins = load_admins()

    if str(user_id) not in admins:
        admins.append(str(user_id))
        save_json(ADMINS_FILE, admins)


# =========================
# 👥 USERS
# =========================
def load_users():
    users = load_json(USERS_FILE)

    for u in users:
        if "source" not in u:
            u["source"] = "web" if str(u["id"]).startswith("web") else "tg"

    return users


def detect_type(user_id):
    return "web" if str(user_id).startswith("web") else "tg"


def add_user(user_id, username=None):
    if not user_id:
        return

    if is_admin(user_id):
        return

    users = load_users()
    user_type = detect_type(user_id)

    for u in users:
        if str(u["id"]) == str(user_id):
            u["source"] = user_type

            if user_type == "tg":
                u["username"] = username
            else:
                u["username"] = None

            save_json(USERS_FILE, users)
            return

    users.append({
        "id": user_id,
        "username": username if user_type == "tg" else None,
        "banned": False,
        "source": user_type
    })

    save_json(USERS_FILE, users)


def is_banned(user_id):
    for u in load_users():
        if str(u["id"]) == str(user_id):
            return u.get("banned", False)
    return False


def ban_user(user_id):
    if not user_id or is_admin(user_id):
        return

    users = load_users()

    for u in users:
        if str(u["id"]) == str(user_id):
            u["banned"] = True

    save_json(USERS_FILE, users)


def unban_user(user_id):
    users = load_users()

    for u in users:
        if str(u["id"]) == str(user_id):
            u["banned"] = False

    save_json(USERS_FILE, users)


# =========================
# 🧠 ЛОГИ И СТАТА
# =========================
@app.route("/stats")
def stats():
    history = load_json(HISTORY_FILE)

    fake = 0
    real = 0
    timeline = []

    for i, item in enumerate(history):
        txt = item.get("bot", "")

        if "ФЕЙК" in txt or "🚨" in txt:
            fake += 1
        else:
            real += 1

        timeline.append({
            "i": i,
            "fake": fake,
            "real": real
        })

    return jsonify({
        "count": len(history),
        "fake": fake,
        "real": real,
        "timeline": timeline,
        "history": history[-30:]
    })


# =========================
# 🚀 ANALYZE
# =========================
@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json() or {}

    text = data.get("text", "").strip()
    user_id = data.get("user_id")
    username = data.get("username")

    if not text:
        return jsonify({"result": "❌ Пустой запрос"})

    if user_id:
        add_user(user_id, username)

        if is_banned(user_id):
            return jsonify({"result": "🚫 Ты заблокирован"})

    result = build_answer(text)

    history = load_json(HISTORY_FILE)
    history.append({
        "user": text[:200],
        "bot": result
    })
    save_json(HISTORY_FILE, history)

    return jsonify({"result": result})


# =========================
# 🗑 CLEAR
# =========================
@app.route("/clear", methods=["POST"])
def clear():
    save_json(HISTORY_FILE, [])
    return jsonify({"status": "ok"})


# =========================
# 🌐 ROUTES
# =========================
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/admin")
def admin():
    password = request.args.get("pass")

    if password != ADMIN_PASSWORD:
        return "❌ Доступ запрещен"

    return render_template("admin.html")


@app.route("/users")
def users_api():
    return jsonify(load_users())


@app.route("/admins")
def admins_api():
    return jsonify(load_admins())


@app.route("/add_admin", methods=["POST"])
def add_admin_api():
    data = request.get_json() or {}
    add_admin(str(data.get("user_id")))
    return jsonify({"status": "ok"})


# =========================
# 🔐 BAN API
# =========================
def check_admin(data):
    return is_admin(data.get("admin_id"))


@app.route("/ban", methods=["POST"])
def ban_api():
    data = request.get_json() or {}

    if not check_admin(data):
        return jsonify({"status": "denied"})

    ban_user(data.get("user_id"))
    return jsonify({"status": "ok"})


@app.route("/unban", methods=["POST"])
def unban_api():
    data = request.get_json() or {}

    if not check_admin(data):
        return jsonify({"status": "denied"})

    unban_user(data.get("user_id"))
    return jsonify({"status": "ok"})


# =========================
# 🚀 RUN (FIX FOR RENDER)
# =========================
if __name__ == "__main__":
    print("🚀 SERVER STARTED")

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)