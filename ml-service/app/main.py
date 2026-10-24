"""FastAPI entrypoint. Loads all four trained/frozen components once at startup.

Run:  uvicorn app.main:app --port 8000   (from the ml-service folder)
"""
from functools import lru_cache

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import config, loaders
from .ner import ResumeNER
from .performance import performance_summary, plot_file
from .role import RoleClassifier
from .scoring import MatchScorer
from .sections import SectionClassifier

app = FastAPI(title="Resume Analyser ML Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    resume_text: str = Field(min_length=50, max_length=60000)
    job_description: str = Field(min_length=20, max_length=60000)
    want_suggestions: bool = True
    target_role: str | None = None


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    analysis: dict
    jd_text: str = ""
    resume_text: str = ""
    history: list = []


class HealthResponse(BaseModel):
    status: str
    models: dict


_state = {}


@app.on_event("startup")
def startup() -> None:
    loaders.extract_all()
    _state["role"] = RoleClassifier(config.ROLE_DIR, config.ROLE_LABELS)
    _state["ner"] = ResumeNER(config.NER_DIR, config.NER_TAGS)
    _state["sections"] = SectionClassifier(config.SECTION_WEIGHTS, config.SECTION_VOCAB, config.SECTION_LABELS)
    from sentence_transformers import SentenceTransformer
    _state["st"] = SentenceTransformer(config.SENTENCE_MODEL)
    _state["scorer"] = MatchScorer(_state["ner"], _state["role"], _state["sections"], _state["st"])


@app.get("/health", response_model=HealthResponse)
def health():
    if not _state:
        raise HTTPException(503, "models still loading")
    return {
        "status": "ok",
        "models": {
            "role_classifier": "distilbert-finetuned",
            "resume_ner": "distilbert-token-cls",
            "section_classifier": "bilstm",
            "sentence_model": config.SENTENCE_MODEL,
        },
    }


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    if "scorer" not in _state:
        raise HTTPException(503, "models still loading")
    analysis = _state["scorer"].analyze(req.resume_text, req.job_description)
    from .coach import analyze_impact_metrics, build_diagnosis
    analysis["impact_analysis"] = analyze_impact_metrics(analysis["section_lines"], req.resume_text)
    analysis["diagnosis"] = build_diagnosis(
        req.resume_text, analysis["section_lines"], analysis["breakdown"],
        req.target_role, analysis["predicted_role"]["role"],
        impact_analysis=analysis["impact_analysis"],
    )
    if req.want_suggestions:
        from .llm import get_rewrites
        analysis["rewrites"] = get_rewrites(analysis["diagnosis"], req.job_description)
    else:
        analysis["rewrites"] = {"available": False, "summary": "", "rewrites": []}
    return analysis


@app.post("/extract")
async def extract_resume(file: UploadFile = File(...)):
    """Turn an uploaded resume file (PDF/DOCX/TXT) into plain text for the analysis box."""
    data = await file.read()
    if len(data) > 15 * 1024 * 1024:
        raise HTTPException(413, "file too large (max 15 MB)")
    from .extract import extract_text
    try:
        text = extract_text(file.filename, data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        raise HTTPException(422, f"could not read '{file.filename}' - is it a valid document?")
    if len(text.strip()) < 100:
        raise HTTPException(
            422,
            "extracted almost no text - this is usually a scanned/image-only PDF. "
            "Please paste the resume text manually instead.",
        )
    return {"text": text, "filename": file.filename, "characters": len(text)}


@app.post("/chat")
def chat(req: ChatRequest):
    """Follow-up questions about the user's analysis, answered by the LLM in
    structured form (summary / points / actions). Stateless: the client sends its
    analysis + chat history each time."""
    from .llm import chat_with_coach
    return chat_with_coach(req.question, req.analysis, req.jd_text, req.history, req.resume_text)


@app.get("/models/performance")
def model_performance():
    return performance_summary()


@app.get("/models/plots/{model}/{name}")
def model_plot(model: str, name: str):
    return plot_file(model, name)
