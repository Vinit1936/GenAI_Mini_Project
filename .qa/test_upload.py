"""Test the /extract endpoint with generated PDF, DOCX and TXT files, then run a full
/analyze on the PDF-extracted text to prove the upload -> analysis path end-to-end."""
import io
import sys
import time

sys.path.insert(0, r"D:\resume-analyser\ml-service")

RESUME_LINES = [
    "Maria Rodriguez",
    "Email: maria.rodriguez@email.com | Phone: +1 415 555 0198 | San Francisco, CA",
    "PROFESSIONAL SUMMARY",
    "Data Scientist with 4 years of experience building machine learning models in production.",
    "TECHNICAL SKILLS",
    "Python, PyTorch, scikit-learn, SQL, pandas, Docker, AWS, Tableau, A/B testing.",
    "WORK EXPERIENCE",
    "Data Scientist - FinTech Labs, San Francisco (2021 - Present)",
    "Built churn prediction model improving retention by 12 percent.",
    "Deployed models with Docker and AWS SageMaker, serving 2M requests/day.",
    "EDUCATION",
    "B.S. Statistics, University of California, Berkeley, 2019",
    "PROJECTS",
    "Demand forecasting dashboard: time-series model with Tableau front-end.",
]
RESUME_TEXT = "\n".join(RESUME_LINES)

JD = """Senior Data Scientist role.
Requirements:
- 4+ years of experience in data science or machine learning
- Strong Python skills; experience with PyTorch or TensorFlow
- Production deployment experience (Docker, AWS or GCP)
- Solid SQL and pandas skills
Nice to have: Kubernetes, Spark, Tableau."""


def make_pdf() -> bytes:
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    for ln in RESUME_LINES:
        pdf.multi_cell(0, 6, ln)
        pdf.ln(1)
    return bytes(pdf.output())


def make_docx() -> bytes:
    from docx import Document
    doc = Document()
    for ln in RESUME_LINES:
        doc.add_paragraph(ln)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def main():
    t0 = time.time()
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        # --- PDF ---
        r = client.post("/extract", files={"file": ("resume.pdf", make_pdf(), "application/pdf")})
        assert r.status_code == 200, r.text
        pdf_text = r.json()["text"]
        print(f"PDF  -> {r.json()['characters']} chars; contains 'PyTorch':", "pytorch" in pdf_text.lower())
        assert "pytorch" in pdf_text.lower() and "berkeley" in pdf_text.lower()

        # --- DOCX ---
        r = client.post("/extract", files={"file": ("resume.docx", make_docx(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
        assert r.status_code == 200, r.text
        print(f"DOCX -> {r.json()['characters']} chars; contains 'Docker':", "docker" in r.json()["text"].lower())

        # --- TXT ---
        r = client.post("/extract", files={"file": ("resume.txt", RESUME_TEXT.encode(), "text/plain")})
        assert r.status_code == 200, r.text
        print(f"TXT  -> {r.json()['characters']} chars")

        # --- rejected types + scanned-pdf guard ---
        r = client.post("/extract", files={"file": ("photo.png", b"\x89PNG" + b"0" * 200, "image/png")})
        assert r.status_code == 400, r.text
        r = client.post("/extract", files={"file": ("empty.pdf", b"not a real pdf", "application/pdf")})
        assert r.status_code == 422, r.text
        print("error cases OK (bad type 400, unreadable 422)")

        # --- full analysis on PDF-extracted text ---
        r = client.post("/analyze", json={"resume_text": pdf_text, "job_description": JD, "want_suggestions": False})
        assert r.status_code == 200, r.text[:300]
        out = r.json()
        print(f"\nanalyze(PDF-extracted text): overall {out['overall_score']}")
        print("  role:", out["predicted_role"]["role"], "| entities:", len(out["entities"]),
              "| matched:", out["breakdown"]["skill_overlap"]["matched"])

    print(f"\nUPLOAD TEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
