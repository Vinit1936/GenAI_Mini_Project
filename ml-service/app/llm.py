"""Groq LLM layer: concrete before -> after rewrites of the resume's weakest lines,
grounded in the analysis (weak bullets, missing skills, section gaps). Fails gracefully:
without GROQ_API_KEY or on any error the dashboard keeps its full deterministic
diagnosis — only the rewrites card shows a hint."""
import json
import os
import re

SYSTEM_PROMPT = (
    "You are a brutally clear resume coach. You receive a resume analysis (detected "
    "problems with the exact weak lines) and a job description. Rewrite the weak lines "
    "so they are specific, quantified and start with strong verbs. Where numbers are not "
    "knowable, insert realistic placeholders like [X%] and tell the candidate to fill "
    "them in. Never invent employers or skills. Never comment on name, gender, age or photo."
)

REWRITE_TEMPLATE = """Job description (excerpt):
{jd}

Detected problems:
{problems}

Weak resume lines to rewrite:
{lines}

Return ONLY a JSON object:
{{
  "summary": "one sentence on the single highest-impact fix",
  "rewrites": [
    {{"before": "the exact weak line", "after": "the rewritten line", "note": "why it's better (max 12 words)"}}
  ]
}}
Rewrite every weak line listed above (max 4). Keep each "after" under 30 words."""


def _weak_lines(diagnosis: dict) -> list:
    return [p["detail"] for p in diagnosis.get("problems", [])
            if p.get("kind") in ("weak_bullet", "weak_verb") and p.get("detail")]


def build_rewrite_prompt(diagnosis: dict, jd_text: str) -> str:
    probs = "\n".join(
        f"- [{p['severity']}] {p['title']}: {p['detail']} Fix: {p['fix']}"
        for p in diagnosis.get("problems", [])
    ) or "- none detected"
    lines = "\n".join(f"- {l}" for l in _weak_lines(diagnosis)) or "- none"
    return REWRITE_TEMPLATE.format(jd=jd_text[:1200], problems=probs, lines=lines)


CHAT_SYSTEM = (
    "You are a resume coach chatting with a candidate about THEIR analysis results, "
    "given to you as JSON. Stay grounded: quote the actual scores, missing skills and "
    "diagnosis items when relevant. Answer only career/resume/job questions; if asked "
    "something else, steer back politely. Be concise and concrete. Never comment on "
    "name, gender, age or photo. Reply ONLY as JSON: "
    '{"summary": "direct answer, 1-2 sentences", "points": ["key point", ...], '
    '"actions": ["concrete next step", ...]} — points and actions may be empty lists.'
)

CHAT_FALLBACKS = [
    "Why is my skill score low?",
    "How do I add the missing skills quickly?",
    "Rewrite my summary for this job.",
]


def compact_analysis(analysis: dict) -> dict:
    """Slim the analysis down for the chat context. Entity list becomes type -> sample
    values so the coach can discuss what was actually detected."""
    b = analysis.get("breakdown", {})
    ent_samples = {}
    for e in analysis.get("entities", []):
        if isinstance(e, dict) and e.get("type"):
            ent_samples.setdefault(e["type"], [])
            if len(ent_samples[e["type"]]) < 4 and e.get("text"):
                ent_samples[e["type"]].append(str(e["text"])[:40])
    pr = analysis.get("predicted_role")
    role = pr.get("role") if isinstance(pr, dict) else pr
    return {
        "overall_score": analysis.get("overall_score"),
        "breakdown": b,
        "predicted_role": role,
        "diagnosis": analysis.get("diagnosis"),
        "entities_detected": ent_samples,
        "sections": analysis.get("sections", {}).get("line_counts") if isinstance(analysis.get("sections"), dict) else None,
    }


def chat_with_coach(question: str, analysis: dict, jd_text: str, history: list,
                    resume_text: str = "") -> dict:
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return {"available": False, "reason": "GROQ_API_KEY not set",
                "summary": "", "points": [], "actions": []}
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        context = json.dumps(compact_analysis(analysis), ensure_ascii=False)
        msgs = [
            {"role": "system", "content":
                CHAT_SYSTEM
                + "\n\nANALYSIS:\n" + context
                + "\n\nJOB DESCRIPTION:\n" + jd_text[:1500]
                + "\n\nFULL RESUME TEXT:\n" + resume_text[:6000]},
        ]
        for h in (history or [])[-8:]:                    # keep the last 8 turns only
            role = h.get("role")
            if role in ("user", "assistant") and h.get("content"):
                msgs.append({"role": role, "content": str(h["content"])[:1500]})
        msgs.append({"role": "user", "content": question[:2000]})
        resp = client.chat.completions.create(
            model=os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b"),
            messages=msgs,
            temperature=0.5,
            max_tokens=1000,          # gpt-oss spends tokens on hidden reasoning first;
            reasoning_effort="low",   # keep the chain short so the JSON fits the budget
            response_format={"type": "json_object"},
        )
        data = _extract_json(resp.choices[0].message.content or "")
        if not data:
            return {"available": False, "reason": "could not parse model output",
                    "summary": "", "points": [], "actions": []}
        clean = lambda v: [str(x).replace("**", "").strip() for x in (v or []) if str(x).strip()]
        return {
            "available": True,
            "summary": str(data.get("summary", "")).replace("**", "").strip(),
            "points": clean(data.get("points"))[:5],
            "actions": clean(data.get("actions"))[:4],
        }
    except Exception as e:
        return {"available": False, "reason": f"groq call failed: {e}",
                "summary": "", "points": [], "actions": []}


def _extract_json(text: str):
    """Model output should be pure JSON; fall back to grabbing the outermost braces."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def get_rewrites(diagnosis: dict, jd_text: str) -> dict:
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return {"available": False, "reason": "GROQ_API_KEY not set", "summary": "", "rewrites": []}
    if not _weak_lines(diagnosis):
        return {"available": False, "reason": "no weak lines worth rewriting", "summary": "", "rewrites": []}
    try:
        from groq import Groq  # imported lazily so the service runs without groq installed
        client = Groq(api_key=api_key)
        resp = client.chat.completions.create(
            model=os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_rewrite_prompt(diagnosis, jd_text)},
            ],
            temperature=0.4,
            max_tokens=1400,          # gpt-oss spends tokens on hidden reasoning first;
            reasoning_effort="low",   # keep the chain short so the JSON fits the budget
            response_format={"type": "json_object"},
        )
        data = _extract_json(resp.choices[0].message.content or "")
        if not data or not isinstance(data.get("rewrites"), list):
            return {"available": False, "reason": "could not parse model output",
                    "summary": str(data.get("summary", "")) if data else "", "rewrites": []}
        clean, seen = [], set()
        for r in data["rewrites"]:
            if not (isinstance(r, dict) and r.get("after")):
                continue
            before = str(r.get("before", "")).strip().lower()
            if before in seen:
                continue                       # model sometimes rewrites the same line twice
            seen.add(before)
            clean.append(r)
        return {"available": True, "summary": str(data.get("summary", "")).strip(),
                "rewrites": clean[:4]}
    except Exception as e:  # rate limits, network, bad key - never break the analysis flow
        return {"available": False, "reason": f"groq call failed: {e}", "summary": "", "rewrites": []}
