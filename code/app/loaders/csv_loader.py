import os
import pandas as pd
from app.config import DATASET_DIR

def load_csv(filepath: str) -> pd.DataFrame:
    """
    Loads a single CSV file into a pandas DataFrame.
    Includes validation of existence, emptiness, and formatting errors.
    """
    if not os.path.exists(filepath):
        print(f"[Error] File not found: {filepath}")
        raise FileNotFoundError(f"File not found: {filepath}")
    
    if os.path.getsize(filepath) == 0:
        print(f"[Error] File is empty: {filepath}")
        raise ValueError(f"File is empty: {filepath}")
        
    try:
        df = pd.read_csv(filepath)
        cols_str = "\n".join([f"  - {col}" for col in df.columns])
        print(f"[Success] Loaded: {os.path.basename(filepath)} | Rows: {df.shape[0]} | Columns:\n{cols_str}")
        return df
    except pd.errors.EmptyDataError:
        print(f"[Error] No columns/data to parse in: {filepath}")
        raise ValueError(f"Empty data error in: {filepath}")
    except pd.errors.ParserError as e:
        print(f"[Error] Parsing error in: {filepath} | Details: {e}")
        raise
    except Exception as e:
        print(f"[Error] Unexpected error reading: {filepath} | Details: {e}")
        raise

def load_all_datasets(dataset_dir: str = DATASET_DIR) -> dict:
    """
    Loads all required CSV datasets from the dataset directory.
    Returns a dictionary of pandas DataFrames.
    """
    required_files = [
        "messages.csv",
        "users.csv",
        "groups.csv",
        "group_members.csv",
        "business_accounts.csv",
        "user_business_history.csv",
        "message_history.csv",
        "message_events.csv",
        "images.csv",
        "voice_notes.csv",
        "daily_notification_summary.csv"
    ]
    
    datasets = {}
    print(f"--- Loading Datasets from {dataset_dir} ---")
    
    for filename in required_files:
        filepath = os.path.join(dataset_dir, filename)
        key = filename.split(".")[0]
        try:
            datasets[key] = load_csv(filepath)
        except Exception as e:
            print(f"[Warning] Failed to load {filename}: {e}")
            datasets[key] = pd.DataFrame() # Fallback to empty DataFrame
            
    print(f"--- Dataset Loading Complete ---")
    return datasets
