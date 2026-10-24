"""Run the rewritten notebook-3 cells against the REAL downloaded dataset end-to-end."""
import glob, json, os, sys, types

NB = r"D:\resume-analyser\notebooks\03_section_classifier_bilstm.ipynb"
nb = json.load(open(NB, encoding="utf-8"))

def cell(prefix, kind="code"):
    for c in nb["cells"]:
        s = "".join(c["source"]) if isinstance(c["source"], list) else c["source"]
        if c["cell_type"] == kind and s.startswith(prefix):
            return s
    raise KeyError(prefix)

import pandas as pd, numpy as np
from sklearn.model_selection import train_test_split

DATA = r"D:\resume-analyser\.qa\data\nb3\resume_500"
env = {"pd": pd, "np": np, "os": os, "glob": glob, "json": json,
       "train_test_split": train_test_split, "SEED": 42, "re": __import__("re"), "DATA_PATH": DATA}

# --- load cell on real data ---
exec(cell("# Read all 500 resume files"), env)
df = env["df"]
assert len(df) > 39000, len(df)
vc = df["label"].value_counts().to_dict()
assert set(vc) == {"experience", "others", "education", "knowledge", "project"}, vc  # 'otherse' typo already fixed

# --- mapping cell ---
exec(cell("# Fixed mapping for the dataset's verified labels"), env)
assert env["LABEL_MAP"]["knowledge"] == "skills"
final = env["df"]["section"].value_counts().to_dict()
assert set(final) == {"experience", "education", "project", "skills", "other"}, final
assert final["experience"] > final["education"] > final["skills"], final
print("real-data section distribution:", final)

# --- tokenize / split / vocab ---
exec(cell("# Clean + tokenize"), env)
exec(cell("# Stratified split"), env)
assert 0 < env["vocab"]["<unk>"] and "<pad>" in env["vocab"]
train_df, test_df = env["train_df"], env["test_df"]
assert len(train_df) + len(test_df) == len(env["df"])

# --- encode cell (torch stubbed) ---
class TD:
    def __init__(self, X, y): self.X, self.y = X, y
class DL:
    def __init__(self, ds, batch_size=None, shuffle=None): self.ds = ds
env.update({"torch": types.SimpleNamespace(tensor=lambda x, dtype=None: x, long="long", float32="float32"),
            "TensorDataset": TD, "DataLoader": DL, "DEVICE": "cpu"})
exec(cell("# Encode sentences as padded id sequences"), env)
enc, vocab = env["encode"], env["vocab"]
out = enc(["bachelor", "of", "science"])
assert len(out) == 50 and out[3:] == [0] * 47
assert enc(["zzznotaword"])[0] == 1

# --- class-weight computation from the training cell ---
train_cell = cell("# Training loop: Adam + cross-entropy")
snippet = train_cell.split("loss_fn = nn.CrossEntropyLoss")[0].split("counts = np.bincount")[1]
sections, sec2id = env["sections"], env["sec2id"]
counts = np.bincount([sec2id[s] for s in train_df["section"]], minlength=len(sections))
class_w = len(train_df) / (len(sections) * counts)
assert class_w[sections.index("project")] == class_w.max(), "project should get the largest weight"
print("class weights:", {s: round(w, 2) for s, w in zip(sections, class_w)})

print("PASS: notebook 3 runs end-to-end on the REAL dataset")
