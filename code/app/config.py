from pathlib import Path

# Root directory of the repository
ROOT_DIR = Path(__file__).resolve().parents[2]

# Dataset Directory Path
DATASET_DIR = ROOT_DIR / "dataset"

# Cache Directory Path
CACHE_DIR = ROOT_DIR / "code" / "cache"

# Output CSV Path (during development)
OUTPUT_CSV_PATH = ROOT_DIR / "code" / "output" / "output.csv"
