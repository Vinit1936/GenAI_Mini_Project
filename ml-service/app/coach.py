"""Diagnosis layer: turn the analysis into a clear report — what's working, what's
hurting the score, and the exact fix for each problem. Deterministic and grounded in
model outputs (no hallucination); the LLM layer adds rewrites on top of this."""
import re

WEAK_VERB_STARTS = (
    "responsible for", "worked on", "working on", "helped with", "assisted in",
    "involved in", "part of", "duties included", "tasked with", "handled",
    "participated in", "attempted to",
)
BULLET_CHARS = "-•·—*"

POWER_ACTION_VERBS = {
    "architected", "engineered", "built", "designed", "developed", "implemented", "constructed",
    "authored", "pioneered", "spearheaded", "orchestrated", "founded", "directed", "managed",
    "championed", "supervised", "led", "steered", "optimized", "scaled", "accelerated",
    "streamlined", "automated", "reduced", "boosted", "maximized", "minimized", "refactored",
    "modernized", "consolidated", "deployed", "shipped", "launched", "delivered", "integrated",
    "migrated", "released", "published", "standardized", "analyzed", "modeled", "evaluated",
    "forecasted", "benchmarked", "discovered", "quantified", "formulated", "established",
    "devised", "created", "generated", "solved", "negotiated", "executed", "transformed",
    "trained", "fine-tuned", "finetuned", "tested", "debugged", "monitored", "curated",
}

# Regex metric patterns
RE_PERCENT = re.compile(r'\b\d+(?:\.\d+)?%', re.IGNORECASE)
RE_MULTIPLIER = re.compile(r'\b\d+(?:\.\d+)?(?:x|ms|sec|seconds?|minutes?|hrs?|hours?)\b', re.IGNORECASE)
RE_CURRENCY = re.compile(r'(?:[\$€£₹]\s*\d+(?:,\d{3})*(?:\.\d+)?\s*(?:[kKmMbBtT]|thousand|million|billion)?|\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:USD|EUR|GBP|INR|dollars?))\b', re.IGNORECASE)
RE_SCALE = re.compile(r'\b\d+(?:,\d{3})*(?:\.\d+)?\+?\s*(?:k|m|b|million|billion|thousand)?\s*(?:users|active users|customers|clients|subscribers|requests(?:\s*/\s*(?:day|sec|second|min))?|qps|rps|tps|events|records|rows|lines|microservices|services|pipelines|engineers|developers|members|teammates|people|projects|dashboards|models|hours(?:\s*/\s*week)?)\b', re.IGNORECASE)
RE_GENERIC_NUM = re.compile(r'\b(?!(?:19\d\d|20[0-3]\d)\b)\d+(?:,\d{3})*(?:\.\d+)?\b')

METHOD_INDICATORS = ("by ", "using ", "via ", "through ", "with ", "leveraging ", "utilizing ", "employing ")


def _bullets(section_lines, full_text=""):
    """Extract all accomplishment bullets from section lines or full resume text."""
    candidates = []
    if section_lines:
        for r in section_lines:
            line = r.get("line", "").strip()
            if line.startswith(tuple(BULLET_CHARS)) and len(line) > 18:
                # Avoid capturing pure comma-separated skill lists
                if not (line.count(",") >= 3 and len(line.split()) <= 6):
                    candidates.append(line)
    if not candidates and full_text:
        for line in full_text.splitlines():
            s = line.strip()
            if s.startswith(tuple(BULLET_CHARS)) and len(s) > 18:
                if not (s.count(",") >= 3 and len(s.split()) <= 6):
                    candidates.append(s)
    return candidates


