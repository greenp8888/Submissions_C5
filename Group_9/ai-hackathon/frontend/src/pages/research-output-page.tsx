import { useParams } from "react-router-dom";

import { ResearchDashboard } from "@/components/research-dashboard";
import { useResearchOutputStore } from "@/store/research-output-store";

export function ResearchOutputPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const currentSessionId = useResearchOutputStore((state) => state.currentSessionId);
  return <ResearchDashboard viewMode="output" sessionId={sessionId ?? currentSessionId ?? undefined} />;
}
