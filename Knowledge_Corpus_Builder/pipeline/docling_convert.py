"""Convert source files to markdown via Docling (with text/PDF fallbacks).

On Windows, Docling/PyTorch may try torch._inductor JIT and fail with
`InvalidCxxCompiler: Compiler: cl is not found`. We disable torch compile
and use a lighter PDF pipeline so conversion works without MSVC Build Tools.
"""

from __future__ import annotations

import os
from pathlib import Path

# Must be set before torch/docling model code runs.
os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")
os.environ.setdefault("TORCHINDUCTOR_DISABLE", "1")

TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".html", ".htm"}
PDF_EXTENSIONS = {".pdf"}
OFFICE_EXTENSIONS = {".docx", ".doc", ".pptx", ".ppt"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}


def detect_cuda() -> bool:
    try:
        import torch

        return bool(torch.cuda.is_available())
    except Exception:  # noqa: BLE001
        return False


def cuda_status() -> dict[str, str | bool | None]:
    """Diagnostic info for the Streamlit sidebar."""
    try:
        import torch

        available = bool(torch.cuda.is_available())
        name = torch.cuda.get_device_name(0) if available else None
        return {
            "torch_version": torch.__version__,
            "cuda_built": torch.version.cuda,
            "cuda_available": available,
            "device_name": name,
            "is_cpu_wheel": "+cpu" in (torch.__version__ or ""),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "torch_version": None,
            "cuda_built": None,
            "cuda_available": False,
            "device_name": None,
            "is_cpu_wheel": True,
            "error": str(exc),
        }


def resolve_device(preferred: str) -> str:
    """Map UI preference to a Docling accelerator device string."""
    pref = (preferred or "cpu").strip().lower()
    if pref in {"gpu", "cuda"}:
        if detect_cuda():
            return "cuda"
        return "cpu"
    if pref == "auto":
        return "cuda" if detect_cuda() else "cpu"
    return "cpu"


def _disable_torch_compile() -> None:
    """Best-effort disable of torch dynamo/inductor (Windows-safe)."""
    try:
        import torch

        torch._dynamo.config.suppress_errors = True
        os.environ["TORCH_COMPILE_DISABLE"] = "1"
        os.environ["TORCHDYNAMO_DISABLE"] = "1"
    except Exception:  # noqa: BLE001
        pass


def _read_text_file(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _fallback_text_markdown(path: Path) -> str:
    body = _read_text_file(path)
    return f"# {path.stem}\n\n{body}"


def _fallback_pdf_markdown(path: Path) -> str:
    """Extract text from PDF without Docling (pypdf / pypdfium2)."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages: list[str] = []
        for i, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                pages.append(f"## Page {i}\n\n{text}")
        if pages:
            return f"# {path.stem}\n\n" + "\n\n".join(pages)
    except Exception:  # noqa: BLE001
        pass

    try:
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(str(path))
        pages = []
        for i in range(len(pdf)):
            page = pdf[i]
            textpage = page.get_textpage()
            text = textpage.get_text_bounded().strip()
            textpage.close()
            page.close()
            if text:
                pages.append(f"## Page {i + 1}\n\n{text}")
        pdf.close()
        if pages:
            return f"# {path.stem}\n\n" + "\n\n".join(pages)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"PDF text fallback failed for {path.name}: {exc}") from exc

    raise RuntimeError(f"PDF text fallback produced no text for {path.name}")


def _build_docling_converter(*, device: str = "cpu", num_threads: int = 4):
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import AcceleratorOptions, PdfPipelineOptions
    from docling.document_converter import DocumentConverter, ImageFormatOption, PdfFormatOption

    accelerator = AcceleratorOptions(num_threads=num_threads, device=device)
    pdf_opts = PdfPipelineOptions(
        do_ocr=False,
        do_table_structure=False,
        generate_parsed_pages=False,
        generate_page_images=False,
        generate_picture_images=False,
        accelerator_options=accelerator,
    )
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_opts),
            InputFormat.IMAGE: ImageFormatOption(pipeline_options=pdf_opts),
        }
    )


def _convert_with_docling(
    path: Path,
    *,
    device: str = "cpu",
    num_threads: int = 4,
) -> str:
    _disable_torch_compile()
    converter = _build_docling_converter(device=device, num_threads=num_threads)
    result = converter.convert(str(path))
    status = getattr(result, "status", None)
    status_name = getattr(status, "name", str(status) if status is not None else "")
    if status_name and status_name.upper() not in {"SUCCESS", "PARTIAL_SUCCESS"}:
        errors = getattr(result, "errors", None) or []
        raise RuntimeError(f"Docling status={status_name}; errors={errors}")
    md = result.document.export_to_markdown()
    if not md or not md.strip():
        raise RuntimeError("Docling returned empty markdown")
    return md


def convert_to_markdown(
    path: str | Path,
    *,
    device: str = "cpu",
    num_threads: int = 4,
) -> str:
    """Convert a file to markdown. Prefer Docling; fall back for text/PDF."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    resolved = resolve_device(device)
    ext = path.suffix.lower()
    docling_error: Exception | None = None

    try:
        return _convert_with_docling(path, device=resolved, num_threads=num_threads)
    except Exception as exc:  # noqa: BLE001
        docling_error = exc

    if ext in TEXT_EXTENSIONS:
        return _fallback_text_markdown(path)

    if ext in PDF_EXTENSIONS:
        try:
            return _fallback_pdf_markdown(path)
        except Exception as pdf_exc:  # noqa: BLE001
            raise RuntimeError(
                f"Docling failed for {path.name} (device={resolved}): {docling_error}. "
                f"PDF fallback also failed: {pdf_exc}"
            ) from pdf_exc

    raise RuntimeError(
        f"Docling failed for {path.name} (device={resolved}): {docling_error}"
    ) from docling_error
