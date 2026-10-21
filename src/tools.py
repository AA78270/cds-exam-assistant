from langchain_core.tools import tool
from src.retriever import search, get_by_number


@tool
def search_cds_papers(query: str, subject: str = "", year: str = "") -> str:
    """Search past CDS exam papers for relevant questions.
    subject must be one of: 'english', 'general studies', 'mathematics' (or empty).
    year is e.g. '2026' (or empty)."""
    results = search(query, subject=subject, year=year, k=5)
    if not results:
        return "No relevant questions found in the papers."
    return "\n\n---\n\n".join(
        f"[CDS {d.metadata['year']} ({d.metadata['session']}) | "
        f"{d.metadata['subject']} | Q{d.metadata['question_number']}]\n{d.page_content}"
        for d in results
    )


@tool
def get_question(subject: str, year: str, question_number: int) -> str:
    """Fetch one exact question by number from a specific paper.
    subject: 'english', 'general studies' or 'mathematics'. year e.g. '2026'."""
    results = get_by_number(subject, year, question_number)
    if not results:
        return "That question was not found in the papers."
    return "\n\n".join(
        f"[CDS {m['year']} ({m['session']}) | {m['subject']} | Q{m['question_number']}]\n{doc}"
        for doc, m in results
    )