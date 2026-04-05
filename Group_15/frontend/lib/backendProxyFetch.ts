/**
 * Server-side fetch to FastAPI. Tries several base URLs because Node/Next on
 * some hosts fails one of 127.0.0.1 vs localhost even when uvicorn is up.
 */
function trimSlash(s: string): string {
  return s.replace(/\/$/, "");
}

export function getServerBackendOrigins(): string[] {
  const fromEnv = [process.env.BACKEND_URL, process.env.NEXT_PUBLIC_API_URL].filter(
    (v): v is string => Boolean(v?.trim())
  );
  const fallbacks = ["http://localhost:8000", "http://127.0.0.1:8000"];
  const seen = new Set<string>();
  const out: string[] = [];
  for (const raw of [...fromEnv, ...fallbacks]) {
    const o = trimSlash(raw.trim());
    if (!seen.has(o)) {
      seen.add(o);
      out.push(o);
    }
  }
  return out;
}

/**
 * GET/POST to FastAPI path (e.g. "/analyze"). Throws the last error if every origin fails.
 */
export async function fetchFromBackend(
  path: string,
  init: RequestInit
): Promise<{ response: Response; origin: string }> {
  const origins = getServerBackendOrigins();
  const suffix = path.startsWith("/") ? path : `/${path}`;
  let lastErr: unknown;
  for (const origin of origins) {
    const url = `${origin}${suffix}`;
    try {
      const response = await fetch(url, init);
      return { response, origin };
    } catch (e) {
      lastErr = e;
    }
  }
  throw lastErr;
}

export function formatBackendUnreachableDetail(origins: string[], cause: unknown): string {
  const msg = cause instanceof Error ? cause.message : String(cause);
  const tried = origins.join(", ");
  return (
    `Cannot reach FastAPI (tried: ${tried}). ${msg}. ` +
    `Confirm uvicorn: cd backend && uvicorn main:app --reload --port 8000. ` +
    `If Next runs in Docker, set BACKEND_URL=http://host.docker.internal:8000 in frontend/.env.local`
  );
}
