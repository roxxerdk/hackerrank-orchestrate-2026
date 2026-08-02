from pathlib import Path

# Root directory of the repository
ROOT_DIR = Path(__file__).resolve().parents[2]

# Dataset Directory Path
DATASET_DIR = ROOT_DIR / "dataset"

# Cache Directory Path
CACHE_DIR = ROOT_DIR / "code" / "cache"

# Output CSV Path (during development)
OUTPUT_CSV_PATH = ROOT_DIR / "code" / "output" / "output.csv"

# Global Model Configurations
IMAGE_MODEL = "gemini-2.5-flash"
VOICE_MODEL = "gemini-2.5-flash"

# Prompt & Cache Version Control
IMAGE_PROMPT_VERSION = "image_v1"
VOICE_PROMPT_VERSION = "voice_v1"
CACHE_VERSION = "1.0"

# Generation & Model Execution Parameters
TEMPERATURE = 0.1
TOP_P = 0.1
TOP_K = 20
MAX_RETRIES = 2

# Feature Extraction Thresholds & Capacities
BUSINESS_REPORT_CAP = 10
NOTIFICATION_LOAD_CAP = 20
INTERACTION_CAP = 50
FORWARD_THRESHOLD = 5
USER_OPEN_CAP = 100
USER_DISMISS_CAP = 50
FREQUENT_CONTACT_THRESHOLD = 15
GROUP_HIGH_ACTIVITY_THRESHOLD = 1000
GROUP_LOW_ACTIVITY_THRESHOLD = 100

# Confidence Scoring Policy Parameters
RULE_WEIGHT_FACTOR = 0.20
ENGAGEMENT_FACTOR = 0.15
SYSTEM_LOAD_FACTOR = 0.10
DOMAIN_MISMATCH_PENALTY = 0.30
UNKNOWN_SENDER_PENALTY = 0.10
REPORTED_BUSINESS_PENALTY = 0.20







