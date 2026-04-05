import { CheckCircle2, LoaderCircle, Network, Sparkles, TriangleAlert } from "lucide-react";

import type { Claim } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { InfoTooltip } from "@/components/info-tooltip";

export function ConfidencePanel({ claims }: { claims: Claim[] }) {
  const avgTrust = claims.length ? Math.round(claims.reduce((sum, claim) => sum + claim.trust_score, 0) / claims.length) : 0;
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <CardTitle>Confidence and credibility</CardTitle>
          <InfoTooltip label="About confidence and trust score" content={PANEL_HELP} />
        </div>
        <CardDescription>Review weighted trust, evidence support, and contested claims in one place.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-4 md:grid-cols-4">
          <MetricCard label="High confidence" value={String(claims.filter((claim) => claim.confidence === "high").length)} icon={CheckCircle2} accent="success" />
          <MetricCard label="Medium confidence" value={String(claims.filter((claim) => claim.confidence === "medium").length)} icon={Sparkles} />
          <MetricCard label="Low confidence" value={String(claims.filter((claim) => claim.confidence === "low").length)} icon={TriangleAlert} />
          <MetricCard label="Avg trust" value={`${avgTrust}%`} icon={Network} />
        </div>
        <div className="overflow-auto rounded-2xl border border-border bg-white/75">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-muted/65 text-xs uppercase tracking-[0.14em] text-muted-foreground">
              <tr>
                <th className="px-4 py-3">Claim</th>
                <th className="px-4 py-3">
                  <div className="inline-flex items-center gap-2">
                    <span>Confidence</span>
                    <InfoTooltip label="What confidence means" content={CONFIDENCE_HELP} />
                  </div>
                </th>
                <th className="px-4 py-3">
                  <div className="inline-flex items-center gap-2">
                    <span>Trust</span>
                    <InfoTooltip label="What trust score means" content={TRUST_HELP} />
                  </div>
                </th>
                <th className="px-4 py-3">Credibility summary</th>
                <th className="px-4 py-3">Evidence summary</th>
              </tr>
            </thead>
            <tbody>
              {claims.map((claim) => (
                <tr key={claim.id} className="border-t border-border/80 align-top">
                  <td className="px-4 py-4 font-semibold">{claim.statement}</td>
                  <td className="px-4 py-4">
                    <Badge variant={claim.confidence === "high" ? "success" : claim.confidence === "medium" ? "secondary" : "warning"}>
                      {claim.confidence} ({claim.confidence_pct}%)
                    </Badge>
                  </td>
                  <td className="px-4 py-4">
                    <div className="space-y-1">
                      <p>{claim.trust_score}%</p>
                      <p className="text-xs text-muted-foreground">Consensus {claim.consensus_pct}%</p>
                    </div>
                  </td>
                  <td className="px-4 py-4 text-muted-foreground">{claim.credibility_summary}</td>
                  <td className="px-4 py-4 text-muted-foreground">{claim.evidence_summary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

const PANEL_HELP =
  "Confidence measures how strongly the gathered evidence supports a claim. It reflects support versus contradiction, agreement across sources, and evidence sufficiency. Trust score measures how trustworthy the evidence base is. It weighs source type, provider quality, metadata completeness, date-window fit, and corroboration. A claim can have high confidence from consistent evidence but only moderate trust if the sources are weak. It can also have strong-trust sources but lower confidence if those sources disagree.";

const CONFIDENCE_HELP =
  "Confidence is claim-level certainty. It increases when multiple sources support the same point, contradictions are limited, and the evidence base is sufficiently dense. It answers: how sure are we about this claim based on the retrieved evidence?";

const TRUST_HELP =
  "Trust score is evidence-quality weighting. It increases when the supporting sources are credible, provider quality is strong, metadata is complete, the source fits the selected date window, and other evidence corroborates it. Current methodology weights source type at 35%, provider trust at 20%, metadata completeness at 15%, date-window fit at 15%, and cross-source agreement at 15%. It answers: how much should we trust the evidence base behind this claim?";

function MetricCard({
  label,
  value,
  icon: Icon,
  accent = "default",
}: {
  label: string;
  value: string;
  icon: typeof LoaderCircle;
  accent?: "default" | "success";
}) {
  return (
    <Card className={cn(accent === "success" && "border-emerald-200 bg-emerald-50/80")}>
      <CardContent className="flex items-center justify-between p-5">
        <div>
          <p className="subtle-label">{label}</p>
          <p className="mt-2 font-heading text-2xl capitalize">{value}</p>
        </div>
        <div className="rounded-2xl bg-white/75 p-3 text-primary">
          <Icon className="h-5 w-5" />
        </div>
      </CardContent>
    </Card>
  );
}