def analyze_impact_metrics(section_lines: list, full_text: str = "") -> dict:
    """Analyze resume experience lines against the Google XYZ formula:
    'Accomplished [X] as measured by [Y], by doing [Z]'."""
    raw_lines = _bullets(section_lines, full_text)

    bullets_analysis = []
    xyz_count = 0
    quant_count = 0
    weak_count = 0

    for raw in raw_lines:
        line = raw.strip()
        clean = line.lstrip(BULLET_CHARS + " ").strip()
        if not clean or len(clean) < 8:
            continue

        words = clean.split()
        first_word = words[0].lower().rstrip(",.:;") if words else ""
        first_phrase = " ".join(words[:2]).lower() if len(words) >= 2 else ""

        # Check weak opener
        is_weak = any(clean.lower().startswith(w) for w in WEAK_VERB_STARTS)
        if is_weak:
            weak_count += 1

        # Check power action verb
        is_power = first_word in POWER_ACTION_VERBS or first_phrase in POWER_ACTION_VERBS
        has_verb_form = first_word.endswith("ed") or is_power
        action_verb = words[0] if (has_verb_form and not is_weak) else ""

        # Extract metrics
        found_metrics = []
        for m in RE_PERCENT.finditer(clean):
            found_metrics.append(m.group(0))
        for m in RE_MULTIPLIER.finditer(clean):
            found_metrics.append(m.group(0))
        for m in RE_CURRENCY.finditer(clean):
            found_metrics.append(m.group(0))
        for m in RE_SCALE.finditer(clean):
            if m.group(0) not in found_metrics:
                found_metrics.append(m.group(0))

        if not found_metrics:
            for m in RE_GENERIC_NUM.finditer(clean):
                val = m.group(0)
                if len(val) >= 2 and val not in ("2020", "2021", "2022", "2023", "2024", "2025", "2026"):
                    found_metrics.append(val)

        has_metric = len(found_metrics) > 0
        if has_metric:
            quant_count += 1

        # Method indicator
        method_match = None
        lower_clean = clean.lower()
        for ind in METHOD_INDICATORS:
            if ind in lower_clean:
                idx = lower_clean.find(ind)
                snippet = clean[idx:idx + 45].strip()
                method_match = snippet
                break

        # Google XYZ Compliance
        is_xyz = bool(action_verb) and has_metric and not is_weak
        if is_xyz:
            xyz_count += 1

        # Status & Coaching Advice
        if is_xyz:
            status = "xyz"
            tip = f"Excellent Google XYZ format: Strong action verb '{action_verb}' backed by measurable metric ({', '.join(found_metrics)})."
        elif is_weak:
            status = "weak_verb"
            tip = f"Starts with passive phrase '{first_phrase or first_word}'. Upgrade to a power verb: Engineered, Architected, Spearheaded, Automated."
        elif not has_metric:
            status = "missing_metric"
            tip = "Lacks quantifiable metric. Add numbers: % efficiency/conversion lift, latency reduction (ms), scale (users/requests), or time/cost saved."
        else:
            status = "good"
            tip = "Has quantifiable metric. Strengthen the opening action verb to make it full Google XYZ standard."

        bullets_analysis.append({
            "raw": line,
            "clean": clean,
            "action_verb": action_verb or (words[0] if words else ""),
            "is_power_verb": bool(is_power),
            "is_weak": is_weak,
            "metrics": found_metrics,
            "has_metric": has_metric,
            "method": method_match,
            "is_xyz": is_xyz,
            "status": status,
            "tip": tip,
        })

    total = len(bullets_analysis)
    if total > 0:
        score = round(100 * ((xyz_count * 1.0) + ((quant_count - xyz_count) * 0.6) + ((total - quant_count - weak_count) * 0.4)) / total)
        score = max(0, min(100, score))
    else:
        score = 0

    return {
        "score": score,
        "total_bullets": total,
        "xyz_count": xyz_count,
        "quantified_count": quant_count,
        "weak_verb_count": weak_count,
        "bullets": bullets_analysis,
    }


def build_diagnosis(resume_text, section_lines, breakdown, target_role, predicted_role, impact_analysis=None):
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

    # ---------------- semantic relevance attribution ----------------
    attrib = b.get("semantic_similarity", {}).get("attribution", {})
    if attrib.get("high", 0) >= 2:
        working.append(f"{attrib['high']} resume bullet point(s) show strong semantic alignment with target JD requirements.")
    if attrib.get("low", 0) >= 3:
        problems.append({
            "kind": "low_relevance_bullets", "severity": "low",
            "title": f"{attrib['low']} low-relevance bullet(s)",
            "detail": "Several bullets have low semantic overlap with the specific requirements in this job posting.",
            "fix": "Toggle the 'Relevance Heatmap' on the left preview to see flagged lines and tailor them.",
        })

    # ---------------- experience bullets & Google XYZ formula ----------------
    if impact_analysis and impact_analysis["total_bullets"] > 0:
        xyz_c = impact_analysis["xyz_count"]
        tot = impact_analysis["total_bullets"]
        quant_c = impact_analysis["quantified_count"]

        if xyz_c >= 2:
            working.append(f"{xyz_c} of {tot} experience bullets follow the Google XYZ formula (Accomplished [X] as measured by [Y] by doing [Z]).")
        elif quant_c == tot:
            working.append(f"All {tot} experience bullets have quantifiable numbers.")

        missing_metrics = [bl for bl in impact_analysis["bullets"] if not bl["has_metric"]]
        for bl in missing_metrics[:2]:
            problems.append({
                "kind": "weak_bullet", "severity": "medium",
                "title": "Bullet has no measurable impact",
                "detail": bl["clean"],
                "fix": "Add numbers: %, users, latency, money or time saved, volume.",
            })

        weak_bullets = [bl for bl in impact_analysis["bullets"] if bl["is_weak"]]
        for bl in weak_bullets[:1]:
            problems.append({
                "kind": "weak_verb", "severity": "medium",
                "title": f"Weak opener: \"{bl['clean'][:24]}…\"",
                "detail": bl["clean"],
                "fix": "Start with a strong verb: Built, Led, Designed, Automated, Shipped.",
            })
    else:
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

