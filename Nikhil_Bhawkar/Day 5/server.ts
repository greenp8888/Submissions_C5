import express from "express";
import { createServer as createViteServer } from "vite";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // API routes FIRST
  app.post("/api/generate-post", async (req, res) => {
    const webhookUrl = "https://nikhil-bhawkar.app.n8n.cloud/webhook-test/85e078f1-c211-453e-b592-df10148e1519";
    
    try {
      console.log("Proxying request to n8n generate webhook:", req.body);
      const response = await fetch(webhookUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(req.body),
      });

      const data = await response.text();
      console.log("n8n generate response status:", response.status);

      if (response.ok) {
        res.json({ success: true, data });
      } else {
        res.status(response.status).json({ 
          success: false, 
          error: `n8n returned status ${response.status}`,
          details: data 
        });
      }
    } catch (error) {
      console.error("Error proxying to n8n generate:", error);
      res.status(500).json({ 
        success: false, 
        error: error instanceof Error ? error.message : "Internal Server Error" 
      });
    }
  });

  app.post("/api/publish-post", async (req, res) => {
    const webhookUrl = "https://nikhil-bhawkar.app.n8n.cloud/webhook-test/16412934-67a5-4fef-9b60-4c20e68d8542";
    
    try {
      console.log("Proxying request to n8n publish webhook:", req.body);
      const response = await fetch(webhookUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(req.body),
      });

      const data = await response.text();
      console.log("n8n publish response status:", response.status);

      if (response.ok) {
        res.json({ success: true, data });
      } else {
        res.status(response.status).json({ 
          success: false, 
          error: `n8n returned status ${response.status}`,
          details: data 
        });
      }
    } catch (error) {
      console.error("Error proxying to n8n publish:", error);
      res.status(500).json({ 
        success: false, 
        error: error instanceof Error ? error.message : "Internal Server Error" 
      });
    }
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
