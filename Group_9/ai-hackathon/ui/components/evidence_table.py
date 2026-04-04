from __future__ import annotations


def render_claim_table(claims: list[dict]) -> list[list[str]]:
    rows: list[list[str]] = []
    for claim in claims:
        rows.append(
            [
                claim["statement"],
                str(len(claim["supporting_source_ids"])),
                str(len(claim["contradicting_source_ids"])),
                f"{claim['confidence']} ({claim['confidence_pct']}%)",
                f"{claim['trust_score']}%",
                claim.get("credibility_summary", ""),
                claim.get("evidence_summary", ""),
            ]
        )
    return rows
