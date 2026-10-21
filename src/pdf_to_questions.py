import json
import time
from pydantic import BaseModel
from google import genai
from src.config import DATA_DIR, EXTRACTED_DIR, EXTRACT_MODEL

client = genai.Client()

MODELS = [EXTRACT_MODEL, "gemini-3.5-flash", "gemini-3.7-flash"]
EXPECTED = {"english": 120, "general studies": 120, "mathematics": 100}
ALIASES = {"general knowledge": "general studies", "elementary mathematics": "mathematics"}
MAX_PDFS_PER_RUN = 3   # 3 PDFs = 1 exam; raise it when things are running smoothly


class Q(BaseModel):
    question_number: int
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str


PROMPT = """This is a UPSC CDS exam question paper. It is bilingual (Hindi and English).
Extract questions numbered {start} to {end} in ENGLISH ONLY. Ignore all Hindi text.
- Include any passage or directions a question depends on inside its 'question' field.
- Write math in plain text or simple LaTeX.
- If a question depends on a figure, add '[figure]' and describe it briefly.
- Do not invent or skip questions. If a number is not in this paper, leave it out."""


def extract_chunk(file, start, end):
    """Try each model in turn. Returns a list of questions, or None if all are busy."""
    for _round in range(3):
        for model in MODELS:
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=[file, PROMPT.format(start=start, end=end)],
                    config={"response_mime_type": "application/json",
                            "response_schema": list[Q]},
                )
                return json.loads(resp.text)
            except Exception as e:
                print(f"    {model}: {str(e)[:70]}")
                time.sleep(5)
        print("    all models busy, waiting 60s...")
        time.sleep(60)
    return None


def main():
    EXTRACTED_DIR.mkdir(exist_ok=True)
    processed = 0

    for pdf in sorted(DATA_DIR.rglob("*.pdf")):
        out = EXTRACTED_DIR / f"{pdf.stem}.json"
        if out.exists():
            continue

        subject = pdf.stem.split(" CDS")[0].strip().lower()
        subject = ALIASES.get(subject, subject)
        if subject not in EXPECTED:
            print(f"Skipping {pdf.name}: the name must start with English, "
                  f"General Studies or Mathematics")
            continue

        if processed >= MAX_PDFS_PER_RUN:
            print("\nReached the per-run limit. Run this command again later for the rest.")
            return

        total = EXPECTED[subject]
        print("Extracting", pdf.name)
        file = client.files.upload(file=pdf)

        questions = []
        for start in range(1, total + 1, 30):
            end = min(start + 29, total)
            print(f"  questions {start}-{end}")
            part = extract_chunk(file, start, end)
            if part is None:
                print("  STOPPED: models are busy or out of quota. "
                      "Nothing saved for this paper. Try again later.")
                return
            questions += part
            time.sleep(8)

        if len(questions) < 0.8 * total:
            print(f"  NOT SAVED: only {len(questions)}/{total} questions found. "
                  f"Check the PDF (one subject per file?).")
            continue

        out.write_text(json.dumps(questions, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  saved {len(questions)} questions -> {out.name}")
        processed += 1

    print("\nAll PDFs in data/ are done.")


if __name__ == "__main__":
    main()