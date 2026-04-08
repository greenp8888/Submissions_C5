"""
FinanceDoctor — Document Parser (Layer 1)
==========================================
Parses uploaded files (CSV, Excel, PDF) into text + optional DataFrame.
Primary: LlamaParse (for PDFs) | Fallback: PyPDF2
"""

from __future__ import annotations

import io
import os
import tempfile
from typing import Optional, Tuple

import pandas as pd


def parse_csv(file) -> Tuple[str, Optional[pd.DataFrame]]:
    """Parse CSV file → (markdown_text, DataFrame)."""
    df = None
    for encoding in ["utf-8", "utf-8-sig", "utf-16", "latin-1", "cp1252"]:
        try:
            file.seek(0)
            df = pd.read_csv(file, encoding=encoding)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if df is None:
        raise ValueError("Could not decode the CSV. Please re-save as UTF-8.")

    text = df.to_markdown(index=False)
    return text, df


def parse_excel(file, filename: str = "") -> Tuple[str, Optional[pd.DataFrame]]:
    """Parse Excel (.xlsx/.xls) file → (markdown_text, combined DataFrame)."""
    file.seek(0)
    dfs = pd.read_excel(file, sheet_name=None, engine="openpyxl")

    all_text_parts = []
    combined_df = None

    for sheet_name, df in dfs.items():
        all_text_parts.append(
            f"## Sheet: {sheet_name}\n{df.to_markdown(index=False)}"
        )
        if combined_df is None:
            combined_df = df.copy()
        else:
            combined_df = pd.concat([combined_df, df], ignore_index=True)

    return "\n\n".join(all_text_parts), combined_df


def parse_pdf_pypdf2(file) -> str:
    """Fallback PDF parser using PyPDF2."""
    from PyPDF2 import PdfReader

    file.seek(0)
    reader = PdfReader(file)
    pages = []
    for i, page in enumerate(reader.pages, 1):
        page_text = page.extract_text()
        if page_text and page_text.strip():
            pages.append(f"--- Page {i} ---\n{page_text.strip()}")
    return "\n\n".join(pages) if pages else "(No readable text found in PDF)"


def parse_pdf_llamaparse(file, api_key: str) -> str:
    """Primary PDF parser using LlamaParse (cloud API)."""
    from llama_parse import LlamaParse

    # LlamaParse needs a file path → save to temp
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file.seek(0)
        tmp.write(file.read())
        tmp_path = tmp.name

    try:
        parser = LlamaParse(
            api_key=api_key,
            result_type="markdown",
            verbose=False,
        )
        documents = parser.load_data(tmp_path)
        return "\n\n".join(doc.text for doc in documents)
    finally:
        os.unlink(tmp_path)


def parse_document(
    file,
    filename: str,
    llamaparse_key: str = None,
) -> Tuple[str, Optional[pd.DataFrame]]:
    """
    Main entry point for document parsing.

    Returns:
        (text, dataframe)  —  text is always present;
                               dataframe is present for tabular files (CSV/Excel).
    """
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext == "csv":
        return parse_csv(file)

    elif ext in ("xlsx", "xls"):
        return parse_excel(file, filename)

    elif ext == "pdf":
        text = None
        # Try LlamaParse first (better quality for complex PDFs)
        if llamaparse_key and llamaparse_key.strip():
            try:
                text = parse_pdf_llamaparse(file, llamaparse_key.strip())
            except Exception as e:
                print(f"[LlamaParse fallback] {e}")
                text = None

        # Fallback to PyPDF2
        if not text:
            text = parse_pdf_pypdf2(file)

        # Try to extract tabular data from text (if it looks like a table)
        df = _try_extract_table_from_text(text)
        return text, df

    else:
        raise ValueError(
            f"Unsupported file type: .{ext}. Supported: CSV, Excel (.xlsx), PDF"
        )


def _try_extract_table_from_text(text: str) -> Optional[pd.DataFrame]:
    """
    Best-effort attempt to extract a table from parsed PDF text.
    Returns None if no clear tabular structure is found.
    """
    lines = text.strip().split("\n")
    # Look for lines that might be CSV-like (contain commas or tabs)
    csv_lines = [l for l in lines if l.count(",") >= 2 or l.count("\t") >= 2]
    if len(csv_lines) >= 3:
        try:
            sep = "\t" if csv_lines[0].count("\t") > csv_lines[0].count(",") else ","
            df = pd.read_csv(io.StringIO("\n".join(csv_lines)), sep=sep)
            if len(df.columns) >= 2 and len(df) >= 2:
                return df
        except Exception:
            pass
    return None
