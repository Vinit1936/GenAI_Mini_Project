"""Regression test: hardened to_spans must survive the messy annotations real Dataturks data contains."""
import json, sys

NB2 = r"D:\resume-analyser\notebooks\02_resume_ner.ipynb"
nb = json.load(open(NB2, encoding="utf-8"))

src = None
for c in nb["cells"]:
    s = "".join(c["source"]) if isinstance(c["source"], list) else c["source"]
    if c["cell_type"] == "code" and s.startswith("# Convert each resume's annotations"):
        src = s
assert src, "cell not found"

text1 = "John Smith worked at Google as Software Engineer."
records = [
    # normal record
    {"content": text1, "annotation": [
        {"label": ["Name"], "points": [{"start": 0, "end": 9, "text": "John Smith"}]},
        {"label": ["Skills"], "points": []},                                   # empty points list
        {"label": [], "points": [{"start": 21, "end": 26, "text": "Google"}]},  # EMPTY label list -> must be skipped, not crash
        {"label": ["Companies worked at"], "points": [{"start": 21, "end": 26, "text": "Google"}]},
        {"label": ["Designation"], "points": [{"start": 31, "end": 48, "text": "Software Engineer"},
                                               {"start": 5, "end": 9, "text": None},   # None text -> skipped
                                               {"text": "no offsets here}]"}]},        # missing start/end -> skipped
    ]},
    # record with zero annotations at all
    {"content": "Just some resume text.", "annotation": []},
]

import pandas as pd
env = {"records": records, "pd": pd, "json": json}
exec(src, env)
parsed = env["parsed"]
assert len(parsed) == 2
t1, spans1 = parsed[0]
got = {(s, e, l) for s, e, l in spans1}
assert (0, 10, "Name") in got
assert (21, 27, "Companies worked at") in got
assert (31, 49, "Designation") in got
assert len(spans1) == 3, spans1                      # none of the junk annotations survived
assert parsed[1][1] == []                            # annotation-less record is fine
print("PASS: hardened to_spans survives empty labels, empty points, None text, missing offsets")
