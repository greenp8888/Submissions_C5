from typing import TypedDict, Optional


class RepoItem(TypedDict):
    source: str
    title: str
    url: str
    summary: str
    relevance_score: float
    metadata: dict


class GraphState(TypedDict):
    # Input
    idea_description: str
    audience: Optional[str]
    product_url: Optional[str]

    # Query Builder output
    query_object: Optional[dict]

    # Retrieval output — parallel, each key is a source name
    raw_results: Optional[dict]

    # After matcher + aggregator
    matched_items: Optional[list[RepoItem]]

    # Analysis output
    analysis: Optional[dict]

    # Final report
    report: Optional[dict]

    # Metadata
    request_id: str
    error: Optional[str]
