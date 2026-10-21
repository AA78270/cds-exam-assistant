import time
import os
import uuid
import streamlit as st
from langchain_core.messages import AIMessageChunk
from src.config import LLM_MODELS
from src.graph import build_agent

st.set_page_config(page_title="CDS Examination Assistant", page_icon="📘", layout="centered")

# ---------- Styling ----------
st.markdown("""
<style>
    #MainMenu, footer {visibility: hidden;}
    .block-container {padding-top: 2rem; max-width: 820px;}

    .app-header {
        border-top: 4px solid #C9A24B;
        border-bottom: 1px solid #2A3550;
        padding: 1.1rem 0 1rem 0;
        margin-bottom: 1.4rem;
    }
    .app-header h1 {
        font-family: Georgia, 'Times New Roman', serif;
        font-size: 1.9rem; font-weight: 700;
        color: #F0F2F7; margin: 0; letter-spacing: 0.3px;
    }
    .app-header p {
        font-family: Georgia, 'Times New Roman', serif;
        color: #9AA5BA; margin: 0.35rem 0 0 0; font-size: 0.98rem;
    }

    [data-testid="stSidebar"] {border-right: 1px solid #2A3550;}
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        font-family: Georgia, 'Times New Roman', serif; color: #C9A24B;
    }
    .side-label {
        font-size: 0.78rem; text-transform: uppercase; letter-spacing: 1px;
        color: #8A94A8; margin: 1.1rem 0 0.4rem 0; font-weight: 600;
    }
    [data-testid="stSidebar"] .stButton button {
        border: 1px solid #2A3550; border-radius: 4px;
        background: #0F1623; color: #E6E9EF; font-size: 0.88rem;
        text-align: left;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        border-color: #C9A24B; color: #C9A24B;
    }

    [data-testid="stChatMessage"] {
        border: 1px solid #2A3550; border-radius: 6px;
        padding: 0.9rem 1rem; background: #141C2C;
    }

    .disclaimer {
        font-size: 0.78rem; color: #8A94A8;
        border-top: 1px solid #2A3550; padding-top: 0.6rem; margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def to_text(content) -> str:
    """Gemini returns a list of blocks; keep only the text parts."""
    if isinstance(content, str):
        return content
    return "".join(
        b.get("text", "") for b in content
        if isinstance(b, dict) and b.get("type") == "text"
    )

@st.cache_resource
def init_tracing():
    if os.getenv("ENABLE_TRACING") != "1":
        return False
    try:
        from src.tracing import setup_tracing
        setup_tracing()
        return True
    except Exception as e:
        print("Tracing disabled:", str(e)[:150])
        return False

init_tracing()
def get_agents():
    # load the embedding model now (when the page opens), then build one agent per model
    from src.retriever import get_vectorstore
    get_vectorstore()
    built = []
    for name in LLM_MODELS:
        try:
            built.append((name, build_agent(name)))
        except Exception as e:
            print(f"Skipping model {name}: {str(e)[:150]}")
    return built


agents = get_agents()
if not agents:
    st.error("No model could be set up. Check GOOGLE_API_KEY in .env and the "
             "LLM_MODELS list in src/config.py.")
    st.stop()


def is_busy(error: str) -> bool:
    return any(k in error for k in ("503", "429", "RESOURCE_EXHAUSTED", "UNAVAILABLE"))


def stream_answer(prompt: str, thread_id: str):
    """Yield the answer piece by piece; if a model is busy or out of quota, try the next."""
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 12,
              "metadata": {"session_id": thread_id, "app": "cds-assistant"}}
    error = ""
    for _round in range(2):
        for name, agent in agents:
            started = False
            try:
                for chunk, _meta in agent.stream(
                    {"messages": [{"role": "user", "content": prompt}]},
                    config,
                    stream_mode="messages",
                ):
                    # only the model's final text, not tool calls or tool results
                    if isinstance(chunk, AIMessageChunk) and not chunk.tool_call_chunks:
                        text = to_text(chunk.content)
                        if text:
                            started = True
                            yield text
                return
            except Exception as e:
                error = str(e)
                if started or not is_busy(error):
                    yield f"\n\nSomething went wrong.\n\n`{error[:150]}`"
                    return
                # busy or out of quota before any output: try the next model
        time.sleep(8)
    yield ("\n\nAll models are busy or out of quota right now. "
           f"Please try again in a minute.\n\n`{error[:120]}`")


if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.messages = []

# ---------- Sidebar ----------
with st.sidebar:
    st.subheader("About")
    st.caption("A reference tool for previous-year question papers of the "
               "Combined Defence Services (CDS) Examination.")

    st.markdown('<div class="side-label">Papers available</div>', unsafe_allow_html=True)
    st.markdown("CDS 2026: (II)  \n- English  \n- General Studies  \n- Elementary Mathematics")

    st.markdown('<div class="side-label">Sample queries</div>', unsafe_allow_html=True)
    examples = [
        "Show a percentages question from the Mathematics paper",
        "Show a question on the Indian Constitution",
        "Show Question 15 from the 2026 Mathematics paper",
        "Show an English synonyms question",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state.pending = ex

    st.markdown('<div class="side-label">Session</div>', unsafe_allow_html=True)
    if st.button("Start new conversation", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

# ---------- Header ----------
st.markdown("""
<div class="app-header">
    <h1>CDS Examination Assistant</h1>
    <p>Previous Year Question Reference &mdash; Combined Defence Services Examination</p>
</div>
""", unsafe_allow_html=True)

# ---------- Chat history ----------
for m in st.session_state.messages:
    avatar = ":material/person:" if m["role"] == "user" else ":material/shield:"
    with st.chat_message(m["role"], avatar=avatar):
        st.markdown(m["content"])

# ---------- New message ----------
prompt = st.chat_input("Enter your query about CDS previous year questions") \
    or st.session_state.pop("pending", None)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=":material/person:"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=":material/shield:"):
        status = st.empty()
        status.caption("Searching the question papers...")

        def generate():
            first = True
            for piece in stream_answer(prompt, st.session_state.thread_id):
                if first:
                    status.empty()
                    first = False
                yield piece

        reply = st.write_stream(generate())
        status.empty()

    st.session_state.messages.append({"role": "assistant", "content": reply})

st.markdown(
    '<div class="disclaimer">Questions are retrieved from the uploaded past papers. '
    'Solutions are generated by AI and are not from an official answer key; '
    'please verify important answers against official sources.</div>',
    unsafe_allow_html=True,
)