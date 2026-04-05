import { useParams } from "react-router-dom";

import { ResearchDashboard } from "@/components/research-dashboard";

export function ResearchOutputPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  return <ResearchDashboard viewMode="output" sessionId={sessionId} />;
}
