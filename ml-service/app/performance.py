"""Model Performance endpoints: metrics from the training artifacts, for the dashboard's
performance page. Also serves the confusion-matrix / distribution PNGs the notebooks saved."""
import json
import os

from fastapi import HTTPException
from fastapi.responses import FileResponse

from . import config


def _read_json(path: str):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def performance_summary() -> dict:
    role = _read_json(config.ROLE_METRICS)
    ner = _read_json(config.NER_METRICS)
    section = _read_json(config.SECTION_METRICS)
    if not (role and ner and section):
        missing = [n for n, m in [("role", role), ("ner", ner), ("section", section)] if not m]
        raise HTTPException(503, f"metrics missing for: {missing} - check notebooks/artifacts")
    report = ""
    if os.path.exists(config.NER_REPORT):
        report = open(config.NER_REPORT, encoding="utf-8").read()
    return {
        "role_classifier": {
            "baseline": role["baseline"],
            "distilbert": role["distilbert"],
            "n_train": role["n_train"], "n_test": role["n_test"], "n_classes": role["n_classes"],
            "plots": ["cm_baseline.png", "cm_distilbert.png", "class_distribution.png"],
        },
        "resume_ner": {
            "precision": ner["precision"], "recall": ner["recall"], "f1": ner["f1"],
            "n_train_resumes": ner["n_train_resumes"], "n_test_resumes": ner["n_test_resumes"],
            "per_type_report": report,
            "plots": ["entity_distribution.png"],
        },
        "section_classifier": {
            "accuracy": section["accuracy"], "macro_f1": section["macro_f1"],
            "n_train": section["n_train"], "n_test": section["n_test"], "vocab_size": section["vocab_size"],
            "plots": ["cm_bilstm.png", "training_curves.png"],
        },
    }


def plot_file(model: str, name: str) -> FileResponse:
    folder = config.PLOT_DIRS.get(model)
    if not folder or ".." in name or "/" in name or "\\" in name or not name.endswith(".png"):
        raise HTTPException(404, "unknown plot")
    path = os.path.join(folder, name)
    if not os.path.exists(path):
        raise HTTPException(404, f"{model}/{name} not found")
    return FileResponse(path, media_type="image/png")
