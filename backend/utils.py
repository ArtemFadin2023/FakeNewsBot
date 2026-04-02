import requests
from bs4 import BeautifulSoup
import re


# 🔥 очистка текста
def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s.,!?а-яА-Яa-zA-Z]", "", text)
    return text.strip()


# 🌐 безопасное извлечение текста
def extract_text_from_url(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        # ⏱️ короткий timeout = НЕ зависает
        response = requests.get(url, headers=headers, timeout=3)

        if response.status_code != 200:
            print("❌ HTTP ошибка:", response.status_code)
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # 🔥 ищем текст
        paragraphs = soup.find_all("p")

        if not paragraphs:
            return None

        text = " ".join(p.get_text() for p in paragraphs)

        text = clean_text(text)

        # ❗ защита от пустого / мусора
        if len(text) < 100:
            return None

        # 🔥 ограничение размера
        return text[:2000]

    except requests.exceptions.Timeout:
        print("⏳ Таймаут при загрузке сайта")
        return None

    except requests.exceptions.RequestException as e:
        print("❌ Ошибка запроса:", e)
        return None

    except Exception as e:
        print("❌ Общая ошибка:", e)
        return None