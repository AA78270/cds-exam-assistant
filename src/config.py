from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "processed_data"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"

COLLECTION_NAME = "cds_pyq"
LLM_MODELS = ["gemini-3.6-flash"]
THINKING_LEVEL = "low"  

DATA_DIR = BASE_DIR / "data"
EXTRACTED_DIR = BASE_DIR / "extracted_questions"
EXTRACT_MODEL = "gemini-3.6-flash"   