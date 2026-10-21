from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from src.config import LLM_MODELS, THINKING_LEVEL
from src.tools import search_cds_papers, get_question

SYSTEM_PROMPT = """You are a CDS (Combined Defence Services) exam assistant.
- ALWAYS call search_cds_papers before answering exam-related questions.
- When the user asks for a specific question number, use get_question.
- Be concise. Format: the question with its options, then 'Source: CDS year (session),
  subject, Q number', then 'Answer: (letter)' and an explanation of at most 3 short lines.
- For maths, show only the key steps, not every line.
- The papers have no answer key, so say once, briefly, that the answer is AI-solved.
- Write math in plain text, never LaTeX.
- If nothing relevant is found, say so, then answer from general knowledge and label it
  as NOT from the papers.
- Never invent a past-paper question.
- Never show more than 5 questions in one answer. If the user asks for 'all' questions,
  show the first 5 and tell them to ask for the next set."""

# one shared memory, so the conversation continues even if a different model answers
_checkpointer = InMemorySaver()


def build_agent(model_name: str | None = None):
    model_name = model_name or LLM_MODELS[0]
    llm = ChatGoogleGenerativeAI(model=model_name, thinking_level=THINKING_LEVEL)
    return create_agent(
        model=llm,
        tools=[search_cds_papers, get_question],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=_checkpointer,
    )