import io
import uuid
from contextlib import asynccontextmanager

import PyPDF2
from docx import Document
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from config import settings
from database import get_db, SessionLocal, Analysis
from ml_engine import ml_engine
from admin_routes import router as admin_router
from models import (
    AnalysisResult,
    RecommendedTopic,
    InterviewQuestion,
    StudyPlan,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Populate the ML engine's skill database + FAISS index from the DB on startup,
    # so it's never running on stale/empty data.
    db = SessionLocal()
    try:
        ml_engine.reload_skills(db)
    finally:
        db.close()

    # Warm up the local Ollama model so it's already loaded into memory
    # before the first real request arrives. Without this, the first
    # analysis that triggers generation has to wait for the model to cold-
    # load (~30-60s on CPU), which causes a timeout. A single cheap warmup
    # prompt at startup eliminates that delay for all subsequent requests.
    if settings.ENABLE_LLM_QUESTION_GENERATION:
        try:
            import requests as req
            req.post(
                "http://localhost:11434/api/generate",
                json={"model": "llama3.2:1b", "prompt": "hi", "stream": False},
                timeout=90,  # generous — this is a one-time cost at startup
            )
            print("[startup] Ollama model warmed up successfully")
        except Exception:
            print("[startup] Ollama warmup skipped — model not available, generation will be disabled")

    yield


app = FastAPI(
    title="Interview Prep System",
    description="AI-powered resume vs JD analysis",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)


# ----------------------------------------------------------------------
# File text extraction
# ----------------------------------------------------------------------
def extract_text_from_pdf(file_content: bytes) -> str:
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text


def extract_text_from_docx(file_content: bytes) -> str:
    doc = Document(io.BytesIO(file_content))
    return "\n".join(para.text for para in doc.paragraphs)


def extract_text_from_txt(file_content: bytes) -> str:
    return file_content.decode("utf-8", errors="ignore")


async def extract_file_text(file: UploadFile) -> str:
    content = await file.read()

    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File '{file.filename}' exceeds the {settings.MAX_FILE_SIZE // (1024*1024)}MB limit",
        )

    file_extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""

    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file format: .{file_extension}")

    if file_extension == "pdf":
        return extract_text_from_pdf(content)
    elif file_extension == "docx":
        return extract_text_from_docx(content)
    elif file_extension == "txt":
        return extract_text_from_txt(content)

    raise HTTPException(status_code=400, detail="Unsupported file format")


# ----------------------------------------------------------------------
# Core analysis endpoint
# ----------------------------------------------------------------------
@app.post("/api/analyze", response_model=AnalysisResult)
async def analyze(
    resume: UploadFile = File(...),
    job_description: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    resume_text = await extract_file_text(resume)
    jd_text = await extract_file_text(job_description)

    if not resume_text.strip() or not jd_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from one of the files")

    # Extract skills (semantic, via FAISS — see ml_engine.extract_skills)
    resume_skills = ml_engine.extract_skills(resume_text)
    jd_skills = ml_engine.extract_skills(jd_text)

    # Both lists come from the same canonical skill vocabulary, so exact-set
    # comparison here is correct (the fuzzy matching already happened upstream).
    matched_skills, missing_skills = ml_engine.find_skill_matches(resume_skills, jd_skills)

    match_score = ml_engine.calculate_match_score(matched_skills, jd_skills)

    recommended_topics = ml_engine.get_recommended_topics(missing_skills)
    interview_questions = ml_engine.get_interview_questions(missing_skills, db=db)

    analysis_id = str(uuid.uuid4())

    study_plan = {
        "topics": [t["name"] for t in recommended_topics],
        "estimated_hours": len(missing_skills) * 10,
        "priority_order": sorted(
            [t["name"] for t in recommended_topics],
            key=lambda name: {"high": 0, "medium": 1, "low": 2}.get(
                next((t["priority"] for t in recommended_topics if t["name"] == name), "low"), 2
            ),
        ),
    }

    analysis = Analysis(
        id=analysis_id,
        resume_text=resume_text,
        jd_text=jd_text,
        match_score=match_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        recommended_topics=recommended_topics,    # store full objects (list of dicts)
        interview_questions=interview_questions,  # store full objects (list of dicts)
        study_plan=study_plan,
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return AnalysisResult(
        id=analysis_id,
        resume_text=resume_text,
        jd_text=jd_text,
        match_score=match_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        recommended_topics=[RecommendedTopic(**t) for t in recommended_topics],
        interview_questions=[InterviewQuestion(**q) for q in interview_questions],
        created_at=analysis.created_at,
    )


@app.get("/api/recommendations/{analysis_id}", response_model=StudyPlan)
async def get_recommendations(analysis_id: str, db: Session = Depends(get_db)):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Group questions by topic without overwriting duplicates (fixes the
    # original dict-comprehension bug that clobbered same-topic questions)
    questions_by_topic: dict[str, list[str]] = {}
    for q in analysis.interview_questions:
        questions_by_topic.setdefault(q["topic"], []).append(q["question"])

    return StudyPlan(
        analysis_id=analysis_id,
        topics=[RecommendedTopic(**t) for t in analysis.recommended_topics],
        estimated_hours=analysis.study_plan["estimated_hours"],
        priority_order=analysis.study_plan["priority_order"],
        questions_by_topic=questions_by_topic,
    )


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "Interview Prep System"}


@app.get("/")
async def root():
    return {
        "message": "Interview Prep System API",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)