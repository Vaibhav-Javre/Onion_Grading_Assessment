import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "oniongrade_ai_dev_secret_key_2026_supersecure")
    
    db_url = os.getenv("DATABASE_URL", "").strip()
    if not db_url or "sqlite:///instance" in db_url:
        db_url = f"sqlite:///{str(BASE_DIR / 'instance' / 'oniongrade.db').replace(os.sep, '/')}"
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Directories
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")
    PDF_REPORT_FOLDER = os.path.join(BASE_DIR, "reports", "pdf")
    MODEL_FOLDER = os.path.join(BASE_DIR, "models")
    STATIC_SAMPLES_FOLDER = os.path.join(BASE_DIR, "static", "samples")
    
    # Upload limits
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB max upload
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    # AI Model Paths
    DETECTION_MODEL = os.getenv("DETECTION_MODEL", "models/best.pt")
    CLASSIFICATION_MODEL = os.getenv("CLASSIFICATION_MODEL", "models/final_onion_quality_model.keras")
    
    DETECTION_MODEL_PATH = os.path.join(BASE_DIR, DETECTION_MODEL)
    CLASSIFICATION_MODEL_PATH = os.path.join(BASE_DIR, CLASSIFICATION_MODEL)
    
    # AI Thresholds
    YOLO_CONFIDENCE_THRESHOLD = float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", 0.25))
    CLASSIFIER_CONFIDENCE_THRESHOLD = float(os.getenv("CLASSIFIER_CONFIDENCE_THRESHOLD", 0.50))
    MOCK_AI_MODE = os.getenv("MOCK_AI_MODE", "False").lower() in ("true", "1", "t")

    # Quality classes order matches Keras classifier output
    QUALITY_CLASSES = ["Damaged", "Healthy", "Rotten", "Sprouted"]

    # Grading mapping:
    # Healthy -> Grade A
    # Damaged -> URS (Under Regular Standard)
    # Rotten -> Rejected
    # Sprouted -> Rejected
    GRADING_RULES = {
        "Healthy": "Grade A",
        "Damaged": "URS",
        "Rotten": "Rejected",
        "Sprouted": "Rejected"
    }

    # Market Price Service & Data.gov.in API
    DATA_GOV_API_KEY = (os.getenv("DATA_GOV_API_KEY") or os.getenv("MARKET_API_KEY") or "").strip()
    MARKET_API_KEY = DATA_GOV_API_KEY
    MARKET_API_URL = os.getenv("MARKET_API_URL", "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070").strip()
    MARKET_CACHE_TTL_SECONDS = int(os.getenv("MARKET_CACHE_TTL_SECONDS", 300))
    DEFAULT_REFERENCE_MANDI = os.getenv("DEFAULT_REFERENCE_MANDI", "Lasalgaon").strip()

    # Price Estimation Engine Factors
    PRICE_FACTORS = {
        "Grade A": 1.0,   # 100%
        "URS": 0.8,       # 80%
        "Rejected": 0.0   # 0%
    }

