# Training Notebooks — GenAI Resume Analyser

Run these in **Google Colab** in this exact order. Each notebook is self-contained:
install → download data (Kaggle API **or** manual upload) → clean/explore → train →
evaluate → save model + tokenizer + metrics.json + PNG plots → zip for download.

| # | Notebook | Model | Colab runtime | Training time | Expected result |
|---|----------|-------|---------------|---------------|-----------------|
| 1 | [01_role_classifier.ipynb](01_role_classifier.ipynb) | TF-IDF + LogReg **vs** fine-tuned DistilBERT | T4 GPU | ~25–40 min total | acc 0.90–0.98, macro-F1 0.88+ (dataset: snehaanbhawal, 2,400+ resumes) |
| 2 | [02_resume_ner.ipynb](02_resume_ner.ipynb) | DistilBERT token classification (BIO) | T4 GPU | ~15–25 min | entity F1 ≈ 0.70–0.85 (only 220 annotated resumes — small-data reality) |
| 3 | [03_section_classifier_bilstm.ipynb](03_section_classifier_bilstm.ipynb) | 2-layer BiLSTM + trained word embeddings | CPU ok / T4 faster | ~2–5 min | acc 0.75–0.90, macro-F1 0.70–0.88 |

## Per-notebook setup (do this once)
1. Kaggle → Settings → API → **Create New Token** → open `kaggle.json` (contains username + key)
2. Colab → 🔑 (Secrets) sidebar icon → add `KAGGLE_USERNAME` and `KAGGLE_KEY`
3. `Runtime` → `Change runtime type` → **T4 GPU** (not needed for notebook 3)
4. `Runtime` → `Run all`

No Kaggle credentials? Each notebook falls back to a manual-upload dialog — the download
link for each dataset is printed in its "Get the dataset" section.

## After training
Each notebook's last cell downloads a zip. Place all three here:

```
notebooks/artifacts/
├── role_classifier_artifacts.zip      (model/, labels.json, metrics.json, model_comparison.csv, PNGs)
├── resume_ner_artifacts.zip           (model/, tags.json, metrics.json, classification_report.txt, PNGs)
└── section_classifier_artifacts.zip   (bilstm_best.pt, vocab.json, labels.json, metrics.json, PNGs)
```

Part 2 (FastAPI + Next.js) loads models from these zips.

## Colab-timeout safety
All notebooks save per-epoch checkpoints under `/content/checkpoints/...` and auto-resume
from the newest one when you re-run training after a session crash. For extra safety on
long sessions, mount Drive and change each notebook's `output_dir` to a Drive path.

## Known honest caveats (say these to the examiner)
- **Notebook 1:** uses [snehaanbhawal's Resume Dataset](https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset)
  (2,400+ resumes, 24 balanced categories). Resume text is PDF-extracted, so some rows are noisy — the cleaning
  cell filters most of that. Classical ML often ties DistilBERT here; that's a valid finding, not a bug.
- **Notebook 2:** dataset was switched from `yashpwrr/resume-ner-training-dataset` to the official
  **Dataturks `resume-entities-for-ner`** mirror (220 resumes) — the yashpwrr dataset's schema could not be
  verified and its Hugging Face mirror is mislabeled chat data, not NER.
- **Notebook 3:** the section dataset's label names are undocumented; the notebook prints its
  label→section mapping at runtime — verify it once before trusting results.
