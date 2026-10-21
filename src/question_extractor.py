import re
import json
from pathlib import Path
from langchain_core.documents import Document

FILE_RE = re.compile(r"^(?P<subject>.+?)\s+CDS-\((?P<session>I+)\)\s+(?P<year>\d{4})", re.I)


def parse_filename(path: Path) -> dict:
    m = FILE_RE.match(path.stem)
    if not m:
        raise ValueError(f"Unexpected file name: {path.name}")
    return {"subject": m["subject"].strip().lower(), "session": m["session"].upper(),
            "year": m["year"], "source": path.name}


def extract_questions(path: Path) -> list[Document]:
    meta = parse_filename(path)
    items = json.loads(path.read_text(encoding="utf-8"))
    docs = []
    for q in sorted(items, key=lambda x: x["question_number"]):
        text = (f"Q{q['question_number']}. {q['question']}\n"
                f"(a) {q['option_a']}\n(b) {q['option_b']}\n"
                f"(c) {q['option_c']}\n(d) {q['option_d']}")
        docs.append(Document(
            page_content=text,
            metadata={**meta,
                      "question_number": q["question_number"],
                      "topic": q.get("topic", "Other")},
        ))
    return docs