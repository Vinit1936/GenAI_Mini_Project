# Resume Analyser — Full Project Context (handoff document)

> **Purpose of this file:** complete, self-contained context on what this project is, every
> decision made, every bug fixed, and exactly what remains. If work continues with a
> different AI/developer, this file plus the code should be everything needed.

**Last updated:** 2026-10-24 · **Owner:** Vinit (GenAI subject mini project)

---

## 1. What the project is

A **Resume Analyser website** for a university GenAI subject. Hard requirement from the
examiner: **real ML models trained by the student** (not an LLM wrapper), clearly covering
syllabus topics: NLP preprocessing, classical ML text classification, transformers &
fine-tuning, embeddings, RNN/LSTM, and LLM prompting.

User flow: paste resume text + job description (JD) → dashboard shows overall match score
(0–100) with breakdown, radar chart, highlighted entities on the resume, predicted role,
matched/missing skills, LLM rewrite suggestions, and a "Model Performance" page with real
training metrics and confusion matrices.

### Syllabus → component mapping (the examiner story)

| Syllabus topic | Where it lives | Evidence |
|---|---|---|
| NLP preprocessing | All notebooks (regex cleaning, tokenization, BIO tagging, vocab) | notebook cells + cleaning code |
| Classical ML classification | Notebook 1 baseline: TF-IDF + Logistic Regression | metrics.json: acc 0.678 / macro-F1 0.654 |
| Transformers & fine-tuning | Notebook 1 (DistilBERT seq classification) + Notebook 2 (DistilBERT token classification) | acc 0.815 / macro-F1 0.738 ; NER F1 0.46 |
| Embeddings | TF-IDF sparse + BiLSTM trained word embeddings + MiniLM sentence embeddings (match score) | three distinct uses of "embeddings" |
| RNN/LSTM | Notebook 3: 2-layer BiLSTM section classifier | acc 0.789 / macro-F1 0.712 |
| LLM prompting | Groq API layer (llm.py): grounded prompt with NER output + missing skills | suggestions in dashboard |

---

## 2. Architecture

```
Google Colab (T4)                     Local machine (D:\resume-analyser)
----------------------                --------------------------------------------
01_role_classifier.ipynb   ──zip──►  notebooks/artifacts/role_classifier_artifacts.zip
02_resume_ner.ipynb        ──zip──►  notebooks/artifacts/resume_ner_artifacts.zip
03_section_classifier…ipynb ─zip──►  notebooks/artifacts/section_classifier_artifacts.zip
                                                │
                                                ▼  (auto-extracted at startup)
                                      ml-service/  (FastAPI, port 8000)
                                      loads all 3 models + sentence-transformers
                                      endpoints: /health /analyze /models/performance
                                                 /models/plots/{model}/{name}
                                                │
                                                ▼  (fetch from browser, CORS enabled)
                                      web/  (Next.js 14 + Tailwind, port 3000)
                                      dashboard + Model Performance page
                                      + Groq suggestions (server-side call in ml-service)
```

- **Score formula** (scoring.py): `40% semantic similarity (MiniLM cosine resume↔JD) +
  30% skill overlap + 15% section completeness + 15% role alignment`, ×100.
- **Privacy rule:** before scoring, names (NER `Name` entities), emails, phone-like
  numbers, URLs and gendered words are stripped from the text models see
  (`strip_personal()`). Entities still shown in UI, but never influence the score.
- **Groq:** called server-side in ml-service (`app/llm.py`), needs env var `GROQ_API_KEY`
  (get free at console.groq.com; model default `llama-3.1-8b-instant`, override with
  `GROQ_MODEL`). Fails gracefully — no key / rate limit → dashboard still works, empty
  suggestions.

---

## 3. Datasets (final choices + why; includes dead ends)

