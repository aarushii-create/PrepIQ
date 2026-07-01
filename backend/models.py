from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime


class RecommendedTopic(BaseModel):
    name: str
    resources: List[str]
    priority: str  # "high", "medium", "low"


class InterviewQuestion(BaseModel):
    question: str
    skill: str
    difficulty: str  # "easy", "medium", "hard"
    topic: str


class AnalysisResult(BaseModel):
    id: str
    resume_text: str
    jd_text: str
    match_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    recommended_topics: List[RecommendedTopic]   # full objects, not just names —
    interview_questions: List[InterviewQuestion]  # frontend needs resources/priority/difficulty
    created_at: datetime


class StudyPlan(BaseModel):
    analysis_id: str
    topics: List[RecommendedTopic]
    estimated_hours: int
    priority_order: List[str]
    questions_by_topic: Dict[str, List[str]]


class UploadResponse(BaseModel):
    analysis_id: str
    message: str
    status: str
