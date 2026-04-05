import { Info } from "lucide-react";

import { cn } from "@/lib/utils";

export function InfoTooltip({
  label,
  content,
  className,
}: {
  label: string;
  content: string;
  className?: string;
}) {
  return (
    <span className={cn("group relative inline-flex items-center", className)}>
      <button
        type="button"
        aria-label={label}
        className="inline-flex h-5 w-5 items-center justify-center rounded-full border border-border bg-white/80 text-muted-foreground transition hover:text-foreground focus:outline-none"
      >
        <Info className="h-3.5 w-3.5" />
      </button>
      <span className="pointer-events-none absolute left-1/2 top-full z-20 mt-2 hidden w-80 -translate-x-1/2 rounded-2xl border border-border bg-white px-4 py-3 text-left text-xs leading-5 text-slate-700 shadow-2xl group-hover:block group-focus-within:block">
        {content}
      </span>
    </span>
  );
}
