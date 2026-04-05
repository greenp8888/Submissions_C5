/**
 * Same-origin path for report/tagline — proxied by Next.js to FastAPI.
 * Avoids browser CORS (e.g. app opened as http://127.0.0.1:3000 vs localhost:3000).
 */
export const REPORT_API_BASE = "/api/backend";
