import { useState } from "react";
import { ChevronDown, Key, Brain, Target, Eye, EyeOff } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useFinancialStore, MODELS } from "../../store/financialStore.js";

function InputField({ label, icon: Icon, type = "text", placeholder, value, onChange, hint }) {
  const [show, setShow] = useState(false);
  const isPassword = type === "password";

  return (
    <div className="flex flex-col gap-1.5">
      <label className="flex items-center gap-2 text-slate-400 text-xs font-medium uppercase tracking-wider">
        <Icon size={12} />
        {label}
      </label>
      <div className="relative">
        <input
          type={isPassword && !show ? "password" : "text"}
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-accent-purple/60 focus:bg-white/[0.05] transition-all font-mono"
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setShow(!show)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
          >
            {show ? <EyeOff size={14} /> : <Eye size={14} />}
          </button>
        )}
      </div>
      {hint && <p className="text-slate-600 text-xs">{hint}</p>}
    </div>
  );
}

export default function ConfigPanel() {
  const { config, setConfig } = useFinancialStore();
  const [open, setOpen] = useState(true);

  return (
    <div className="glass rounded-2xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-white/[0.02] transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: "rgba(139,92,246,0.2)", border: "1px solid rgba(139,92,246,0.3)" }}
          >
            <Key size={14} className="text-accent-purple" />
          </div>
          <span className="text-white font-semibold text-sm">Configuration</span>
        </div>
        <motion.div animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDown size={16} className="text-slate-400" />
        </motion.div>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5 flex flex-col gap-4 border-t border-white/5">
              <div className="pt-4 flex flex-col gap-4">
                <InputField
                  label="OpenRouter API Key"
                  icon={Key}
                  type="password"
                  placeholder="sk-or-..."
                  value={config.openrouterKey}
                  onChange={(v) => setConfig({ openrouterKey: v })}
                  hint="Get your key at openrouter.ai"
                />
                <InputField
                  label="Tavily API Key (Optional)"
                  icon={Key}
                  type="password"
                  placeholder="tvly-..."
                  value={config.tavilyKey}
                  onChange={(v) => setConfig({ tavilyKey: v })}
                  hint="Enables live bank rate search"
                />

                {/* Model selector */}
                <div className="flex flex-col gap-1.5">
                  <label className="flex items-center gap-2 text-slate-400 text-xs font-medium uppercase tracking-wider">
                    <Brain size={12} />
                    AI Model
                  </label>
                  <div className="relative">
                    <select
                      value={config.model}
                      onChange={(e) => setConfig({ model: e.target.value })}
                      className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-accent-purple/60 appearance-none cursor-pointer transition-all"
                    >
                      {MODELS.map((m) => (
                        <option key={m.value} value={m.value} className="bg-bg-card">
                          {m.label}
                        </option>
                      ))}
                    </select>
                    <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                  </div>
                </div>

                <InputField
                  label="Financial Goals"
                  icon={Target}
                  type="text"
                  placeholder="e.g. Pay off credit card debt, save for a house..."
                  value={config.goals}
                  onChange={(v) => setConfig({ goals: v })}
                />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
