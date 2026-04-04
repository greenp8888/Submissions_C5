from __future__ import annotations


def render_claim_table(claims: list[dict]) -> list[list[str]]:
    rows = [["Claim", "Supporting Sources", "Contradicting Sources", "Confidence", "Trust"]]
    for claim in claims:
        rows.append(
            [
                claim["statement"],
                str(len(claim["supporting_source_ids"])),
                str(len(claim["contradicting_source_ids"])),
                f"{claim['confidence']} ({claim['confidence_pct']}%)",
                f"{claim['trust_score']}%",
            ]
        )
    return rows

