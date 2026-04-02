import requests
import re

API_KEY = "682871dfca05d3f81f64f1086ec9b35c47e72e83"

# =========================
# 🔥 доверенные источники (FIX)
# =========================
TRUSTED_SITES = [
    "bbc.com",
    "reuters.com",
    "cnn.com",
    "nytimes.com",
    "theguardian.com",
    "forbes.com",
    "bloomberg.com",
    "wsj.com",
    "apnews.com",
    "rbc.ru",
    "ria.ru",
    "tass.ru",
    "lenta.ru",
    "gazeta.ru",
    "interfax.ru",
    "vedomosti.ru",
    "wikipedia.org"
]


def is_trusted(url):
    if not url:
        return False
    return any(site in url for site in TRUSTED_SITES)


# =========================
# 🔍 поиск (БЫСТРЫЙ)
# =========================
def google_search(text):
    try:
        url = "https://google.serper.dev/search"

        payload = {
            "q": text,
            "num": 5
        }

        headers = {
            "X-API-KEY": API_KEY,
            "Content-Type": "application/json"
        }

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=10
        )

        data = response.json()

        results = []

        for item in data.get("organic", []):
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "url": item.get("link", ""),
                "trusted": is_trusted(item.get("link", ""))
            })

        return results

    except Exception as e:
        print("❌ Serper error:", e)
        return []


# =========================
# 🧠 анализ (БЫСТРЫЙ И СТАБИЛЬНЫЙ)
# =========================
def build_answer(text, ai_result=None):

    results = google_search(text)

    trusted_count = 0
    combined_text = ""
    sources = ""

    if results:
        for r in results:
            title = r["title"]
            snippet = r["snippet"]
            url = r["url"]

            if r["trusted"]:
                sources += f"\n🔹 ✅ {title}\n{snippet}\n🌐 {url}\n"
                trusted_count += 1
            else:
                sources += f"\n🔹 {title}\n{snippet}\n🌐 {url}\n"

            combined_text += " " + title.lower() + " " + snippet.lower()
    else:
        sources = "\n❌ Нет подтверждений в интернете"


    # 🔢 проверка чисел
    numbers = re.findall(r"\d+", text.lower())

    number_mismatch = False
    if numbers:
        mismatch = sum(1 for n in numbers if n not in combined_text)
        number_mismatch = mismatch > len(numbers) * 0.7


    # 🧠 логика
    if trusted_count >= 2:
        verdict = "🟢 ПОДТВЕРЖДЕНО ИСТОЧНИКАМИ"
        percent = 90

    elif trusted_count == 1:
        if number_mismatch:
            verdict = "⚠️ Данные могут быть искажены"
            percent = 60
        else:
            verdict = "⚠️ Один источник — нужна проверка"
            percent = 65

    elif number_mismatch:
        verdict = "⚠️ Возможно ошибка в цифрах"
        percent = 50

    elif results:
        verdict = "🟡 Есть упоминания, но слабые"
        percent = 55

    else:
        verdict = "❓ НЕИЗВЕСТНО"
        percent = 50


    return f"""
🧠 Результат анализа:

{verdict}

📊 Уверенность: {percent}%

🌐 Проверка:
{sources}
"""