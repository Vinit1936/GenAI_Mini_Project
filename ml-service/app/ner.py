"""Resume NER: the fine-tuned DistilBERT token classifier from Notebook 2.

Inference runs over overlapping 512-token windows (stride 128) so entities deep inside
long resumes are still found, then B/I tags are aggregated into entity spans."""
import json
from collections import defaultdict

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer

WINDOW = 512
STRIDE = 128
MIN_TOKENS = 1            # entities shorter than this (in wordpieces) are dropped
CONF_THRESHOLD = 0.60     # per-token confidence below this keeps the tag but is noted


class ResumeNER:
    def __init__(self, model_dir: str, tags_path: str):
        self.tok = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForTokenClassification.from_pretrained(model_dir)
        self.model.eval()
        with open(tags_path, encoding="utf-8") as f:
            data = json.load(f)
        self.entity_types = [t.replace("_", " ") for t in data.get("entity_types", [])]
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

    def _windows(self, text: str):
        enc = self.tok(
            text,
            truncation=True,
            max_length=WINDOW,
            stride=STRIDE,
            return_overflowing_tokens=True,
            return_offsets_mapping=True,
        )
        for ids, mask, offs in zip(enc["input_ids"], enc["attention_mask"], enc["offset_mapping"]):
            yield ids, mask, offs

    def extract(self, text: str) -> list:
        """Returns [{type, text, start, end, confidence}] over the whole document."""
        found = {}
        with torch.no_grad():
            for ids, mask, offs in self._windows(text):
                ids_t = torch.tensor([ids]).to(self.device)
                mask_t = torch.tensor([mask]).to(self.device)
                logits = self.model(input_ids=ids_t, attention_mask=mask_t).logits[0]
                probs = torch.softmax(logits, dim=-1)
                scores, preds = probs.max(dim=-1)

                current = None  # (etype, start_char, end_char, token_count, conf_sum)
                for (s, e), tag_id, conf in zip(offs, preds.tolist(), scores.tolist()):
                    if s == e:  # special/padding offsets
                        tag = "O"
                    else:
                        tag = self.model.config.id2label[tag_id]
                    if tag.startswith("B-"):
                        if current:
                            self._flush(current, found)
                        current = [tag[2:], s, e, 1, float(conf)]
                    elif tag.startswith("I-") and current and current[0] == tag[2:]:
                        current[2] = e
                        current[3] += 1
                        current[4] += float(conf)
                    else:
                        if current:
                            self._flush(current, found)
                        current = None
                if current:
                    self._flush(current, found)

        entities = []
        for (etype, s, e), (count, conf) in found.items():
            entities.append({
                "type": etype.replace("_", " "),
                "text": text[s:e].strip(),
                "start": s,
                "end": e,
                "confidence": round(conf / count, 3),
            })
        entities.sort(key=lambda x: x["start"])
        return entities

    @staticmethod
    def _flush(current, found):
        etype, s, e, count, conf = current
        if count >= MIN_TOKENS:
            key = (etype, s, e)
            old = found.get(key)
            if old is None or old[1] < conf:      # keep the most confident window's version
                found[key] = (count, conf)

    def by_type(self, text: str) -> dict:
        """Convenience view: {entity_type: [texts]} with de-duplicated lowercase values."""
        out = defaultdict(list)
        for ent in self.extract(text):
            val = ent["text"]
            low = val.lower()
            if low not in [v.lower() for v in out[ent["type"]]]:
                out[ent["type"]].append(val)
        return dict(out)
