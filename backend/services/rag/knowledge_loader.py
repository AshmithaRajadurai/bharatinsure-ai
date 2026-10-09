import os
import json
from typing import List, Dict, Any

KB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "knowledge_base"))

def load_all_knowledge_documents() -> List[Dict[str, Any]]:
    """
    Load all structured insurance knowledge chunks from JSON files in knowledge_base directory.
    """
    documents = []
    if not os.path.exists(KB_DIR):
        return documents

    for filename in os.listdir(KB_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(KB_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        documents.extend(data)
            except Exception as e:
                print(f"[KB Loader] Error loading {filepath}: {e}")

    return documents
