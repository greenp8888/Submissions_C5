// Load .env from project root (one level up from server/)
require("dotenv").config({ path: require("path").resolve(__dirname, "../.env") });
require("dotenv").config(); // also load server/.env if present
const express = require("express");
const cors = require("cors");
const multer = require("multer");
const nodemailer = require("nodemailer");
const https = require("https");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

// ── PDF generation via puppeteer-core + local Chrome ─────────────────────────
const CHROME_PATHS = [
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/usr/bin/google-chrome-stable",
  "/usr/bin/chromium-browser",
  "/usr/bin/chromium",
];

async function generatePdfBuffer(html) {
  const puppeteer    = require("puppeteer-core");
  const executablePath = CHROME_PATHS.find(p => fs.existsSync(p));
  if (!executablePath) throw new Error("Chrome/Chromium not found on this machine");

  const browser = await puppeteer.launch({
    executablePath,
    headless: "new",
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
  });
  try {
    const page = await browser.newPage();
    await page.setContent(html, { waitUntil: "networkidle0", timeout: 30000 });
    return await page.pdf({ format: "A4", printBackground: true });
  } finally {
    await browser.close();
  }
}

// ── Email credentials ─────────────────────────────────────────────────────────
const BREVO_SMTP_KEY   = process.env.BREVO_API_KEY      || "";
const BREVO_FROM_EMAIL = process.env.BREVO_FROM_EMAIL   || "";
// Gmail fallback — set GMAIL_USER + GMAIL_APP_PASSWORD in .env for guaranteed delivery
// Generate at: myaccount.google.com/apppasswords (requires 2FA enabled)
const GMAIL_USER       = process.env.GMAIL_USER         || "sandeepjoseph4@gmail.com";
const GMAIL_APP_PASS   = process.env.GMAIL_APP_PASSWORD || "";

// ── Brevo email — REST API (xkeysib-) or SMTP (xsmtpsib-) ────────────────────
async function sendViaBrevo(to, subject, html, pdfBuffer = null, opts = {}) {
  const key      = opts.brevoApiKey    || BREVO_SMTP_KEY;
  const fromMail = opts.brevoFromEmail || BREVO_FROM_EMAIL;

  if (!key)      throw new Error("No Brevo key configured.");
  if (!fromMail) throw new Error("No Brevo From email configured.");

  // ── Path A: REST API — works with xkeysib- API keys (preferred) ──────────
  const payload = {
    sender:      { name: "FinanceIQ", email: fromMail },
    to:          [{ email: to }],
    subject,
    htmlContent: html,
  };
  if (pdfBuffer) {
    const date = new Date().toISOString().slice(0, 10);
    payload.attachment = [{ name: `FinanceIQ-Report-${date}.pdf`, content: pdfBuffer.toString("base64") }];
  }
  const body = JSON.stringify(payload);
  const apiResult = await new Promise((resolve, reject) => {
    const req = https.request({
      hostname: "api.brevo.com", path: "/v3/smtp/email", method: "POST",
      headers: { "Content-Type": "application/json", "api-key": key, "Content-Length": Buffer.byteLength(body) },
    }, (res) => {
      let data = "";
      res.on("data", c => { data += c; });
      res.on("end", () => {
        if (res.statusCode >= 200 && res.statusCode < 300) resolve({ ok: true });
        else resolve({ ok: false, status: res.statusCode, body: data });
      });
    });
    req.on("error", e => resolve({ ok: false, status: 0, body: e.message }));
    req.write(body); req.end();
  });

  if (apiResult.ok) {
    console.log(`[email] Brevo REST API success → ${to}`);
    return { hasAttachment: !!pdfBuffer };
  }
  console.warn(`[email] REST API failed (${apiResult.status}): ${apiResult.body} — trying SMTP...`);

  // ── Path B: SMTP fallback — xsmtpsib- keys with Brevo account login email ─
  // NOTE: SMTP username must be the Brevo ACCOUNT LOGIN email (the email used
  // to sign in to app.brevo.com) which may differ from the From/sender email.
  const mailOpts = {
    from: `"FinanceIQ" <${fromMail}>`, to, subject, html,
    ...(pdfBuffer ? { attachments: [{ filename: `FinanceIQ-Report-${new Date().toISOString().slice(0,10)}.pdf`, content: pdfBuffer, contentType: "application/pdf" }] } : {}),
  };
  const smtpCfgs = [
    { host: "smtp-relay.brevo.com", port: 587, secure: false },
    { host: "smtp-relay.brevo.com", port: 465, secure: true  },
  ];
  let lastSmtpErr = null;
  for (const cfg of smtpCfgs) {
    try {
      await nodemailer.createTransport({
        ...cfg, auth: { user: fromMail, pass: key },
        tls: { rejectUnauthorized: false }, connectionTimeout: 10000,
      }).sendMail(mailOpts);
      console.log(`[email] SMTP success via ${cfg.host}:${cfg.port}`);
      return { hasAttachment: !!pdfBuffer };
    } catch (e) {
      lastSmtpErr = e;
      console.error(`[email] SMTP ${cfg.host}:${cfg.port}: ${e.message}`);
    }
  }

  // ── Path C: Gmail SMTP — reliable fallback when Brevo fails ─────────────────
  if (GMAIL_APP_PASS) {
    try {
      await nodemailer.createTransport({
        service: "gmail",
        auth: { user: GMAIL_USER, pass: GMAIL_APP_PASS },
      }).sendMail({
        from: `"FinanceIQ" <${GMAIL_USER}>`, to, subject, html,
        ...(pdfBuffer ? { attachments: [{ filename: `FinanceIQ-Report-${new Date().toISOString().slice(0,10)}.pdf`, content: pdfBuffer, contentType: "application/pdf" }] } : {}),
      });
      console.log(`[email] Gmail SMTP success → ${to}`);
      return { hasAttachment: !!pdfBuffer };
    } catch (e) {
      console.error(`[email] Gmail SMTP failed: ${e.message}`);
    }
  }

  // All paths failed
  const hint = apiResult.status === 401
    ? "Brevo xsmtpsib- key requires the Brevo account login email as SMTP username (not the sender email). Fix: get an xkeysib- API key from app.brevo.com → SMTP & API → API Keys. OR set GMAIL_APP_PASSWORD in .env (generate at myaccount.google.com/apppasswords)."
    : (lastSmtpErr?.message || "All email providers failed.");
  throw new Error(hint);
}

