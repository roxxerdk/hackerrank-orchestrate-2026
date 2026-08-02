import sys
import os

# Ensure the root of the project is in the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.loaders.csv_loader import load_all_datasets
from app.features.feature_context import build_extraction_context

if __name__ == "__main__":
    datasets = load_all_datasets()
    print("\n--- Running Context Smoke Test ---")
    context = build_extraction_context(datasets)
    print("Statistics:", context.statistics)
    
    # Grab first key to test dictionary loading
    test_user_id = list(context.users_index.keys())[0]
    print(f"Sample User lookup ({test_user_id}):", type(context.users_index[test_user_id]))
    print(f"Sample User data:", context.users_index[test_user_id])
    
    # Grab first key for conversation history verification
    test_conv_key = list(context.conversation_history.keys())[0]
    print(f"Sample Conversation Key ({test_conv_key}):", context.conversation_history[test_conv_key])
    print("\n[OK] Smoke test finished successfully.")