| Model | Dataset | Source | Size | Notes |
|---|---|---|---|---|
| Role classifier | **snehaanbhawal Resume Dataset** | kaggle `snehaanbhawal/resume-dataset`, file `data.json` | 2,483 usable resumes, 24 balanced categories | livecareer.com; fields `Resume_str`, `Category` (UPPERCASE → `.str.title()` applied). Chosen over jillanisofttech's 962-resume `UpdatedResumeDataSet.csv` (same 24 classes, 2.5× more data) |
| Resume NER | **Dataturks Resume Entities for NER** | kaggle `dataturks/resume-entities-for-ner`, file `Entity Recognition in Resumes.json` (JSONL, filename contains spaces) | 220 resumes, 3,444 usable spans | fields `content` + `annotation[]` with `label` (sometimes EMPTY list!) and `points[{start,end,text}]` where **end is INCLUSIVE** (+1 needed). Entity types: College Name, Companies worked at, Degree, Designation, Email Address, Graduation Year, Location, Name, Skills, UNKNOWN(junk, 2), Years of Experience |
| Section classifier | **chingkuangkam Resume Text Classification** | kaggle `chingkuangkam/resume-text-classification-dataset` | 500 txt files in `resume_500/`, 40,004 lines | **NOT a CSV!** Each line: `position \t section \t text` (split with maxsplit=2). Sections: experience 18471, others 10581, education 6190, knowledge 4049, project 713, `otherse`×1 (typo→others). **knowledge = the TECHNICAL SKILLS block → maps to `skills`** |

### Dead ends (do not revisit)
- `yashpwrr/resume-ner-training-dataset` (Kaggle): schema unverifiable; its HF mirror
  `yashpwr/resume-ner-training-data` is **mislabeled chat/summary data, zero NER labels**.
- `Mehyaar/Annotated_NER_PDF_Resumes` (HF, 5,029 resumes): **skills-only** annotations
  (`SKILL: python`), no companies/degrees/designations — useless for multi-entity NER.
- jillanisofttech `UpdatedResumeDataSet.csv`: works but only 962 rows; superseded.
- jainishkumar resume–JD matching dataset (500 pairs): noted as optional future eval of
  the match scorer; not used.

---

## 4. Models — final configs and ACTUAL measured results

### 4.1 Role classifier (`notebooks/01_role_classifier.ipynb`) — DONE ✅
- Pipeline: clean (URLs/emails/symbols stripped, lowercase) → stratified 80/20 →
  (a) TF-IDF 5000 word+bigram + LogisticRegression(class_weight=balanced);
  (b) DistilBERT-base-uncased, 4 epochs, lr 2e-5, batch 16, fp16, max_len 256.
- **Results (metrics.json):** TF-IDF acc 0.6781 / macro-F1 0.6536 ·
  DistilBERT **acc 0.8149 / macro-F1 0.7383** (transformer clearly wins → good viva point).
- Artifacts: model/ (DistilBERT+tokenizer), labels.json (24 classes),
  metrics.json, model_comparison.csv, cm_baseline.png, cm_distilbert.png, class_distribution.png.

### 4.2 Resume NER (`notebooks/02_resume_ner.ipynb`) — DONE ✅ (after a saga, see §6)
- BIO tagging via offset_mapping; `-100` on special tokens; spans cleaned (empty labels,
  blank/duplicate/overlapping spans dropped; inclusive end +1).
- DistilBERT token classification, **23 tags**, **25 epochs, lr 5e-5**, batch 16, fp16,
  load_best_model_at_end on eval F1.
- **Results (metrics.json):** precision 0.4218, recall 0.5057, **F1 0.4599**.
  Per-type F1: Name 0.896, Location 0.719, Companies_worked_at 0.474, Email 0.460,
  Designation 0.452, Degree 0.417, College_Name 0.245, Graduation_Year 0.207,
  **Skills 0.112 (weak — see fallback in §5)**, Years_of_Experience 0.0 (1 example).
- Known data caveats: 28% of spans fall beyond the 512-token truncation; 5.7% of span
  starts misalign with token boundaries; dataset is tiny → 0.46 F1 is honest for 220 docs.
  **Prepared but NOT applied** (optional future upgrade): sliding-window tokenization
  (max_length 512, stride 128, return_overflowing_tokens) to recover truncated entities —
  draft code exists in git history of this file's creation, see also
  `.qa/train_ner_local.py`.
- Artifacts: model/, tags.json (tag list + id2tag + entity_types), metrics.json,
  classification_report.txt, entity_distribution.png.

