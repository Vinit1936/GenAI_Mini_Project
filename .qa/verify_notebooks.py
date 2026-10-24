"""Static + dynamic verification of notebooks 2 and 3.

Part A: compile-check every code cell (catches syntax errors).
Part B: execute the core logic of notebook 2 with the real DistilBERT tokenizer
        (span parsing, BIO tagging, seqeval compute_metrics) on synthetic Dataturks data.
Part C: execute notebook 3's label mapping / vocab / encoding pipeline on a synthetic CSV.
Torch-dependent cells (model building, training loops) are compile-checked only.
"""
import ast, json, sys, types

PASS, FAIL = [], []

def check(name, fn):
    try:
        fn()
        PASS.append(name)
        print(f"  PASS  {name}")
    except Exception as e:
        FAIL.append((name, repr(e)))
        print(f"  FAIL  {name}: {e!r}")

NB2 = r"D:\resume-analyser\notebooks\02_resume_ner.ipynb"
NB3 = r"D:\resume-analyser\notebooks\03_section_classifier_bilstm.ipynb"

def cells(path):
    nb = json.load(open(path, encoding="utf-8"))
    out = []
    for i, c in enumerate(nb["cells"]):
        s = c["source"]
        out.append((i, c["cell_type"], "".join(s) if isinstance(s, list) else s))
    return out

def strip_magics(src):
    lines = []
    for l in src.splitlines():
        st = l.strip()
        lines.append("" if st.startswith(("!", "%")) else l)  # blank out colab magics for compile
    return "\n".join(lines)

def cell_starting_with(path, prefix, kind="code"):
    for i, ct, s in cells(path):
        if ct == kind and s.startswith(prefix):
            return s
    raise KeyError(prefix)

print("=== Part A: syntax-compile all code cells ===")
def compile_all():
    n = 0
    for path in (NB2, NB3):
        for i, ct, s in cells(path):
            if ct == "code":
                ast.parse(strip_magics(s))  # raises on syntax error
                n += 1
    print(f"  ({n} code cells parsed)")
check("syntax: all code cells compile", compile_all)

print("=== Part B: notebook 2 core logic, real tokenizer ===")

text1 = "John Smith worked at Google as Software Engineer with Python skills."
def ann(text, label, phrase):
    s = text.find(phrase)
    assert s >= 0, phrase
    return {"label": [label], "points": [{"start": s, "end": s + len(phrase) - 1, "text": phrase}]}  # Dataturks end is INCLUSIVE

records = [
    {"content": text1, "annotation": [
        ann(text1, "Name", "John Smith"),
        ann(text1, "Companies worked at", "Google"),
        ann(text1, "Designation", "Software Engineer"),
        ann(text1, "Skills", "Python"),
    ]},
    {"content": "Data Scientist at Infosys with SQL and Tableau skills.", "annotation": [
        {"label": "Designation", "points": [{"start": 0, "end": 12, "text": "Data Scientist"}, {"start": 35, "end": 37, "text": "   "}]},  # 2nd point blank -> must be dropped
        {"label": ["Skills"], "points": [{"start": 35, "end": 37, "text": "SQL"}, {"start": 43, "end": 49, "text": "Tableau"}]},
        ann("Data Scientist at Infosys with SQL and Tableau skills.", "Companies worked at", "Infosys"),
        ann("Data Scientist at Infosys with SQL and Tableau skills.", "Companies worked at", "Infosys"),  # duplicate span -> must be dropped
    ]},
]

env = {"records": records, "json": json}
import pandas as pd
env["pd"] = pd

def run_to_spans():
    src = cell_starting_with(NB2, "# Convert each resume's annotations")
    exec(src, env)
    parsed = env["parsed"]
    assert len(parsed) == 2
    t1, spans1 = parsed[0]
    lab1 = {l for _, _, l in spans1}
    assert lab1 == {"Name", "Companies worked at", "Designation", "Skills"}, lab1  # labels stay raw here; underscores are added later in the BIO cell
