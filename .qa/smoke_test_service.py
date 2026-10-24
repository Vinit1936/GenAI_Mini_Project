"""End-to-end smoke test of the ML service using the REAL trained artifacts.
Runs the full pipeline offline (no server needed) via FastAPI's TestClient."""
import json
import sys
import time

sys.path.insert(0, r"D:\resume-analyser\ml-service")

RESUME = """Maria Rodriguez
Email: maria.rodriguez@email.com | Phone: +1 415 555 0198 | San Francisco, CA

PROFESSIONAL SUMMARY
Data Scientist with 4 years of experience building machine learning models in production.

TECHNICAL SKILLS
Python, PyTorch, scikit-learn, SQL, pandas, Docker, AWS, Tableau, A/B testing.

WORK EXPERIENCE
Data Scientist - FinTech Labs, San Francisco (2021 - Present)
- Built churn prediction model (XGBoost) improving retention by 12%.
- Deployed models with Docker and AWS SageMaker, serving 2M requests/day.
Junior Data Analyst - RetailCo, Oakland (2019 - 2021)
- Automated reporting pipelines with SQL and pandas, saving 15 hours/week.

EDUCATION
B.S. Statistics, University of California, Berkeley, 2019

PROJECTS
- Demand forecasting dashboard: time-series model (Prophet) with Tableau front-end."""

JD = """We are hiring a Senior Data Scientist to join our ML platform team.

Requirements:
- 4+ years of experience in data science or machine learning
- Strong Python skills; experience with PyTorch or TensorFlow
- Production deployment experience (Docker, AWS or GCP)
- Solid SQL and data-wrangling skills (pandas)
- Experience with A/B testing and experimentation
- Communication skills and business sense

Nice to have: Kubernetes, Spark, Tableau, NLP experience. Degree in Statistics,
CS, Mathematics or related field."""


def main():
    t0 = time.time()
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:  # triggers startup: extract zips + load all models
        print(f"[{time.time()-t0:.0f}s] models loaded")

        r = client.get("/health")
        assert r.status_code == 200, r.text
        print("health:", r.json()["models"])

        r = client.post("/analyze", json={
            "resume_text": RESUME, "job_description": JD, "want_suggestions": False})
        assert r.status_code == 200, r.text[:400]
        out = r.json()
        print(f"\n[{time.time()-t0:.0f}s] OVERALL SCORE:", out["overall_score"])
        for k, v in out["breakdown"].items():
            print(f"  {k:24s} {v['score']:5.1f}  (weight {v['weight']})")
        print("predicted role:", out["predicted_role"]["role"],
              "| confidence:", out["predicted_role"]["confidence"])
        print("matched skills:", out["breakdown"]["skill_overlap"]["matched"])
        print("missing skills:", out["breakdown"]["skill_overlap"]["missing"][:8])
        print("sections present:", out["breakdown"]["section_completeness"]["present"],
              "missing:", out["breakdown"]["section_completeness"]["missing"])
        print("names stripped:", out["privacy"]["names_stripped"])
        types = {}
        for e in out["entities"]:
            types[e["type"]] = types.get(e["type"], 0) + 1
        print("entities found:", types)

        r = client.get("/models/performance")
        assert r.status_code == 200, r.text[:300]
        perf = r.json()
        print("\nperformance endpoint ok:",
              {m: ("f1" in str(v) or "accuracy" in str(v)) for m, v in perf.items()})
        r = client.get("/models/plots/role_classifier/cm_distilbert.png")
        assert r.status_code == 200 and r.headers["content-type"] == "image/png"
        print("plot serving ok (confusion matrix png)")

    print(f"\nSMOKE TEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