### 4.3 Section classifier (`notebooks/03_section_classifier_bilstm.ipynb`) — DONE ✅
- BiLSTM: Embedding(vocab≈14.7k,100,padding_idx=0) → LSTM(100,128,2 layers,bidirectional,
  dropout .3, batch_first) → concat last fwd+bwd hidden → Dropout .3 → Linear(256→5).
  Adam lr 1e-3, 10 epochs, batch 64, max_len 50, regex tokenizer `[a-z]+`,
  **class-weighted CrossEntropyLoss** (weights ≈ experience .41 / education 1.49 /
  project 10.71 / skills 1.87 / other .78), best-F1 checkpoint kept.
- **Results:** accuracy 0.7894, macro-F1 0.7115.
- Artifacts: bilstm_best.pt, vocab.json, labels.json (sections + raw_label_map + max_len),
  metrics.json, cm_bilstm.png, training_curves.png.
- **Architecture class copied verbatim into `ml-service/app/sections.py` — keep in sync
  if notebook changes.**

### 4.4 Sentence embeddings (no training)
`sentence-transformers/all-MiniLM-L6-v2` (downloaded at service startup, ~90 MB, needs
internet on first run). Used for semantic similarity + role alignment.

---

## 5. ml-service (FastAPI) — COMPLETE & SMOKE-TESTED ✅

Location: `ml-service/` — run: `pip install -r requirements.txt` then
`uvicorn app.main:app --port 8000` (from `ml-service/`). Startup takes ~10–15 s
(extracts zips once into `ml-service/artifacts_extracted/`, cached by `.extracted_from`
marker; replace a zip → re-extracts automatically).

**OPS NOTE (2026-10-24):** on this machine `uvicorn` is NOT on PATH (a background
restart died with exit 127 that way) and the system Pythons (3.11/3.13) lack the deps.
The working env is the project venv `D:\resume-analyser\.testenv` (.testenv has
torch 2.14.1+cpu / transformers 5.20.2 — fine for inference; the `>=4.44,<5` pin only
matters for the TRAINING notebooks). GROQ_API_KEY loads from `ml-service/.env`.
**Start detached** — agent background bash tasks get reaped and kill hosted servers:
```
powershell -NoProfile -Command "Start-Process -FilePath 'D:\resume-analyser\.testenv\Scripts\python.exe' -ArgumentList '-m','uvicorn','app.main:app','--port','8000','--host','127.0.0.1' -WorkingDirectory 'D:\resume-analyser\ml-service' -WindowStyle Hidden -RedirectStandardOutput 'D:\resume-analyser\.qa\data\mlservice.log' -RedirectStandardError 'D:\resume-analyser\.qa\data\mlservice.err.log'"
```
(plain interactive use: `cd ml-service && ../.testenv/Scripts/python.exe -m uvicorn app.main:app --port 8000`)

Files: `requirements.txt`, `app/{__init__,config,loaders,role,ner,sections,scoring,performance,llm,main}.py`.

### Endpoints
- `GET /health` → `{status:"ok", models:{...}}`
- `POST /extract` (multipart `file`) → `{text, filename, characters}` — PDF (pypdf),
  DOCX (python-docx, incl. table cells), TXT. Guards: 15 MB max, 400 unsupported type,
  422 unreadable or <100 extracted chars (scanned PDFs). Tested in `.qa/test_upload.py`.
- `POST /analyze` `{resume_text, job_description, want_suggestions=true}` → see shape below
- `GET /models/performance` → metrics of all 3 models + NER per-type report text + plot filenames
- `GET /models/plots/{role_classifier|resume_ner|section_classifier}/{*.png}` → image

