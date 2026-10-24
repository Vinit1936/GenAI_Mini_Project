"""Match-score engine.

Score = 40% semantic similarity (MiniLM cosine, resume vs job description)
      + 30% skill overlap      (NER Skills of resume vs JD skills)
      + 15% section completeness (BiLSTM: which canonical sections exist)
      + 15% role alignment     (classifier's role name vs JD, MiniLM cosine)

Fairness: before ANY component is computed, personal identifiers are stripped from the
text that models see for scoring — NER 'Name' entities, emails, phones, URLs and
gendered words. The dashboard still shows entities, but names never touch the score.
"""
import math
import re

from . import config
from .ner import ResumeNER
from .role import RoleClassifier
from .sections import SectionClassifier

_PRONOUNS = config.GENDER_STOPWORDS


def strip_personal(text: str, name_spans: list) -> str:
    """Remove name spans and gendered/marker words from text (used for scoring only)."""
    chars = list(text)
    for ent in name_spans:
        for i in range(ent["start"], min(ent["end"], len(chars))):
            chars[i] = " "
    cleaned = "".join(chars)
    cleaned = re.sub(r"\S+@\S+", " ", cleaned)                     # emails
    cleaned = re.sub(r"(?:\+?\d[\d\s\-().]{7,}\d)", " ", cleaned)  # phone-like numbers
    cleaned = re.sub(r"http\S+|www\.\S+", " ", cleaned)            # URLs
    words = [w if w.lower().strip(".,:;") not in _PRONOUNS else "" for w in cleaned.split()]
    return re.sub(r"\s+", " ", " ".join(words)).strip()


