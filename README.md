# PrepIQ: AI-Powered Resume Analysis 
(Renamed from Interview Prep System)

## What changed from the original code

**Backend bugs fixed:**
- `ml_engine.py` — skills now load dynamically from the database (`Skill` table) instead of a hardcoded dict; `reload_skills(db)` rebuilds the FAISS index after any admin change.
- `extract_skills()` — combines exact-substring matching (reliable for short tokens like "AWS", "SQL") with FAISS semantic search (catches paraphrases), instead of relying on FAISS alone with an unused `k=10` cutoff.
- `re` import — was unused dead code; now actually used in `_clean_text()` to normalize resume/JD text before matching.
- `get_recommended_topics()` / `get_interview_questions()` — now read from DB tables (`LearningResource`, `InterviewQuestionDB`) instead of 4–5 hardcoded skills, so **any** skill in the database works, with a graceful fallback for skills with no curated resources yet.
- `app.py` — `find_skill_matches()` now works correctly because both `resume_skills` and `jd_skills` come from the same canonical vocabulary (the skill DB), so exact-set comparison is valid again.
- `app.py` — fixed `get_recommendations` endpoint, which previously overwrote duplicate-topic interview questions in a dict comprehension; now properly groups by topic.
- `app.py` — added file-size enforcement (`MAX_FILE_SIZE` was defined in config but never checked) and extension validation before parsing.
- `models.py` — `recommended_topics` / `interview_questions` now return full objects (with `resources`, `priority`, `difficulty`) instead of bare strings, matching what the frontend actually needs.
- Added `admin_routes.py` — Bearer-token-protected CRUD for skills (`POST /api/admin/skills/`, `PATCH /api/admin/skills/{name}`, `DELETE /api/admin/skills/{name}`), each triggering a live FAISS rebuild.
- Added `seed_data.py` — idempotent seeding for skills/questions/resources (safe to re-run).

**Frontend changes:**
- `Results.jsx` — updated to render full topic/question objects (priority badges, difficulty badges, resource lists) instead of plain strings.
- `App.css` — added styles for the new topic cards and badges.
- `App.jsx`, `Upload.jsx`, `index.js`, `index.html` — unchanged, no bugs found.

**Database: PostgreSQL → MySQL**
- `database.py` — uses `pymysql` driver, added `pool_pre_ping`/`pool_recycle` (MySQL connections time out differently than Postgres).
- `schema.sql` — added `ENGINE=InnoDB`, `utf8mb4` charset, `ON DUPLICATE KEY UPDATE` instead of Postgres-style upserts, `LONGTEXT` for large text fields.
- `requirements.txt` — `pymysql` instead of `psycopg2-binary`.

---

## Setup

### 1. Install MySQL and create the database
```bash
mysql -u root -p < backend/schema.sql
```
This creates the `interview_prep` database, tables, and a small set of sample rows.

### 2. Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL / ADMIN_TOKEN
python seed_data.py    # idempotent — populates skills/questions/resources
python app.py          # runs on http://localhost:8000
```

### 3. Frontend
```bash
cd frontend
npm install
npm start               # runs on http://localhost:3000
```

---

## Admin API usage

```bash
# List all skills
curl -H "Authorization: Bearer <ADMIN_TOKEN>" http://localhost:8000/api/admin/skills/

# Add a skill — searchable immediately, no restart needed
curl -X POST http://localhost:8000/api/admin/skills/ \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Kubernetes", "category": "DevOps", "difficulty": "hard"}'

# Update a skill
curl -X PATCH http://localhost:8000/api/admin/skills/Kubernetes \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"difficulty": "medium"}'

# Delete a skill
curl -X DELETE http://localhost:8000/api/admin/skills/Kubernetes \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

To add resources/questions for new skills, insert rows into `learning_resources` / `interview_questions` directly (or extend `admin_routes.py` with equivalent endpoints — same pattern as the skills CRUD).

---

## Testing notes

All backend logic (FAISS index build, skill extraction, matching, scoring, recommendations, admin CRUD + live reload) was verified end-to-end with FastAPI's `TestClient` using a SQLite stand-in database and a mocked embedding model (this sandbox has no network access to Hugging Face or a live MySQL server). Swap in real MySQL + the real `sentence-transformers` model and no code changes are needed — only `DATABASE_URL`.
