from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProviderAdapter:
    name: str
    enabled: bool = False
    description: str = ""


def secondary_adapters() -> list[ProviderAdapter]:
    return [
        ProviderAdapter(name="semantic_scholar", description="Academic expansion adapter"),
        ProviderAdapter(name="pubmed", description="Medical literature expansion adapter"),
        ProviderAdapter(name="newsapi", description="News expansion adapter"),
        ProviderAdapter(name="gdelt", description="Events/news expansion adapter"),
    ]

