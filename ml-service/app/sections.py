"""Section classifier: the 2-layer BiLSTM from Notebook 3.
Architecture copied verbatim from the training notebook so the checkpoint loads exactly."""
import json
import re

import torch
import torch.nn as nn


class SectionBiLSTM(nn.Module):
    def __init__(self, vocab_size, n_classes, emb_dim=100, hidden=128):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
        self.lstm = nn.LSTM(emb_dim, hidden, num_layers=2, bidirectional=True, batch_first=True, dropout=0.3)
        self.drop = nn.Dropout(0.3)
        self.out = nn.Linear(hidden * 2, n_classes)

    def forward(self, x):
        emb = self.emb(x)
        _, (h, _) = self.lstm(emb)
        feat = torch.cat([h[-2], h[-1]], dim=1)
        return self.out(self.drop(feat))


class SectionClassifier:
    def __init__(self, weights_path: str, vocab_path: str, labels_path: str):
        with open(vocab_path, encoding="utf-8") as f:
            self.vocab = json.load(f)
        with open(labels_path, encoding="utf-8") as f:
            meta = json.load(f)
        self.sections = meta["sections"]
        self.max_len = meta.get("max_len", 50)
        self.model = SectionBiLSTM(len(self.vocab), len(self.sections))
        self.model.load_state_dict(torch.load(weights_path, map_location="cpu"))
        self.model.eval()

    def _encode(self, tokens):
        ids = [self.vocab.get(t, 1) for t in tokens[: self.max_len]]
        return ids + [0] * (self.max_len - len(ids))

    def classify_lines(self, text: str) -> list:
        """One prediction per non-empty line: {line, section, confidence}."""
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if not lines:
            return []
        batch = torch.tensor(
            [self._encode(re.findall(r"[a-z]+", ln.lower())) for ln in lines], dtype=torch.long
        )
        with torch.no_grad():
            logits = self.model(batch)
            probs = torch.softmax(logits, dim=-1)
            conf, pred = probs.max(dim=-1)
        return [
            {"line": ln, "section": self.sections[p], "confidence": round(float(c), 3)}
            for ln, p, c in zip(lines, pred.tolist(), conf.tolist())
        ]

    def section_presence(self, text: str, lines: list | None = None) -> dict:
        """Which of the canonical sections appear anywhere in the resume."""
        if lines is None:
            lines = self.classify_lines(text)
        counts = {}
        for row in lines:
            counts[row["section"]] = counts.get(row["section"], 0) + 1
        # heading-text fallback: an explicit "EDUCATION / PROJECTS / ..." heading counts as
        # one line of that section even when the BiLSTM mislabels the heading itself
        import re as _re
        heading_hints = {
            "experience": r"\b(work experience|professional experience|employment|work history)\b",
            "education": r"\b(education|academics?)\b",
            "skills": r"\b(technical skills|skills)\b",
            "project": r"\bprojects?\b",
        }
        for sec_key, pat in heading_hints.items():
            if any(len(r["line"]) < 45 and _re.search(pat, r["line"], _re.I) for r in lines):
                counts[sec_key] = counts.get(sec_key, 0) + 1
        # experience/education/skills need >=2 lines; a single project line already counts
        present = {
            "experience": counts.get("experience", 0) >= 2,
            "education": counts.get("education", 0) >= 2,
            "skills": counts.get("skills", 0) >= 2,
            "project": counts.get("project", 0) >= 1,
        }
        present["other"] = counts.get("other", 0) > 0
        return {"presence": present, "line_counts": counts}
