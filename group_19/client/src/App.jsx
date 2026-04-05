import { AnimatePresence, motion } from "framer-motion";
import { useEffect } from "react";
import { useFinancialStore } from "./store/financialStore.js";
import { Sidebar, BottomBar } from "./components/layout/Sidebar.jsx";
import TopBar from "./components/layout/TopBar.jsx";
import Footer from "./components/layout/Footer.jsx";
import DotField from "./components/ui/DotField.jsx";
import ChatPage from "./pages/ChatPage.jsx";
import ConfigPage from "./pages/ConfigPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import DocsPage from "./pages/DocsPage.jsx";

const PAGE_TRANSITION = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.28, ease: [0.16, 1, 0.3, 1] } },
  exit:    { opacity: 0, y: -6, transition: { duration: 0.16 } },
};

export default function App() {
  const { page, resetKey, fetchServerDefaults } = useFinancialStore();

  // Pre-populate Brevo fields from server env vars (only fills empty fields)
  useEffect(() => { fetchServerDefaults(); }, []);

  return (
    <div className="min-h-screen flex flex-col">
      {/* Ambient orbs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden" style={{ zIndex: 0 }}>
        <div style={{
          position: "absolute", top: "-15%", right: "-8%",
          width: 480, height: 480, borderRadius: "50%",
          background: "radial-gradient(circle, rgba(139,92,246,0.08) 0%, transparent 70%)",
          filter: "blur(50px)",
        }} />
        <div style={{
          position: "absolute", bottom: "0%", left: "-6%",
          width: 360, height: 360, borderRadius: "50%",
          background: "radial-gradient(circle, rgba(59,130,246,0.06) 0%, transparent 70%)",
          filter: "blur(50px)",
        }} />
      </div>

      {/* Beacon dot field */}
      <DotField count={16} />

      {/* ── Top bar (full width, sticky) ─────────────────────────────── */}
      <TopBar />

      {/* ── Body: sidebar + main ─────────────────────────────────────── */}
      <div className="flex flex-1 min-h-0 relative" style={{ zIndex: 1 }}>
        <Sidebar />

        <main className="flex-1 flex flex-col min-h-0 min-w-0 overflow-hidden">
          <AnimatePresence mode="wait">
            {page === "chat" && (
              <motion.div key={`chat-${resetKey}`} {...PAGE_TRANSITION} className="flex-1 flex flex-col min-h-0 overflow-hidden">
                <ChatPage />
              </motion.div>
            )}
            {page === "config" && (
              <motion.div key="config" {...PAGE_TRANSITION} className="flex-1 overflow-y-auto">
                <ConfigPage />
              </motion.div>
            )}
            {page === "dashboard" && (
              <motion.div key="dashboard" {...PAGE_TRANSITION} className="flex-1 overflow-y-auto">
                <DashboardPage />
              </motion.div>
            )}
            {page === "docs" && (
              <motion.div key="docs" {...PAGE_TRANSITION} className="flex-1 overflow-y-auto">
                <DocsPage />
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      {page !== "dashboard" && page !== "docs" && <Footer />}

      {/* ── Mobile bottom tab bar ─────────────────────────────────────── */}
      <BottomBar />
    </div>
  );
}
