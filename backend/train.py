from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from transformers import Trainer, TrainingArguments

import torch
import pandas as pd
import json
import os
from sklearn.model_selection import train_test_split


# =========================
# 📥 загрузка данных
# =========================

data = []

# основной датасет
try:
    df = pd.read_csv("data/dataset.csv")

    for _, row in df.iterrows():
        data.append({
            "text": str(row["text"]),
            "label": int(row["label"])
        })

    print(f"✅ dataset: {len(data)}")

except Exception as e:
    print("❌ dataset error:", e)


# =========================
# 🔥 ДОБАВЛЯЕМ FEEDBACK
# =========================

if os.path.exists("feedback.json"):
    try:
        with open("feedback.json", "r", encoding="utf-8") as f:
            feedback = json.load(f)

        for item in feedback:
            label = 1 if item["label"] == "real" else 0

            data.append({
                "text": item["text"],
                "label": label
            })

        print(f"🔥 feedback добавлен: {len(feedback)}")

    except Exception as e:
        print("❌ feedback error:", e)


# =========================
# ⚠️ если данных мало
# =========================

if len(data) < 20:
    print("⚠️ мало данных для обучения")
    exit()


# =========================
# 🔀 разделение
# =========================

texts = [x["text"] for x in data]
labels = [x["label"] for x in data]

train_texts, val_texts, train_labels, val_labels = train_test_split(
    texts, labels, test_size=0.1
)


# =========================
# 🔤 токенизация
# =========================

tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")

train_encodings = tokenizer(train_texts, truncation=True, padding=True)
val_encodings = tokenizer(val_texts, truncation=True, padding=True)


# =========================
# 📦 Dataset
# =========================

class Dataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)


train_dataset = Dataset(train_encodings, train_labels)
val_dataset = Dataset(val_encodings, val_labels)


# =========================
# 🧠 модель
# =========================

model = DistilBertForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=2
)


# =========================
# ⚙️ настройки
# =========================

training_args = TrainingArguments(
    output_dir="./model",

    num_train_epochs=3,              # 🔥 больше эпох
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,

    evaluation_strategy="epoch",    # 🔥 проверка
    save_strategy="epoch",

    logging_dir="./logs",

    load_best_model_at_end=True,
)


# =========================
# 🧠 обучение
# =========================

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
)

trainer.train()


# =========================
# 💾 сохранение
# =========================

model.save_pretrained("model")
tokenizer.save_pretrained("model")

print("✅ Модель обновлена")