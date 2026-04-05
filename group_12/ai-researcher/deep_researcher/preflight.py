"""Human-in-the-loop preflight: summarize uploads vs research question before full graph run."""

from __future__ import annotations

from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader

from .config import Settings
from .graph import get_llm, normalize_excerpt_whitespace
from .retrieval import _classify_local_paths, _documents_from_image


def _pdf_leading_excerpt(path: str, max_pages: int = 2, max_chars: int = 2800) -> str:
    try:
        loader = PyPDFLoader(path)
        pages = loader.load()
        parts = [p.page_content or "" for p in pages[:max_pages]]
        return normalize_excerpt_whitespace(" ".join(parts))[:max_chars]
    except Exception as exc:
        return f"_(Could not read PDF: {exc!s})_"


def _image_caption_line(path: str) -> str:
    name = Path(path).name
    try:
        doc = _documents_from_image(path)[0]
        raw = (doc.page_content or "").strip()
        if raw.startswith("[Image:") and "]" in raw:
            raw = raw.split("]", 1)[1].strip()
        return f"**{name}:** {raw}"
    except Exception as exc:
        return f"**{name}:** _(caption error: {exc!s})_"


def build_upload_digest(local_paths: list[str]) -> str:
    """Markdown describing what we see in uploads (no full research)."""
    pdfs, images, audios, skipped = _classify_local_paths(local_paths)
    blocks: list[str] = []

    if images:
        blocks.append("### What the uploaded images show (auto-caption)\n")
        blocks.append(
            "_Captions come from BLIP; they can be wrong or vague. Use them as a quick sanity check._\n"
        )
        for p in images:
            blocks.append(_image_caption_line(p))
            blocks.append("")

    if pdfs:
        blocks.append("### What the uploaded PDFs start with (first ~2 pages each)\n")
        for p in pdfs[:6]:
            name = Path(p).name
            ex = _pdf_leading_excerpt(p)
            blocks.append(f"**{name}**\n\n{ex}\n")

    if audios:
        blocks.append("### Audio files\n")
        blocks.append(
            ", ".join(f"`{Path(a).name}`" for a in audios)
            + " — _Full Whisper transcription runs only **after** you confirm._\n"
        )

    if skipped:
        blocks.append("### Could not classify as PDF / image / audio\n")
        blocks.append(", ".join(f"`{Path(s).name}`" for s in skipped))

    if not blocks:
        blocks.append(
            "_No local files uploaded. If you continue, research will rely on Wikipedia, arXiv, "
            "and web search (when enabled) only._\n"
        )

    return "\n".join(blocks).strip()


def assemble_preflight_markdown(digest: str, analysis: str) -> str:
    return "\n\n".join(
        [
            "## Human review (before full research)",
            "",
            digest,
            "",
            "---",
            "",
            analysis.strip(),
            "",
            "---",
            "",
            "### Continue?",
            "**Do you want to run the full deep research pipeline now?**",
            "",
            "- Click **Yes — run full research** to start planning, retrieval, analysis, and the report.",
            "- Click **No — cancel** to stay on this page and change your question or files (then review again).",
        ]
    ).strip()


def llm_preflight_analysis(question: str, digest: str, settings: Settings) -> str:
    """LLM alignment section only (caller may run after streaming a digest-building step)."""
    q = (question or "").strip()
    if not q:
        raise ValueError("Research question is empty.")

    llm = get_llm(settings, temperature=0.15)
    prompt = f"""
You are helping a researcher decide whether to start an **expensive multi-agent deep research run**.

Their **research question** is:
---
{q}
---

Here is what we automatically extracted from **their uploads** (image captions may be imperfect; PDF text is only the beginning of each file):

---
{digest}
---

Write **clear, concise markdown** (no JSON) with these sections:

## Alignment with your search
- State whether the uploads (especially **image captions** vs PDF intros) appear **in sync**, **partially related**, or **misaligned** with the research question.
- Call out any **risk** (e.g. wrong image, unrelated PDF, question needs web-only data).

## Recommendation
- One short paragraph: should they proceed, adjust the question, or swap files?

Keep a practical tone. Do not invent file contents not shown above.
""".strip()

    response = llm.invoke(prompt)
    return getattr(response, "content", str(response)).strip()


def human_preflight_markdown(question: str, local_paths: list[str], settings: Settings) -> str:
    """Full preflight panel: upload digest + LLM alignment note + prompt for Yes/No."""
    q = (question or "").strip()
    if not q:
        raise ValueError("Research question is empty.")

    digest = build_upload_digest(local_paths)
    analysis = llm_preflight_analysis(q, digest, settings)
    return assemble_preflight_markdown(digest, analysis)
