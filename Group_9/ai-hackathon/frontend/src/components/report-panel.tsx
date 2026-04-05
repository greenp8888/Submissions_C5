import type { ResearchSession } from "@/lib/types";

export function ReportPanel({ session }: { session: ResearchSession }) {
  return (
    <div className="grid gap-4 xl:grid-cols-[220px_minmax(0,1fr)]">
      <div className="rounded-2xl border border-border bg-muted/45 p-4">
        <p className="subtle-label">Sections</p>
        <div className="mt-3 space-y-2">
          {session.report_sections.map((section) => (
            <a key={section.section_type} href={`#${section.section_type}`} className="block rounded-xl px-3 py-2 text-sm font-semibold text-foreground hover:bg-white/80">
              {section.title}
            </a>
          ))}
        </div>
      </div>
      <div className="max-h-[820px] space-y-5 overflow-auto pr-1">
        {session.report_sections.map((section) => (
          <section key={section.section_type} id={section.section_type} className="rounded-2xl border border-border bg-white/80 p-5">
            <p className="subtle-label">{section.section_type.replace(/_/g, " ")}</p>
            <h3 className="mt-2 text-2xl">{section.title}</h3>
            <div className="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate-700">{section.content}</div>
          </section>
        ))}
      </div>
    </div>
  );
}
