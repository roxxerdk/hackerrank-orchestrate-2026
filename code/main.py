import sys
import os

# Ensure the root of the project is in the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.loaders.csv_loader import load_all_datasets

if __name__ == "__main__":
    datasets = load_all_datasets()
