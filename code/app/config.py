from pathlib import Path

# Root directory of the repository
ROOT_DIR = Path(__file__).resolve().parents[2]

# Dataset Directory Path
DATASET_DIR = ROOT_DIR / "dataset"

# Cache Directory Path
CACHE_DIR = ROOT_DIR / "code" / "cache"

# Output CSV Path (during development)
OUTPUT_CSV_PATH = ROOT_DIR / "code" / "output" / "output.csv"

# Global Model Configuration
MODEL_NAME = "gemini-2.5-flash"  # Default configuration model

# Prompt & Cache Version Control
PROMPT_VERSION = "media_v1"
CACHE_VERSION = "1.0"

