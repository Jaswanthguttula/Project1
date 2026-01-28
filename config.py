"""
Configuration management for the Contract Clause Detection System
"""

import os

# Optional dependency: allow running even if python-dotenv isn't installed.
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except ModuleNotFoundError:
    # .env loading is optional; environment variables can still be provided
    # through the shell/process manager.
    pass


class Config:
    """Base configuration"""

    # Database
    IS_VERCEL = os.environ.get("VERCEL") == "1"
    DEFAULT_DB = "sqlite:////tmp/contracts.db" if IS_VERCEL else "sqlite:///./contracts.db"
    DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB)

    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-12345")

    # API
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 5000))
    # Default to non-debug for a cleaner, more stable "launch" experience.
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # NLP Models
    SPACY_MODEL = os.getenv("SPACY_MODEL", "en_core_web_lg")
    TRANSFORMER_MODEL = os.getenv(
        "TRANSFORMER_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )

    # Risk Assessment Thresholds
    HIGH_RISK_THRESHOLD = float(os.getenv("HIGH_RISK_THRESHOLD", 0.8))
    MEDIUM_RISK_THRESHOLD = float(os.getenv("MEDIUM_RISK_THRESHOLD", 0.5))

    # Conflict Detection
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 0.85))
    CONFLICT_THRESHOLD = float(os.getenv("CONFLICT_THRESHOLD", 0.3))

    # Directories
    # On Vercel, we must use /tmp for any writable operations
    IS_VERCEL = os.environ.get("VERCEL") == "1"
    
    BASE_DIR = "/tmp" if IS_VERCEL else "."
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    REPORTS_FOLDER = os.path.join(BASE_DIR, "generated_reports")
    TEMP_FOLDER = os.path.join(BASE_DIR, "temp_files")

    # Clause Types (Common contract clause categories)
    CLAUSE_TYPES = [
        "OBLIGATION",
        "EXCLUSION",
        "TERMINATION",
        "LIABILITY",
        "PAYMENT",
        "CONFIDENTIALITY",
        "INTELLECTUAL_PROPERTY",
        "WARRANTY",
        "INDEMNIFICATION",
        "FORCE_MAJEURE",
        "DISPUTE_RESOLUTION",
        "AMENDMENT",
        "GENERAL",
    ]

    # Risk Levels
    RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    @classmethod
    def init_directories(cls):
        """Create necessary directories if they don't exist"""
        for folder in [cls.UPLOAD_FOLDER, cls.REPORTS_FOLDER, cls.TEMP_FOLDER]:
            os.makedirs(folder, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
