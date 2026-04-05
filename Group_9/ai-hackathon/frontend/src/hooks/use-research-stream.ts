import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

export type StreamState = "idle" | "connecting" | "live" | "disconnected";

export function useResearchStream(sessionId?: string, enabled = true) {
  const queryClient = useQueryClient();
  const [streamState, setStreamState] = useState<StreamState>("idle");
  const [lastEventType, setLastEventType] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId || !enabled) {
      setStreamState("idle");
      return;
    }

    let closed = false;
    let eventSource: EventSource | null = null;
    let reconnectTimer: number | null = null;

    const connect = () => {
      if (closed) {
        return;
      }
      setStreamState("connecting");
      eventSource = new EventSource(`/api/research/${sessionId}/stream`);

      eventSource.onopen = () => {
        setStreamState("live");
      };

      eventSource.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as { event_type?: string };
          setLastEventType(payload.event_type ?? null);
          queryClient.invalidateQueries({ queryKey: ["session", sessionId] });
          if (payload.event_type === "complete" || payload.event_type === "error") {
            eventSource?.close();
            setStreamState("disconnected");
          }
        } catch {
          queryClient.invalidateQueries({ queryKey: ["session", sessionId] });
        }
      };

      eventSource.onerror = () => {
        eventSource?.close();
        if (!closed) {
          setStreamState("disconnected");
          queryClient.invalidateQueries({ queryKey: ["session", sessionId] });
          reconnectTimer = window.setTimeout(connect, 3000);
        }
      };
    };

    connect();

    return () => {
      closed = true;
      if (reconnectTimer) {
        window.clearTimeout(reconnectTimer);
      }
      eventSource?.close();
    };
  }, [enabled, queryClient, sessionId]);

  return { streamState, lastEventType };
}
