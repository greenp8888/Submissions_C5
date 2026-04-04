import { NextResponse } from "next/server";

const PROMPT = `Generate exactly 4 creative, profitable, and timely product ideas worth building in 2025.

Rules:
- Each idea must be a single sentence (15–25 words) that describes the product clearly, written as an analysis prompt for an AI product intelligence tool.
- Each idea must feel fresh and different — vary domains across B2B SaaS, mobile, marketplace, developer tools, consumer apps, etc.
- Include a 1–2 word ALL-CAPS category tag (e.g. "SAAS", "MOBILE", "B2B", "MARKETPLACE", "AI TOOL", "PLATFORM", "API").

Return ONLY a valid JSON array — no markdown, no explanation:
[
  { "prompt": "...", "tag": "..." },
  { "prompt": "...", "tag": "..." },
  { "prompt": "...", "tag": "..." },
  { "prompt": "...", "tag": "..." }
]`;

export async function GET() {
  const apiKey = process.env.OPENROUTER_API_KEY;

  if (!apiKey) {
    return NextResponse.json({ error: "OPENROUTER_API_KEY is not set" }, { status: 500 });
  }

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
        temperature: 1.0,
        messages: [{ role: "user", content: PROMPT }],
      }),
    });

    if (!res.ok) {
      return NextResponse.json({ error: "Upstream LLM error" }, { status: 502 });
    }

    const data = await res.json();
    const raw: string = data.choices[0].message.content ?? "";

    // Strip possible ```json ... ``` code fences
    const cleaned = raw.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/, "").trim();
    const ideas: { prompt: string; tag: string }[] = JSON.parse(cleaned);

    if (!Array.isArray(ideas) || ideas.length === 0) {
      throw new Error("Unexpected LLM response shape");
    }

    return NextResponse.json({ ideas: ideas.slice(0, 4) });
  } catch {
    return NextResponse.json({ error: "Failed to generate ideas" }, { status: 500 });
  }
}
