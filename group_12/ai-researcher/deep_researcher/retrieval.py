
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import arxiv
import wikipedia
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .models import EvidenceItem


def _safe_text(value: str | None) -> str:
    return (value or "").strip()


LOCAL_FILE_LABEL = "Local uploads"

PDF_EXT = frozenset({".pdf"})
IMAGE_EXT = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"})
AUDIO_EXT = frozenset({".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm"})

_BLIP_PIPE: Any = None
_ASR_PIPES: dict[str, Any] = {}


def _sniff_file_category(path: str) -> str | None:
    """Classify as pdf / image / audio from a small prefix read only.

    Gradio temp uploads often have no extension. PIL ``Image.open().load()`` and
    ``librosa.load()`` decode real media and can freeze the UI when ``File.change``
    runs on large files — use magic bytes instead.
    """
    try:
        with open(path, "rb") as f:
            head = f.read(8192)
    except OSError:
        return None
    if len(head) < 4:
        return None
    if head.startswith(b"%PDF"):
        return "pdf"
    if head.startswith(b"\xff\xd8\xff"):
        return "image"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image"
    if head.startswith((b"GIF87a", b"GIF89a")):
        return "image"
    if len(head) >= 12 and head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        return "image"
    if head.startswith(b"BM"):
        return "image"
    if head.startswith((b"II*\x00", b"MM\x00*")):
        return "image"
    # Matroska / WebM (EBML)
    if head.startswith(b"\x1a\x45\xdf\xa3"):
        return "audio"
    if head.startswith(b"OggS"):
        return "audio"
    if head.startswith(b"fLaC"):
        return "audio"
    if len(head) >= 12 and head.startswith(b"RIFF") and head[8:12] == b"WAVE":
        return "audio"
    if head.startswith(b"ID3"):
        return "audio"
    if head[0] == 0xFF and (head[1] & 0xE0) == 0xE0:
        return "audio"
    if len(head) >= 12 and head[4:8] == b"ftyp":
        brand = head[8:12]
        if brand in (b"M4A ", b"M4B ", b"mp4a", b"isom", b"mp41", b"mp42", b"qt  ", b"3gp6"):
            return "audio"
        return None
    return None


def _classify_local_paths(paths: list[str]) -> tuple[list[str], list[str], list[str], list[str]]:
    """Classify by extension; Gradio temp files often have no suffix — sniff a few bytes only."""
    pdfs, images, audios, skipped = [], [], [], []
    for raw in paths:
        p = _safe_text(raw)
        if not p:
            continue
        ext = Path(p).suffix.lower()
        if ext in PDF_EXT:
            pdfs.append(p)
        elif ext in IMAGE_EXT:
            images.append(p)
        elif ext in AUDIO_EXT:
            audios.append(p)
        else:
            kind = _sniff_file_category(p)
            if kind == "pdf":
                pdfs.append(p)
            elif kind == "image":
                images.append(p)
            elif kind == "audio":
                audios.append(p)
            else:
                skipped.append(p)
    return pdfs, images, audios, skipped


def _get_blip_pipeline() -> Any:
    global _BLIP_PIPE
    if _BLIP_PIPE is None:
        from transformers import pipeline

        model_id = "Salesforce/blip-image-captioning-base"
        # transformers removed the "image-to-text" task in favor of "image-text-to-text";
        # keep "image-to-text" as fallback for older installs.
        last_exc: Exception | None = None
        for task in ("image-text-to-text", "image-to-text"):
            try:
                _BLIP_PIPE = pipeline(task, model=model_id)
                break
            except Exception as exc:
                last_exc = exc
                _BLIP_PIPE = None
        if _BLIP_PIPE is None:
            raise RuntimeError(
                "Could not load BLIP captioning pipeline. "
                "Try upgrading transformers/torch, or see the inner error."
            ) from last_exc
    return _BLIP_PIPE


def _run_blip_on_image(pipe: Any, im: Any) -> Any:
    """Call BLIP pipeline across transformers versions.

    ImageTextToTextPipeline requires ``text=`` when given a valid PIL image (text may be empty).
    Legacy image-to-text only accepted a single image argument.
    """
    try:
        try:
            return pipe(images=im, text="")
        except Exception:
            # Some BLIP/processor builds prefer a short conditional prefix for captioning.
            return pipe(images=im, text="a picture of")
    except TypeError:
        return pipe(im)


def _get_asr_pipeline(model_id: str) -> Any:
    if model_id not in _ASR_PIPES:
        from transformers import pipeline

        _ASR_PIPES[model_id] = pipeline(
            "automatic-speech-recognition",
            model=model_id,
        )
    return _ASR_PIPES[model_id]


def _load_split_one_pdf(path: str, chunk_size: int, chunk_overlap: int) -> list[Document]:
    loader = PyPDFLoader(path)
    pages = loader.load()
    for page in pages:
        page.metadata["source_path"] = path
        page.metadata["modality"] = "pdf"
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    return splitter.split_documents(pages)