### /analyze response shape (web app depends on this)
```jsonc
{
  "overall_score": 84.3,
  "breakdown": {
    "semantic_similarity": {"score": 73.3, "weight": 0.4},
    "skill_overlap": {"score": 100.0, "weight": 0.3, "matched": ["python", ...], "missing": ["gcp", ...]},
    "section_completeness": {"score": 100.0, "weight": 0.15, "present": [...], "missing": [...]},
    "role_alignment": {"score": 66.6, "weight": 0.15}
  },
  "predicted_role": {"role": "Information-Technology", "confidence": 0.1061,
                     "top3": [{"role": "...", "probability": 0.1061}, ...]},
  "entities": [{"type": "Name", "text": "Maria Rodriguez", "start": 0, "end": 15, "confidence": 0.99}, ...],
  "sections": {"presence": {"experience": true, ...}, "line_counts": {"experience": 12, ...}},
  "privacy": {"names_stripped": 1, "scored_text_length": 914},
  "suggestions": {"available": false, "reason": "GROQ_API_KEY not set", "advice": []}
}
```

### Key implementation details a future dev must know
- **NER inference is windowed** (512 tokens, stride 128, `return_overflowing_tokens`) —
  entities deep in long resumes are found; duplicate spans across windows resolved by
  highest mean confidence.
- **Skill extraction fallback** (because NER Skills F1 is only 0.11): skills come from
  NER `Skills` entities ∪ phrases harvested from lines the **BiLSTM labels `skills`**
  (split on `, ; • | · / ( ) or`, keep 1–5 word phrases, lowercase, drop generic words
  list in `scoring.py::_GENERIC`). JD skills from NER on JD ∪ harvest under
  Requirements/Skills/Qualifications headings. matched = resume skills named in JD;
  missing = JD skills not in resume. Smoke test: matched python/pytorch/docker/aws/sql/
  pandas/tableau, missing gcp/machine-learning — correct.
- Section presence thresholds: experience/education/skills ≥2 lines, **project ≥1 line**.
- CORS allows `http://localhost:3000` and `http://127.0.0.1:3000`.
- Tested end-to-end locally (`.qa/smoke_test_service.py`, TestClient): all endpoints OK,
  sample analysis = 84.3 overall.

---

## 6. Bug history (so the same traps are never re-triggered)

1. **Colab AI assistant edited cells** in the user's Colab copies twice (changed dict keys
   `content`→`context`, removed `[0]` from label lists, etc.). Rule: never accept Colab AI
   cell edits; master notebooks live in `D:\resume-analyser\notebooks\`.
2. **Missing GPU:** fresh Colab notebook upload resets runtime to CPU; `fp16=True` then
   dies instantly. Fix: notebook 2 prints device and asserts CUDA with plain-English msg;
   fp16 conditional.
3. **Missing `DataCollatorForTokenClassification`:** default Trainer collator does NOT pad
   labels → `ValueError ... expected sequence of length 512 ... got 149` at first batch.
   Fix: explicit `data_collator=DataCollatorForTokenClassification(tokenizer=tok)` in
   notebook 2 AND at inference NER is manual so unaffected.
4. **Empty `label: []` annotations** in Dataturks JSON crashed `ann["label"][0]`
   (IndexError). Fix: hardened `to_spans` skips empty/unlabeled/blank/None/missing-offset
   annotations (regression-tested in `.qa/test_to_spans.py`).
5. **Stale-checkpoint zip incident:** re-running "Run all" over a finished run recreated
   a random-head model + auto-resume did 0 steps → bad model zipped silently (F1 0.026).
   Fix: train cell now WIPES `output_dir` each run + eval cell has
   `assert final_f1 > 0.40` with an explanatory message before saving.
6. **Undertrained recipe (root cause of the 0.07 F1):** 5 epochs = only 60 optimizer steps
   on 187 resumes. Reproduced locally bit-for-bit (F1 0.0736 = Colab's 0.0736). Fix:
   25 epochs + lr 5e-5 → F1 0.46. Lesson: **verify training recipes by local replication
   before telling the user expected numbers.**
7. **transformers 5.x renamed TrainingArguments args** (`warmup_ratio` gone, etc.) —
   keep pins `"transformers>=4.44,<5"` everywhere (ml-service requirements.txt too).
8. **notebook 3 dataset has no CSV** — it's 500 txt files with `position\tsection\ttext`;
   load cell rewritten accordingly; label `knowledge`→`skills` mapping is VERIFIED.
9. BOM tolerance (`utf-8-sig`), latin-1 CSV fallback, deterministic globs — all patched in.

---

## 7. Current status & what remains

**UI REDESIGN v2 (2026-10-24, "SaaS product flow" per user spec + pasted Framer-style design.md):**
- Design system in `globals.css` follows design.md: near-black canvas `#0b0b0e`, surface-1/2
  lifts, hairline borders, white pill CTAs (`pill-primary/secondary`), charcoal cards
  20px radius, **gradient spotlight cards** (magenta/orange/violet) used sparingly, accent
  blue `#0099ff` only for selection/focus, Inter Variable with `cv01/cv05/cv09/cv11/ss03/ss07/tnum`,
  display type with −4.5% tracking.
