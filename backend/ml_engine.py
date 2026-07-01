import re
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session

from config import settings


class MLEngine:
    """
    Semantic skill-matching engine.

    All skill/question/resource data is loaded dynamically from the database
    (see database.py: Skill, InterviewQuestionDB, LearningResource) rather than
    hardcoded, so an admin API can add/edit/remove skills at runtime via
    `reload_skills(db)` without restarting the service.
    """

    def __init__(self):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.skill_database: Dict[str, dict] = {}
        self.index: Optional[faiss.IndexFlatIP] = None
        self.index_skills: List[str] = []
        # Cached lookups, rebuilt alongside the FAISS index
        self._questions_by_skill: Dict[str, List[dict]] = {}
        self._resources_by_skill: Dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Text cleanup (this is what `re` is actually for)
    # ------------------------------------------------------------------
    def _clean_text(self, text: str) -> str:
        """
        Normalize raw resume/JD text before embedding or matching.
        Strips noisy punctuation/markup while preserving tokens that matter
        for skill names, e.g. 'C++', 'C#', 'Node.js', 'CI/CD'.
        """
        text = re.sub(r"\s+", " ", text)                      # collapse whitespace/newlines
        text = re.sub(r"[^\w\s+#./-]", " ", text)              # strip stray punctuation
        return text.strip()

    # ------------------------------------------------------------------
    # Dynamic loading from DB + FAISS index build
    # ------------------------------------------------------------------
    def reload_skills(self, db: Session):
        """
        Reload skills, interview questions, and learning resources from the
        database, then rebuild the FAISS index. Call this after any admin
        create/update/delete operation so search stays in sync.
        """
        from database import Skill, InterviewQuestionDB, LearningResource  # local import avoids circular import

        skills = db.query(Skill).all()
        self.skill_database = {
            s.name: {"category": s.category, "difficulty": s.difficulty} for s in skills
        }

        questions = db.query(InterviewQuestionDB).all()
        self._questions_by_skill = {}
        for q in questions:
            self._questions_by_skill.setdefault(q.skill, []).append(
                {"question": q.question, "difficulty": q.difficulty, "topic": q.topic, "skill": q.skill}
            )

        resources = db.query(LearningResource).all()
        self._resources_by_skill = {}
        for r in resources:
            entry = self._resources_by_skill.setdefault(
                r.topic, {"resources": [], "priority": r.priority or "medium"}
            )
            entry["resources"].append(r.title)

        self._build_faiss_index()

    def _build_faiss_index(self):
        skill_names = list(self.skill_database.keys())
        if not skill_names:
            self.index = None
            self.index_skills = []
            return

        embeddings = self.model.encode(skill_names, convert_to_numpy=True)
        faiss.normalize_L2(embeddings)

        self.index = faiss.IndexFlatIP(embeddings.shape[1])  # inner product == cosine on normalized vecs
        self.index.add(embeddings)
        self.index_skills = skill_names

    # ------------------------------------------------------------------
    # Explicit skill relationships (specific product implies general skill)
    # ------------------------------------------------------------------
    # Embeddings alone don't reliably capture "is-a-specific-instance-of"
    # relationships at the 0.70 threshold (e.g. "MySQL" vs "SQL" — related
    # but not synonymous, so FAISS often scores them just under threshold).
    # This is encoded explicitly rather than left to chance, so the system's
    # behavior here is predictable and easy to debug.
    SKILL_IMPLICATIONS: Dict[str, List[str]] = {
        "MySQL": ["SQL"],
        "PostgreSQL": ["SQL"],
        "SQLite": ["SQL"],
        "AWS EC2": ["AWS"],
        "AWS S3": ["AWS"],
        "Next.js": ["React"],
        "Express.js": ["Node.js"],
    }

    def _expand_implied_skills(self, skills: List[str]) -> List[str]:
        """
        If someone lists "MySQL", they necessarily know SQL — expand the
        detected skill set with these explicit, always-true implications
        before matching against the JD's required skills.
        """
        expanded = set(skills)
        for skill in skills:
            expanded.update(self.SKILL_IMPLICATIONS.get(skill, []))
        return list(expanded)

    # ------------------------------------------------------------------
    # Skill extraction (semantic, via FAISS)
    # ------------------------------------------------------------------
    def extract_skills(self, text: str, threshold: float = None) -> List[str]:
        """
        Extract skills from resume/JD text using semantic similarity search
        against the skill index, PLUS an exact-substring pass as a safety net
        for short/abbreviation-heavy skill names FAISS sometimes under-scores
        (e.g. 'SQL', 'AWS').
        """
        if threshold is None:
            threshold = settings.SKILL_MATCH_THRESHOLD

        if not self.index or not self.skill_database:
            return []

        cleaned = self._clean_text(text)
        text_lower = cleaned.lower()

        found = set()

        # 1) Exact substring pass — cheap and very reliable for short skill tokens
        for skill in self.skill_database.keys():
            if re.search(rf"\b{re.escape(skill.lower())}\b", text_lower):
                found.add(skill)

        # 2) Semantic pass via FAISS — catches paraphrases/synonyms exact match misses
        # Chunk long text into sentences so one embedding doesn't dilute the signal
        chunks = [c.strip() for c in re.split(r"[.\n;]", cleaned) if c.strip()]
        if not chunks:
            chunks = [cleaned]

        chunk_embeddings = self.model.encode(chunks, convert_to_numpy=True)
        faiss.normalize_L2(chunk_embeddings)

        k = min(5, len(self.index_skills))
        scores, indices = self.index.search(chunk_embeddings, k=k)

        for score_row, idx_row in zip(scores, indices):
            for score, i in zip(score_row, idx_row):
                if i == -1:
                    continue
                if score >= threshold:
                    found.add(self.index_skills[i])

        return self._expand_implied_skills(list(found))

    # ------------------------------------------------------------------
    # Similarity / matching / scoring
    # ------------------------------------------------------------------
    def calculate_similarity(self, resume_text: str, jd_text: str) -> float:
        """Overall semantic similarity between resume and JD (cosine, via sentence embeddings)."""
        resume_embedding = self.model.encode(resume_text, convert_to_numpy=True)
        jd_embedding = self.model.encode(jd_text, convert_to_numpy=True)

        similarity = np.dot(resume_embedding, jd_embedding) / (
            np.linalg.norm(resume_embedding) * np.linalg.norm(jd_embedding)
        )
        return float(similarity)

    def find_skill_matches(self, resume_skills: List[str], jd_skills: List[str]) -> Tuple[List[str], List[str]]:
        """
        Find matched/missing skills.
        Since extract_skills() now returns canonical skill names (from the same
        skill_database key set for both resume and JD), exact set comparison
        is correct here — both lists are already normalized against the same
        vocabulary, so no separate fuzzy-matching step is needed at this stage.
        """
        resume_set = set(resume_skills)
        jd_set = set(jd_skills)

        matched = list(resume_set & jd_set)
        missing = list(jd_set - resume_set)

        return matched, missing

    def calculate_match_score(self, matched_skills: List[str], jd_skills: List[str]) -> float:
        if not jd_skills:
            return 0.0
        return (len(matched_skills) / len(jd_skills)) * 100

    # ------------------------------------------------------------------
    # Recommendations (now DB-backed, works for ANY skill in the DB)
    # ------------------------------------------------------------------
    def get_recommended_topics(self, missing_skills: List[str]) -> List[Dict]:
        topics = []
        for skill in missing_skills:
            entry = self._resources_by_skill.get(skill)
            if entry and entry["resources"]:
                topics.append({
                    "name": skill,
                    "resources": entry["resources"],
                    "priority": entry["priority"],
                })
            else:
                # Fallback so newly-added skills with no curated resources yet
                # still show up instead of silently disappearing.
                topics.append({
                    "name": skill,
                    "resources": [f"Search for '{skill}' courses on Coursera, Udemy, or official docs"],
                    "priority": "medium",
                })
        return topics

    def get_interview_questions(self, missing_skills: List[str], db: Session = None) -> List[Dict]:
        """
        Returns interview questions for each missing skill. For any skill
        with no curated questions in the database, attempts to generate
        them via a local LLM (see question_generator.py) and caches the
        result by writing new rows into InterviewQuestionDB — so the same
        skill is only ever generated once across all future requests.

        Falls back silently to "no questions for this skill" if generation
        fails (e.g. Ollama isn't running) rather than breaking the request.
        """
        from database import InterviewQuestionDB  # local import avoids circular import
        import uuid
        import question_generator

        questions = []
        for skill in missing_skills:
            existing = self._questions_by_skill.get(skill)
            print(f"[get_interview_questions] skill='{skill}' existing={bool(existing)} db={db is not None}")

            if existing:
                questions.extend(existing)
                continue

            # No curated questions for this skill — try generating + caching them.
            if db is None or not settings.ENABLE_LLM_QUESTION_GENERATION:
                print(f"[get_interview_questions] skipping generation for '{skill}' — db={db is not None} flag={settings.ENABLE_LLM_QUESTION_GENERATION}")
                continue  # generation disabled (e.g. deployed env) or no DB session — skip, no crash

            print(f"[get_interview_questions] attempting generation for '{skill}'")
            generated = question_generator.generate_questions_for_skill(skill)
            if not generated:
                continue  # local model unavailable or failed — degrade gracefully, no crash

            for q in generated:
                db.add(InterviewQuestionDB(
                    id=str(uuid.uuid4()),
                    question=q["question"],
                    skill=q["skill"],
                    difficulty=q["difficulty"],
                    topic=q["topic"],
                ))
            db.commit()

            # Update the in-memory cache too, so a second missing skill in
            # this same request (or the next request) doesn't regenerate.
            self._questions_by_skill[skill] = generated
            questions.extend(generated)

        return questions[:30]  # enough for all missing skills without being overwhelming


# Global ML engine instance — call ml_engine.reload_skills(db) at app startup
# (see app.py lifespan) to populate it from the database before first use.
ml_engine = MLEngine()