def _pdf_documents_parallel(
    pdf_paths: list[str],
    chunk_size: int,
    chunk_overlap: int,
    max_workers: int,
) -> list[Document]:
    if not pdf_paths:
        return []
    workers = min(max_workers, len(pdf_paths))
    if len(pdf_paths) == 1:
        return _load_split_one_pdf(pdf_paths[0], chunk_size, chunk_overlap)

    def _one(p: str) -> list[Document]:
        return _load_split_one_pdf(p, chunk_size, chunk_overlap)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        chunk_lists = list(pool.map(_one, pdf_paths))
    return [c for lst in chunk_lists for c in lst]


def _documents_from_image(path: str) -> list[Document]:
    name = Path(path).name
    try:
        from PIL import Image
    except ImportError:
        return [
            Document(
                page_content=f"[Image: {name}] Install Pillow to load this file.",
                metadata={"source_path": path, "page": 0, "modality": "image"},
            )
        ]
    try:
        pipe = _get_blip_pipeline()
        im = Image.open(path).convert("RGB")
        res = _run_blip_on_image(pipe, im)
        if isinstance(res, str):
            cap = res
        elif isinstance(res, list) and res:
            first = res[0]
            if isinstance(first, dict):
                cap = first.get("generated_text") or first.get("text") or str(first)
            else:
                cap = str(first)
        elif isinstance(res, dict):
            cap = res.get("generated_text") or res.get("text") or str(res)
        else:
            cap = str(res)
    except Exception as exc:
        cap = f"(Caption failed — install torch+transformers or check the file: {exc!s})"
    return [
        Document(
            page_content=f"[Image: {name}] {cap}",
            metadata={"source_path": path, "page": 0, "modality": "image"},
        )
    ]


def _documents_from_audio(path: str, asr_model: str, max_seconds: float) -> list[Document]:
    name = Path(path).name
    try:
        import librosa
    except ImportError:
        return [
            Document(
                page_content=f"[Audio: {name}] Install librosa + soundfile to transcribe.",
                metadata={"source_path": path, "page": 0, "modality": "audio"},
            )
        ]
    try:
        audio, _sr = librosa.load(path, sr=16000, duration=max_seconds)
        pipe = _get_asr_pipeline(asr_model)
        res = pipe(audio)
        text = res.get("text", str(res)) if isinstance(res, dict) else str(res)
    except Exception as exc:
        text = f"(Transcription failed — install torch+transformers or check the file: {exc!s})"
    return [
        Document(
            page_content=f"[Audio transcript: {name}] {text}",
            metadata={"source_path": path, "page": 0, "modality": "audio"},
        )
    ]


def _doc_to_evidence_item(doc: Document, query: str, seen: set[tuple[str, str, str]]) -> EvidenceItem | None:
    path = doc.metadata.get("source_path", "")
    modality = (doc.metadata.get("modality") or "pdf").lower()
    name = Path(str(path)).name or "upload"

    if modality == "image":
        source_type = "local_image"
        title = f"{name} (image caption)"
    elif modality == "audio":
        source_type = "local_audio"
        title = f"{name} (transcript)"
    else:
        source_type = "local_pdf"
        page = doc.metadata.get("page", "n/a")
        title = f"{name} (page {page})"

    excerpt = _safe_text(doc.page_content)[:1200]
    signature = (title, excerpt[:200], query)
    if signature in seen:
        return None
    seen.add(signature)
    return EvidenceItem(
        source_type=source_type,
        source_label=LOCAL_FILE_LABEL,
        title=title,
        url="",
        excerpt=excerpt,
        query_used=query,
        relevance_hint="Retrieved from local FAISS (PDF / image caption / audio transcript)",
    )


