import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Navigate, createBrowserRouter, RouterProvider } from "react-router-dom";
import "reactflow/dist/style.css";

import "@/index.css";
import { AppShell } from "@/components/app-shell";
import { DocsPage } from "@/pages/docs-page";
import { KnowledgePage } from "@/pages/knowledge-page";
import { ResearchOutputPage } from "@/pages/research-output-page";
import { ResearchSetupPage } from "@/pages/research-setup-page";
import { SessionPage } from "@/pages/session-page";
import { SettingsPage } from "@/pages/settings-page";

const queryClient = new QueryClient();

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/research/setup" replace /> },
      { path: "research/setup", element: <ResearchSetupPage /> },
      { path: "research/output", element: <ResearchOutputPage /> },
      { path: "research/output/:sessionId", element: <ResearchOutputPage /> },
      { path: "sessions/:sessionId", element: <SessionPage /> },
      { path: "knowledge", element: <KnowledgePage /> },
      { path: "docs", element: <DocsPage /> },
      { path: "settings", element: <SettingsPage /> },
    ],
  },
]);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </React.StrictMode>,
);
