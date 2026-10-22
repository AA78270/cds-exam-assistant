# CDS Examination Assistant

**A traceable AI agent for CDS exam preparation, built on previous-year question papers.**

## Overview

The CDS Examination Assistant is a prototype of a custom AI agent that helps candidates
prepare for the **Combined Defence Services (CDS)** exam. It is built on top of real
previous-year question papers: you ask for questions by topic, subject, year or question
number, and the agent retrieves matching questions from the papers and explains the solution.

Most chatbots answer from memory and can invent exam questions. This agent uses
**RAG (Retrieval-Augmented Generation)**: it first searches a database built from the actual
papers, and only then writes its answer from what it found. Every answer shows which paper
and question number it came from.

## Purpose: traceability

The main goal of this project is to make an AI agent **transparent**. It does not only give an
answer: it lets you see **how the agent produced that answer from the existing question
papers**, which path it followed, and what it cost in tokens.

The agent is instrumented with **OpenTelemetry**, the open standard for tracing. Every
question you ask is recorded as a trace and exported to an OpenTelemetry tool (this project
uses [Arize Phoenix](https://github.com/Arize-ai/phoenix) running locally), so you can open
any answer and follow it step by step.

## What you can see in a trace

| Question you may have | Where to find it in the trace |
|---|---|
| Which path did the agent follow? | The sequence of steps: model call, tool call, model call |
| Which past-paper questions did it use? | The tool output: the retrieved questions with year, session, subject and question number |
| What did the model receive and what did it return? | The input and output of each model call |
| How many tokens were used? | Token counts per model call (shown when the model provider reports them) |
| How long did each step take? | The duration of each step |
| What went wrong? | Errors such as a busy or out-of-quota model, and the fallback to the next model |
| Which questions belong to one conversation? | A shared `session_id` on every trace in the chat |

A typical trace:

```
agent run
 |- model call 1      the model decides which tool to use
 |- tool: search_cds_papers
 |     input : search text, subject and year chosen by the model
 |     output: the retrieved past-paper questions
 |- model call 2      writes the final answer from those questions
```

The traces are also saved as plain logs in `logs/agent_traces.jsonl`.


## How it works

This is a RAG (Retrieval-Augmented Generation) system. The AI does not answer from memory
alone: it first searches the past papers, then answers using what it found.

```
PDF papers -> Gemini vision extracts questions -> JSON files
          -> embeddings (Hugging Face, local) -> Chroma vector database

User question -> LangChain/LangGraph agent (Gemini)
                   |- tool: search_cds_papers
                   |- tool: get_question
              -> answer with source (year, session, subject, question number)
              -> Streamlit chat interface
```

## Features

- Search past-paper questions by meaning, not just keywords
- Fetch an exact question, for example "Question 15 from the 2026 Mathematics paper"
- Conversation memory, so follow-ups like "give me another one" work
- Streaming answers and automatic fallback between Gemini models when one is busy or
  out of quota
- Answers cite the source question and say when something is not from the papers
- Optional observability: step-by-step traces of the agent exported through OpenTelemetry

## Tech stack

| Part | Technology |
|---|---|
| Language | Python |
| Agent framework | LangChain and LangGraph |
| LLM | Google Gemini (Flash models) |
| PDF reading | Gemini vision with structured JSON output (Pydantic) |
| Embeddings | Local Hugging Face sentence-transformers model |
| Vector database | ChromaDB |
| Interface | Streamlit |
| | Tracing | OpenTelemetry (via OpenInference), Arize Phoenix |

## Papers included

Currently: CDS (II) 2026 - English, General Studies and Elementary Mathematics
(120 + 120 + 100 questions). More papers can be added, see "Adding more papers" below.

## Setup

1. Clone the repository and create a virtual environment:
```
   git clone https://github.com/AA78270/cds-exam-assistant.git
   cd cds-exam-assistant
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
```
2. Copy `.env.example` to `.env` and add your Google Gemini API key:
```
   GOOGLE_API_KEY=your_google_api_key_here
```
3. Build the search database from the included question files:
```
   python -m src.ingestion
```
4. Start the app:
```
   streamlit run app.py
```

The first start takes longer because the embedding model loads.

## Adding more papers

1. Put one PDF per subject in `data/english`, `data/general_studies` and
   `data/mathematics`, named like:
   - `English CDS-(I) 2025.pdf`
   - `General Studies CDS-(I) 2025.pdf`
   - `Mathematics CDS-(I) 2025.pdf`
2. Extract the questions with Gemini (processes a few PDFs per run to protect the free quota):
```
   python -m src.pdf_to_questions
```
3. Check that each file has the expected number of questions (English 120,
   General Studies 120, Mathematics 100).
4. Add them to the database:
```
   python -m src.ingestion
```

## Observability (optional)

The agent can export a trace of every question so you can see how it works: which model
calls were made, which tool was used with what input, which past-paper questions were
retrieved, how long each step took, and any errors such as a busy model.

- **Trace:** one question followed from start to finish.
- **Span:** one step inside a trace (model call, tool call).
- **Export:** spans are sent over OTLP (the OpenTelemetry protocol) to Arize Phoenix, which
  runs locally on your machine and does not send data to the internet. Changing the
  endpoint in `src/tracing.py` sends the same traces to any other OpenTelemetry backend.
- **Local log:** every span is also saved to `logs/agent_traces.jsonl`.

What a typical trace looks like:

```
agent run
 |- model call 1      the model decides to use a tool
 |- tool: search_cds_papers
 |     input : search text, subject, year chosen by the model
 |     output: the retrieved past-paper questions
 |- model call 2      writes the final answer from those questions
```

Each trace carries the conversation id (`session_id`), so all questions in one chat can be
followed together.

### Enabling tracing

1. Install the tracing packages in the project environment:
```
   pip install openinference-instrumentation-langchain opentelemetry-sdk opentelemetry-exporter-otlp
```
2. Install and start Phoenix in a separate environment (it has many dependencies):
```
   python -m venv phoenix-env
   phoenix-env\Scripts\Activate.ps1
   pip install arize-phoenix
   python -m phoenix.server.main serve
```
   Open http://localhost:6006 and keep that terminal running.
3. Add this line to `.env`:
```
   ENABLE_TRACING=1
```
4. Start the app in another terminal with `streamlit run app.py`, ask a question, and open
   the `cds-assistant` project in Phoenix.

Set `ENABLE_TRACING=0` (or remove the line) to turn tracing off. The app works the same
either way.

To print a text summary of the saved agent logs (steps, type, duration, status):
```
python summarize_traces.py
```

Note: the log file contains the questions asked and the answers, so it is excluded from
Git by `.gitignore`.

## Limitations

- The papers contain questions but no official answer key, so answers are generated by AI
  and can be wrong, especially for General Studies facts. Verify important answers.
- The free Gemini tier has rate limits, so heavy use may hit quota or overload errors
  (the app retries and falls back to other models).
- The assistant only knows the papers that have been added to the database.

## Project structure

```
app.py                      Streamlit interface
src/config.py               Settings and model list
src/graph.py                Agent (LangChain + LangGraph)
src/tools.py                Search and exact-lookup tools
src/retriever.py            Vector database access
src/pdf_to_questions.py     PDF -> JSON extraction with Gemini
src/question_extractor.py   JSON -> documents
src/validate_questions.py   Question count checks
src/ingestion.py            Builds the vector database
src/tracing.py              OpenTelemetry tracing setup (optional)
summarize_traces.py         Text summary of the saved agent logs
extracted_questions/        Extracted questions (JSON)
.streamlit/config.toml      App theme
```

## Future improvements

- Add more years of papers
- Add official answer keys so the assistant can state the correct option
- Tag questions by topic for filtering
- Quiz mode

## Disclaimer

Educational project. Question papers are published by UPSC. This tool is not affiliated
with UPSC.