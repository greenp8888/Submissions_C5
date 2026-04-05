import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileSpreadsheet, X, CheckCircle2 } from "lucide-react";
import { useFinancialStore } from "../../store/financialStore.js";

export default function FileDropzone() {
  const { file, setFile } = useFinancialStore();

  const onDrop = useCallback((accepted) => {
    if (accepted[0]) setFile(accepted[0]);
  }, [setFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
  });

  return (
    <div className="w-full">
      <AnimatePresence mode="wait">
        {!file ? (
          <motion.div
            key="dropzone"
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.97 }}
            {...getRootProps()}
            className={`relative rounded-2xl p-8 text-center cursor-pointer transition-all duration-300 ${
              isDragActive
                ? "border-2 border-accent-purple bg-accent-purple/10"
                : "border-2 border-dashed border-white/10 hover:border-accent-purple/50 hover:bg-white/[0.02]"
            }`}
            style={{
              boxShadow: isDragActive
                ? "0 0 40px rgba(139,92,246,0.2) inset"
                : undefined,
            }}
          >
            <input {...getInputProps()} />

            {/* Animated upload icon */}
            <div className="flex flex-col items-center gap-4">
              <motion.div
                animate={isDragActive ? { scale: [1, 1.15, 1], y: [-4, -12, -4] } : { y: [0, -6, 0] }}
                transition={isDragActive ? { repeat: Infinity, duration: 0.6 } : { repeat: Infinity, duration: 2.5, ease: "easeInOut" }}
                className="relative"
              >
                <div className="w-20 h-20 rounded-2xl flex items-center justify-center"
                  style={{
                    background: "linear-gradient(135deg, rgba(139,92,246,0.2), rgba(59,130,246,0.1))",
                    border: "1px solid rgba(139,92,246,0.3)",
                    boxShadow: "0 0 30px rgba(139,92,246,0.2)",
                  }}
                >
                  <Upload size={32} className="text-accent-purple" />
                </div>
                {/* Ripple rings */}
                {isDragActive && (
                  <>
                    <div className="absolute inset-0 rounded-2xl border border-accent-purple/40 animate-ping" />
                    <div className="absolute -inset-3 rounded-3xl border border-accent-purple/20 animate-ping" style={{ animationDelay: "0.2s" }} />
                  </>
                )}
              </motion.div>

              <div>
                <p className="text-lg font-semibold text-white mb-1">
                  {isDragActive ? "Drop your file here" : "Upload Transaction File"}
                </p>
                <p className="text-slate-400 text-sm">
                  Drag & drop or{" "}
                  <span className="text-accent-purple font-medium">click to browse</span>
                </p>
                <p className="text-slate-500 text-xs mt-2">
                  Supports CSV, XLSX · Max 10MB
                </p>
              </div>

              {/* Format hint */}
              <div className="glass rounded-xl p-3 text-left w-full max-w-sm">
                <p className="text-slate-400 text-xs mb-2 font-medium">Expected columns:</p>
                <div className="flex flex-wrap gap-1.5">
                  {["Date", "Amount", "Category", "Type", "Description"].map((col) => (
                    <span key={col} className="font-mono text-xs px-2 py-0.5 rounded bg-white/5 text-slate-300 border border-white/10">
                      {col}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="file-preview"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass rounded-2xl p-5 flex items-center gap-4"
            style={{ border: "1px solid rgba(16,185,129,0.3)" }}
          >
            <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{ background: "rgba(16,185,129,0.15)", border: "1px solid rgba(16,185,129,0.3)" }}
            >
              <FileSpreadsheet size={22} className="text-green-400" />
            </div>

            <div className="flex-1 min-w-0">
              <p className="text-white font-semibold text-sm truncate">{file.name}</p>
              <p className="text-slate-400 text-xs mt-0.5">
                {(file.size / 1024).toFixed(1)} KB · Ready to analyze
              </p>
            </div>

            <div className="flex items-center gap-2">
              <CheckCircle2 size={18} className="text-green-400" />
              <button
                onClick={(e) => { e.stopPropagation(); setFile(null); }}
                className="w-7 h-7 rounded-lg flex items-center justify-center text-slate-400 hover:text-white hover:bg-white/10 transition-all"
              >
                <X size={14} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
