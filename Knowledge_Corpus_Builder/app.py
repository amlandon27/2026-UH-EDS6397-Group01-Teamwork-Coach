"""Knowledge Corpus Builder — Streamlit app.

Run from project root:
  streamlit run Knowledge_Corpus_Builder/app.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Disable torch inductor before Docling/torch import (Windows: no MSVC `cl`).
os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")
os.environ.setdefault("TORCHINDUCTOR_DISABLE", "1")

# Ensure project root is on path for Knowledge_Corpus_Builder.* imports
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from Knowledge_Corpus_Builder.config.settings import get_settings
from Knowledge_Corpus_Builder.pipeline.chunker import structure_chunk_markdown
from Knowledge_Corpus_Builder.pipeline.docling_convert import (
    convert_to_markdown,
    cuda_status,
    detect_cuda,
    resolve_device,
)
from Knowledge_Corpus_Builder.pipeline.embed_cluster import assign_hierarchical_clusters
from Knowledge_Corpus_Builder.pipeline.export import (
    export_corpus,
    hydrate_markdown_from_disk,
    load_workspace,
    output_dirs,
    save_markdown_artifacts,
    save_workspace,
)
from Knowledge_Corpus_Builder.pipeline.markdown_repair import repair_markdown
from Knowledge_Corpus_Builder.pipeline.ollama_client import check_ollama
from Knowledge_Corpus_Builder.pipeline.scanner import scan_inputs
from Knowledge_Corpus_Builder.pipeline.tag_suggester import load_taxonomy, suggest_tags_batch
from Knowledge_Corpus_Builder.schemas.models import ChunkRecord, SourceRecord, WorkspaceState

STEPS = [
    "1. Inputs",
    "2. Convert & Repair",
    "3. Source Metadata",
    "4. Chunk & Cluster",
    "5. Tag Suggest",
    "6. Review",
    "7. Export",
]

SOURCE_TYPES = [
    "open_access_research",
    "professional_guidance",
    "engineering_framework",
    "behavioral_rubric",
    "approved_summary",
]


def _init_state() -> None:
    if "workspace" not in st.session_state:
        st.session_state.workspace = load_workspace()
    if "step" not in st.session_state:
        st.session_state.step = STEPS[0]
    if "input_files" not in st.session_state:
        st.session_state.input_files = []


def _ws() -> WorkspaceState:
    return st.session_state.workspace


def _persist() -> None:
    save_workspace(_ws())


def page_inputs() -> None:
    settings = get_settings()
    st.subheader("Scan Corpus_Inputs")
    st.caption(f"Looking in `{settings.corpus_inputs_dir}`")

    if st.button("Rescan folders", type="primary"):
        st.session_state.input_files = scan_inputs(settings.corpus_inputs_dir)

    files = st.session_state.input_files or scan_inputs(settings.corpus_inputs_dir)
    st.session_state.input_files = files

    if not files:
        st.warning("No supported files found. Add PDF/PPTX/DOCX/TXT/MD/HTML/JPG/PNG under Corpus_Inputs.")
        return

    by_ext: dict[str, int] = {}
    by_domain: dict[str, int] = {}
    for f in files:
        by_ext[f.extension] = by_ext.get(f.extension, 0) + 1
        by_domain[f.domain] = by_domain.get(f.domain, 0) + 1

    c1, c2 = st.columns(2)
    with c1:
        st.write("**By extension**")
        st.json(by_ext)
    with c2:
        st.write("**By domain (from folder)**")
        st.json(by_domain)

    labels = [f"{f.relative_path}  [{f.domain}] ({f.source_id})" for f in files]
    path_by_label = {lab: f for lab, f in zip(labels, files)}
    previously = set(_ws().selected_paths)
    default = [lab for lab, f in path_by_label.items() if f.path in previously] or labels

    chosen = st.multiselect("Select files to process", labels, default=default)
    selected = [path_by_label[lab] for lab in chosen]

    if st.button("Save selection"):
        ws = _ws()
        ws.selected_paths = [f.path for f in selected]
        for f in selected:
            if f.source_id not in ws.sources:
                ws.sources[f.source_id] = SourceRecord(
                    source_id=f.source_id,
                    citation_key=f.source_id.replace("src_", ""),
                    source_title=Path(f.path).stem,
                    domain=f.domain,
                    source_path=f.relative_path,
                    folder_name=f.folder_name,
                    source_type="open_access_research",
                    publicly_verifiable=True,
                )
        # Drop sources no longer selected
        keep_ids = {f.source_id for f in selected}
        ws.sources = {k: v for k, v in ws.sources.items() if k in keep_ids}
        ws.last_step = "inputs"
        _persist()
        st.success(f"Saved {len(selected)} file(s).")


def page_convert_repair() -> None:
    settings = get_settings()
    ok, msg = check_ollama(settings)
    st.info(msg if ok else msg)
    if not ok:
        st.error("Start Ollama and pull the model before repair. Conversion can still run.")

    ws = _ws()
    # Pull any on-disk markdown into workspace (checkpoint hydrate)
    hydrate_markdown_from_disk(ws, settings=settings)

    files = [f for f in (st.session_state.input_files or []) if f.path in set(ws.selected_paths)]
    if not files and ws.selected_paths:
        # Rescan if session lost file list after refresh
        st.session_state.input_files = scan_inputs(settings.corpus_inputs_dir)
        files = [f for f in st.session_state.input_files if f.path in set(ws.selected_paths)]
    if not files:
        st.warning("Select files on the Inputs step first.")
        return

    device_pref = ws.preferred_device or settings.docling_device
    resolved = resolve_device(device_pref)
    st.write(
        f"{len(files)} selected file(s) · Docling device: **{resolved}** "
        f"(preference: {device_pref})"
    )
    if device_pref in {"cuda", "gpu", "auto"} and resolved == "cpu":
        st.error(
            "GPU was requested but this Python process has no CUDA torch. "
            "Conversion will hammer CPU/RAM. Restart Streamlit after installing "
            "`torch` with cu124 in the active venv."
        )
    elif resolved == "cuda":
        st.info(
            "Docling will use CUDA. Ollama repair also uses the GPU — with only 6 GB VRAM "
            "they may compete. Prefer: Convert-only first (resume checkpoint), then Repair."
        )

    already_converted = sum(1 for f in files if f.source_id in ws.raw_markdown)
    already_repaired = sum(1 for f in files if f.source_id in ws.repaired_markdown)
    c1, c2, c3 = st.columns(3)
    c1.metric("Converted (checkpoint)", f"{already_converted}/{len(files)}")
    c2.metric("Repaired (checkpoint)", f"{already_repaired}/{len(files)}")
    c3.metric("Prior errors", len(ws.convert_errors))

    do_convert = st.checkbox("Run Docling conversion", value=True)
    do_repair = st.checkbox("Run Ollama markdown repair", value=True)
    resume = st.checkbox(
        "Resume from checkpoint",
        value=True,
        help=(
            "Skip files that already have raw.md / repaired.md in the workspace "
            "or under Corpus_Output/markdown/. Progress is saved after each file."
        ),
    )
    force = st.checkbox(
        "Force reprocess (ignore checkpoint)",
        value=False,
        help="Re-run conversion/repair even when checkpoint files exist.",
    )
    if force:
        resume = False

    if ws.convert_errors:
        with st.expander(f"Previous errors ({len(ws.convert_errors)})"):
            st.json(ws.convert_errors)

    if st.button("Convert / Repair selected", type="primary"):
        progress = st.progress(0.0)
        status = st.empty()
        skipped_convert = 0
        skipped_repair = 0
        done_ok = 0
        failed = 0

        for i, f in enumerate(files):
            status.write(f"Processing `{f.relative_path}` …")
            try:
                # --- Convert ---
                has_raw = f.source_id in ws.raw_markdown and bool(ws.raw_markdown[f.source_id].strip())
                if do_convert:
                    if resume and has_raw and not force:
                        raw = ws.raw_markdown[f.source_id]
                        skipped_convert += 1
                    else:
                        raw = convert_to_markdown(
                            f.path,
                            device=device_pref,
                            num_threads=settings.docling_num_threads,
                        )
                        ws.raw_markdown[f.source_id] = raw
                        if f.source_id not in ws.convert_done:
                            ws.convert_done.append(f.source_id)
                        ws.convert_errors.pop(f.source_id, None)
                        save_markdown_artifacts(f.source_id, raw=raw, settings=settings)
                else:
                    if not has_raw:
                        raise RuntimeError("No raw markdown checkpoint and conversion is disabled")
                    raw = ws.raw_markdown[f.source_id]

                # --- Repair ---
                has_repaired = (
                    f.source_id in ws.repaired_markdown
                    and bool(ws.repaired_markdown[f.source_id].strip())
                )
                if do_repair:
                    if resume and has_repaired and not force:
                        skipped_repair += 1
                    else:
                        if not ok:
                            st.warning(f"Skipping repair for {f.source_id} — Ollama unavailable.")
                            repaired = raw
                        else:
                            title = (
                                (ws.sources.get(f.source_id) or SourceRecord(source_id=f.source_id)).source_title
                                or Path(f.path).stem
                            )
                            repaired = repair_markdown(
                                raw, source_title=title, settings=settings
                            )
                            if f.source_id not in ws.repair_done:
                                ws.repair_done.append(f.source_id)
                        ws.repaired_markdown[f.source_id] = repaired
                        save_markdown_artifacts(
                            f.source_id, repaired=repaired, settings=settings
                        )
                elif not has_repaired:
                    # Conversion-only: keep repaired in sync with raw for downstream steps
                    ws.repaired_markdown[f.source_id] = raw
                    save_markdown_artifacts(f.source_id, repaired=raw, settings=settings)

                done_ok += 1
            except Exception as exc:  # noqa: BLE001
                failed += 1
                ws.convert_errors[f.source_id] = str(exc)
                st.error(f"Failed on {f.relative_path}: {exc}")

            # Checkpoint after every file so a crash can resume
            ws.last_step = "convert"
            _persist()
            progress.progress((i + 1) / len(files))

        status.write("Done.")
        st.success(
            f"Finished. ok={done_ok}, failed={failed}, "
            f"skipped_convert={skipped_convert}, skipped_repair={skipped_repair}. "
            "Markdown saved under Corpus_Output/markdown/."
        )

    # Preview
    ids = [
        f.source_id
        for f in files
        if f.source_id in ws.raw_markdown or f.source_id in ws.repaired_markdown
    ]
    if ids:
        pick = st.selectbox("Preview source", ids)
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Raw**")
            st.text_area(
                "raw",
                ws.raw_markdown.get(pick, ""),
                height=360,
                label_visibility="collapsed",
            )
        with col_b:
            st.markdown("**Repaired**")
            edited = st.text_area(
                "repaired",
                ws.repaired_markdown.get(pick, ""),
                height=360,
                label_visibility="collapsed",
            )
            if st.button("Save repaired edits"):
                ws.repaired_markdown[pick] = edited
                save_markdown_artifacts(pick, repaired=edited, settings=settings)
                _persist()
                st.success("Saved repaired markdown.")

def page_source_metadata() -> None:
    ws = _ws()
    if not ws.sources:
        st.warning("No sources yet — select files on Inputs.")
        return

    sid = st.selectbox("Source", list(ws.sources.keys()))
    src = ws.sources[sid]
    st.caption(f"Domain (from folder): `{src.domain}` · Path: `{src.source_path}`")

    with st.form(f"source_form_{sid}"):
        citation_key = st.text_input("citation_key", src.citation_key or "")
        citation_text = st.text_area("citation_text", src.citation_text or "", height=100)
        authors = st.text_input("authors", src.authors or "")
        year = st.number_input(
            "publication_year",
            min_value=0,
            max_value=2100,
            value=int(src.publication_year or 0),
            step=1,
        )
        source_title = st.text_input("source_title", src.source_title or "")
        publication_title = st.text_input("publication_title", src.publication_title or "")
        doi = st.text_input("doi", src.doi or "")
        url = st.text_input("url", src.url or "")
        source_type = st.selectbox(
            "source_type",
            SOURCE_TYPES,
            index=SOURCE_TYPES.index(src.source_type) if src.source_type in SOURCE_TYPES else 0,
        )
        access_status = st.text_input("access_status", src.access_status or "")
        license_ = st.text_input("license", src.license or "")
        publicly_verifiable = st.checkbox("publicly_verifiable", value=src.publicly_verifiable)
        submitted = st.form_submit_button("Save source metadata", type="primary")

    if submitted:
        src.citation_key = citation_key
        src.citation_text = citation_text
        src.authors = authors or None
        src.publication_year = int(year) if year else None
        src.source_title = source_title or None
        src.publication_title = publication_title or None
        src.doi = doi or None
        src.url = url or None
        src.source_type = source_type
        src.access_status = access_status or None
        src.license = license_ or None
        src.publicly_verifiable = publicly_verifiable
        ws.sources[sid] = src
        ws.last_step = "metadata"
        _persist()
        st.success("Source metadata saved.")


def page_chunk_cluster() -> None:
    settings = get_settings()
    ws = _ws()
    md_map = ws.repaired_markdown or ws.raw_markdown
    if not md_map:
        st.warning("Convert/repair markdown first.")
        return

    st.write(f"Markdown available for {len(md_map)} source(s).")
    if st.button("Chunk + hierarchical cluster", type="primary"):
        draft: list[ChunkRecord] = []
        for source_id, md in md_map.items():
            src = ws.sources.get(source_id)
            pieces = structure_chunk_markdown(md, settings=settings)
            for i, text in enumerate(pieces, start=1):
                stem = source_id.replace("src_", "chk_", 1)
                draft.append(
                    ChunkRecord(
                        chunk_id=f"{stem}_{i:03d}",
                        source_id=source_id,
                        text=text,
                        domain=src.domain if src else None,
                        source_path=src.source_path if src else None,
                        review_status="pending",
                        human_reviewed=False,
                    )
                )
        with st.spinner("Embedding + clustering (MiniLM)…"):
            result = assign_hierarchical_clusters(draft, settings=settings)
        ws.chunks = result.chunks
        ws.last_step = "chunk_cluster"
        _persist()
        st.success(
            f"Created {len(result.chunks)} chunks across {result.n_clusters} clusters "
            f"(merged {result.n_merged} near-duplicates)."
        )

    if ws.chunks:
        st.metric("Chunks", len(ws.chunks))
        clusters = sorted({c.cluster_id or "?" for c in ws.chunks})
        st.write(f"Clusters: {len(clusters)}")
        view = st.selectbox("Preview cluster", clusters)
        for c in ws.chunks:
            if c.cluster_id == view:
                with st.expander(c.chunk_id):
                    st.write(c.text[:2000])


def page_tag_suggest() -> None:
    settings = get_settings()
    ok, msg = check_ollama(settings)
    st.info(msg)
    ws = _ws()
    if not ws.chunks:
        st.warning("Run chunk & cluster first.")
        return

    tax = load_taxonomy(settings.taxonomy_path)
    st.caption(f"Taxonomy loaded from `{settings.taxonomy_path}` ({sum(len(v) for v in tax.values())} terms).")

    only_pending = st.checkbox("Only tag chunks with empty challenge_tags", value=True)
    targets = [
        c
        for c in ws.chunks
        if (not only_pending) or not c.challenge_tags
    ]
    st.write(f"Will tag {len(targets)} / {len(ws.chunks)} chunk(s) with `{settings.ollama_model}`.")

    if st.button("Suggest tags (Ollama)", type="primary", disabled=not ok):
        bar = st.progress(0.0)
        status = st.empty()

        def _progress(done: int, total: int) -> None:
            bar.progress(done / max(total, 1))
            status.write(f"Tagged {done}/{total}")

        tagged = suggest_tags_batch(targets, settings=settings, progress_callback=_progress)
        by_id = {c.chunk_id: c for c in tagged}
        ws.chunks = [by_id.get(c.chunk_id, c) for c in ws.chunks]
        ws.last_step = "tag"
        _persist()
        st.success("Tag suggestion complete.")


def _multiselect_from_tax(
    label: str, options: list[str], current: list[str], *, key: str
) -> list[str]:
    return st.multiselect(
        label,
        options,
        default=[x for x in current if x in options],
        key=key,
    )


def page_review() -> None:
    settings = get_settings()
    ws = _ws()
    if not ws.chunks:
        st.warning("No chunks to review.")
        return

    tax = load_taxonomy(settings.taxonomy_path)
    mode = st.radio("Batch by", ["source", "cluster"], horizontal=True)

    if mode == "source":
        keys = sorted({c.source_id for c in ws.chunks})
        pick = st.selectbox("Source", keys)
        batch = [c for c in ws.chunks if c.source_id == pick]
    else:
        keys = sorted({c.cluster_id or "none" for c in ws.chunks})
        pick = st.selectbox("Cluster", keys)
        batch = [c for c in ws.chunks if (c.cluster_id or "none") == pick]

    st.write(f"{len(batch)} chunk(s) in this batch")
    statuses = {"pending": 0, "approved": 0, "rejected": 0, "needs_rewrite": 0}
    for c in ws.chunks:
        statuses[c.review_status] = statuses.get(c.review_status, 0) + 1
    st.json(statuses)

    for idx, chunk in enumerate(batch):
        cid = chunk.chunk_id
        with st.expander(f"{cid} · {chunk.review_status} · conf={chunk.tagging_confidence}", expanded=idx == 0):
            text = st.text_area("text", chunk.text, height=220, key=f"text_{cid}")
            challenge_tags = _multiselect_from_tax(
                "challenge_tags",
                tax.get("challenge_tags", []),
                chunk.challenge_tags,
                key=f"ch_{cid}",
            )
            conflict_types = _multiselect_from_tax(
                "conflict_types",
                tax.get("conflict_types", []),
                chunk.conflict_types,
                key=f"ct_{cid}",
            )
            possible_conflict_sources = _multiselect_from_tax(
                "possible_conflict_sources",
                tax.get("possible_conflict_sources", []),
                chunk.possible_conflict_sources,
                key=f"pcs_{cid}",
            )
            signal_tags = _multiselect_from_tax(
                "signal_tags",
                tax.get("signal_tags", []),
                chunk.signal_tags,
                key=f"sig_{cid}",
            )
            supported_intervention_tags = _multiselect_from_tax(
                "supported_intervention_tags",
                tax.get("supported_intervention_tags", []),
                chunk.supported_intervention_tags,
                key=f"sup_{cid}",
            )
            mentioned_intervention_tags = _multiselect_from_tax(
                "mentioned_intervention_tags",
                tax.get("supported_intervention_tags", []),
                chunk.mentioned_intervention_tags,
                key=f"men_{cid}",
            )
            evidence_roles = _multiselect_from_tax(
                "evidence_roles",
                tax.get("evidence_roles", []),
                chunk.evidence_roles,
                key=f"er_{cid}",
            )
            action_levels = _multiselect_from_tax(
                "action_levels",
                tax.get("action_levels", []),
                chunk.action_levels,
                key=f"al_{cid}",
            )
            applicable_contexts = st.text_area(
                "applicable_contexts (one per line)",
                "\n".join(chunk.applicable_contexts),
                key=f"ctx_{chunk.chunk_id}",
            )
            limitations = st.text_area(
                "limitations (one per line)",
                "\n".join(chunk.limitations),
                key=f"lim_{chunk.chunk_id}",
            )
            status = st.selectbox(
                "review_status",
                ["pending", "approved", "rejected", "needs_rewrite"],
                index=["pending", "approved", "rejected", "needs_rewrite"].index(chunk.review_status),
                key=f"status_{chunk.chunk_id}",
            )
            conf = st.selectbox(
                "tagging_confidence",
                ["high", "medium", "low"],
                index=["high", "medium", "low"].index(chunk.tagging_confidence),
                key=f"conf_{chunk.chunk_id}",
            )
            if st.button("Save chunk", key=f"save_{chunk.chunk_id}"):
                chunk.text = text
                chunk.challenge_tags = challenge_tags
                chunk.conflict_types = conflict_types
                chunk.possible_conflict_sources = possible_conflict_sources
                chunk.signal_tags = signal_tags
                chunk.supported_intervention_tags = supported_intervention_tags
                chunk.mentioned_intervention_tags = mentioned_intervention_tags
                chunk.evidence_roles = evidence_roles
                chunk.action_levels = action_levels
                chunk.applicable_contexts = [x.strip() for x in applicable_contexts.splitlines() if x.strip()]
                chunk.limitations = [x.strip() for x in limitations.splitlines() if x.strip()]
                chunk.review_status = status  # type: ignore[assignment]
                chunk.tagging_confidence = conf  # type: ignore[assignment]
                chunk.human_reviewed = status == "approved"
                # write back into ws.chunks
                ws.chunks = [chunk if c.chunk_id == chunk.chunk_id else c for c in ws.chunks]
                _persist()
                st.success(f"Saved {chunk.chunk_id}")


def page_export() -> None:
    settings = get_settings()
    ws = _ws()
    dirs = output_dirs(settings)
    st.write(f"Output root: `{dirs['root']}`")
    st.write(f"Sources in workspace: {len(ws.sources)} · Chunks: {len(ws.chunks)}")

    only_approved = st.checkbox("Export only approved chunks", value=True)
    if st.button("Write Corpus_Output JSON", type="primary"):
        paths = export_corpus(ws, include_builder_fields=True, only_approved=only_approved, settings=settings)
        st.success("Export complete.")
        for name, path in paths.items():
            st.code(f"{name}: {path}")
        st.info(
            "Next: from the project root, replace the active corpus and rebuild:\n\n"
            "`cp Knowledge_Corpus_Builder/Corpus_Output/sources/sources_mvp.json corpus/sources/sources.json`\n"
            "`cp Knowledge_Corpus_Builder/Corpus_Output/chunks/chunks_mvp.json corpus/chunks/chunks.json`\n"
            "`python -m ingestion.build_index`"
        )


def main() -> None:
    st.set_page_config(page_title="Knowledge Corpus Builder", layout="wide")
    st.title("Knowledge Corpus Builder")
    st.caption("Docling → Ollama repair/tag → structure chunk → hierarchical cluster → human review → Corpus_Output")
    _init_state()

    step = st.sidebar.radio("Steps", STEPS, index=STEPS.index(st.session_state.step) if st.session_state.step in STEPS else 0)
    st.session_state.step = step

    if st.sidebar.button("Reload workspace from disk"):
        st.session_state.workspace = load_workspace()
        st.sidebar.success("Reloaded.")

    settings = get_settings()
    st.sidebar.markdown("---")
    st.sidebar.subheader("Docling device")
    status = cuda_status()
    cuda_ok = bool(status.get("cuda_available"))
    if cuda_ok:
        st.sidebar.success(
            f"PyTorch CUDA OK · `{status.get('torch_version')}` · {status.get('device_name')}"
        )
    else:
        st.sidebar.error(
            f"PyTorch cannot use GPU (`{status.get('torch_version')}`). "
            "Docling will run on CPU even if Task Manager shows an NVIDIA GPU. "
            "Install CUDA torch in the SAME venv Streamlit uses."
        )
        if status.get("is_cpu_wheel"):
            st.sidebar.code(
                "pip uninstall -y torch torchvision torchaudio\n"
                "pip install torch torchvision torchaudio "
                "--index-url https://download.pytorch.org/whl/cu124",
                language="bash",
            )

    current = _ws().preferred_device or settings.docling_device
    if current not in {"cpu", "cuda", "auto"}:
        current = "cpu"
    device_choice = st.sidebar.radio(
        "Rendering device",
        options=["cpu", "cuda", "auto"],
        format_func=lambda x: {
            "cpu": "CPU",
            "cuda": "GPU (CUDA)",
            "auto": "Auto",
        }[x],
        index=["cpu", "cuda", "auto"].index(current),
        horizontal=True,
    )
    if device_choice != _ws().preferred_device:
        _ws().preferred_device = device_choice
        _persist()
    active = resolve_device(device_choice)
    st.sidebar.write(f"Active Docling device: `{active}`")
    if device_choice in {"cuda", "auto"} and active == "cpu":
        st.sidebar.warning("Requested GPU but fell back to CPU — torch.cuda is unavailable in this process.")
    st.sidebar.caption(
        "Note: Quadro RTX 3000 has 6 GB VRAM. Ollama often uses ~4 GB already. "
        "If GPU convert OOMs, run Convert only (disable Repair), or stop Ollama first."
    )
    st.sidebar.markdown("---")
    st.sidebar.write(f"Model: `{settings.ollama_model}`")
    st.sidebar.write(f"Ollama: `{settings.ollama_host}`")
    ok, msg = check_ollama(settings)
    st.sidebar.write(("✅ " if ok else "⚠️ ") + msg)

    if step.startswith("1"):
        page_inputs()
    elif step.startswith("2"):
        page_convert_repair()
    elif step.startswith("3"):
        page_source_metadata()
    elif step.startswith("4"):
        page_chunk_cluster()
    elif step.startswith("5"):
        page_tag_suggest()
    elif step.startswith("6"):
        page_review()
    else:
        page_export()


if __name__ == "__main__":
    main()
