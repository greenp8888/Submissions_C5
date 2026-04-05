import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import "reactflow/dist/style.css";

import "@/index.css";
import { AppShell } from "@/components/app-shell";
import { HomePage } from "@/pages/home-page";
import { KnowledgePage } from "@/pages/knowledge-page";
import { SessionPage } from "@/pages/session-page";
import { SettingsPage } from "@/pages/settings-page";

const queryClient = new QueryClient();

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "sessions/:sessionId", element: <SessionPage /> },
      { path: "knowledge", element: <KnowledgePage /> },
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
