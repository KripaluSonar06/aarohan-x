"""
Global configuration loaded from environment variables.
All settings are centralized here for easy modification.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    """Application settings."""

    # --- LLM ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_TEMPERATURE_CLASSIFY: float = 0.0
    GROQ_TEMPERATURE_GENERATE: float = 0.7
    GROQ_MAX_TOKENS: int = 500

    # Ollama fallback (if Groq fails)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = "llama3.2:3b"

    # --- LangSmith ---
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
    LANGSMITH_TRACING_V2: str = os.getenv("LANGSMITH_TRACING_V2", "false")
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "aarohan-x")

    # --- Razorpay ---
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_TEST_MODE: bool = True  # always test in this build

    # --- Voice (Sarvam) ---
    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")
    SARVAM_BASE_URL: str = "https://api.sarvam.ai/v1"

    # --- Database ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'aarohan.db'}")

    # --- Policy defaults (can be overridden by merchant in UI) ---
    # These are system maximums; merchant can only lower them.
    SYSTEM_MAX_SILENT_RETRIES: int = 2
    SYSTEM_MAX_CUSTOMER_CONTACTS: int = 2
    SYSTEM_MAX_PTP_PROMISES: int = 2
    VOICE_MIN_AMOUNT_PAISE: int = 50000  # ₹500
    QUIET_HOURS_START: int = 21  # 9 PM
    QUIET_HOURS_END: int = 9    # 9 AM
    STOP_WORDS: list = ["ruko", "stop", "mat call karo", "unsubscribe", "band karo"]

    # --- Channel costs (in INR) ---
    SMS_COST: float = 0.10
    VOICE_COST: float = 5.00
    PAYMENT_LINK_COST: float = 0.0
    DISCOUNT_MAX_PERCENT: float = 5.0  # merchant can set lower

    # --- Scheduling ---
    TIMEZONE: str = "Asia/Kolkata"

    # --- Paths ---
    MODEL_SAVE_DIR: Path = BASE_DIR / "models" / "saved_models"
    DATA_DIR: Path = BASE_DIR / "data"
    LOG_DIR: Path = BASE_DIR / "logs"

    def __init__(self):
        # Ensure directories exist
        self.MODEL_SAVE_DIR.mkdir(parents=True, exist_ok=True)
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)

        # If LangSmith tracing is enabled, set environment
        if self.LANGSMITH_TRACING_V2.lower() == "true":
            os.environ["LANGSMITH_TRACING"] = "true"
            os.environ["LANGSMITH_API_KEY"] = self.LANGSMITH_API_KEY
            os.environ["LANGSMITH_PROJECT"] = self.LANGSMITH_PROJECT

settings = Settings()