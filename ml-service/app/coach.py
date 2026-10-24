"""Diagnosis layer: turn the analysis into a clear report — what's working, what's
hurting the score, and the exact fix for each problem. Deterministic and grounded in
model outputs (no hallucination); the LLM layer adds rewrites on top of this."""
import re

WEAK_VERB_STARTS = (
    "responsible for", "worked on", "working on", "helped with", "assisted in",
    "involved in", "part of", "duties included", "tasked with", "handled",
)
BULLET_CHARS = "-•·—*"


def _bullets(section_lines, section="experience"):
    return [
        r["line"] for r in section_lines
        if r["section"] == section and r["line"].lstrip().startswith(tuple(BULLET_CHARS))
    ]


def build_diagnosis(resume_text, section_lines, breakdown, target_role, predicted_role):
    b = breakdown
    working, problems = [], []

    # ---------------- sections ----------------
    present = b["section_completeness"]["present"]
    missing_sections = b["section_completeness"]["missing"]
    if len(present) == 4:
        working.append("All four core sections detected — experience, education, projects and skills.")
    for s in missing_sections:
        problems.append({
            "kind": "missing_section", "severity": "medium",
            "title": f"No {s} section",
            "detail": "The section classifier (BiLSTM) found no lines belonging to a "
                      f"{s} section.",
            "fix": f"Add a {s.upper()} section with 1–3 concrete entries.",
        })

    # ---------------- skills ----------------
    matched = b["skill_overlap"]["matched"]
    missing = [s for s in b["skill_overlap"]["missing"] if len(s) <= 30 and not any(c.isdigit() for c in s)]
    cov = b["skill_overlap"]["score"]
    semantic_matches = b["skill_overlap"].get("semantic_matches", [])
    if semantic_matches:
        top_sem = semantic_matches[:2]
        summary_str = ", ".join(f"'{m['resume_skill']}' -> '{m['jd_skill']}'" for m in top_sem)
        working.append(f"Semantic skill matching recognized {len(semantic_matches)} skill synonym(s) ({summary_str}) without penalizing different naming conventions.")
    if matched and cov >= 70:
        working.append(f"{len(matched)} job skills already on the resume ({cov}% coverage): "
                       + ", ".join(matched[:6]) + ("…" if len(matched) > 6 else ""))
    if missing:
        problems.append({
            "kind": "missing_skills", "severity": "high",
            "title": f"{len(missing)} job skills missing",
            "detail": "Asked for in the job description, nowhere on the resume: " + ", ".join(missing[:6]) + ".",
            "fix": "Add them to your skills list — a course, certification or project counts.",
        })
    elif cov < 70 and matched:
        problems.append({
            "kind": "low_coverage", "severity": "medium",
            "title": f"Low skill coverage ({cov}%)",
            "detail": "The resume covers fewer than a third of the skills this job asks for.",
            "fix": "Mirror the job description's terminology in your summary and skills.",
        })

    # ---------------- experience bullets ----------------
    exp = _bullets(section_lines)
    quantified = [l for l in exp if any(c.isdigit() for c in l)]
    unquantified = [l for l in exp if not any(c.isdigit() for c in l) and len(l.strip()) > 25]
    weak_verbs = [l for l in exp
                  if l.lstrip(BULLET_CHARS + " ").strip().lower().startswith(WEAK_VERB_STARTS)]
    if exp and not unquantified and not weak_verbs:
        working.append(f"Every experience bullet is quantified ({len(exp)} bullets) — recruiters scan for numbers.")
    for line in unquantified[:2]:
        problems.append({
            "kind": "weak_bullet", "severity": "medium",
            "title": "Bullet has no measurable impact",
            "detail": line.strip(),
            "fix": "Add numbers: %, users, money or time saved, volume.",
        })
    for line in weak_verbs[:1]:
        opener = line.lstrip(BULLET_CHARS + " ").strip().split(" ")
        problems.append({
            "kind": "weak_verb", "severity": "medium",
            "title": f'Weak opener: "{" ".join(opener[:3])}…"',
            "detail": line.strip(),
            "fix": "Start with a strong verb: Built, Led, Designed, Automated, Shipped.",
        })

    # ---------------- semantic / role alignment ----------------
    sem = b["semantic_similarity"]["score"]
    if sem < 55:
        problems.append({
            "kind": "language_mismatch", "severity": "medium",
            "title": "Resume language doesn't mirror the job description",
            "detail": f"Sentence-level similarity is only {sem}%.",
            "fix": "Echo the job description's key terms in your summary and experience lines.",
        })
    if target_role and predicted_role:
        p = predicted_role.lower().replace("-", " ")
        if p not in target_role.lower() and target_role.lower() not in p:
            problems.append({
                "kind": "title_mismatch", "severity": "low",
                "title": f"Resume reads as “{predicted_role}”, not “{target_role}”",
                "detail": "The role classifier predicts a different category than the job you're applying for.",
                "fix": f"Use the exact title “{target_role}” in your summary or headline.",
            })
    elif predicted_role:
        working.append(f"Role classifier reads this resume as “{predicted_role}”.")

    order = {"high": 0, "medium": 1, "low": 2}
    problems.sort(key=lambda i: order[i["severity"]])
    return {"working": working[:4], "problems": problems[:6]}