- **Flow**: `/` landing (hero + upload CTA + stats strip + features bento with 2 spotlight
  cards + how-it-works + CTA band) → upload extracts text → `/analyse` wizard:
  step 1 resume (upload/paste fallback), step 2 JD (6 preset roles in `lib/presets.js` +
  paste-your-own), step 3 `Analyzing.jsx` scan-beam animation (min 4.2 s), step 4 results:
  LEFT `ResumeXray.jsx` (**rough.js double-stroke hand-drawn ellipses** over NER entities +
  marker highlights + toggle "Section map" per-line BiLSTM view; svg sized to
  scrollWidth/scrollHeight, redraw on font-load/resize) — RIGHT `ResultsPanel.jsx`
  (ATS Match Score ring + component weight bars, role card, radar, skill coverage,
  sections, Groq suggestions, copy/download report).
- `/performance` (Model card) moved OUT of the nav; linked from footer — still fully styled for the viva.
- **DEMO RESUMES (2026-10-24)**: 5 engineered demo PDFs in `C:\Users\vinit\Downloads`
  (generator: `.qa/make_demo_resumes.py`) for viva demos — pair each with its preset role
  in the wizard: strong-data-scientist→Data Scientist (≈84), frontend-developer→Frontend
  Developer (≈79), weak-vague→Data Analyst (≈43), fresh-graduate→Data Analyst (≈75),
  ml-engineer→ML Engineer (≈83). While validating these, `_harvest_section_skills` gained
  a second signal: harvest the 1–2 content lines directly AFTER a "SKILLS" heading
  (position-based), because the BiLSTM sometimes fails to label comma-list skill lines
  as `skills` (was causing skills=0 on well-formed resumes).
- **DIAGNOSIS + REWRITES (2026-10-24 v6)**: right panel rebuilt as a clear report.
  Server: `coach.py::build_diagnosis` returns `{working:[...], problems:[{kind,severity,
  title,detail,fix}]}` — deterministic, grounded in model outputs (missing skills, section
  gaps, unquantified bullets, weak verbs, language mismatch, title mismatch, positives).
  `llm.py::get_rewrites` asks Groq (gpt-oss-20b, json_object response_format,
  reasoning_effort low, max_tokens 1400) for before→after rewrites of the EXACT weak
  bullet lines (deduped by `before`), with `[X%]` placeholders; `/analyze` now returns
  `diagnosis` + `rewrites` (old `suggestions` field removed). UI ResultsPanel: Diagnosis
  card (✓ working list + severity-dotted problems each with "→ fix:"), Bullet-rewrites
  card (strikethrough before / teal after / note), skill coverage + role/radar merged to
  one row, sections card; report.js exports diagnosis+rewrites. Graceful: no key or parse
  failure → deterministic diagnosis still shows, rewrites card explains why.
