from src.graph import build_agent


def to_text(content) -> str:
    """Gemini 3 returns a list of blocks; keep only the text parts."""
    if isinstance(content, str):
        return content
    return "".join(
        b.get("text", "") for b in content
        if isinstance(b, dict) and b.get("type") == "text"
    )


def run():
    agent = build_agent()
    config = {"configurable": {"thread_id": "student-1"}}
    print("CDS Exam Assistant (type 'exit' to quit)")
    while True:
        q = input("\nYou: ").strip()
        if q.lower() in {"exit", "quit"}:
            break
        result = agent.invoke({"messages": [{"role": "user", "content": q}]}, config)
        print("\nAssistant:", to_text(result["messages"][-1].content))


if __name__ == "__main__":
    run()