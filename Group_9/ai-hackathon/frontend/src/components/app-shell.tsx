import { useEffect } from "react";
import { BrainCircuit, Database, FileCode2, PanelLeftOpen, Settings2 } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { updateProviderSettings } from "@/lib/api";
import { loadCachedProviderSettings } from "@/lib/browser-provider-settings";
import { useResearchOutputStore } from "@/store/research-output-store";
import { cn } from "@/lib/utils";

export function AppShell() {
  const currentSessionId = useResearchOutputStore((state) => state.currentSessionId);

  useEffect(() => {
    const cached = loadCachedProviderSettings();
    if (!cached.openrouter_api_key && !cached.tavily_api_key) {
      return;
    }
    updateProviderSettings({
      openrouter_api_key: cached.openrouter_api_key,
      tavily_api_key: cached.tavily_api_key,
      persist: false,
    }).catch(() => {
      // Ignore silent boot-time sync errors; the Settings page can recover them explicitly.
    });
  }, []);

  const navigation = [
    { to: "/research/setup", label: "Research Setup", icon: BrainCircuit },
    { to: currentSessionId ? `/research/output/${currentSessionId}` : "/research/output", label: "Research Output", icon: BrainCircuit },
    { to: "/knowledge", label: "Research Documents", icon: Database },
    { to: "/docs", label: "Docs", icon: FileCode2 },
    { to: "/settings", label: "Settings", icon: Settings2 },
  ];

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(45,212,191,0.18),transparent_26%),radial-gradient(circle_at_top_right,rgba(251,191,36,0.16),transparent_26%),linear-gradient(180deg,#f8fbff_0%,#edf5fb_100%)] px-4 py-6 md:px-6 lg:px-10">
      <div className="mx-auto flex max-w-[1600px] flex-col gap-6">
        <header className="panel-surface flex flex-col gap-5 overflow-hidden p-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-panel">
                <PanelLeftOpen className="h-6 w-6" />
              </div>
              <div>
                <p className="subtle-label">AI Research Console</p>
                <h1 className="text-3xl">Multi-Agent Deep Research Dashboard</h1>
              </div>
            </div>
            <p className="max-w-3xl text-sm text-muted-foreground md:text-base">
              Run local-first investigations, stream agent activity in real time, inspect evidence credibility, and export structured research reports from a production-style workspace.
            </p>
          </div>
          <div className="flex flex-col gap-3 md:items-end">
            <Badge variant="secondary" className="w-fit">
              React dashboard powered by FastAPI research APIs
            </Badge>
            <nav className="flex flex-wrap gap-2">
              {navigation.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    cn(
                      "inline-flex items-center gap-2 rounded-xl border border-border px-4 py-2 text-sm font-semibold transition",
                      isActive ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20" : "bg-white/80 text-foreground hover:bg-white",
                    )
                  }
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </NavLink>
              ))}
            </nav>
          </div>
        </header>

        <Outlet />
      </div>
    </div>
  );
}
