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

    # 🔥 ФИКС СТАРЫХ ПОЛЬЗОВАТЕЛЕЙ
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
# 🧠 SIMILARITY
# =========================
def normalize(text):
    return re.sub(r"[^\w\s]", "", text.lower()).strip()

def similarity(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

# =========================
# 👍👎 ОБУЧЕНИЕ
# =========================
def clean_text_for_db(text):
    text = text.lower().strip()
    text = re.sub(r"https?://\S+", "", text)
    return text[:300]


def update_news(text, label):
    if not text or not label:
        return

    text = clean_text_for_db(text)
    news = load_json(NEWS_FILE)

    for item in news:
        if similarity(item["text"], text) > 0.7:
            if label == "real":
                item["likes"] += 1
            else:
                item["dislikes"] += 1
            save_json(NEWS_FILE, news)
            return

    news.append({
        "text": text,
        "likes": 1 if label == "real" else 0,
        "dislikes": 1 if label == "fake" else 0
    })

    save_json(NEWS_FILE, news)


def get_override_score(text):
    text = clean_text_for_db(text)
    news = load_json(NEWS_FILE)

    best = None
    best_score = 0

    for item in news:
        score = similarity(item["text"], text)
        if score > best_score:
            best_score = score
            best = item

    if best and best_score > 0.7:
        likes = best["likes"]
        dislikes = best["dislikes"]

        total = likes + dislikes
        if total == 0:
            return None

        return (likes - dislikes) / total

    return None

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
# 🔐 защита
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
# 🚀 RUN
# =========================
if __name__ == "__main__":
    print("🚀 SERVER STARTED")
    app.run(host="0.0.0.0", port=5000, debug=False)