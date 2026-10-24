"""Generate 5 demo resume PDFs in the user's Downloads folder, each engineered to
produce a DIFFERENT analysis outcome in ResumeLens."""
import os
from fpdf import FPDF

OUT = r"C:\Users\vinit\Downloads"

def build(filename, blocks):
    """blocks: list of (text, size, bold) or ('spacer', h, None)"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(True, margin=15)
    for text, size, bold in blocks:
        if text == "spacer":
            pdf.ln(size / 2)
            continue
        pdf.set_font("Helvetica", "B" if bold else "", size=size)
        pdf.multi_cell(0, size * 0.5, text)
        pdf.ln(1.5)
    path = os.path.join(OUT, filename)
    with open(path, "wb") as f:
        f.write(bytes(pdf.output()))
    return path

H1, H2, BOD, BLT = 15, 11.5, 10.5, 10.5

resumes = []

# ---------------- 1. STRONG DATA SCIENTIST (expect ~85+) ----------------
resumes.append(("demo-resume-1-strong-data-scientist.pdf", [
    ("Priya Sharma", H1, True),
    ("priya.sharma@email.com | +91 98200 12345 | Mumbai, India", 10, False),
    ("spacer", 8, None),
    ("PROFESSIONAL SUMMARY", H2, True),
    ("Data Scientist with 5 years of experience shipping machine learning models to production in fintech and e-commerce.", BOD, False),
    ("spacer", 6, None),
    ("TECHNICAL SKILLS", H2, True),
    ("Python, PyTorch, TensorFlow, scikit-learn, SQL, pandas, statistics, A/B testing, Docker, AWS, Kubernetes, Spark, Tableau, NLP.", BOD, False),
    ("spacer", 6, None),
    ("WORK EXPERIENCE", H2, True),
    ("Senior Data Scientist - PayU Finance, Mumbai (2022 - Present)", H2, True),
    ("- Built fraud detection model (XGBoost) cutting false positives by 23% and saving $1.2M annually.", BLT, False),
    ("- Deployed 6 models on AWS SageMaker with Docker and Kubernetes, serving 4M requests per day.", BLT, False),
    ("- Designed A/B testing framework that improved approval rates by 3.5% across 12 experiments.", BLT, False),
    ("- Led a team of 3 analysts; mentored 2 interns to full-time offers.", BLT, False),
    ("Data Scientist - ShopKart, Bengaluru (2020 - 2022)", H2, True),
    ("- Built demand forecasting model (Prophet) reducing stockouts by 18% across 40 warehouses.", BLT, False),
    ("- Automated ETL pipelines with SQL, Spark and pandas, saving 20 hours per week.", BLT, False),
    ("spacer", 6, None),
    ("EDUCATION", H2, True),
    ("M.S. Statistics, Indian Institute of Technology, Bombay, 2020", BOD, False),
    ("B.S. Mathematics, University of Pune, 2018", BOD, False),
    ("spacer", 6, None),
    ("PROJECTS", H2, True),
    ("- Churn prediction API: end-to-end PyTorch service with 94% recall, deployed on AWS.", BLT, False),
    ("- Resume parser: fine-tuned DistilBERT NER on 220 annotated resumes, 0.46 entity F1.", BLT, False),
]))

# ---------------- 2. FRONTEND DEVELOPER, decent but with gaps (expect ~60-70) ----------------
resumes.append(("demo-resume-2-frontend-developer.pdf", [
    ("Arjun Mehta", H1, True),
    ("arjun.mehta@email.com | +91 99887 66554 | Pune, India", 10, False),
    ("spacer", 8, None),
    ("SUMMARY", H2, True),
    ("Frontend Developer with 3 years of experience building responsive web applications.", BOD, False),
    ("spacer", 6, None),
    ("SKILLS", H2, True),
    ("JavaScript, TypeScript, React, HTML, CSS, Tailwind, REST APIs, Git.", BOD, False),
    ("spacer", 6, None),
    ("EXPERIENCE", H2, True),
    ("Frontend Developer - Zeta WebWorks, Pune (2022 - Present)", H2, True),
    ("- Built 15+ responsive React components used by 200k monthly users.", BLT, False),
    ("- Responsible for fixing bugs reported by QA.", BLT, False),
    ("- Worked on improving page speed.", BLT, False),
    ("Junior Web Developer - CraftPixel, Remote (2021 - 2022)", H2, True),
    ("- Helped with landing pages and email templates.", BLT, False),
    ("spacer", 6, None),
    ("EDUCATION", H2, True),
    ("B.E. Computer Engineering, Pune Institute of Technology, 2021", BOD, False),
]))

# ---------------- 3. WEAK / VAGUE resume (expect low, ~40s) ----------------
resumes.append(("demo-resume-3-weak-vague.pdf", [
    ("John Dsouza", H1, True),
    ("john.dsouza@email.com", 10, False),
    ("spacer", 8, None),
    ("OBJECTIVE", H2, True),
    ("Looking for a good position in a reputed company where I can grow my career and learn new things.", BOD, False),
    ("spacer", 6, None),
    ("EXPERIENCE", H2, True),
    ("Worked at a company doing various tasks related to the job.", BLT, False),
    ("Responsible for many duties as assigned by the manager.", BLT, False),
    ("Helped the team with daily activities and office work.", BLT, False),
    ("spacer", 6, None),
    ("EDUCATION", H2, True),
    ("Bachelor of Commerce, Mumbai University", BOD, False),
]))

# ---------------- 4. FRESH GRADUATE (expect medium; education+projects strong, thin experience) ----------------
resumes.append(("demo-resume-4-fresh-graduate.pdf", [
    ("Sneha Kulkarni", H1, True),
    ("sneha.kulkarni@email.com | +91 90000 11223 | Hyderabad, India", 10, False),
    ("spacer", 8, None),
    ("SUMMARY", H2, True),
    ("Recent graduate in statistics with hands-on project experience in data analysis and machine learning.", BOD, False),
    ("spacer", 6, None),
    ("TECHNICAL SKILLS", H2, True),
    ("Python, pandas, SQL, R, Tableau, Power BI, statistics, Excel.", BOD, False),
    ("spacer", 6, None),
    ("INTERNSHIP EXPERIENCE", H2, True),
    ("Data Analyst Intern - MetroMart, Hyderabad (2024, 6 months)", H2, True),
    ("- Automated weekly sales dashboard in Tableau used by 25 store managers.", BLT, False),
    ("- Analyzed 500k rows of transaction data with SQL and pandas to find a 7% checkout drop-off.", BLT, False),
    ("spacer", 6, None),
    ("EDUCATION", H2, True),
    ("B.S. Statistics, Osmania University, Hyderabad, 2025 - CGPA 8.9/10", BOD, False),
    ("spacer", 6, None),
    ("PROJECTS", H2, True),
    ("- Crop price predictor: regression model on 10 years of government data, 88% R-squared.", BLT, False),
    ("- Campus placement study: statistical analysis of 400 student records presented at college symposium.", BLT, False),
]))

# ---------------- 5. ML ENGINEER, strong (expect high vs ML Engineer preset) ----------------
resumes.append(("demo-resume-5-ml-engineer.pdf", [
    ("Rahul Verma", H1, True),
    ("rahul.verma@email.com | +91 98111 22334 | Bengaluru, India", 10, False),
    ("spacer", 8, None),
    ("SUMMARY", H2, True),
    ("Machine Learning Engineer with 6 years of experience taking models from notebook to production at scale.", BOD, False),
    ("spacer", 6, None),
    ("TECHNICAL SKILLS", H2, True),
    ("Python, PyTorch, TensorFlow, Docker, Kubernetes, AWS, GCP, Airflow, Spark, SQL, MLOps, CI/CD, monitoring, model drift detection.", BOD, False),
    ("spacer", 6, None),
    ("WORK EXPERIENCE", H2, True),
    ("Senior ML Engineer - FlipCloud, Bengaluru (2021 - Present)", H2, True),
    ("- Owned the recommendation system serving 12M users; lifted CTR by 9% with a two-tower retrieval model.", BLT, False),
    ("- Built the MLOps platform (Airflow, Kubernetes, AWS) used by 4 teams; deployment time cut from 2 weeks to 2 hours.", BLT, False),
    ("- Set up model monitoring and drift detection that caught 3 regressions before customers did.", BLT, False),
    ("ML Engineer - DataForge, Bengaluru (2019 - 2021)", H2, True),
    ("- Fine-tuned BERT classifiers for support-ticket routing, 91% accuracy on 40k tickets per month.", BLT, False),
    ("- Migrated training pipelines from VMs to Spark clusters, reducing cost by 35%.", BLT, False),
    ("spacer", 6, None),
    ("EDUCATION", H2, True),
    ("B.Tech Computer Science, NIT Trichy, 2019", BOD, False),
    ("spacer", 6, None),
    ("PROJECTS", H2, True),
    ("- open-source contributor to a feature-store project (500+ GitHub stars).", BLT, False),
    ("- LLM fine-tuning experiments: LoRA adapters on 7B models for domain QA.", BLT, False),
]))

paths = [build(fname, blocks) for fname, blocks in resumes]

# verify each extracts cleanly with pypdf (same library the service uses)
from pypdf import PdfReader
for p in paths:
    text = "\n".join((page.extract_text() or "") for page in PdfReader(p).pages)
    print(f"{os.path.basename(p):45s} {os.path.getsize(p)//1024:3d} KB  {len(text):5d} chars extracted")
print("\nAll 5 written to", OUT)
