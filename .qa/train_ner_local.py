"""Replicate notebook-2 training EXACTLY (seed, data, split, encode, Trainer config) on CPU.
Watch per-epoch eval F1 to decide: does the recipe work, and are 5 epochs enough?
"""
import json, glob, random
import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split

NB2 = r"D:\resume-analyser\notebooks\02_resume_ner.ipynb"
DATA = r"D:\resume-analyser\.qa\data\nb2\Entity Recognition in Resumes.json"
SEED = 42
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)

nb = json.load(open(NB2, encoding="utf-8"))
def cell(prefix):
    for c in nb["cells"]:
        s = "".join(c["source"]) if isinstance(c["source"], list) else c["source"]
        if c["cell_type"] == "code" and s.startswith(prefix):
            return s
    raise KeyError(prefix)

# --- notebook's parse + span cleaning, verbatim ---
records = [json.loads(l) for l in open(DATA, encoding="utf-8-sig") if l.strip()]
env = {"records": records, "pd": pd, "json": json}
exec(cell("# Convert each resume's annotations"), env)
parsed = env["parsed"]
entity_types = env["entity_types"]

train_data, test_data = train_test_split(parsed, test_size=0.15, random_state=SEED)
print(f"{len(train_data)} train / {len(test_data)} test, {len(entity_types)} entity types")

# --- notebook's BIO encode, verbatim (uses transformers tokenizer) ---
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("distilbert-base-uncased")
tag_set = ["O"]
for et in entity_types:
    safe = et.replace(" ", "_")
    tag_set += [f"B-{safe}", f"I-{safe}"]
tag2id = {t: i for i, t in enumerate(tag_set)}
id2tag = {i: t for t, i in tag2id.items()}

encode_src = cell("# Tokenize with offset mapping")
body = "id2tag =" + encode_src.split("id2tag =", 1)[1].split("from datasets import", 1)[0]
local = {"tok": tok, "tag_set": tag_set, "tag2id": tag2id, "id2tag": id2tag}
exec(body, local)
encode_resume = local["encode_resume"]

from torch.utils.data import Dataset as TorchDataset
class NERDataset(TorchDataset):
    def __init__(self, items): self.rows = [encode_resume(x) for x in items]
    def __len__(self): return len(self.rows)
    def __getitem__(self, i): return self.rows[i]

ds_train, ds_test = NERDataset(train_data), NERDataset(test_data)
print("encoded", len(ds_train), "/", len(ds_test), "| tags:", len(tag_set))

from transformers import AutoModelForTokenClassification, TrainingArguments, Trainer, DataCollatorForTokenClassification
from seqeval.metrics import precision_score, recall_score, f1_score
model = AutoModelForTokenClassification.from_pretrained("distilbert-base-uncased", num_labels=len(tag_set), id2label=id2tag, label2id=tag2id)

def compute_metrics(p):
    preds = np.argmax(p.predictions, axis=2)
    t, y = [], []
    for tr, pr in zip(p.label_ids, preds):
        t.append([id2tag[i] for i in tr if i != -100])
        y.append([id2tag[j] for i, j in zip(tr, pr) if i != -100])
    return {"precision": precision_score(t, y), "recall": recall_score(t, y), "f1": f1_score(t, y)}

data_collator = DataCollatorForTokenClassification(tokenizer=tok)
args = TrainingArguments(
    output_dir=r".qa/ckpt_ner_local",
    eval_strategy="epoch", save_strategy="epoch",
    learning_rate=5e-5, num_train_epochs=25,
    load_best_model_at_end=True, metric_for_best_model="f1", greater_is_better=True, save_total_limit=1,
    per_device_train_batch_size=16, per_device_eval_batch_size=16,
    weight_decay=0.01, warmup_ratio=0.1, fp16=False,     # CPU: fp16 off — the ONLY difference from Colab
    logging_steps=12, report_to="none", seed=SEED, use_cpu=True, disable_tqdm=True,
)
trainer = Trainer(model=model, args=args, train_dataset=ds_train, eval_dataset=ds_test,
                  processing_class=tok, data_collator=data_collator, compute_metrics=compute_metrics)
trainer.train()
out = trainer.predict(ds_test)
m = compute_metrics(out)
print(f"\nFINAL (25 epochs, lr 5e-5, best-checkpoint): precision={m['precision']:.4f} recall={m['recall']:.4f} f1={m['f1']:.4f}")