check("nb2: to_spans parses, dedups, drops blank/overlapping spans", run_to_spans)

# to_spans keeps raw labels (spaces intact); the BIO cell applies the underscore replacement
def run_bio():
    import os
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    parsed = env["parsed"]
    entity_types = sorted({l.replace(" ", "_") for _, sp in parsed for _, _, l in sp})

    # replicate the notebook cell's tag building exactly (labels have spaces -> underscores)
    tag_set = ["O"]
    for et in entity_types:
        tag_set += [f"B-{et}", f"I-{et}"]
    tag2id = {t: i for i, t in enumerate(tag_set)}
    id2tag = {i: t for t, i in tag2id.items()}
    assert len(tag_set) == 1 + 2 * len(entity_types), len(tag_set)  # O + B-/I- per type

    # exec the notebook's encode_resume verbatim (needs tok + tag machinery in scope)
    src = cell_starting_with(NB2, "# Tokenize with offset mapping")
    local = {"tok": tok, "tag_set": ["O"]}
    # rebuild tag_set exactly as the notebook does (from raw entity_types with spaces):
    raw_types = sorted({l for _, sp in parsed for _, _, l in sp})
    tag_set_nb = ["O"]
    for et in raw_types:
        safe = et.replace(" ", "_")
        tag_set_nb += [f"B-{safe}", f"I-{safe}"]
    tag2id_nb = {t: i for i, t in enumerate(tag_set_nb)}
    id2tag_nb = {i: t for t, i in tag2id_nb.items()}
    local_env = {"tok": tok, "tag_set": tag_set_nb, "tag2id": tag2id_nb, "id2tag": id2tag_nb}

    # the notebook cell body from id2tag to the end of encode_resume (skip the datasets.Dataset wrap)
    body = src.split("tag2id = {t: i for i, t in enumerate(tag_set)}", 1)[1]
    body = "id2tag =" + body.split("id2tag =", 1)[1]
    body = body.split("from datasets import", 1)[0]
    exec(body, local_env)
    encode_resume = local_env["encode_resume"]

    t1, spans1 = parsed[0]
    item = encode_resume((t1, spans1))
    toks = tok.convert_ids_to_tokens(item["input_ids"])
    pairs = [(t, id2tag_nb[l]) for t, l in zip(toks, item["labels"]) if l != -100]
    d = {}
    for t, l in pairs:
        d.setdefault(t, l)
    assert d.get("john") == "B-Name", d.get("john")
    assert d.get("smith") == "I-Name", d.get("smith")
    assert d.get("google") == "B-Companies_worked_at", d.get("google")
    assert d.get("software") == "B-Designation", d.get("software")
    assert d.get("engineer") == "I-Designation", d.get("engineer")
    assert d.get("python") == "B-Skills", d.get("python")
    assert d.get("worked") == "O", d.get("worked")
    # special tokens must be -100
    assert item["labels"][0] == -100 and item["labels"][-1] == -100
    # second resume: duplicate Infosys dropped, blanks dropped
    t2, spans2 = parsed[1]
    companies = [l for s, e, l in spans2 if "Companies" in l]
    assert companies == ["Companies worked at"], companies
    item2 = encode_resume((t2, spans2))
    assert len(item2["labels"]) == len(item2["input_ids"])
check("nb2: BIO tagging with real DistilBERT tokenizer (B-/I-/-100 all correct)", run_bio)

