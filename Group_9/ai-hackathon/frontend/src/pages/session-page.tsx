import { useParams } from "react-router-dom";

import { ResearchDashboard } from "@/components/research-dashboard";

export function SessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  return <ResearchDashboard sessionId={sessionId} />;
}
