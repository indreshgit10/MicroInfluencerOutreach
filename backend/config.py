import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# File paths for all pipeline deliverables
RAW_DATA_PATH = DATA_DIR / "influencers_discovered.json"
RAW_DATA_CSV = DATA_DIR / "influencers_discovered.csv"

FILTERED_DATA_PATH = DATA_DIR / "influencers_filtered.json"
FILTERED_DATA_CSV = DATA_DIR / "influencers_filtered.csv"

ENRICHED_DATA_PATH = DATA_DIR / "influencers_enriched.json"
ENRICHED_DATA_CSV = DATA_DIR / "influencers_enriched.csv"

OUTREACH_DATA_PATH = DATA_DIR / "personalized_outreach.json"
OUTREACH_DATA_CSV = DATA_DIR / "personalized_outreach.csv"

TRACKER_DATA_PATH = DATA_DIR / "outreach_tracker.json"
TRACKER_DATA_CSV = DATA_DIR / "outreach_tracker.csv"

# Pipeline Default Configuration
DEFAULT_TARGET_NICHE = os.getenv("TARGET_NICHE", "Technology")
MIN_FOLLOWERS = int(os.getenv("MIN_FOLLOWERS", "5000"))
MAX_FOLLOWERS = int(os.getenv("MAX_FOLLOWERS", "100000"))
MIN_ENGAGEMENT_RATE = float(os.getenv("MIN_ENGAGEMENT_RATE", "1.5"))

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto") # auto, gemini, openai, groq, heuristic
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Outreach & Sending Configuration
SENDING_MODE = os.getenv("SENDING_MODE", "simulation") # simulation or smtp
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "partnerships@edxso-outreach.io")
SENDER_NAME = os.getenv("SENDER_NAME", "Alex from EDXSO AI")
BRAND_NAME = os.getenv("BRAND_NAME", "EDXSO AI Developer Studio")
BRAND_VALUE_PROP = os.getenv("BRAND_VALUE_PROP", "cutting-edge AI developer tools and agentic workflows that supercharge software engineering")
