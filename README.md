# Teamwork & Leadership Coach (MVP)

AI-powered teamwork and leadership coach for engineering students (EDS 6397 — University of Houston).

Students submit a de-identified teamwork reflection. The system:

1. Redacts PII and checks for high-risk content
2. Diagnoses likely teamwork challenges
3. Retrieves evidence from a tagged research corpus (RAG)
4. Generates practical, evidence-grounded coaching
5. Validates safety / citations / scope before display
6. Finalizes coaching, abstains safely, or escalates to UH support resources

This repository also includes:

- **Knowledge Corpus Builder** — Docling + Ollama pipeline to expand the evidence corpus
- **Evaluation harness** — 72-case golden set, gated-RAG vs no-RAG baselines, scorecard

## Stack

| Component | Choice |
| --- | --- |
| Orchestration | LangGraph |
| LLM (default) | Local Ollama `llama3.1:8b` (`LLM_PROVIDER=ollama`) |
| LLM (optional) | Google Gemini 3.5 Flash (`LLM_PROVIDER=gemini`) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store | ChromaDB (local) |
| UI | Streamlit |
| Observability | LangSmith (optional, sanitized nested traces) |

## Repository layout

```text
.
├── README.md
├── PRD.md
├── requirements.txt
├── .env.example
├── contract.py                 # Shared Pydantic state contract
├── main_system.py              # CLI / run_coach entry
├── agents/                     # LangGraph nodes
├── config/                     # Settings, taxonomy, safety, escalation
├── corpus/                     # Active MVP evidence corpus (indexed)
│   ├── chunks/chunks.json
│   ├── sources/sources.json
│   └── expanded_from_builder/  # Optional larger builder export (not default index)
├── guardrails/
├── ingestion/                  # build_index (+ ingestion stubs)
├── interface/app.py            # Student coach UI
├── services/                   # LLM, embeddings, retrieval, tracing
├── evaluation/                 # Golden-set eval + reports
├── Knowledge_Corpus_Builder/   # Standalone corpus expansion app
├── tests/
└── report/                     # Course write-up placeholder
```

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) with `llama3.1:8b` (recommended default)

```bash
ollama pull llama3.1:8b
```

- Optional: Google AI Studio API key for Gemini
- Optional: LangSmith API key for tracing

## Setup

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env — defaults use Ollama. For Gemini set LLM_PROVIDER=gemini and GOOGLE_API_KEY.

python -m ingestion.build_index
```

### Environment variables (`.env`)

```bash
# LLM: ollama (local) or gemini
LLM_PROVIDER=ollama
LLM_FALLBACK_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Optional Gemini
GOOGLE_API_KEY=
GEMINI_MODEL=gemini-3.5-flash

# Retrieval / corpus
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHROMA_PERSIST_DIR=./.chroma
RETRIEVAL_TOP_K=4
RETRIEVAL_MIN_SCORE=0.05

# LangSmith (optional)
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=teamwork-leadership-coach
```

When `LLM_PROVIDER=gemini` and free-tier quota is exhausted (429), the coach can fall back to Ollama if `LLM_FALLBACK_PROVIDER=ollama`.

## Run the coach

```bash
# CLI smoke
python main_system.py

# Student UI
streamlit run interface/app.py
```

The coaching UI shows section-by-section guidance with **Chunk text** + **Source** for retrieved evidence under each paragraph.

## Knowledge Corpus Builder

Expand the evidence corpus from PDFs, slides, transcripts, and images:

```bash
pip install -r Knowledge_Corpus_Builder/requirements.txt
# Ollama required for markdown repair + tag suggestion
streamlit run Knowledge_Corpus_Builder/app.py
```

Pipeline: scan `Corpus_Inputs` → Docling → Ollama repair → structure chunk → hierarchical cluster → tag suggest → human review → export to `Knowledge_Corpus_Builder/Corpus_Output/`.

### Promote builder output into the coach corpus

1. Export `sources_mvp.json` and `chunks_mvp.json` from the builder
2. Copy into `corpus/sources/sources.json` and `corpus/chunks/chunks.json` (or merge carefully — keep unique `source_id` / `chunk_id`)
3. Rebuild the index:

```bash
python -m ingestion.build_index
```

**Note:** The default MVP corpus is the small hand-tagged set used by the evaluation golden set. A larger builder export may be stored under `corpus/expanded_from_builder/` for later promotion after review. Do not replace the MVP corpus with unreviewed chunks before evaluation unless you update gold labels.

## Evaluation

72-case golden set + gated RAG vs no-RAG baseline. See `evaluation/README.md`.

```bash
python -m evaluation --dry-run
python -m evaluation                       # gated RAG (needs LLM + Chroma)
python -m evaluation --system compare      # gated RAG vs no-RAG
python -m evaluation --system scorecard    # rebuild one-page scorecard
python -m evaluation --suites safety,privacy
```

Reports: `evaluation/reports/` (`latest.md`, `latest_compare.md`, `latest_scorecard.md`).

Offline metric tests (no API key):

```bash
pytest -q tests/test_evaluation.py
```

## Tests

```bash
pytest -q
```

## LangSmith tracing (optional)

1. Create an API key at [smith.langchain.com](https://smith.langchain.com)
2. In `.env` set `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY=...`
3. Each `run_coach` call appears as one nested trace: privacy → diagnosis/retrieval → advice → validation → finalize/repair/fallback/escalation

Raw reflections are omitted from telemetry; sensitive fields are redacted before upload.

## Shipping to GitHub

### What to commit

- Source code (`agents/`, `services/`, `interface/`, `evaluation/`, `Knowledge_Corpus_Builder/` Python modules, etc.)
- MVP `corpus/` JSON (hand-tagged)
- `PRD.md`, `README.md`, `requirements.txt`, `.env.example`, `pytest.ini`
- `Knowledge_Corpus_Builder/Corpus_Inputs/` only if license allows sharing those materials

### What NOT to commit (already gitignored)

- `.env` (secrets)
- `.venv/`, `Knowledge_Corpus_Builder/.venv/`
- `.chroma/` (rebuild with `python -m ingestion.build_index`)
- Generated `evaluation/reports/*` (keep `.gitkeep`)
- Generated `Knowledge_Corpus_Builder/Corpus_Output/` workspace JSON/markdown
- `__pycache__/`, model caches
- `Latest Update XX/` snapshot folders (local merge artifacts)

### Suggested first push

```bash
git init   # if needed
git add .
git status   # confirm .env is NOT staged
git commit -m "Merge evaluation harness with corpus builder and Ollama coach path"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

## Team roles (PRD)

| Member | Focus |
| --- | --- |
| Francisco | Advice generation |
| Alex | Project management / evaluation |
| Luija | Reflection interface / workflow |
| Kashfin | Diagnosis / RAG / corpus builder |
| Roberto | Security / privacy / reliability |

## Notes

- Product requirements: `PRD.md`
- Decision log: `cursor_calls.md`
- The product is advisory only and does not replace instructors, counselors, or emergency services
