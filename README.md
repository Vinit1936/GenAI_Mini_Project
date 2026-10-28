# Resume Analyser — GenAI Mini Project

Resume ↔ job-description match analysis powered by **four models trained/fine-tuned by the
author** (DistilBERT role classifier, DistilBERT NER, BiLSTM section classifier, TF-IDF
baseline) + MiniLM sentence embeddings + a Groq LLM advice layer.

📖 **Full project context, decisions, metrics and bug history: [project.md](project.md)**

## Run it (2 terminals)

**Prerequisites:** Python 3.10+ and Node.js 18+

```bash
git clone https://github.com/Vinit1936/GenAI_Mini_Project.git
cd GenAI_Mini_Project
```

**Terminal 1 — ML service** (run from repo root):

```bash
cd ml-service
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt  # first time only
uvicorn app.main:app --port 8000
```

*Note:* For optional AI suggestions, get a free key at https://console.groq.com/keys, copy `ml-service/.env.example` to `ml-service/.env` and paste the key; setting `GROQ_API_KEY` in the shell also works; the app works without it.

**Terminal 2 — website** (run from repo root):

```bash
cd web
npm install  # first time only
npm run dev
```

*Note:* The site calls the ML service at http://localhost:8000 by default; set `NEXT_PUBLIC_ML_API` to point elsewhere (this is read in `web/lib/api.js`).

Open **http://localhost:3000** → **upload your resume (PDF / DOCX / TXT)** or paste text,
add the job description (or click *load sample*) → **Analyse match**. The **Model
Performance** page shows every model's real training metrics and confusion matrices.
Scanned/image-only PDFs have no text layer — the app tells you to paste text instead.

## What's inside

```
notebooks/           3 Colab training notebooks + README + artifacts/ (the trained model zips)
ml-service/          FastAPI service: loads all models, /analyze, /models/performance
web/                 Next.js + Tailwind dashboard (score gauge, radar, entity highlights)
project.md           complete handoff document (datasets, configs, metrics, history)
.qa/                 verification scripts + local test harnesses (safe to ignore/delete)
```

## Syllabus coverage

| Topic | Where |
|---|---|
| NLP preprocessing | all notebooks: regex cleaning, tokenization, BIO tagging, vocab building |
| Classical ML text classification | TF-IDF + Logistic Regression baseline (67.8% acc) |
| Transformers & fine-tuning | DistilBERT role classifier (**81.5% acc**) + DistilBERT NER (entity F1 46%) |
| Embeddings | TF-IDF sparse + BiLSTM word embeddings + MiniLM sentence embeddings |
| RNN / LSTM | 2-layer BiLSTM section classifier (**78.9% acc**, 0.71 macro-F1) |
| LLM prompting | Groq layer grounded in NER output + missing skills |

**Fairness:** names, emails, phones and gendered words are stripped from all scored text
(`ml-service/app/scoring.py::strip_personal`) — visible entities never influence the score.
