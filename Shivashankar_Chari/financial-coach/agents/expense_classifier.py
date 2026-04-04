from typing import Dict, List

import pandas as pd


CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Food": ["swiggy", "zomato", "restaurant", "cafe", "food", "dining"],
    "Transport": ["uber", "ola", "metro", "bus", "fuel", "petrol", "diesel"],
    "Entertainment": ["netflix", "spotify", "prime", "movie", "bookmyshow"],
    "Shopping": ["amazon", "flipkart", "myntra", "ajio", "shopping"],
    "Bills": ["rent", "maintenance", "electricity", "water", "gas", "broadband"],
    "Income": ["salary", "income", "bonus", "credit interest"],
    "Debt / EMI": ["loan", "emi", "debt", "credit card"],
    "Healthcare": ["hospital", "medical", "pharmacy", "doctor", "health"],
}


def classify_transaction(description: str) -> str:
    """Classify a single transaction description into a category"""
    desc = str(description).lower().strip()

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in desc for keyword in keywords):
            return category

    return "Other"


def add_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Add category column to transaction dataframe"""
    working_df = df.copy()

    if "description" not in working_df.columns:
        working_df["category"] = "Other"
        return working_df

    working_df["category"] = working_df["description"].apply(classify_transaction)
    return working_df


def get_category_summary(df: pd.DataFrame) -> Dict[str, float]:
    """Return category-wise absolute expense totals"""
    if df.empty or "amount" not in df.columns or "category" not in df.columns:
        return {}

    expense_df = df[df["amount"] < 0].copy()
    if expense_df.empty:
        return {}

    category_spend = (
        expense_df.groupby("category")["amount"]
        .sum()
        .abs()
        .sort_values(ascending=False)
    )

    return {category: round(amount, 2) for category, amount in category_spend.items()}


def get_biggest_category(df: pd.DataFrame) -> str:
    """Return highest spending category"""
    summary = get_category_summary(df)
    if not summary:
        return "N/A"
    return next(iter(summary))
