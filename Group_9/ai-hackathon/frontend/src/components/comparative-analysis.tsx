import type { Claim, Contradiction, ResearchSession, Source } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { truncate } from "@/lib/utils";

type ComparisonRow = {
  id: string;
  topic: string;
  left: string;
  right: string;
  consensus: number;
  favored: string;
  citations: string;
};

export function ComparativeAnalysis({
  session,
  expandedSections,
  onToggleSection,
}: {
  session: ResearchSession;
  expandedSections: string[];
  onToggleSection: (section: string, expanded: boolean) => void;
}) {
  const sourceIndex = new Map(session.sources.map((source, index) => [source.id, index + 1]));
  const rows = buildRows(session, sourceIndex);
  const contestedClaims = session.claims.filter((claim) => claim.contested || claim.consensus_pct < 60);
  const hasContent = session.debate_mode || session.contradictions.length > 0 || contestedClaims.length > 0;

  if (!hasContent) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center gap-2">
          <CardTitle>Comparative Analysis</CardTitle>
          {session.debate_mode ? <Badge variant="secondary">Debate enabled</Badge> : null}
          {session.contradictions.length ? <Badge variant="warning">{session.contradictions.length} disagreements</Badge> : null}
        </div>
        <CardDescription>Scan the main points of disagreement quickly, then expand the accordions to inspect debate evidence, contested claims, and credibility-weighted reasoning.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="overflow-auto rounded-2xl border border-border bg-white/80">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-muted/65 text-xs uppercase tracking-[0.14em] text-muted-foreground">
              <tr>
                <th className="px-4 py-3">Claim cluster</th>
                <th className="px-4 py-3">{session.position_a || "Supporting evidence"}</th>
                <th className="px-4 py-3">{session.position_b || "Opposing evidence"}</th>
                <th className="px-4 py-3">Consensus</th>
                <th className="px-4 py-3">Lean</th>
                <th className="px-4 py-3">Citations</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-t border-border/80 align-top">
                  <td className="px-4 py-4 font-semibold">{row.topic}</td>
                  <td className="px-4 py-4 text-muted-foreground">{row.left}</td>
                  <td className="px-4 py-4 text-muted-foreground">{row.right}</td>
                  <td className="px-4 py-4">{row.consensus}%</td>
                  <td className="px-4 py-4">
                    <Badge variant={row.favored === "mixed" ? "secondary" : "success"}>{humanize(row.favored)}</Badge>
                  </td>
                  <td className="px-4 py-4 font-mono text-xs">{row.citations}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <details className="overflow-hidden rounded-2xl border border-border bg-white/80" open={expandedSections.includes("debate")} onToggle={(event) => onToggleSection("debate", (event.currentTarget as HTMLDetailsElement).open)}>
          <summary className="cursor-pointer list-none px-5 py-4 font-semibold">Debate Evidence</summary>
          <div className="border-t border-border px-5 py-4 text-sm text-slate-700">
            {session.debate_mode ? (
              <div className="grid gap-4 lg:grid-cols-2">
                <PositionColumn
                  title={`Position A: ${session.position_a || "Position A"}`}
                  claims={session.claims.filter((claim) => claim.debate_position === "position_a")}
                  sourceIndex={sourceIndex}
                />
                <PositionColumn
                  title={`Position B: ${session.position_b || "Position B"}`}
                  claims={session.claims.filter((claim) => claim.debate_position === "position_b")}
                  sourceIndex={sourceIndex}
                />
              </div>
            ) : (
              <p>Debate mode was not enabled for this run. Comparative analysis here is driven by source disagreement only.</p>
            )}
          </div>
        </details>

        <details className="overflow-hidden rounded-2xl border border-border bg-white/80" open={expandedSections.includes("disagreement")} onToggle={(event) => onToggleSection("disagreement", (event.currentTarget as HTMLDetailsElement).open)}>
          <summary className="cursor-pointer list-none px-5 py-4 font-semibold">Source Disagreement</summary>
          <div className="border-t border-border px-5 py-4">
            {session.contradictions.length ? (
              <div className="space-y-3">
                {session.contradictions.map((item) => (
                  <div key={item.id} className="rounded-2xl border border-border bg-muted/35 p-4 text-sm">
                    <p className="font-semibold">{item.analysis}</p>
                    <p className="mt-2 text-slate-700">Source A: {item.claim_a} ({item.source_a_label || "unknown"})</p>
                    <p className="mt-1 text-slate-700">Source B: {item.claim_b} ({item.source_b_label || "unknown"})</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                        <Badge variant={item.credibility_lean === "mixed" ? "secondary" : "success"}>Lean: {humanize(item.credibility_lean || "mixed")}</Badge>
                    </div>
                    <p className="mt-3 text-xs text-muted-foreground">{item.weighting_rationale || item.resolution || "Comparable support across conflicting sources."}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No material cross-source disagreements were detected.</p>
            )}
          </div>
        </details>

        <details className="overflow-hidden rounded-2xl border border-border bg-white/80" open={expandedSections.includes("contested")} onToggle={(event) => onToggleSection("contested", (event.currentTarget as HTMLDetailsElement).open)}>
          <summary className="cursor-pointer list-none px-5 py-4 font-semibold">Contested Claims</summary>
          <div className="border-t border-border px-5 py-4">
            {contestedClaims.length ? (
              <div className="space-y-3">
                {contestedClaims.map((claim) => (
                  <div key={claim.id} className="rounded-2xl border border-border bg-muted/35 p-4 text-sm">
                    <p className="font-semibold">{claim.statement}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Badge variant="warning">Consensus {claim.consensus_pct}%</Badge>
                      <Badge variant="secondary">Confidence {claim.confidence_pct}%</Badge>
                      <Badge variant="secondary">Trust {claim.trust_score}%</Badge>
                    </div>
                    <p className="mt-3 text-slate-700">{claim.evidence_summary}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No low-consensus claims were detected.</p>
            )}
          </div>
        </details>

        <details className="overflow-hidden rounded-2xl border border-border bg-white/80" open={expandedSections.includes("weighted")} onToggle={(event) => onToggleSection("weighted", (event.currentTarget as HTMLDetailsElement).open)}>
          <summary className="cursor-pointer list-none px-5 py-4 font-semibold">Why One Side Was Weighted More</summary>
          <div className="border-t border-border px-5 py-4 text-sm text-slate-700">
            {session.contradictions.length ? (
              <ul className="space-y-3">
                {session.contradictions.map((item) => (
                  <li key={`${item.id}-why`} className="rounded-2xl border border-border bg-muted/35 p-4">
                    <p className="font-semibold">{humanize(item.credibility_lean || "mixed")}</p>
                    <p className="mt-2 text-muted-foreground">{item.weighting_rationale || "No additional weighting rationale was produced."}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p>No weighted-side explanation is needed because the evidence does not currently show material disagreement.</p>
            )}
          </div>
        </details>
      </CardContent>
    </Card>
  );
}

function PositionColumn({
  title,
  claims,
  sourceIndex,
}: {
  title: string;
  claims: Claim[];
  sourceIndex: Map<string, number>;
}) {
  return (
    <div className="space-y-3 rounded-2xl border border-border bg-muted/35 p-4">
      <p className="font-semibold">{title}</p>
      {claims.length ? (
        claims.map((claim) => (
          <div key={claim.id} className="rounded-2xl border border-border bg-white/80 p-4">
            <p className="font-semibold">{truncate(claim.statement, 150)}</p>
            <p className="mt-2 text-sm text-muted-foreground">{claim.evidence_summary}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Badge variant="secondary">Confidence {claim.confidence_pct}%</Badge>
              <Badge variant="secondary">Trust {claim.trust_score}%</Badge>
              <Badge variant={claim.contested ? "warning" : "success"}>Consensus {claim.consensus_pct}%</Badge>
              <Badge variant="muted">{formatCitations(claim.supporting_source_ids, sourceIndex)}</Badge>
            </div>
          </div>
        ))
      ) : (
        <p className="text-sm text-muted-foreground">No evidence was classified under this position.</p>
      )}
    </div>
  );
}

function buildRows(session: ResearchSession, sourceIndex: Map<string, number>): ComparisonRow[] {
  if (session.contradictions.length) {
    return session.contradictions.slice(0, 8).map((item) => {
      const leftClaim = session.claims.find((claim) => claim.id === item.claim_a_id);
      const rightClaim = session.claims.find((claim) => claim.id === item.claim_b_id);
      const consensus = Math.min(leftClaim?.consensus_pct ?? 100, rightClaim?.consensus_pct ?? 100);
      return {
        id: item.id,
        topic: truncate(leftClaim?.statement || item.claim_a, 110),
        left: truncate(item.claim_a, 120),
        right: truncate(item.claim_b, 120),
        consensus,
        favored: item.credibility_lean || "mixed",
        citations: [item.source_a_id, item.source_b_id]
          .map((sourceId) => sourceIndex.get(sourceId))
          .filter((value): value is number => typeof value === "number")
          .map((value) => `[${value}]`)
          .join(" "),
      };
    });
  }

  return session.claims
    .filter((claim) => claim.debate_position === "position_a" || claim.debate_position === "position_b")
    .slice(0, 8)
    .map((claim) => ({
      id: claim.id,
      topic: truncate(claim.statement, 110),
      left: claim.debate_position === "position_a" ? truncate(claim.evidence_summary, 120) : "See opposing evidence",
      right: claim.debate_position === "position_b" ? truncate(claim.evidence_summary, 120) : "See supporting evidence",
      consensus: claim.consensus_pct,
      favored: claim.debate_position || "mixed",
      citations: formatCitations(claim.supporting_source_ids, sourceIndex),
    }));
}

function formatCitations(sourceIds: string[], sourceIndex: Map<string, number>) {
  const labels = sourceIds
    .map((sourceId) => sourceIndex.get(sourceId))
    .filter((value): value is number => typeof value === "number")
    .slice(0, 4)
    .map((value) => `[${value}]`);
  return labels.join(" ") || "No refs";
}

function humanize(value: string) {
  return value.replace(/_/g, " ").replace(/—|–/g, "-");
}
