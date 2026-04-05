from typing import List, Tuple
from functools import lru_cache

import pandas as pd
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


def dataframe_to_text_chunks(df: pd.DataFrame) -> Tuple[List[str], List[dict]]:
    if df is None or df.empty:
        return [], []

    working_df = df.copy()
    chunks = []
    metadatas = []

    for idx, row in working_df.iterrows():
        date_value = row.get("date", "N/A")
        description = row.get("description", "N/A")
        amount = row.get("amount", "N/A")
        category = row.get("category", "N/A")
        balance = row.get("balance", "N/A")
        txn_type = row.get("type", "N/A")

        chunk = (
            f"Transaction record\n"
            f"Date: {date_value}\n"
            f"Description: {description}\n"
            f"Amount: {amount}\n"
            f"Category: {category}\n"
            f"Type: {txn_type}\n"
            f"Balance: {balance}"
        )

        chunks.append(chunk)
        metadatas.append(
            {
                "row_index": str(idx),
                "date": str(date_value),
                "description": str(description),
                "amount": str(amount),
                "category": str(category),
                "type": str(txn_type),
                "balance": str(balance),
            }
        )

    return chunks, metadatas


@lru_cache(maxsize=1)
def get_embedding_model() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


def build_faiss_vector_store(df: pd.DataFrame):
    chunks, metadatas = dataframe_to_text_chunks(df)
    if not chunks:
        return None

    embeddings = get_embedding_model()

    vector_store = FAISS.from_texts(
        texts=chunks,
        embedding=embeddings,
        metadatas=metadatas,
    )
    return vector_store