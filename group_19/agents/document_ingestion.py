import os
from typing import Dict, Any
from agents.state import FinancialState
from utils.file_parser import parse_financial_file


def document_ingestion_agent(state: FinancialState) -> Dict[str, Any]:
    """
    Document Ingestion Agent
    ------------------------
    - Takes raw file paths or already-parsed data from `state['raw_data']`.
    - Parses financial files (CSV/Excel) using file_parser.
    - Validates required columns and data integrity.
    - Populates `financial_snapshot` for downstream agents.
    - Records any errors in `state['errors']`.
    """

    errors = list(state.get("errors", []))
    raw_data = state.get("raw_data")

    # If raw_data is a dict with file_path, parse it
    if raw_data and isinstance(raw_data, dict) and "file_path" in raw_data:
        file_path = raw_data["file_path"]

        if not os.path.exists(file_path):
            errors.append(f"[document_ingestion] File not found: {file_path}")
            return {
                "financial_snapshot": None,
                "errors": errors,
                "current_agent": "document_ingestion",
            }

        try:
            parsed = parse_financial_file(file_path)
        except Exception as e:
            errors.append(f"[document_ingestion] Failed to parse file: {str(e)}")
            return {
                "financial_snapshot": None,
                "errors": errors,
                "current_agent": "document_ingestion",
            }

    elif raw_data and isinstance(raw_data, dict) and "total_income" in raw_data:
        # Already parsed — pass-through (useful for testing)
        parsed = raw_data
    else:
        errors.append("[document_ingestion] No valid raw_data provided. Expected a dict with 'file_path' key or pre-parsed financial data.")
        return {
            "financial_snapshot": None,
            "errors": errors,
            "current_agent": "document_ingestion",
        }

    # Validate essential fields
    required_keys = ["total_income", "total_expenses", "net_savings", "savings_rate",
                     "expense_by_category", "income_sources"]
    missing = [k for k in required_keys if k not in parsed]
    if missing:
        errors.append(f"[document_ingestion] Missing required fields in parsed data: {', '.join(missing)}")

    # Build financial snapshot
    financial_snapshot = {
        "total_income": parsed.get("total_income", 0.0),
        "total_expenses": parsed.get("total_expenses", 0.0),
        "gross_expenses": parsed.get("gross_expenses", 0.0),
        "refund_amount": parsed.get("refund_amount", 0.0),
        "transfer_amount": parsed.get("transfer_amount", 0.0),
        "net_savings": parsed.get("net_savings", 0.0),
        "savings_rate": parsed.get("savings_rate", 0.0),
        "expense_by_category": parsed.get("expense_by_category", {}),
        "income_sources": parsed.get("income_sources", {}),
        "transaction_count": parsed.get("transaction_count", 0),
    }

    return {
        "raw_data": parsed,          # Replace raw input with parsed dict for downstream
        "financial_snapshot": financial_snapshot,
        "errors": errors,
        "current_agent": "document_ingestion",
    }
