def retrieve_relevant_context(vector_store, query: str, top_k: int = 3) -> str:
    if vector_store is None:
        return "No retrieval context is available."

    if not query or not query.strip():
        return "No retrieval query provided."

    docs = vector_store.similarity_search(query, k=top_k)
    if not docs:
        return "No matching transaction context found."

    formatted_docs = []
    for idx, doc in enumerate(docs, start=1):
        metadata = getattr(doc, "metadata", {}) or {}

        date = metadata.get("date", "N/A")
        description = metadata.get("description", "N/A")
        category = metadata.get("category", "N/A")
        amount = metadata.get("amount", "N/A")
        txn_type = metadata.get("type", "N/A")
        balance = metadata.get("balance", "N/A")

        formatted_docs.append(
            f"Match {idx}\n"
            f"Date: {date}\n"
            f"Description: {description}\n"
            f"Category: {category}\n"
            f"Amount: {amount}\n"
            f"Type: {txn_type}\n"
            f"Balance: {balance}\n"
            f"Source Text:\n{doc.page_content}"
        )

    return "\n\n".join(formatted_docs)