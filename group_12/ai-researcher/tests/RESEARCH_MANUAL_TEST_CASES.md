# Manual research test cases (Local Multi-Agent Deep Researcher)

Use these **public PDFs** and **questions** to exercise local retrieval, multi-source behavior, inline citations, and (optionally) a second analyst pass.

## How to obtain the PDFs

**Option A — script (recommended)**  
From the `ai-researcher` directory:

```bash
bash tests/scripts/download_test_pdfs.sh
```

PDFs land in `tests/fixtures/pdfs/` (gitignored).

**Option B — manual download**  
Open each link in a browser and save the file with the suggested filename.

| # | Document | Suggested filename | Direct PDF URL |
|---|----------|-------------------|----------------|
| 1 | **NIST AI Risk Management Framework (AI RMF 1.0)** | `NIST_AI_RMF_1.0.pdf` | https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf |
| 2 | **Retrieval-Augmented Generation for Knowledge-Intensive NLP** (Lewis et al., 2020) | `RAG_arxiv_2005.11401.pdf` | https://arxiv.org/pdf/2005.11401.pdf |
| 3 | **BERT: Pre-training of Deep Bidirectional Transformers** (Devlin et al., 2018) | `BERT_arxiv_1810.04805.pdf` | https://arxiv.org/pdf/1810.04805.pdf |

**License / use:** NIST publications are public; arXiv papers are under the [arXiv non-exclusive license](https://arxiv.org/licenses/nonexclusive-distrib/1.0/). Suitable for local testing only; do not redistribute as if you authored them.

---

## Test case matrix

For each run, note: **single-pass vs 2 analyst passes**, **web search on/off**, and whether the **Report** shows a **narrative first** with **clickable inline links** plus **References** below.

### TC-1 — NIST AI RMF only (`NIST_AI_RMF_1.0.pdf`)

| ID | Research question | What to verify |
|----|-------------------|----------------|
| TC-1a | What are the **four functions** of the AI RMF (Govern, Map, Measure, Manage)? For each function, give **one concrete example** for an enterprise chatbot that uses an LLM. | Local chunks cite NIST framing; appendix still useful. |
| TC-1b | How does the document define **trustworthy AI** (characteristics / attributes)? Which two characteristics are **hardest to operationalize** for generative AI, according to your reading of the text? | Contradictions/caveats may be thin; report should say so if evidence is vague. |
| TC-1c | Summarize **measurement** vs **governance** emphasis in the RMF for **high-impact** AI. Where does the document stress **documentation** or **risk tolerance**? | Good test for long-PDF retrieval and excerpt normalization. |

### TC-2 — RAG paper only (`RAG_arxiv_2005.11401.pdf`)

| ID | Research question | What to verify |
|----|-------------------|----------------|
| TC-2a | Explain **RAG** vs storing facts only in model parameters. What **trade-offs** does the paper highlight (accuracy, latency, updatability)? | Core definitions should come from local PDF. |
| TC-2b | Describe the **retrieve-then-generate** setup: what plays the role of **retriever** and **generator** in the experiments? | Tests multi-page scientific layout. |
| TC-2c | What **datasets or tasks** does the paper use to show knowledge-intensive performance? Name them briefly. | Factual grounding; optional web for “later work” if enabled. |

### TC-3 — BERT paper only (`BERT_arxiv_1810.04805.pdf`)

| ID | Research question | What to verify |
|----|-------------------|----------------|
| TC-3a | What is **masked language modeling** and **next sentence prediction**, and why does BERT use **both**? | Classic PDF stress test (equations, tables). |
| TC-3b | List **several NLP tasks** the paper reports on (e.g. GLUE, SQuAD) and whether fine-tuning required **task-specific** architectural changes beyond a small output layer. | Checks retrieval across distant sections. |
| TC-3c | Compare **BERT** (bidirectional context in pre-training) to a **left-to-right** LM as described in the paper—what limitation of prior models does BERT address? | Narrative synthesis from one doc. |

### TC-4 — Two papers (upload **RAG** + **BERT**)

| ID | Research question | What to verify |
|----|-------------------|----------------|
| TC-4a | How could **dense passage encoders** or **representations** used in RAG relate to **BERT-style** encoders? Ground the answer in **both** PDFs where possible. | Multi-document local merge + dedupe behavior. |
| TC-4b | If we built a **RAG system** whose retriever uses a BERT-family encoder, what does each paper imply about **training objectives** (MLM/NSP vs passage indexing)? | Cross-document reasoning; may need higher **Top-K**. |

### TC-5 — NIST + RAG (upload **NIST** + **RAG**)

| ID | Research question | What to verify |
|----|-------------------|----------------|
| TC-5a | Map the **RAG pipeline** (retrieve → condition → generate) to the NIST AI RMF **functions** (Govern, Map, Measure, Manage). Which function most clearly owns **retrieval quality** vs **output monitoring**? | Mix of policy + methods PDFs. |
| TC-5b | What **risks** does RAG mitigate compared to parametric-only models, and how would you **document** those in an AI RMF-style risk profile? | Tests synthesis + `_(uploaded: …)_` style local cites alongside any web/arXiv hits. |

### TC-6 — Full stack (all **three** PDFs + **web search ON**)

| ID | Research question | What to verify |
|----|-------------------|----------------|
| TC-6a | Give a **short literature bridge**: from **BERT-style pre-training** to **dense retrieval in RAG** to **NIST-style governance** of deployed LLM systems. Use the three uploads for the technical core and the web for **one** current example (product, regulation, or benchmark). | Inline **clickable** source chips + numbered references. |
| TC-6b | Same as TC-6a but set **Max analyst passes = 2** and confirm **gap / follow-up** appears in **Trace & gaps** when the model requests another retrieval wave. | Phase 2 path. |

---

## Pass/fail checklist (quick)

- [ ] Report opens with **substantive narrative**, not a wall of “channel summaries.”
- [ ] **Inline markdown links** appear after factual claims where URLs exist; locals use **uploaded-doc** phrasing without fake URLs.
- [ ] **References** section lists sources; **Appendix** per-channel notes sit **below** the narrative.
- [ ] **Sources** tab shows excerpts without **one-word-per-line** PDF garbage (whitespace normalization).
- [ ] With **web on**, Tavily results contribute; with **web off**, report still completes from PDFs + Wikipedia/arXiv as configured.

---

## Suggested defaults for manual runs

- **Top-K local:** 6–8 when using 2–3 large PDFs.  
- **Web results per query:** 3–5 when testing TC-6.  
- **Max analyst passes:** 1 for baseline; 2 for TC-6b.

---

*URLs verified from public sources (NIST, arXiv). Re-run downloads if a link moves; update this file if needed.*
