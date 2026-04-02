import torch
import os

print("📦 predict.py загружен")

model = None
tokenizer = None
loaded = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model")

device = torch.device("cpu")


def load_model():
    global model, tokenizer, loaded

    if loaded:
        return

    try:
        from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

        print("🔄 Загружаю модель...")

        tokenizer = DistilBertTokenizer.from_pretrained(MODEL_PATH)
        model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)

        model.to(device)
        model.eval()

        loaded = True
        print("✅ Модель загружена")

    except Exception as e:
        print("❌ Ошибка модели:", e)


def predict(text):
    try:
        load_model()

        if not model or not tokenizer:
            return {"fake": 0.5, "real": 0.5}

        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=256
        )

        with torch.no_grad():
            outputs = model(**inputs)

        probs = torch.nn.functional.softmax(outputs.logits, dim=1)

        return {
            "fake": float(probs[0][0]),
            "real": float(probs[0][1])
        }

    except Exception as e:
        print("❌ predict error:", e)
        return {"fake": 0.5, "real": 0.5}