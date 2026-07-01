import uuid
from typing import Optional, Literal

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config import settings
from database import get_db, Skill
from ml_engine import ml_engine

router = APIRouter(prefix="/api/admin/skills", tags=["Admin - Skills"])
security = HTTPBearer()


def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")


class SkillCreate(BaseModel):
    name: str = Field(..., examples=["Kubernetes"])
    category: str = Field(..., examples=["DevOps"])
    difficulty: Literal["easy", "medium", "hard"]


class SkillUpdate(BaseModel):
    category: Optional[str] = None
    difficulty: Optional[Literal["easy", "medium", "hard"]] = None


@router.get("/")
def list_skills(db: Session = Depends(get_db), _=Depends(verify_admin)):
    """Get all skills in the database"""
    skills = db.query(Skill).all()
    return [{"name": s.name, "category": s.category, "difficulty": s.difficulty} for s in skills]


@router.post("/", status_code=201)
def create_skill(skill: SkillCreate, db: Session = Depends(get_db), _=Depends(verify_admin)):
    """Add a new skill and rebuild the semantic search index"""
    existing = db.query(Skill).filter(Skill.name == skill.name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Skill '{skill.name}' already exists")

    new_skill = Skill(id=str(uuid.uuid4()), name=skill.name, category=skill.category, difficulty=skill.difficulty)
    db.add(new_skill)
    db.commit()

    ml_engine.reload_skills(db)  # rebuild FAISS index so the new skill is searchable immediately

    return {"name": skill.name, "category": skill.category, "difficulty": skill.difficulty}


@router.patch("/{skill_name}")
def update_skill(skill_name: str, update: SkillUpdate, db: Session = Depends(get_db), _=Depends(verify_admin)):
    """Update an existing skill's metadata"""
    existing = db.query(Skill).filter(Skill.name == skill_name).first()
    if not existing:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")

    if update.category is not None:
        existing.category = update.category
    if update.difficulty is not None:
        existing.difficulty = update.difficulty

    db.commit()
    ml_engine.reload_skills(db)

    return {"name": existing.name, "category": existing.category, "difficulty": existing.difficulty}


@router.delete("/{skill_name}", status_code=204)
def delete_skill(skill_name: str, db: Session = Depends(get_db), _=Depends(verify_admin)):
    """Delete a skill and rebuild the semantic search index"""
    existing = db.query(Skill).filter(Skill.name == skill_name).first()
    if not existing:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")

    db.delete(existing)
    db.commit()
    ml_engine.reload_skills(db)
    return None