def build_local_media_evidence(
    file_paths: list[str],
    queries: list[str],
    embedding_model: str,
    chunk_size: int,
    chunk_overlap: int,
    top_k: int,
    *,
    research_question: str = "",
    parallel_workers: int = 4,
    asr_model_id: str = "openai/whisper-small",
    asr_max_seconds: float = 180.0,
) -> tuple[list[EvidenceItem], str]:
    """Build evidence from PDFs, raster images (BLIP), and audio (Whisper). Returns (evidence, status note)."""
    if not file_paths:
        return [], "no paths"

    pdfs, images, audios, skipped = _classify_local_paths(file_paths)
    notes: list[str] = []
    if skipped:
        notes.append(f"skipped unsupported extension(s): {len(skipped)} file(s)")

    all_docs: list[Document] = []
    all_docs.extend(_pdf_documents_parallel(pdfs, chunk_size, chunk_overlap, parallel_workers))

    for img_path in images:
        all_docs.extend(_documents_from_image(img_path))

    for aud_path in audios:
        all_docs.extend(_documents_from_audio(aud_path, asr_model_id, asr_max_seconds))

    if not all_docs:
        return [], "no documents extracted" + ("; " + "; ".join(notes) if notes else "")

    embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
    vectorstore = FAISS.from_documents(all_docs, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})

    evidence: list[EvidenceItem] = []
    seen: set[tuple[str, str, str]] = set()
    paths_with_hit: set[str] = set()

    for query in queries:
        q = _safe_text(query)
        if not q:
            continue
        for doc in retriever.invoke(q):
            item = _doc_to_evidence_item(doc, q, seen)
            if item is not None:
                evidence.append(item)
                sp = _safe_text(doc.metadata.get("source_path"))
                if sp:
                    paths_with_hit.add(sp)

    # Image/audio docs are often missed by pure semantic top-k vs. planner sub-questions — always surface them once.
    fallback_q = _safe_text(queries[0]) if queries else _safe_text(research_question)
    if not fallback_q:
        fallback_q = "Uploaded local files (image/audio)"

    for doc in all_docs:
        mod = doc.metadata.get("modality")
        if mod not in ("image", "audio"):
            continue
        sp = _safe_text(doc.metadata.get("source_path"))
        if sp and sp in paths_with_hit:
            continue
        item = _doc_to_evidence_item(doc, fallback_q, seen)
        if item is not None:
            evidence.append(item)
            if sp:
                paths_with_hit.add(sp)

    summary = (
        f"pdfs={len(pdfs)} images={len(images)} audio={len(audios)} chunks/docs={len(all_docs)} hits={len(evidence)}"
    )
    if notes:
        summary += "; " + "; ".join(notes)
    return evidence, summary


def build_pdf_evidence(
    pdf_paths: list[str],
    queries: list[str],
    embedding_model: str,
    chunk_size: int,
    chunk_overlap: int,
    top_k: int,
) -> list[EvidenceItem]:
    """Backward-compatible wrapper: PDF paths only."""
    ev, _ = build_local_media_evidence(
        pdf_paths,
        queries,
        embedding_model,
        chunk_size,
        chunk_overlap,
        top_k,
        research_question="",
        parallel_workers=4,
    )
    return ev


def build_wikipedia_evidence(queries: list[str], max_pages_per_query: int = 1) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    seen = set()

    for query in queries[:4]:
        try:
            titles = wikipedia.search(query, results=max_pages_per_query)
        except Exception:
            continue

        for title in titles:
            try:
                page = wikipedia.page(title, auto_suggest=False)
            except Exception:
                continue

            signature = page.title
            if signature in seen:
                continue
            seen.add(signature)

            evidence.append(
                EvidenceItem(
                    source_type="wikipedia",
                    source_label="Wikipedia",
                    title=page.title,
                    url=page.url,
                    excerpt=_safe_text(page.summary)[:1200],
                    query_used=query,
                    relevance_hint="Background or explanatory context",
                )
            )
    return evidence


def build_arxiv_evidence(queries: list[str], max_results_per_query: int = 2) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    seen = set()

    for query in queries[:3]:
        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results_per_query,
                sort_by=arxiv.SortCriterion.Relevance,
            )
            results = list(search.results())
        except Exception:
            continue

        for paper in results:
            signature = getattr(paper, "entry_id", "") or paper.title
            if signature in seen:
                continue
            seen.add(signature)

            summary = _safe_text(getattr(paper, "summary", ""))
            evidence.append(
                EvidenceItem(
                    source_type="arxiv",
                    source_label="arXiv",
                    title=_safe_text(getattr(paper, "title", "Untitled paper")),
                    url=_safe_text(getattr(paper, "entry_id", "")),
                    excerpt=summary[:1200],
                    query_used=query,
                    relevance_hint="Academic or technical source",
                )
            )
    return evidence


def build_tavily_evidence(
    api_key: str | None,
    queries: list[str],
    max_results_per_query: int = 3,
) -> list[EvidenceItem]:
    if not api_key:
        return []

    try:
        from tavily import TavilyClient
    except Exception:
        return []

    client = TavilyClient(api_key=api_key)
    evidence: list[EvidenceItem] = []
    seen = set()

    for query in queries[:3]:
        try:
            response = client.search(
                query=query,
                topic="general",
                max_results=max_results_per_query,
                include_raw_content=False,
            )
        except Exception:
            continue

        for item in response.get("results", []):
            title = _safe_text(item.get("title"))
            url = _safe_text(item.get("url"))
            excerpt = _safe_text(item.get("content"))[:1200]
            signature = url or title
            if not signature or signature in seen:
                continue
            seen.add(signature)

            evidence.append(
                EvidenceItem(
                    source_type="web",
                    source_label="Tavily Web",
                    title=title or "Web result",
                    url=url,
                    excerpt=excerpt,
                    query_used=query,
                    relevance_hint="Current web evidence",
                )
            )

    return evidence
