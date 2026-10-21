import time
from src.config import EXTRACTED_DIR
from src.question_extractor import extract_questions
from src.validate_questions import validate, EXPECTED_COUNTS
from src.retriever import get_vectorstore


def main():
    vs = get_vectorstore()
    for path in sorted(EXTRACTED_DIR.glob("*.json")):
        print(f"Processing {path.name}")
        docs = extract_questions(path)
        print(f"  loaded {len(docs)} questions")
        if not docs:
            continue
        subject = docs[0].metadata["subject"]
        validate(docs, subject)

        if len(docs) < 0.8 * EXPECTED_COUNTS.get(subject, 100):
            print("  SKIPPED: too few questions, fix extraction first")
            continue

        ids = [f'{d.metadata["year"]}_{d.metadata["session"]}_'
               f'{subject.replace(" ", "")}_{d.metadata["question_number"]}' for d in docs]
        vs.add_documents(docs, ids=ids)

    print("Done. Total chunks:", vs._collection.count())


if __name__ == "__main__":
    main()