- **COACH CHAT (2026-10-24 v7)**: floating "💬 Ask the coach" drawer on the results screen
  (`web/components/CoachChat.jsx`): starter-question chips, message history (last 8 turns
  sent back), structured answers rendered as summary + bullet points + "→" action chips;
  graceful "coach unavailable" bubble when Groq is off. Server: `POST /chat`
  {question, analysis, jd_text, history} → `llm.py::chat_with_coach` — stateless, the
  client posts its analysis each time; context = compacted analysis (breakdown, diagnosis,
  predicted_role made str/dict-safe, entity COUNTS not the full list) + JD excerpt;
  gpt-oss-20b, json_object, reasoning_effort low, max_tokens 1000. Verified live:
  starter question returned grounded structured answer; history turn ("rewrite my summary
  - **SEMANTIC SKILL SYNONYM MATCHING (2026-10-24 v10)**: hybrid 3-tier skill matching engine in `ml-service/app/scoring.py` replacing strict keyword counting. (1) Exact & punctuation-normalized token match; (2) Tech alias & acronym dictionary (resolves `aws` ↔ `amazon web services`, `k8s` ↔ `kubernetes`, `sql` ↔ `relational databases`, `postgres` ↔ `postgresql`, `ci/cd` ↔ `continuous integration`); (3) MiniLM sentence embedding cosine similarity ($\ge 0.74$) for natural language phrases & synonyms. Output breakdown now returns `exact_matches` and `semantic_matches` with similarity scores. UI `ResultsPanel.jsx` renders emerald green semantic chips (`≈ jd_skill (resume_skill)`), semantic count badge, and MiniLM explainer. Diagnosis acknowledges synonyms as a positive match in "What's working".
- **GEIST + GRADIENTASCII HERO (2026-10-24 v8)**: typography switched to Vercel's
  `geist` package (GeistSans/GeistMono CSS vars on <html>; @fontsource-variable/inter
  removed). Low weights: display-xl/lg 300 (tracking -5%/-4.2%), display-md 400, subhead
  font-light; .font-mono/pre/code/kbd/textarea forced to Geist Mono. Landing hero mounts
  React Bits' GradientASCII (web/components/GradientASCII.jsx, WebGL2, no-op fallback)
  behind the hero: shape=horizon, deep-blue-to-white ramp, Geist Mono glyphs at weight
  300, gradientOpacity 0.5 + glow 0.28, masked fade to transparent at 97% height,
  speed 0.55, mouse scramble + click wave. Verified live: canvas mounted, both Geist
  faces check() true at 300, h1 computed weight 300.
- **HERO REDO, REACT BITS DEMO LOOK (2026-10-24 v9)**: user rejected the v8 hero ("we want
  something like this" + React Bits demo reference). Changes: hero is now full-bleed
  `min-h-[92vh]` with the ASCII canvas filling the ENTIRE section (mask only at the very
  bottom 86%→100%), and the content anchored BOTTOM-LEFT (`flex flex-col justify-end`,
  `text-left`, max-w-2xl) instead of centered mid-hero — headline weight 500 (not 300),
  buttons left-aligned row, stats strip moved OUT into its own band on plain canvas below
  the hero, soft floor gradient (transparent→#0b0b0e) under the copy for contrast.
  **TRAP — GradientASCII color ramp ORDER matters**: the `colors` prop is a tone ramp
  (tone() maps field intensity → ramp index); putting white LAST paints the whole sky
  white/washed-out (looked like a blank page). The demo look needs the React Bits default
  order `['#1e3fd8','#f6f8ff','#a5d8ff','#38bdf8']` (white mid-ramp). Final props:
  defaults + cellSize 18, density 0.85, gradientOpacity 0.8, glow 0.28, speed 0.6,
  Geist Mono family. Debug note: the in-app browser's WebGL renders fine but verify with a
  plain red-triangle test canvas before blaming WebGL. Verified in-browser: glow band
  upper-left, navy below, glyphs dissolving, headline crisp bottom-left.
- **REVERT (2026-10-24 v5)**: per user decision the coach-marks UI was REMOVED and then
  (same day, user follow-up) ALL highlights were removed from the left preview entirely.
  Results screen is now: LEFT = plain rendered PDF preview (or plain text preview with a
  "Section map" toggle in text mode) — no bands, badges, legends or overlays; RIGHT = ATS
  score ring + role/radar/skills/sections/suggestions. PdfXray no longer imports rough.js
  or computes text-layer matching (render only); pdftext.js + rough.js remain installed
  for potential future use. The server-side `issues` field is still computed and returned
  by /analyze (unused by the UI). The v4 server fixes are KEPT because they fix real bugs
  regardless of any UI: JD harvester handles single-line JDs, resume skills harvester
  filters degree/year/university junk, section_presence counts explicit heading lines.
- **PDF X-RAY (2026-10-24 v3)**: results screen renders the user's ACTUAL uploaded PDF
  (pdfjs-dist@4, worker at `public/pdf.worker.min.mjs`) and draws the same rough.js
  hand-drawn annotations on top. Mapping pipeline (`web/lib/pdftext.js`): build a
  normalised "soup" of pdf.js text-layer items (per-char → item/idx backmap), string-match
  each NER entity with a moving cursor + global + shortened-prefix fallbacks (pypdf and
  pdf.js can disagree on order), convert matched ranges to per-line rects via item
  transform + `viewport.convertToViewportPoint` (proportional within-item x), draw
  ellipses (short entities) or hachure marker-boxes (line-spanning) per page overlay SVG.
  The uploaded File is stashed as base64 in sessionStorage (`rl.pdf`, ≤3.5 MB guard,
  `lib/flow.js`) to survive the landing → wizard route change; DOCX/TXT/paste flows fall
  back to the text X-ray. "✨ try the sample PDF" button on wizard step 1 fetches
  `public/sample-resume.pdf` through the REAL upload path. Verified in-browser:
  8/8 annotations correctly positioned over the rendered page (vision audit).
- Session flow state in `lib/flow.js` (sessionStorage `rl.resume`/`rl.resumeName`).
- Verified in-browser end to end (landing DOM audit, full wizard run, vision audit of
  results screen: hand-drawn ellipses confirmed, no clipping, ~9/10 polish score).
- roughjs + @fontsource-variable/inter added to deps.
- OPS NOTES: running `npm run build` while the dev server is up breaks its static assets
  (.next gets swapped) — restart `npm run dev` after any production build; on Windows,
  killing the npm wrapper can leave a zombie node on :3000 (`netstat -ano | findstr :3000`
  + `taskkill /PID <pid> /F`).

**DONE:** everything — all 3 models trained, ml-service (+/extract upload endpoint),
full redesigned web app, verified live.

**Optional polish (only if time):** windowed-retrain of NER (recipe in §4.2), resume–JD
pairs dataset for scorer evaluation, deploy (Vercel + HF Spaces/Render).

---

## 8. Environment & credentials

- **GROQ (configured 2026-10-24):** key lives in `ml-service/.env` (git-ignored; loaded
  by `config.py::load_env_file` at startup, real env vars win). Current Groq model
  line-up changed since training data — `llama-3.1-8b-instant` is GONE (404 model_not_found);
  working models include `openai/gpt-oss-20b` (default in llm.py), `openai/gpt-oss-120b`,
  `qwen/qwen3.8-27b`; list live via `GET api.groq.com/openai/v1/models`. GOTCHA found:
  gpt-oss spends tokens on hidden reasoning BEFORE content — with max_tokens=400 the
  content came back empty (`finish_reason=length`); fixed with `reasoning_effort="low"` +
  max_tokens=1200. Advice lines are stripped of markdown bullets/bold. Verified live:
  6 grounded suggestions returned.

- Machine: Windows 11, Git Bash, Python 3.13.1. Project root: **`D:\resume-analyser`**.
- Kaggle credentials live in **Colab Secrets** (`KAGGLE_USERNAME`, `KAGGLE_KEY`) — do not
  hardcode them anywhere. Training is FINISHED; Kaggle no longer needed unless retraining.
- Groq: set `GROQ_API_KEY` env var before starting ml-service for suggestions.
- `.qa/` folder = verification scripts + downloaded raw datasets (Dataturks json,
  section-classifier txt files) + local replication scripts — safe to delete, but keep
  for re-verification. `.testenv/` = local Python venv used for testing (deletable).
- `ml-service/artifacts_extracted/` is generated; safe to delete; regenerated on start.

## 9. Quick-start (once web app is finished)

```bash
# terminal 1 — ML service
cd D:\resume-analyser\ml-service
pip install -r requirements.txt        # first time only
set GROQ_API_KEY=your_key_here         # optional, for suggestions
uvicorn app.main:app --port 8000

# terminal 2 — web
cd D:\resume-analyser\web
npm install                            # first time only
npm run dev                            # open http://localhost:3000
```
