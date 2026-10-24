"""Paths and constants for the ML service. Everything resolves relative to this file,
so the service runs from any working directory."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # ml-service/
PROJECT_ROOT = os.path.dirname(BASE_DIR)                                        # resume-analyser/


def load_env_file() -> None:
    """Load ml-service/.env (KEY=value lines) into the environment. Real environment
    variables always win, so this only fills gaps. Lets the user configure the Groq
    key by editing a file instead of exporting env vars every session."""
    path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            val = val.strip().strip('"').strip("'")
            if val and key.strip() not in os.environ:
                os.environ[key.strip()] = val


load_env_file()
ARTIFACT_ZIPS = os.path.join(PROJECT_ROOT, "notebooks", "artifacts")
EXTRACT_DIR = os.path.join(BASE_DIR, "artifacts_extracted")                     # zips unpacked here on first run

ROLE_DIR = os.path.join(EXTRACT_DIR, "role_classifier", "model")
ROLE_LABELS = os.path.join(EXTRACT_DIR, "role_classifier", "labels.json")
ROLE_METRICS = os.path.join(EXTRACT_DIR, "role_classifier", "metrics.json")

NER_DIR = os.path.join(EXTRACT_DIR, "resume_ner", "model")
NER_TAGS = os.path.join(EXTRACT_DIR, "resume_ner", "tags.json")
NER_METRICS = os.path.join(EXTRACT_DIR, "resume_ner", "metrics.json")
NER_REPORT = os.path.join(EXTRACT_DIR, "resume_ner", "classification_report.txt")

SECTION_WEIGHTS = os.path.join(EXTRACT_DIR, "section_classifier", "bilstm_best.pt")
SECTION_VOCAB = os.path.join(EXTRACT_DIR, "section_classifier", "vocab.json")
SECTION_LABELS = os.path.join(EXTRACT_DIR, "section_classifier", "labels.json")
SECTION_METRICS = os.path.join(EXTRACT_DIR, "section_classifier", "metrics.json")

PLOT_DIRS = {
    "role_classifier": os.path.join(EXTRACT_DIR, "role_classifier"),
    "resume_ner": os.path.join(EXTRACT_DIR, "resume_ner"),
    "section_classifier": os.path.join(EXTRACT_DIR, "section_classifier"),
}

# Match-score weights (see scoring.py for the formulas)
W_SEMANTIC = 0.40
W_SKILL = 0.30
W_SECTION = 0.15
W_ROLE = 0.15

SENTENCE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Words removed from scored text so name/gender can never influence the score
GENDER_STOPWORDS = {
    "he", "she", "his", "her", "him", "hers", "himself", "herself", "male", "female",
    "man", "woman", "men", "women", "mr", "mrs", "ms", "miss", "sir", "madam",
    "gentleman", "lady", "guys", "guy", "gal", "boy", "girl", "father", "mother",
}
