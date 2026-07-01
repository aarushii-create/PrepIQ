"""
Debug helper: traces each stage of the resume/JD matching pipeline so you can
see exactly where a 0% match score is coming from, instead of guessing.

Usage:
    python debug_match.py path/to/resume.txt path/to/jd.txt

(Use .txt files for this test to rule out PDF extraction issues first —
 if matching works on .txt but not .pdf, the bug is in PDF text extraction,
 not in ml_engine.)
"""
import sys
from database import SessionLocal
from ml_engine import ml_engine


def main():
    if len(sys.argv) != 3:
        print("Usage: python debug_match.py <resume.txt> <jd.txt>")
        sys.exit(1)

    resume_path, jd_path = sys.argv[1], sys.argv[2]

    with open(resume_path, "r", encoding="utf-8") as f:
        resume_text = f.read()
    with open(jd_path, "r", encoding="utf-8") as f:
        jd_text = f.read()

    print("=" * 70)
    print("STAGE 0: Raw extracted text (first 200 chars)")
    print("=" * 70)
    print("RESUME:", repr(resume_text[:200]))
    print("JD:    ", repr(jd_text[:200]))
    print()

    if not resume_text.strip() or not jd_text.strip():
        print("!!! One of the files is EMPTY after reading. That's your bug.")
        return

    # Load skills from DB into ml_engine, same as app.py's lifespan does
    db = SessionLocal()
    ml_engine.reload_skills(db)
    db.close()

    print("=" * 70)
    print(f"STAGE 1: Skill database loaded ({len(ml_engine.skill_database)} skills)")
    print("=" * 70)
    print(sorted(ml_engine.skill_database.keys()))
    print()

    if len(ml_engine.skill_database) == 0:
        print("!!! Skill database is EMPTY. Did seed_data.py actually commit to the DB")
        print("!!! you're connecting to? Check your .env DATABASE_URL matches.")
        return

    print("=" * 70)
    print("STAGE 2: extract_skills() output")
    print("=" * 70)
    resume_skills = ml_engine.extract_skills(resume_text)
    jd_skills = ml_engine.extract_skills(jd_text)
    print("RESUME skills found:", sorted(resume_skills))
    print("JD skills found:    ", sorted(jd_skills))
    print()

    if len(jd_skills) == 0:
        print("!!! No skills detected in the JD at all. Either the JD text doesn't")
        print("!!! contain any of the seeded skill names, or extraction is broken.")
        print("!!! Try lowering the threshold below and re-running:")
        print("!!!   ml_engine.extract_skills(jd_text, threshold=0.5)")
        return

    print("=" * 70)
    print("STAGE 3: find_skill_matches() output")
    print("=" * 70)
    matched, missing = ml_engine.find_skill_matches(resume_skills, jd_skills)
    print("Matched:", sorted(matched))
    print("Missing:", sorted(missing))
    print()

    print("=" * 70)
    print("STAGE 4: Final match score")
    print("=" * 70)
    score = ml_engine.calculate_match_score(matched, jd_skills)
    print(f"Score: {score}%")
    print()

    if score == 0.0 and len(matched) == 0 and len(resume_skills) > 0 and len(jd_skills) > 0:
        print("Both resume and JD have skills detected, but ZERO overlap.")
        print("Check: do the skill *names* match exactly between the two lists above?")
        print("(extract_skills should return canonical names from skill_database,")
        print(" so this would be unusual unless skill names differ in case/spacing)")


if __name__ == "__main__":
    main()
