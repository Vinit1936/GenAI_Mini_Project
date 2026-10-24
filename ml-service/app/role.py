"""Role classifier: the fine-tuned DistilBERT from Notebook 1 (fallback: TF-IDF pipeline is
reported in /models/performance for comparison, but serving uses the transformer)."""
import json

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class RoleClassifier:
    def __init__(self, model_dir: str, labels_path: str):
        self.tok = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        self.model.eval()
        with open(labels_path, encoding="utf-8") as f:
            data = json.load(f)
        self.labels = data["labels"]
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

    def predict(self, text: str, max_length: int = 256) -> dict:
        """Returns the top role plus the top-3 probability distribution."""
        enc = self.tok(text, truncation=True, max_length=max_length, return_tensors="pt").to(self.device)
        with torch.no_grad():
            logits = self.model(**enc).logits[0]
        probs = torch.softmax(logits, dim=-1).cpu().tolist()
        ranked = sorted(range(len(probs)), key=lambda i: -probs[i])[:3]
        return {
            "role": self.labels[ranked[0]],
            "confidence": round(probs[ranked[0]], 4),
            "top3": [{"role": self.labels[i], "probability": round(probs[i], 4)} for i in ranked],
        }