class MatchScorer:
    def __init__(self, ner: ResumeNER, role: RoleClassifier, sections: SectionClassifier, st_model):
        self.ner, self.role, self.sections, self.st = ner, role, sections, st_model

    # ---- component 1: semantic similarity -------------------------------------------
    def semantic_similarity(self, resume_clean: str, jd: str) -> float:
        emb = self.st.encode([resume_clean[:6000], jd[:6000]], normalize_embeddings=True)
        sim = float(emb[0] @ emb[1])
        return max(0.0, min(1.0, (sim + 1) / 2))        # cosine [-1,1] -> [0,1]

    # ---- component 2: skill overlap --------------------------------------------------
    _SPLIT_RE = re.compile(r"[,;•|·/]|\s{2,}|\bor\b|\band\b")
    _PREAMBLE_RE = re.compile(
        r"^(?:strong\s+|solid\s+|deep\s+|hands-on\s+)?(?:experience\s+(?:with|in)|knowledge\s+of|expertise\s+in|familiarity\s+with|proficiency\s+in|understanding\s+of|working\s+with|skills?\s+in|ability\s+to\s+use|background\s+in|building|designing|developing|deploying|managing)\s+",
        re.I,
    )
    _TRAILING_PLUS_RE = re.compile(r"\s+is\s+(?:a\s+)?(?:plus|bonus|preferred|nice\s+to\s+have).*$", re.I)
    _GENERIC = {"experience", "strong", "skills", "skill", "communication", "business", "degree",
                "related", "field", "years", "plus", "solid", "nice", "have", "and", "in",
                "with", "the", "a", "an", "of", "to", "work", "working", "sense", "candidates"}
    _DEGREE_STARTS = ("b.s", "b.e", "b.sc", "b.tech", "b.com", "m.s", "m.sc", "m.tech",
                      "mba", "phd", "bachelor", "master")
    _YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")

    @classmethod
    def _keep_phrase(cls, p: str) -> bool:
        if not (2 <= len(p) <= 40 and 1 <= len(p.split()) <= 5):
            return False
        if set(p.split()) & cls._GENERIC:
            return False
        if cls._YEAR_RE.search(p):
            return False
        if any(p.startswith(d) for d in cls._DEGREE_STARTS):
            return False
        if "university" in p or "college" in p:
            return False
        return True

    @classmethod
    def _harvest_section_skills(cls, lines: list) -> list:
        """Skill phrases from the skills section. Two signals: (a) lines the BiLSTM
        labels 'skills', (b) the 1-2 lines directly AFTER a 'SKILLS' heading (the model
        sometimes misses comma-list lines). Degree/year junk is filtered."""
        out = []

        def add(line):
            if re.search(r"\bskills?\b", line) and len(line) < 60:
                return                                     # the heading itself
            for phrase in cls._SPLIT_RE.split(line):
                p = phrase.strip(" -.:\u2022").lower()
                if cls._keep_phrase(p):
                    out.append(p)

        grab = 0
        for row in lines:
            line = row["line"]
            if re.search(r"\bskills?\b", line, re.I) and len(line) < 60:
                grab = 2                                   # harvest the next 2 content lines
                continue
            if grab > 0 and len(line.strip()) > 15:
                grab -= 1
                add(line)
            elif row["section"] == "skills":
                add(line)
        return out

    @classmethod
    def _harvest_jd_skills(cls, jd: str) -> list:
        """Skills from a JD: text after Requirements/Skills/Qualifications headings —
        on the same line (single-line JDs) and on following lines until a blank line."""
        out = []

        def harvest(blob: str):
            cleaned = cls._TRAILING_PLUS_RE.sub("", blob.lstrip("-*\u2022 0123456789. \t"))
            cleaned = cls._PREAMBLE_RE.sub("", cleaned)
            for phrase in cls._SPLIT_RE.split(cleaned):
                p = phrase.strip(" -.:\u2022").lower()
                p = cls._PREAMBLE_RE.sub("", p).strip()
                if cls._keep_phrase(p):
                    out.append(p)

        grab = False
        for ln in jd.splitlines():
            heading = re.search(
                r"requirements|qualifications|technical skills|skills|what you.{0,2}ll (need|bring)", ln, re.I)
            if heading:
                grab = True
                harvest(ln[heading.end():].lstrip(" :-"))   # same-line list: "Requirements: X, Y, Z"
                continue
            if grab:
                if not ln.strip():
                    grab = False
                    continue
                harvest(ln)
        return out

    ALIASES = {
        # Cloud & DevOps
        "k8s": "kubernetes", "kubernetes": "k8s",
        "gcp": "google cloud", "google cloud": "gcp", "google cloud platform": "gcp",
        "aws": "amazon web services", "amazon web services": "aws",
        "azure": "microsoft azure", "microsoft azure": "azure",
        "ci/cd": "continuous integration", "continuous integration": "ci/cd",
        "cd": "continuous delivery", "continuous delivery": "cd",
        # Data & ML
        "ml": "machine learning", "machine learning": "ml",
        "ai": "artificial intelligence", "artificial intelligence": "ai",
        "dl": "deep learning", "deep learning": "dl",
        "nlp": "natural language processing", "natural language processing": "nlp",
        "cv": "computer vision", "computer vision": "cv",
        "llm": "large language models", "large language models": "llm",
        "genai": "generative ai", "generative ai": "genai",
        "tf": "tensorflow", "tensorflow": "tf",
        "sklearn": "scikit-learn", "scikit-learn": "sklearn",
        # Databases & Storage
        "postgres": "postgresql", "postgresql": "postgres",
        "mongo": "mongodb", "mongodb": "mongo",
        "mssql": "sql server", "sql server": "mssql",
        "sql": "relational databases", "relational databases": "sql", "relational database": "sql", "rdbms": "sql",
        # Languages & Web
        "js": "javascript", "javascript": "js",
        "ts": "typescript", "typescript": "ts",
        "py": "python", "python": "py",
        "golang": "go",
        "react": "reactjs", "reactjs": "react",
        "vue": "vuejs", "vuejs": "vue",
        "angular": "angularjs", "angularjs": "angular",
        "node": "nodejs", "nodejs": "node",
        "next": "nextjs", "nextjs": "next.js", "next.js": "nextjs",
        "rest": "restful api", "rest api": "restful api", "restful api": "rest api",
    }

    @staticmethod
    def _clean_token(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", s.lower())

    def skill_overlap(self, resume_entities: dict, resume_lines: list, jd_text: str) -> tuple:
        ner_skills = {s.lower().strip() for s in resume_entities.get("Skills", []) if s.strip()}
        harvested = {s.lower().strip() for s in self._harvest_section_skills(resume_lines) if s.strip()}
        resume_skills = ner_skills | harvested
        if not resume_skills:
            return 0.0, [], [], [], []

        jd_lower = jd_text.lower()
        jd_entities = self.ner.by_type(jd_text)
        jd_skills_raw = {s.lower().strip() for s in jd_entities.get("Skills", []) if s.strip()} | set(
            s.lower().strip() for s in self._harvest_jd_skills(jd_text) if s.strip()
        )

        if not jd_skills_raw:
            jd_skills_raw = {s for s in resume_skills if s in jd_lower}
            if not jd_skills_raw:
                return 0.0, [], sorted(resume_skills), [], []

        exact_matches = []
        semantic_matches = []
        missing = []

        resume_clean_map = {self._clean_token(s): s for s in resume_skills}
        resume_lower_set = set(resume_skills)

        unmatched_jd = []
        for jd_s in sorted(jd_skills_raw):
            j_clean = self._clean_token(jd_s)

            if jd_s in resume_lower_set:
                exact_matches.append(jd_s)
                continue

            if j_clean in resume_clean_map:
                exact_matches.append(jd_s)
                continue

            # Substring match if skill token is sufficiently long (>= 4 chars)
            matched_by_sub = False
            if len(jd_s) >= 4:
                for r_s in resume_skills:
                    if len(r_s) >= 4 and (jd_s in r_s or r_s in jd_s):
                        exact_matches.append(jd_s)
                        matched_by_sub = True
                        break
            if matched_by_sub:
                continue

            # Direct or phrase-contained alias match
            alias_match_found = False
            for k, val in self.ALIASES.items():
                if k == jd_s or (len(k) >= 4 and k in jd_s):
                    if val in resume_lower_set or self._clean_token(val) in resume_clean_map:
                        matched_r = val if val in resume_lower_set else resume_clean_map.get(self._clean_token(val))
                        semantic_matches.append({
                            "jd_skill": jd_s,
                            "resume_skill": matched_r,
                            "similarity": 0.98,
                            "method": "alias"
                        })
                        alias_match_found = True
                        break
            if alias_match_found:
                continue

            unmatched_jd.append(jd_s)

        # Embedding semantic match via MiniLM for remaining unmatched skills
        if unmatched_jd and resume_skills:
            jd_list = list(unmatched_jd)
            res_list = list(resume_skills)
            jd_embs = self.st.encode(jd_list, normalize_embeddings=True)
            res_embs = self.st.encode(res_list, normalize_embeddings=True)
            sim_matrix = jd_embs @ res_embs.T

            for i, jd_s in enumerate(jd_list):
                best_idx = int(sim_matrix[i].argmax())
                best_sim = float(sim_matrix[i][best_idx])
                best_r_skill = res_list[best_idx]

                if best_sim >= 0.74:
                    semantic_matches.append({
                        "jd_skill": jd_s,
                        "resume_skill": best_r_skill,
                        "similarity": round(best_sim, 2),
                        "method": "embedding"
                    })
                else:
                    missing.append(jd_s)
        else:
            missing.extend(unmatched_jd)

        matched_jd_skills = sorted(set(exact_matches) | {m["jd_skill"] for m in semantic_matches})
        total_skills = len(jd_skills_raw) or 1
        score_points = len(exact_matches) * 1.0 + sum(m["similarity"] for m in semantic_matches)
        final_score = min(1.0, score_points / total_skills)

        return (
            final_score,
            matched_jd_skills,
            sorted(missing),
            sorted(exact_matches),
            semantic_matches,
        )

    # ---- component 3: section completeness --------------------------------------------
    @staticmethod
    def section_completeness(section_info: dict) -> tuple:
        presence = section_info["presence"]
        required = ["experience", "education", "project", "skills"]
        present = [s for s in required if presence.get(s)]
        return len(present) / len(required), present, [s for s in required if not presence.get(s)]

    # ---- component 4: role alignment ----------------------------------------------------
    def role_alignment(self, predicted_role: str, jd: str) -> float:
        emb = self.st.encode([f"job role: {predicted_role}", jd[:6000]], normalize_embeddings=True)
        sim = float(emb[0] @ emb[1])
        return max(0.0, min(1.0, (sim + 1) / 2))

    # ---- full analysis -------------------------------------------------------------------
    def analyze(self, resume_text: str, jd_text: str) -> dict:
        entities = self.ner.extract(resume_text)
        name_spans = [e for e in entities if e["type"].lower() == "name"]
        resume_clean = strip_personal(resume_text, name_spans)

        role_pred = self.role.predict(resume_clean)
        resume_lines = self.sections.classify_lines(resume_text)
        section_info = self.sections.section_presence(resume_text, lines=resume_lines)

        sem = self.semantic_similarity(resume_clean, jd_text)
        skill_score, matched_skills, missing_skills, exact_matches, semantic_matches = self.skill_overlap(
            self.ner.by_type(resume_text), resume_lines, jd_text
        )
        section_score, present_sections, missing_sections = self.section_completeness(section_info)
        role_score = self.role_alignment(role_pred["role"], jd_text)

        total = (
            config.W_SEMANTIC * sem
            + config.W_SKILL * skill_score
            + config.W_SECTION * section_score
            + config.W_ROLE * role_score
        ) * 100

        return {
            "overall_score": round(total, 1),
            "breakdown": {
                "semantic_similarity": {"score": round(sem * 100, 1), "weight": config.W_SEMANTIC},
                "skill_overlap": {
                    "score": round(skill_score * 100, 1),
                    "weight": config.W_SKILL,
                    "matched": matched_skills,
                    "missing": missing_skills,
                    "exact_matches": exact_matches,
                    "semantic_matches": semantic_matches,
                },
                "section_completeness": {"score": round(section_score * 100, 1), "weight": config.W_SECTION,
                                         "present": present_sections, "missing": missing_sections},
                "role_alignment": {"score": round(role_score * 100, 1), "weight": config.W_ROLE},
            },
            "predicted_role": role_pred,
            "entities": entities,
            "sections": section_info,
            "section_lines": [{"line": r["line"], "section": r["section"]} for r in resume_lines],
            "privacy": {"names_stripped": len(name_spans), "scored_text_length": len(resume_clean)},
        }
