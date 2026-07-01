from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, JSON, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from config import settings

# MySQL connection (uses PyMySQL driver — see config.py / .env for DATABASE_URL format)
# Example DATABASE_URL: mysql+pymysql://user:password@localhost:3306/interview_prep
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,   # avoids stale connection errors with MySQL's connection timeout
    pool_recycle=3600,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True)
    resume_text = Column(Text)
    jd_text = Column(Text)
    match_score = Column(Float)
    matched_skills = Column(JSON)
    missing_skills = Column(JSON)
    recommended_topics = Column(JSON)
    interview_questions = Column(JSON)
    study_plan = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class Skill(Base):
    __tablename__ = "skills"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50))
    difficulty = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)


class InterviewQuestionDB(Base):
    __tablename__ = "interview_questions"

    id = Column(String(36), primary_key=True)
    question = Column(Text, nullable=False)
    skill = Column(String(100))
    difficulty = Column(String(20))
    topic = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class LearningResource(Base):
    __tablename__ = "learning_resources"

    id = Column(String(36), primary_key=True)
    topic = Column(String(100))
    title = Column(String(255))
    url = Column(String(500))
    resource_type = Column(String(50))  # "video", "article", "course"
    priority = Column(String(20), default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)


class PendingSkill(Base):
    """
    Skills suggested by the local LLM (see skill_discovery.py) that have
    NOT been added to the live Skill table yet. LLM suggestions are never
    trusted directly — a human approves or rejects each one via the admin
    API before it can affect real resume/JD matching. This prevents
    hallucinated or low-quality suggestions (e.g. "SumoBot Competition")
    from polluting the skill database.
    """
    __tablename__ = "pending_skills"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50))
    difficulty = Column(String(20))
    source_text_snippet = Column(Text)  # the original phrase it was extracted from, for human review
    status = Column(String(20), default="pending")  # "pending", "approved", "rejected"
    created_at = Column(DateTime, default=datetime.utcnow)


# Create tables
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
