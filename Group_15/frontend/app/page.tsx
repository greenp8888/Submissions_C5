"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  const [ideaDescription, setIdeaDescription] = useState("");
  const [audience, setAudience] = useState("");
  const [productUrl, setProductUrl] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!ideaDescription.trim()) {
      return;
    }

    setLoading(true);

    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          idea_description: ideaDescription,
          audience,
          product_url: productUrl,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to start analysis");
      }

      const data = await response.json();
      router.push(`/report/${data.id}?idea=${encodeURIComponent(ideaDescription)}&audience=${encodeURIComponent(audience)}&url=${encodeURIComponent(productUrl)}`);
    } catch (error) {
      console.error("Error:", error);
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-2xl">
        <h1 className="font-serif text-6xl mb-4 leading-tight">
          What are you building?
        </h1>
        <p className="font-mono text-sm text-muted mb-12 uppercase tracking-wide">
          Competitive intelligence from 6 sources in ~30 seconds
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <textarea
              value={ideaDescription}
              onChange={(e) => setIdeaDescription(e.target.value)}
              placeholder="e.g. A browser extension that summarizes long email threads for busy executives"
              className="w-full h-32 px-4 py-3 border border-border bg-paper text-ink font-serif text-lg resize-none focus:outline-none focus:border-ink transition-colors"
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              type="text"
              value={audience}
              onChange={(e) => setAudience(e.target.value)}
              placeholder="Target audience (optional)"
              className="px-4 py-3 border border-border bg-paper text-ink font-mono text-sm focus:outline-none focus:border-ink transition-colors"
            />
            <input
              type="url"
              value={productUrl}
              onChange={(e) => setProductUrl(e.target.value)}
              placeholder="Product URL (optional)"
              className="px-4 py-3 border border-border bg-paper text-ink font-mono text-sm focus:outline-none focus:border-ink transition-colors"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !ideaDescription.trim()}
            className="w-full md:w-auto px-12 py-4 bg-ink text-paper font-mono text-sm uppercase tracking-wide hover:opacity-80 disabled:opacity-40 transition-opacity"
          >
            {loading ? "Analyzing..." : "Analyze idea →"}
          </button>
        </form>
      </div>
    </main>
  );
}
