require("dotenv").config();
const express = require("express");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(express.json());

const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY || "";
const PORT = process.env.PORT || 3001;
// Cost efficient openrouter model:
const MODEL = "google/gemini-2.5-flash";

app.post("/api/agents", async (req, res) => {
  try {
    const { system, messages, max_tokens, temperature } = req.body;

    const payload = {
      model: MODEL,
      messages: [
        { role: "system", content: system },
        ...messages
      ],
      max_tokens: max_tokens || 1000,
      temperature: temperature || 0
    };

    const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${OPENROUTER_API_KEY}`,
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "Financial Coach MVP"
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errTxt = await response.text();
      console.error("OpenRouter Error:", errTxt);
      return res.status(response.status).json({ error: "API call failed", details: errTxt });
    }

    const data = await response.json();
    const reply = data.choices[0].message.content;
    
    res.json({ content: reply });
  } catch (error) {
    console.error("Agent Endpoint Error:", error);
    res.status(500).json({ error: "Internal Server Error" });
  }
});

app.listen(PORT, () => {
  console.log(`Backend proxy running on http://localhost:${PORT}`);
});