// ── SMTP provider rotation (EMAIL_1_* … EMAIL_5_*) ───────────────────────────
let _emailProviderIdx = 0;

function getSmtpProviders() {
  const providers = [];
  for (let i = 1; i <= 5; i++) {
    const host    = process.env[`EMAIL_${i}_HOST`];
    const service = process.env[`EMAIL_${i}_SERVICE`];
    const user    = process.env[`EMAIL_${i}_USER`];
    const pass    = process.env[`EMAIL_${i}_PASS`];
    const port    = parseInt(process.env[`EMAIL_${i}_PORT`] || "587");
    if (user && pass) {
      if (host) providers.push({ host, port, secure: port === 465, auth: { user, pass } });
      else if (service) providers.push({ service, auth: { user, pass } });
    }
  }
  return providers;
}

const app = express();
const PORT = process.env.PORT || 3001;
const ROOT_DIR = path.join(__dirname, "..");

// ── Multer upload config ──────────────────────────────────────────────────────
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const dir = path.join(__dirname, "uploads");
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    cb(null, dir);
  },
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname);
    cb(null, `upload_${Date.now()}${ext}`);
  },
});
const upload = multer({
  storage,
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB
  fileFilter: (req, file, cb) => {
    const allowed = [".csv", ".xlsx", ".xls"];
    const ext = path.extname(file.originalname).toLowerCase();
    cb(null, allowed.includes(ext));
  },
});

// ── Middleware ────────────────────────────────────────────────────────────────
app.use(cors({ origin: "*" }));
app.use(express.json());

// ── Health check ─────────────────────────────────────────────────────────────
app.get("/api/health", (req, res) => res.json({ status: "ok" }));

// ── Config defaults (pre-fill client Config UI from server env vars) ─────────
// Expose non-sensitive defaults so a deployed instance can be pre-configured.
// Set BREVO_API_KEY / BREVO_FROM_EMAIL in your server .env to pre-fill the UI.
app.get("/api/config/defaults", (req, res) => {
  res.json({
    brevoApiKey:    process.env.BREVO_API_KEY    || "",
    brevoFromEmail: process.env.BREVO_FROM_EMAIL  || "",
  });
});

// ── Analysis endpoint (SSE streaming) ────────────────────────────────────────
app.post("/api/analyze", upload.single("file"), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: "No file uploaded" });
  }

  const { openrouterKey, tavilyKey, model, goals } = req.body;
  const filePath = req.file.path;

  const config = JSON.stringify({
    file_path: filePath,
    openrouter_key: openrouterKey || process.env.OPENROUTER_API_KEY || "",
    tavily_key: tavilyKey || process.env.TAVILY_API_KEY || "",
    model: model || "openai/gpt-4o-mini",
    goals: goals || "",
  });

  // ── SSE headers ─────────────────────────────────────────────────────────
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.setHeader("X-Accel-Buffering", "no");
  res.flushHeaders();

  const sendEvent = (data) => {
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  };

  // ── Resolve Python interpreter (prefer venv) ─────────────────────────────
  const venvPy = path.join(ROOT_DIR, ".venv", "bin", "python3");
  const pythonBin = fs.existsSync(venvPy) ? venvPy : "python3";
  const bridgeScript = path.join(ROOT_DIR, "agents", "run_pipeline.py");

  const python = spawn(pythonBin, [bridgeScript, config], {
    cwd: ROOT_DIR,
    env: { ...process.env },
  });

  let buffer = "";

  python.stdout.on("data", (chunk) => {
    buffer += chunk.toString();
    const lines = buffer.split("\n");
    buffer = lines.pop(); // keep incomplete line
    lines.forEach((line) => {
      line = line.trim();
      if (!line) return;
      try {
        const event = JSON.parse(line);
        sendEvent(event);
      } catch {
        // non-JSON stdout — ignore
      }
    });
  });

  python.stderr.on("data", (data) => {
    const msg = data.toString().trim();
    if (msg) console.error("[Python stderr]", msg);
  });

  python.on("close", (code) => {
    // Flush any remaining buffer
    if (buffer.trim()) {
      try {
        sendEvent(JSON.parse(buffer.trim()));
      } catch {}
    }
    // Clean up temp file
    fs.unlink(filePath, () => {});
    sendEvent({ type: "stream_end", code });
    res.end();
  });

  // Handle client disconnect
  req.on("close", () => {
    python.kill("SIGTERM");
    fs.unlink(filePath, () => {});
  });
});

