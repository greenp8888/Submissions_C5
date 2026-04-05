import { ReportVisualBlock } from "@/components/report-visual";
import type { ReportBlock, ResearchSession } from "@/lib/types";

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
            <p className="subtle-label">{humanize(section.section_type)}</p>
            <h3 className="mt-2 text-2xl">{section.title}</h3>
            {section.lead_summary ? <p className="mt-4 text-base leading-7 text-slate-700">{section.lead_summary}</p> : null}
            <div className="mt-4 space-y-4">
              {section.blocks.map((block, index) => (
                <ReportBlockCard key={`${section.section_type}-${index}`} block={block} />
              ))}
              {section.visual ? <ReportVisualBlock visual={section.visual} /> : null}
              {section.footer_notes.length ? (
                <div className="rounded-2xl border border-border bg-muted/35 p-4">
                  <p className="font-semibold">Notes</p>
                  <div className="mt-3 space-y-2">
                    {section.footer_notes.map((note, index) => (
                      <p key={`${section.section_type}-note-${index}`} className="text-sm text-muted-foreground">
                        {note}
                      </p>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

function ReportBlockCard({ block }: { block: ReportBlock }) {
  return (
    <div className="rounded-2xl border border-border bg-muted/30 p-4">
      {block.title ? <p className="text-sm font-semibold uppercase tracking-[0.12em] text-muted-foreground">{humanize(block.title)}</p> : null}
      {block.summary ? <p className="mt-2 text-base leading-7 text-slate-800">{block.summary}</p> : null}
      {block.narrative ? <p className="mt-3 text-sm leading-6 text-slate-600">{block.narrative}</p> : null}
      {block.visual ? <div className="mt-4"><ReportVisualBlock visual={block.visual} /></div> : null}
      {block.citations.length ? (
        <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-500">
          {block.citations.map((citation) =>
            citation.url ? (
              <a key={`${citation.source_id}-${citation.label}`} href={citation.url} target="_blank" rel="noreferrer" className="rounded-full bg-white px-2.5 py-1 hover:text-foreground">
                {citation.label} {citation.title ? `• ${citation.title}` : ""}
              </a>
            ) : (
              <span key={`${citation.source_id}-${citation.label}`} className="rounded-full bg-white px-2.5 py-1">
                {citation.label} {citation.title ? `• ${citation.title}` : ""}
              </span>
            ),
          )}
        </div>
      ) : null}
      {block.metadata.length ? (
        <div className="mt-3 space-y-1 text-xs text-slate-500">
          {block.metadata.map((item, index) => (
            <p key={`${item.label}-${index}`}>
              <span className="font-semibold text-slate-500">{humanize(item.label)}:</span> {item.value}
            </p>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function humanize(value: string) {
  return value.replace(/_/g, " ").replace(/—|–/g, "-");
}