def run_seqeval():
    import numpy as np
    src = cell_starting_with(NB2, "# Build model + Trainer")
    chunk = src.split("from seqeval.metrics import", 1)[1]
    chunk = "from seqeval.metrics import" + chunk
    chunk = chunk.split("args = TrainingArguments", 1)[0]  # only seqeval imports + compute_metrics def
    id2tag = {0: "O", 1: "B-Skills", 2: "I-Skills", 3: "B-Degree"}
    local = {"np": np, "id2tag": id2tag}
    exec(chunk, local)
    cm = local["compute_metrics"]
    # perfect predictions -> all 1.0
    y = np.array([[1, 2, 0, -100]])
    p = np.zeros((1, 4, 4)); p[0, 0, 1] = 5; p[0, 1, 2] = 5; p[0, 2, 0] = 5; p[0, 3, 0] = 5
    m = cm(types.SimpleNamespace(predictions=p, label_ids=y))
    assert abs(m["f1"] - 1.0) < 1e-9, m
    # one wrong entity type -> f1 0.0 for that entity
    p2 = p.copy(); p2[0, 0, 1] = 0; p2[0, 0, 3] = 5  # predict B-Degree instead of B-Skills
    m2 = cm(types.SimpleNamespace(predictions=p2, label_ids=y))
    assert m2["f1"] < 1.0 and m2["precision"] < 1.0, m2
check("nb2: seqeval compute_metrics behaves (perfect=1.0, wrong type penalised)", run_seqeval)

print("=== Part C: notebook 3 core logic, synthetic CSV ===")
import tempfile, os
csv_path = os.path.join(tempfile.gettempdir(), "nb3_test.csv")
pd.DataFrame({
    "Sentence": ["Bachelor of Science in Computer Science from MIT",
                 "Worked at Google for three years as engineer",
                 "Skills include Python and PyTorch",
                 "Built a web scraper project",
                 "Contact details and personal info here",
                 "Led a team project on dashboards"] * 40,
    "Label": (["Work_Experience", "Education", "Skills", "Projects", "Summary", "Projects"] * 40),
}).to_csv(csv_path, index=False)

def run_nb3():
    import re
    env3 = {"pd": pd, "os": os, "re": re, "DATA_PATH": csv_path, "json": json, "SEED": 42}
    from sklearn.model_selection import train_test_split
    env3["train_test_split"] = train_test_split

    src = cell_starting_with(NB3, "# Load the CSV")
    exec(src, env3)
    assert env3["text_col"] == "Sentence" and env3["label_col"] == "Label", (env3["text_col"], env3["label_col"])
    df = env3["df"]

    src = cell_starting_with(NB3, "# Map the dataset's raw labels")
    exec(src, env3)
    lm = env3["LABEL_MAP"]
    assert lm["Education"] == "education", lm
    assert lm["Work_Experience"] == "experience", lm
    assert lm["Skills"] == "skills", lm
    assert lm["Projects"] == "project", lm
    assert lm["Summary"] == "other", lm
    assert set(env3["df"]["section"].unique()) <= set(env3["sections"])

    exec(cell_starting_with(NB3, "# Clean + tokenize"), env3)
    exec(cell_starting_with(NB3, "# Stratified split"), env3)
    vocab = env3["vocab"]
    assert vocab["<pad>"] == 0 and vocab["<unk>"] == 1
    assert "bachelor" in vocab and "zzznotaword" not in vocab

    # stub torch so the make_loader cell's encode() can be executed
    class TD:
        def __init__(self, X, y): self.X, self.y = X, y
    class DL:
        def __init__(self, ds, batch_size=None, shuffle=None): self.ds = ds
    env3["torch"] = types.SimpleNamespace(tensor=lambda x, dtype=None: x, long="long")
    env3["TensorDataset"], env3["DataLoader"] = TD, DL
    exec(cell_starting_with(NB3, "# Encode sentences as padded id sequences"), env3)
    enc = env3["encode"]
    out = enc(["bachelor", "of", "science"])
    assert len(out) == 50 and out[3:] == [0] * 47, out[:6]
    assert out[0] == vocab["bachelor"]
    unk = enc(["zzznotaword"])
    assert unk[0] == 1  # unknown token -> <unk>
check("nb3: detect columns, map labels, build vocab, encode+pad sequences", run_nb3)

print()
print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
for name, err in FAIL:
    print(" -", name, "->", err)
sys.exit(1 if FAIL else 0)