// ── Email report endpoint ─────────────────────────────────────────────────────
app.post("/api/send-report", async (req, res) => {
  const { to, subject, html, pdfHtml, brevoApiKey, brevoFromEmail } = req.body;
  if (!to) return res.status(400).json({ error: "Missing recipient email" });

  const sub  = subject || "Your FinanceIQ Financial Report";
  const date = new Date().toISOString().slice(0, 10);

  // Generate PDF buffer if pdfHtml provided
  let pdfBuffer = null;
  if (pdfHtml) {
    try {
      pdfBuffer = await generatePdfBuffer(pdfHtml);
      console.log(`[email] PDF generated: ${(pdfBuffer.length / 1024).toFixed(0)} KB`);
    } catch (err) {
      console.error("[email] PDF generation failed (sending without attachment):", err.message);
    }
  }

  // Send via Brevo (hardcoded fallback credentials guarantee delivery)
  try {
    const result = await sendViaBrevo(to, sub, html, pdfBuffer, { brevoApiKey, brevoFromEmail });
    return res.json({ success: true, provider: "brevo", hasAttachment: !!pdfBuffer, ...result });
  } catch (err) {
    console.error("[email] Brevo failed:", err.message);
    return res.status(500).json({ error: "Email failed", detail: err.message });
  }

  // 2. Fall back to generic SMTP rotation
  const providers = getSmtpProviders();
  if (!providers.length) {
    return res.status(503).json({
      error: "No email providers configured.",
      hint: "Add BREVO_SMTP_KEY and BREVO_FROM_EMAIL to your .env and restart the server.",
    });
  }

  const errors = [];
  for (let attempt = 0; attempt < providers.length; attempt++) {
    const provider = providers[_emailProviderIdx % providers.length];
    _emailProviderIdx = (_emailProviderIdx + 1) % providers.length;
    try {
      const transporter = nodemailer.createTransport(provider);
      const mailOpts = { from: `"FinanceIQ" <${provider.auth.user}>`, to, subject: sub, html };
      if (pdfBuffer) {
        const date = new Date().toISOString().slice(0, 10);
        mailOpts.attachments = [{ filename: `FinanceIQ-Report-${date}.pdf`, content: pdfBuffer, contentType: "application/pdf" }];
      }
      await transporter.sendMail(mailOpts);
      return res.json({ success: true, provider: "smtp", hasAttachment: !!pdfBuffer });
    } catch (err) {
      errors.push(`${provider.auth.user}: ${err.message}`);
    }
  }
  return res.status(500).json({ error: "All email providers failed", details: errors });
});

// ── Sample files listing ──────────────────────────────────────────────────────
const SAMPLE_DIR = path.join(ROOT_DIR, "data", "sample_data");

app.get("/api/samples", (req, res) => {
  const allowed = [".csv", ".xlsx", ".xls"];
  try {
    const files = fs.readdirSync(SAMPLE_DIR)
      .filter(f => allowed.includes(path.extname(f).toLowerCase()))
      .map(f => {
        const stat = fs.statSync(path.join(SAMPLE_DIR, f));
        return { name: f, size: stat.size };
      });
    res.json(files);
  } catch {
    res.json([]);
  }
});

// ── Sample file serve (by name or fmt) ───────────────────────────────────────
app.get("/api/sample", (req, res) => {
  // ?file=sample_transactions.xlsx  OR  ?fmt=csv (legacy)
  const filename = req.query.file
    ? path.basename(req.query.file)   // strip any path traversal
    : `sample_transactions.${req.query.fmt === "csv" ? "csv" : "xlsx"}`;

  const samplePath = path.join(SAMPLE_DIR, filename);
  if (!fs.existsSync(samplePath)) {
    return res.status(404).json({ error: "Sample file not found" });
  }
  res.download(samplePath, filename);
});

// ── Serve built React client in production ────────────────────────────────────
const clientBuild = path.join(ROOT_DIR, "client", "dist");
if (fs.existsSync(clientBuild)) {
  app.use(express.static(clientBuild));
  app.get("*", (req, res) => {
    res.sendFile(path.join(clientBuild, "index.html"));
  });
}

app.listen(PORT, () => {
  console.log(`\n  🚀  Financial Advisor API → http://localhost:${PORT}\n`);
});
