# Teamwork & Leadership Coach (MVP)

AI-powered teamwork coaching for engineering students (EDS 6397).

## Stack

- LLM: Google Gemini 3.5 Flash
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- Vector store: ChromaDB (local)
- UI: Streamlit
- Orchestration: LangGraph

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add GOOGLE_API_KEY to .env
python -m ingestion.build_index
```

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

## Notes

- Hand-built corpus in `corpus/` (replace later with fuller ingestion).
- Key decisions are logged in `cursor_calls.md`.
- Requirements and scope: `PRD.md`.
