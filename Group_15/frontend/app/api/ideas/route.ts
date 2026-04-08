import { NextRequest, NextResponse } from "next/server";
import { DEFAULT_SAMPLE_IDEAS } from "@/lib/sampleIdeas";
import { fetchFromBackend } from "@/lib/backendProxyFetch";

export const dynamic = "force-dynamic";
export const revalidate = 0;

const NO_STORE = {
  "Cache-Control": "private, no-store, max-age=0",
};

const FALLBACK_PROMPT = (seed: string) =>
  `Generate exactly 4 creative, profitable, and timely product ideas worth building in 2026.

Rules:
- Each idea must be a single sentence (15–25 words) that describes the product clearly, written as an analysis prompt for an AI product intelligence tool.
- Each idea must feel fresh and different — vary domains across B2B SaaS, mobile, marketplace, developer tools, consumer apps, etc.
- Variation nonce (make this response unlike any prior one): ${seed}
- Include a 1–2 word ALL-CAPS category tag (e.g. "SAAS", "MOBILE", "B2B", "MARKETPLACE", "AI TOOL", "PLATFORM", "API").

Return ONLY a valid JSON array — no markdown, no explanation:
[
  { "prompt": "...", "tag": "..." },
  { "prompt": "...", "tag": "..." },
  { "prompt": "...", "tag": "..." },
  { "prompt": "...", "tag": "..." }
]`;

async function ideasFromOpenRouter(seed: string): Promise<{ prompt: string; tag: string }[] | null> {
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) return null;

  try {
    const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "openai/gpt-4.1",
        max_tokens: 512,
        temperature: 1.12,
        messages: [{ role: "user", content: FALLBACK_PROMPT(seed) }],
      }),
    });

    if (!res.ok) return null;

    const data = await res.json();
    const raw: string = data.choices[0].message.content ?? "";
    const cleaned = raw.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/, "").trim();
    const ideas: { prompt: string; tag: string }[] = JSON.parse(cleaned);

    if (!Array.isArray(ideas) || ideas.length === 0) return null;
    return ideas.slice(0, 4);
  } catch {
    return null;
  }
}

export async function GET(request: NextRequest) {
  const seed =
    request.nextUrl.searchParams.get("t") ||
    `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;

  try {
    const { response } = await fetchFromBackend(
      `/sample-ideas?seed=${encodeURIComponent(seed)}`,
      { method: "GET", cache: "no-store" }
    );
    if (response.ok) {
      const data = (await response.json()) as { ideas?: { prompt: string; tag: string }[] };
      if (Array.isArray(data.ideas) && data.ideas.length > 0) {
        return NextResponse.json({ ideas: data.ideas }, { headers: NO_STORE });
      }
    }
  } catch {
    /* try OpenRouter or static */
  }

  const fromRouter = await ideasFromOpenRouter(seed);
  if (fromRouter?.length) {
    return NextResponse.json({ ideas: fromRouter }, { headers: NO_STORE });
  }

  return NextResponse.json({ ideas: DEFAULT_SAMPLE_IDEAS }, { headers: NO_STORE });
}
