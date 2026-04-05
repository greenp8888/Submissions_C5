#!/usr/bin/env bash
# Download public PDF fixtures for manual research tests (see RESEARCH_MANUAL_TEST_CASES.md).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEST="${ROOT}/tests/fixtures/pdfs"
mkdir -p "${DEST}"

echo "Downloading test PDFs into ${DEST} ..."

curl -fsSL -o "${DEST}/NIST_AI_RMF_1.0.pdf" \
  "https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf"
echo "  OK NIST AI RMF 1.0"

curl -fsSL -o "${DEST}/RAG_arxiv_2005.11401.pdf" \
  "https://arxiv.org/pdf/2005.11401.pdf"
echo "  OK RAG (Lewis et al.)"

curl -fsSL -o "${DEST}/BERT_arxiv_1810.04805.pdf" \
  "https://arxiv.org/pdf/1810.04805.pdf"
echo "  OK BERT (Devlin et al.)"

echo "Done. Upload these files in Gradio and use the questions in tests/RESEARCH_MANUAL_TEST_CASES.md"
