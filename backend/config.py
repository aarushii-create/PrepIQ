from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database — MySQL via PyMySQL driver
    # Format: mysql+pymysql://<user>:<password>@<host>:<port>/<db_name>
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/interview_prep"

    # ML Models
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    SKILL_MATCH_THRESHOLD: float = 0.70  # cosine similarity threshold for FAISS skill matching

    # Local LLM question generation (via Ollama) — only works where Ollama is
    # actually running, which free hosting tiers generally don't support
    # (no persistent server, often <512MB RAM, no GPU). Set to False in any
    # deployed/production environment via .env; leave True for local dev.
    ENABLE_LLM_QUESTION_GENERATION: bool = True

    # API Config
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True

    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "docx", "txt"]

    # Admin API
    ADMIN_TOKEN: str = "change-me-in-env"

    class Config:
        env_file = ".env"


settings = Settings()
