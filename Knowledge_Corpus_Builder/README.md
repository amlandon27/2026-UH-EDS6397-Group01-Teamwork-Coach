# Knowledge Corpus Builder

Standalone Streamlit app that turns raw materials in `Corpus_Inputs/` into tagged evidence chunks for the Teamwork & Leadership Coach.

It does **not** replace the coach runtime. After review, you export MVP-compatible JSON and copy it into the main project `corpus/` folder, then rebuild Chroma.

## What it does

```text
Corpus_Inputs/{domain folders}/
        │  pdf, pptx, docx, txt, md, html, jpg, png, …
        ▼
Docling → markdown
        ▼
Ollama llama3.1:8b → repair (strip ads/noise, fix structure)
        ▼
Structure-based chunking (headings / slides / paragraphs)
        ▼
MiniLM embeddings + hierarchical clustering (+ near-dupe merge)
        ▼
Ollama → taxonomy tag suggestions
        ▼
Human review (batch by source / cluster)
        ▼
Corpus_Output/
  markdown/{source_id}/raw.md + repaired.md
  sources/sources.json (+ sources_mvp.json)
  chunks/chunks.json   (+ chunks_mvp.json)
  review/workspace.json
```

Folder names under `Corpus_Inputs/` map to domain tags (for example `Psychological Safety and Team Climate` → `psychological_safety`).

## Prerequisites

- Python 3.10+
- Project root available (taxonomy is loaded from `../config/teamwork_taxonomy.yaml`)
- [Ollama](https://ollama.com/) running with:

```bash
ollama pull llama3.1:8b
```

- Optional NVIDIA GPU + CUDA PyTorch for faster Docling conversion (CPU works)

## Setup

From the **project root** (recommended — same venv as the coach):

```bash
# Windows PowerShell
.\.venv\Scripts\activate
pip install -r Knowledge_Corpus_Builder/requirements.txt
```

Or create a dedicated venv inside this folder:

```bash
python -m venv .venv
.\.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## Run

From the **project root**:

```bash
streamlit run Knowledge_Corpus_Builder/app.py
```

## App steps (sidebar)

| Step | Action |
| --- | --- |
| 1. Inputs | Scan `Corpus_Inputs`, select files |
| 2. Convert & Repair | Docling convert + Ollama markdown repair |
| 3. Source Metadata | Manual citation fields (authors, year, DOI, …) |
| 4. Chunk & Cluster | Structure chunking + hierarchical clustering |
| 5. Tag Suggest | Ollama suggests controlled-vocabulary tags |
| 6. Review | Edit text/tags; approve / reject / needs_rewrite |
| 7. Export | Write `Corpus_Output` JSON |

### Convert & Repair tips

- **Resume from checkpoint** (default): skips files that already have `raw.md` / `repaired.md`
- **Force reprocess**: ignore checkpoints and redo everything
- Progress is saved after each file under `Corpus_Output/`
- Sidebar **Docling device**: CPU / GPU (CUDA) / Auto  
  - GPU only works if this Python process has CUDA-enabled PyTorch (`torch.cuda.is_available()`)
  - Quadro / laptop GPUs with 6 GB VRAM: prefer Convert-only first, then Repair (Ollama also uses VRAM)

### Windows / Docling note

If you see `InvalidCxxCompiler: Compiler: cl is not found`, the app already disables Torch Dynamo / inductor and uses a lighter PDF pipeline. Plain-text PDFs can also fall back to `pypdf` / `pypdfium2`.

## Output layout

```text
Knowledge_Corpus_Builder/
├── app.py
├── requirements.txt
├── README.md
├── config/                 # Builder settings + domain map
├── pipeline/               # Convert, repair, chunk, cluster, tag, export
├── schemas/                # Source/chunk/workspace models
├── Corpus_Inputs/          # Put raw PDFs, slides, transcripts, images here
└── Corpus_Output/
    ├── markdown/{source_id}/raw.md
    ├── markdown/{source_id}/repaired.md
    ├── sources/sources.json
    ├── sources/sources_mvp.json    # coach-compatible (no builder-only fields)
    ├── chunks/chunks.json
    ├── chunks/chunks_mvp.json      # coach-compatible
    └── review/workspace.json       # progress / review state
```

Generated `Corpus_Output` JSON and markdown are gitignored; keep `Corpus_Inputs` if licensing allows sharing.

## Promote into the main coach corpus

1. Finish review (prefer approving chunks you want in the coach)
2. Export (optionally “only approved”)
3. From project root, copy MVP files:

```powershell
Copy-Item "Knowledge_Corpus_Builder\Corpus_Output\sources\sources_mvp.json" "corpus\sources\sources.json" -Force
Copy-Item "Knowledge_Corpus_Builder\Corpus_Output\chunks\chunks_mvp.json" "corpus\chunks\chunks.json" -Force
python -m ingestion.build_index
```

**Important for evaluation:** the golden-set eval expects the small hand-tagged MVP corpus (`chk_role_clarity_01`, etc.). Replacing it with a large unreviewed builder dump will break gold chunk IDs. Prefer merging carefully, or keep builder dumps under `corpus/expanded_from_builder/` until gold labels are updated.

Correct mapping:

| Builder export | Coach path |
| --- | --- |
| `Corpus_Output/chunks/chunks_mvp.json` | `corpus/chunks/chunks.json` |
| `Corpus_Output/sources/sources_mvp.json` | `corpus/sources/sources.json` |

Do **not** copy `sources_mvp.json` into `chunks.json`.

## Schema

Exports match the coach MVP fields:

- **Sources:** `source_id`, `citation_key`, `citation_text`, authors, year, titles, DOI, URL, license, …
- **Chunks:** `chunk_id`, `source_id`, `text`, taxonomy tags, `human_reviewed`, `tagging_confidence`, …

Builder-only extras (`domain`, `cluster_id`, `review_status`, `source_path`) appear in the full JSON and are stripped in `*_mvp.json`.

Empty `citation_text` is auto-filled from `source_title` / authors / year on export when possible. Fill real APA-style citations in Step 3 when you can.

## Related docs

- Project root `README.md` — full coach setup
- `PRD.md` — product requirements and corpus metadata rules
- `config/teamwork_taxonomy.yaml` — controlled vocabulary used for tagging
