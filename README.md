# Teamwork & Leadership Coach (MVP)

AI-powered teamwork coaching for engineering students (EDS 6397).

## Stack

- LLM: Google Gemini 3.5 Flash
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- Vector store: ChromaDB (local)
- UI: Streamlit
- Orchestration: LangGraph
- Observability: LangSmith (optional, sanitized nested traces)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add GOOGLE_API_KEY to .env
python -m ingestion.build_index
```

### LangSmith tracing (optional)

1. Create an API key at [smith.langchain.com](https://smith.langchain.com).
2. In `.env` set:

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=teamwork-leadership-coach
```

3. Run the CLI or Streamlit UI. Each `run_coach` call appears as **one** nested trace:
   `teamwork_coach_run` → graph nodes (privacy, diagnosis/retrieval, advice, validation, …) → LLM and retrieval spans.

Raw reflections are omitted from telemetry; sensitive fields are redacted before upload.

## Run

```bash
# CLI smoke
python main_system.py

# UI
streamlit run interface/app.py
```

## Test

```bash
pytest -q
```

## Evaluation

72-case golden set + gated RAG vs no-RAG baseline: see `evaluation/README.md`.

```bash
python -m evaluation --dry-run
python -m evaluation                       # gated RAG (needs API key + Chroma)
python -m evaluation --system compare      # gated RAG vs no-RAG
python -m evaluation --system scorecard    # rebuild one-page scorecard
python -m evaluation --suites safety,privacy
```

Scorecard: `evaluation/reports/latest_scorecard.md`

## Notes

- Hand-built corpus in `corpus/` (replace later with fuller ingestion).
- Key decisions are logged in `cursor_calls.md`.
- Requirements and scope: `PRD.md`.
