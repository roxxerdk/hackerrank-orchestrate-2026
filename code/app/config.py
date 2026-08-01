import os

# Root directory of the repository
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Dataset Directory Path
DATASET_DIR = os.path.join(ROOT_DIR, "dataset")

# Cache Directory Path
CACHE_DIR = os.path.join(ROOT_DIR, "code", "app", "cache")

# Output CSV Path
OUTPUT_CSV_PATH = os.path.join(ROOT_DIR, "dataset", "output.csv")
