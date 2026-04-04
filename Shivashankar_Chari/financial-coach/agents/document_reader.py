from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".pdf", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE_MB = 5

COLUMN_ALIASES = {
    "date": ["date", "transaction_date", "txn_date", "posted_date"],
    "description": ["description", "narration", "details", "transaction_details", "remarks"],
    "amount": ["amount", "transaction_amount", "value", "debit_credit_amount"],
    "type": ["type", "transaction_type", "dr_cr", "debit_credit"],
}


def _normalize_column_name(column_name: str) -> str:
    """Normalize raw column names for matching."""
    return (
        str(column_name).strip().lower().replace(" ", "_").replace("-", "_")
    )


def _map_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map input columns to standardized names."""
    renamed_columns = {}

    for original_col in df.columns:
        normalized = _normalize_column_name(original_col)

        for standard_col, aliases in COLUMN_ALIASES.items():
            if normalized in aliases:
                renamed_columns[original_col] = standard_col
                break

    return df.rename(columns=renamed_columns)


def _ensure_required_columns(df: pd.DataFrame) -> None:
    """Validate that required columns are present."""
    missing = [col for col in ["date", "description", "amount"] if col not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns: {missing}. Expected at least date, description, and amount."
        )


def _clean_amount_column(df: pd.DataFrame) -> pd.DataFrame:
    """Convert amount column to numeric."""
    df["amount"] = (
        df["amount"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("₹", "", regex=False)
        .str.strip()
    )
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    return df


def _clean_date_column(df: pd.DataFrame) -> pd.DataFrame:
    """Convert date column to datetime."""
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def _standardize_type_column(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize transaction type if present."""
    if "type" not in df.columns:
        df["type"] = "unknown"
        return df

    df["type"] = df["type"].astype(str).str.strip().str.lower()

    df["type"] = df["type"].replace(
        {
            "dr": "debit",
            "cr": "credit",
            "debit": "debit",
            "credit": "credit",
        }
    )
    return df


def _final_cleanup(df: pd.DataFrame) -> pd.DataFrame:
    """Drop invalid rows and sort by date."""
    df = df.dropna(subset=["date", "description", "amount"]).copy()
    df["description"] = df["description"].astype(str).str.strip()
    df = df.sort_values(by="date").reset_index(drop=True)
    return df


def validate_uploaded_file(uploaded_file) -> Tuple[bool, str]:
    """Validate uploaded file type and size."""
    if uploaded_file is None:
        return False, "No file uploaded."

    file_name = uploaded_file.name
    extension = Path(file_name).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        return (
            False,
            f"Unsupported file type: {extension}. Supported types are CSV, Excel, PDF, PNG, JPG, JPEG.",
        )

    file_size_bytes = len(uploaded_file.getvalue())
    file_size_mb = file_size_bytes / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        return False, f"File size exceeds {MAX_FILE_SIZE_MB} MB limit."

    return True, "File is valid."


def read_tabular_file(uploaded_file) -> pd.DataFrame:
    """Read CSV or Excel file into a DataFrame."""
    extension = Path(uploaded_file.name).suffix.lower()
    file_bytes = BytesIO(uploaded_file.getvalue())

    if extension == ".csv":
        df = pd.read_csv(file_bytes)
    elif extension in {".xlsx", ".xls"}:
        df = pd.read_excel(file_bytes)
    else:
        raise ValueError("Only CSV and Excel files are supported for direct tabular parsing.")

    return df


def preprocess_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize and clean uploaded transaction data."""
    df = _map_columns(df)
    _ensure_required_columns(df)
    df = _clean_amount_column(df)
    df = _clean_date_column(df)
    df = _standardize_type_column(df)
    df = _final_cleanup(df)
    return df


def load_transactions(uploaded_file) -> pd.DataFrame:
    """Load and preprocess CSV or Excel transaction files."""
    is_valid, message = validate_uploaded_file(uploaded_file)
    if not is_valid:
        raise ValueError(message)

    extension = Path(uploaded_file.name).suffix.lower()

    if extension in {".csv", ".xlsx", ".xls"}:
        df = read_tabular_file(uploaded_file)
        return preprocess_transactions(df)

    raise ValueError(
        "PDF and image parsing are planned, but this version currently supports CSV and Excel for transaction extraction."
    )


def get_supported_file_message() -> str:
    """Return supported file types message for UI."""
    return "Supported formats: CSV, Excel, PDF, PNG, JPG, JPEG | Max file size: 5 MB"


def get_current_backend_support_message() -> str:
    """Return current backend support status for UI."""
    return "Current extraction support: CSV and Excel fully supported. PDF and image support will be added next."