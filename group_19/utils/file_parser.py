import pandas as pd
from typing import Dict, Any, Optional

# ---------------------------------------------------------------------------
# Configurable category classification
# ---------------------------------------------------------------------------
# Each category maps to one of four transaction types:
#   "income"    — real money coming in (salary, interest, reimbursements)
#   "expense"   — money going out (all spending)
#   "transfer"  — internal account movement (excluded from income & expense)
#   "refund"    — returns/credits that reduce expenses (not counted as income)
#
# Categories NOT listed here default to "expense".
# ---------------------------------------------------------------------------
CATEGORY_CLASSIFICATION: Dict[str, str] = {
    # Income — real money coming in
    "Salary": "income",
    "Interest": "income",
    "Reimbursement": "income",

    # Transfers — internal account movement (not income, not expense)
    "Transfer": "transfer",
    "Credit Card Payment": "transfer",   # paying off a card from checking/bank

    # Refunds / returns (reduce expenses, not counted as income)
    "Refunds": "refund",
}


def _classify_transaction(row: pd.Series) -> str:
    """
    Classify a single transaction as income / expense / transfer / refund.

    Rules (strict explicit-only):
      1. If category is in CATEGORY_CLASSIFICATION, use that mapping.
      2. Otherwise default to "expense" — regardless of credit/debit type.

    We do NOT auto-treat credits as refunds because bank statements use
    'credit' for many things (statement credits, card payments, etc.) that
    are not product returns.  Only explicitly mapped categories get special
    treatment.
    """
    category = row.get("category", "")

    if category in CATEGORY_CLASSIFICATION:
        return CATEGORY_CLASSIFICATION[category]

    return "expense"


def parse_financial_file(
    file_path: str,
    category_classification: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Parse Excel or CSV financial data into structured dict.

    Expected columns: Date, Category, Amount, Type (credit/debit), Description
    (Account column is optional and currently unused.)

    Parameters
    ----------
    file_path : str
        Path to CSV or Excel file.
    category_classification : dict, optional
        Override the default CATEGORY_CLASSIFICATION mapping for custom datasets.

    Returns
    -------
    dict with keys:
        total_income, total_expenses, net_savings, savings_rate,
        expense_by_category, income_sources, income_by_category,
        refund_amount, transfer_amount, transaction_count, raw_dataframe
    """
    global CATEGORY_CLASSIFICATION
    if category_classification is not None:
        CATEGORY_CLASSIFICATION = category_classification

    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    df.columns = df.columns.str.lower().str.strip()

    # Classify each transaction
    df["classification"] = df.apply(_classify_transaction, axis=1)

    # --- Income ---
    income_mask = df["classification"] == "income"
    income_df = df[income_mask]
    total_income = income_df["amount"].sum()
    income_by_category = income_df.groupby("category")["amount"].sum().to_dict()

    # --- Expenses ---
    # For expense-category transactions, debit = positive expense, credit = return (negative expense)
    expense_mask = df["classification"] == "expense"
    expense_df = df[expense_mask].copy()
    expense_df["signed_amount"] = expense_df.apply(
        lambda r: r["amount"] if str(r.get("type", "")).lower().strip() == "debit" else -r["amount"],
        axis=1,
    )
    total_expenses = expense_df["signed_amount"].sum()
    expense_by_category = expense_df.groupby("category")["signed_amount"].sum().to_dict()

    # --- Refunds (reduce expenses) ---
    refund_mask = df["classification"] == "refund"
    refund_amount = df.loc[refund_mask, "amount"].sum()
    net_expenses = total_expenses - refund_amount

    # --- Transfers (excluded) ---
    transfer_mask = df["classification"] == "transfer"
    transfer_amount = df.loc[transfer_mask, "amount"].sum()

    # --- Summary ---
    net_savings = total_income - net_expenses
    savings_rate = round(net_savings / total_income * 100, 2) if total_income > 0 else 0

    return {
        "total_income": float(total_income),
        "total_expenses": float(net_expenses),       # expenses minus refunds
        "gross_expenses": float(total_expenses),
        "refund_amount": float(refund_amount),
        "transfer_amount": float(transfer_amount),
        "net_savings": float(net_savings),
        "savings_rate": float(savings_rate),
        # Explicitly convert numpy types to plain Python floats so json.dumps works
        "expense_by_category": {k: float(v) for k, v in expense_by_category.items()},
        "income_sources": {k: float(v) for k, v in income_by_category.items()},
        "transaction_count": int(len(df)),
        "raw_dataframe": df.to_dict(orient="records"),
    }

def create_sample_excel():
    """Creates a sample Excel file for testing/demo."""
    import os
    data = {
        'Date': ['2024-01-01','2024-01-05','2024-01-10','2024-01-15',
                 '2024-01-20','2024-01-25','2024-01-28','2024-01-30'],
        'Category': ['Salary','Rent','Groceries','Credit Card',
                     'Netflix','Car Payment','Dining Out','Freelance'],
        'Amount': [5000, 1500, 400, 300, 15, 350, 200, 800],
        'Type': ['income','expense','expense','expense',
                 'expense','expense','expense','income'],
        'Description': ['Monthly salary','Apartment rent','Weekly groceries',
                        'Visa card payment','Subscription','Car loan',
                        'Restaurant','Side project']
    }
    df = pd.DataFrame(data)
    os.makedirs('data/sample_data', exist_ok=True)
    df.to_excel('data/sample_data/sample_finances.xlsx', index=False)
    print("✅ Sample file created at data/sample_data/sample_finances.xlsx")
    return df