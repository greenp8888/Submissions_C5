import { CheckCircle2, LoaderCircle, Network, Sparkles, TriangleAlert } from "lucide-react";

import type { Claim } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function ConfidencePanel({ claims }: { claims: Claim[] }) {
  const avgTrust = claims.length ? Math.round(claims.reduce((sum, claim) => sum + claim.trust_score, 0) / claims.length) : 0;
  return (
    <Card>
      <CardHeader>
        <CardTitle>Confidence and credibility</CardTitle>
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
                <th className="px-4 py-3">Confidence</th>
                <th className="px-4 py-3">Trust</th>
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
                  <td className="px-4 py-4">{claim.trust_score}%</td>
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
