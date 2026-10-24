"""Evaluate the SHIPPED NER model locally on the exact same seeded test split Colab used.

Verdict logic:
- local F1 ~0.7-0.9  -> model is fine, Colab's final-eval cell is the bug
- local F1 ~0.0-0.1  -> the model itself is bad, training genuinely failed
"""
import json, glob, random, sys
import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split

NB2 = r"D:\resume-analyser\notebooks\02_resume_ner.ipynb"
MODEL_DIR = r"D:\resume-analyser\.qa\ner_check\model"
DATA = r"D:\resume-analyser\.qa\data\nb2\Entity Recognition in Resumes.json"

SEED = 42
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)

# --- reproduce to_spans exactly from the master notebook ---
nb = json.load(open(NB2, encoding="utf-8"))
src = None
for c in nb["cells"]:
    s = "".join(c["source"]) if isinstance(c["source"], list) else c["source"]
    if c["cell_type"] == "code" and s.startswith("# Convert each resume's annotations"):
        src = s
assert src
records = [json.loads(l) for l in open(DATA, encoding="utf-8-sig") if l.strip()]
env = {"records": records, "pd": pd, "json": json}
exec(src, env)
parsed = env["parsed"]
print(f"parsed {len(parsed)} resumes; entity types: {len(env['entity_types'])}")

# --- same seeded split as the notebook ---
train_data, test_data = train_test_split(parsed, test_size=0.15, random_state=SEED)
print(f"split: {len(train_data)} train / {len(test_data)} test (same seed as Colab)")

# --- load the shipped model ---
from transformers import AutoTokenizer, AutoModelForTokenClassification
tok = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForTokenClassification.from_pretrained(MODEL_DIR)
model.eval()
id2label = {int(k): v for k, v in model.config.id2label.items()}
label2id = model.config.label2id
print("model loaded; labels:", len(id2label))

# --- BIO encode using the SHIPPED config's label ids (self-consistent with model output) ---
def encode(item):
    text, spans = item
    enc = tok(text, truncation=True, max_length=512, return_offsets_mapping=True)
    labels = []
    for s, e in enc["offset_mapping"]:
        if s == e:
            labels.append(-100); continue
        lab = "O"
        for es, ee, el in spans:
            if s >= es and e <= ee:
                lab = ("B-" if s == es else "I-") + el.replace(" ", "_")
                break
        labels.append(label2id[lab])
    return enc, labels

from seqeval.metrics import precision_score, recall_score, f1_score, classification_report

y_true_all, y_pred_all = [], []
with torch.no_grad():
    for idx, item in enumerate(test_data):
        enc, labels = encode(item)
        ids = torch.tensor([enc["input_ids"]])
        mask = torch.tensor([enc["attention_mask"]])
        logits = model(input_ids=ids, attention_mask=mask).logits[0]
        pred = logits.argmax(dim=-1).tolist()
        # align on non-special positions (exactly what compute_metrics does)
        t = [id2label[i] for i in labels if i != -100]
        p = [id2label[j] for i, j in zip(labels, pred) if i != -100]
        y_true_all.append(t); y_pred_all.append(p)

P = precision_score(y_true_all, y_pred_all)
R = recall_score(y_true_all, y_pred_all)
F = f1_score(y_true_all, y_pred_all)
print(f"\nLOCAL EVAL OF SHIPPED MODEL:  precision={P:.4f}  recall={R:.4f}  f1={F:.4f}")
print("\nper-type report:")
print(classification_report(y_true_all, y_pred_all, digits=3))

# demo: show what it predicts on test resume #0
enc, labels = encode(test_data[0])
with torch.no_grad():
    logits = model(input_ids=torch.tensor([enc["input_ids"]]), attention_mask=torch.tensor([enc["attention_mask"]])).logits[0]
pred = logits.argmax(dim=-1).tolist()
toks = tok.convert_ids_to_tokens(enc["input_ids"])
found = [(t, id2label[j]) for t, i, j in zip(toks, labels, pred) if i != -100 and id2label[j] != "O"]
print("\ndemo entities on test resume #0 (first 20):")
for t, l in found[:20]:
    print(f"  {l:28s} {t}")

verdict = "MODEL_FINE_EVAL_BUG" if F > 0.5 else "MODEL_BAD"
print(f"\nVERDICT: {verdict}")
