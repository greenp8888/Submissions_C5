"""PDF document loader tool for local file ingestion.

Wraps PyPDF (via LangChain's PyPDFLoader) as a LangChain @tool
for use by the Retriever agent. Allows users to include their own
research documents in the investigation.
"""

import json
import logging
import os
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Maximum characters extracted per page to avoid overwhelming the LLM context
_MAX_CHARS_PER_PAGE = 1500
_MAX_PAGES = 20


@tool
def load_pdf_document(file_path: str, max_pages: Optional[int] = None) -> str:
    """Load and extract text from a local PDF document.

    Uses PyPDFLoader to parse the PDF and chunk it by page.
    Returns structured content from each page, capped to avoid
    context overflow. Best for user-provided research papers,
    technical reports, and whitepapers.

    Args:
        file_path: Absolute or relative path to the PDF file.
        max_pages: Maximum number of pages to extract (default 20).

    Returns:
        str: JSON string containing a list of page dicts, each with:
            source, file_path, page_number, content, total_pages.
    """
    if not os.path.exists(file_path):
        logger.error("PDF file not found: %s", file_path)
        return json.dumps(
            {"error": f"File not found: {file_path}", "results": []}
        )

    if not file_path.lower().endswith(".pdf"):
        logger.error("File is not a PDF: %s", file_path)
        return json.dumps(
            {"error": f"Not a PDF file: {file_path}", "results": []}
        )

    logger.info("Loading PDF: %s", file_path)

    try:
        from langchain_community.document_loaders import PyPDFLoader

        loader = PyPDFLoader(file_path)
        pages = loader.load()

        limit = min(max_pages or _MAX_PAGES, _MAX_PAGES, len(pages))
        results = []

        for i, page in enumerate(pages[:limit]):
            content = page.page_content.strip()
            if not content:
                continue

            results.append(
                {
                    "source": "pdf",
                    "file_path": file_path,
                    "file_name": os.path.basename(file_path),
                    "page_number": i + 1,
                    "content": content[:_MAX_CHARS_PER_PAGE],
                    "total_pages": len(pages),
                }
            )

    except Exception as exc:
        logger.error("PDF loading failed for '%s': %s", file_path, exc)
        return json.dumps({"error": str(exc), "results": []})

    logger.info(
        "PDF loaded: file=%s, pages_extracted=%d", os.path.basename(file_path), len(results)
    )
    return json.dumps(
        {
            "source": "pdf",
            "file_path": file_path,
            "pages_extracted": len(results),
            "results": results,
        },
        indent=2,
    )
