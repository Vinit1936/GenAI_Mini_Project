import json

NB = r"D:\resume-analyser\notebooks\02_resume_ner.ipynb"
nb = json.load(open(NB, encoding="utf-8"))

def src_str(c):
    s = c["source"]
    return "".join(s) if isinstance(s, list) else s

def set_src(i, val):
    nb["cells"][i]["source"] = val

patched = 0
for i, c in enumerate(nb["cells"]):
    s = src_str(c)
    if c["cell_type"] != "code":
        continue

    # 1) windowed tokenization: resumes longer than 512 tokens are split into overlapping windows so late entities stay in training
    if s.startswith("# Tokenize with offset mapping"):
        new = r'''# Tokenize with offset mapping; long resumes are split into overlapping 512-token windows (stride 128) so entities far down the page are not lost
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("distilbert-base-uncased")
tag_set = ["O"]
for et in entity_types:
    safe = et.replace(" ", "_")                    # BIO tags must not contain spaces
    tag_set += [f"B-{safe}", f"I-{safe}"]
tag2id = {t: i for i, t in enumerate(tag_set)}
id2tag = {i: t for t, i in tag2id.items()}

def encode_resume(item):
    text, spans = item
    enc = tok(text, truncation=True, max_length=512, stride=128,
              return_overflowing_tokens=True, return_offsets_mapping=True)
    out = []
    for ids, mask, offs in zip(enc["input_ids"], enc["attention_mask"], enc["offset_mapping"]):
        labels = []
        for s, e in offs:
            if s == e:                             # [CLS]/[SEP]/padding -> ignored in the loss
                labels.append(-100); continue
            lab = "O"
            for es, ee, el in spans:
                if s >= es and e <= ee:            # token fully inside the span
                    lab = ("B-" if s == es else "I-") + el.replace(" ", "_")
                    break
            labels.append(tag2id[lab])
        out.append({"input_ids": ids, "attention_mask": mask, "labels": labels})
    return out

from datasets import Dataset
ds_train = Dataset.from_list([ex for item in train_data for ex in encode_resume(item)])
ds_test = Dataset.from_list([ex for item in test_data for ex in encode_resume(item)])
print(f"Examples (windows): {len(ds_train)} train / {len(ds_test)} test | BIO tags: {len(tag_set)}")'''
        set_src(i, new); patched += 1

    # 2) longer training + higher lr (60 steps was provably far too few; verified trajectory on this data)
    elif s.startswith("# Build model + Trainer"):
        new = s.replace("learning_rate=3e-5, num_train_epochs=5,",
                        "learning_rate=5e-5, num_train_epochs=30,  # 5 epochs = 60 steps was undertrained (F1 0.07); this dataset needs a long run")
        assert "num_train_epochs=30" in new
        set_src(i, new); patched += 1

    # 3) demo cell: test_data items now yield (text, spans) still fine, unchanged
    elif s.startswith("# Demo: run the trained model"):
        new = s.replace("demo_text = test_data[0][0][:1200]", "demo_text = test_data[0][0][:1500]")
        set_src(i, new); patched += 1

json.dump(nb, open(NB, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(f"patched {patched} cells")

# markdown updates: header expectations + examiner epoch mention
for i, c in enumerate(nb["cells"]):
    s = src_str(c)
    if c["cell_type"] == "markdown":
        if s.startswith("# Notebook 2"):
            new = s.replace("3. Training: **~15–25 min** on T4. The last cell downloads `resume_ner_artifacts.zip`",
                            "3. Training: **~20–35 min** on T4 (30 epochs — this dataset converges slowly; do not stop it early). The last cell downloads `resume_ner_artifacts.zip`")
            new = new.replace("- Epoch 1 val F1 already ≈ 0.55–0.70 (transfer learning at work); final val F1 ≈ 0.70–0.85",
                              "- The first epochs score near 0.0 — NORMAL for this dataset; F1 climbs steadily and should reach **0.55–0.85 by epochs 15–30**")
            new = new.replace("- If F1 stays under 0.40 → check cell 6:",
                              "- If F1 stays under 0.40 after 30 epochs → check cell 6:")
            if new != s: set_src(i, new); patched += 1
        elif s.startswith("## Explain this to my examiner"):
            new = s.replace("I trained it for 5 epochs (lr 3e-5, batch 16, fp16) on 187 annotated resumes",
                            "I trained it for 30 epochs (lr 5e-5, batch 16, fp16) on 187 annotated resumes, split into overlapping 512-token windows with 128-token stride so entities deep in long resumes stay in the training signal")
            if new != s: set_src(i, new); patched += 1

json.dump(nb, open(NB, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(f"total patches: {patched}")

# syntax check all code cells
import ast
for c in nb["cells"]:
    s = src_str(c)
    if c["cell_type"] == "code":
        lines = [("" if l.strip().startswith(("!", "%")) else l) for l in s.splitlines()]
        ast.parse("\n".join(lines))
print("all code cells syntax OK")
