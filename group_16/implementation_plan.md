# Financial Coach UI & Integration Refactor Plan

This plan details the steps to fully build and integrate the Financial Coach application, focusing on completing the missing logic (CSV parsing and AI integrations) and entirely overhauling the UI to meet a premium, modern design standard.

## User Review Required

> [!IMPORTANT]
> The original PRD mentions an Express proxy to protect the Anthropic API key. In this plan, I propose setting up a **full-stack approach** within an `app` directory containing both the React UI (managed by Vite) and an Express proxy to properly hit the Claude API without exposing the key or running into browser CORS issues. 
> Also, per instructions, I will NOT use TailwindCSS. I will use standard Vanilla CSS and implement a modern Glassmorphism-based aesthetic.

## Proposed Changes

We will create a clean application directory named `app` inside `c:\Users\yashd\Downloads\financial agent`.

### Project Setup
#### [NEW] `c:\Users\yashd\Downloads\financial agent\app\package.json`
Setup a monorepo-style structure or a simple Vite + Express combo.
#### [NEW] `c:\Users\yashd\Downloads\financial agent\app\server.js`
A thin Express backend that serves as a proxy for the Anthropic Claude API to avoid CORS issues and secure the API Key.

---

### Core Logic (Missing Implementations)
#### [NEW] `c:\Users\yashd\Downloads\financial agent\app\src\lib\csv_parser.js`
Implementation of PapaParse logic to read standard bank statement CSVs and convert them into the `financialJSON` schema expected by the agents.
#### [NEW] `c:\Users\yashd\Downloads\financial agent\app\src\lib\agent_prompts.js`
Functions to craft the actual agent prompts for Agent 1 (Debt), Agent 2 (Budget), Agent 3 (Savings), and Agent 4 (Payoff), injecting the `financialJSON`.

---

### Frontend Components & Styling
#### [NEW] `c:\Users\yashd\Downloads\financial agent\app\src\index.css`
A comprehensive Vanilla CSS design system. We will define robust CSS variables targeting a premium aesthetic: sleek dark/light mode harmonized palettes, smooth gradients, glassmorphism utilities, subtle micro-animations (hover effects, skeleton loaders during agent execution), and modern typography (e.g., 'Inter').
#### [MODIFY] `c:\Users\yashd\Downloads\financial agent\financial_dashboard.tsx` -> `app/src/App.tsx`
We will migrate the existing dashboard code into the new Vite structure. It will be refactored to:
- Be broken down into smaller components.
- Rely strictly on the predefined design system styling for a state-of-the-art "Wow" experience.
- Connect accurately to the actual parsing logic and the proxy API (removing the mock data reliance for the actual upload flow).

## Open Questions

> [!WARNING]  
> 1. To securely call the Anthropic Claude API, do you already have an API key I should expect you to inject via `.env`, or should we use placeholder mock responses in the final build for the proxy?
> 2. Should the new directory be inside `c:\Users\yashd\Downloads\financial agent\app` or do you prefer a different folder name? 

## Verification Plan

### Automated Tests
- N/A for MVP, manual testing will be prioritized.

### Manual Verification
- We will boot up the Vite + Express servers respectively.
- Using the provided mock CSVs or synthetic CSVs, we'll verify the file uploads successfully.
- We will visually inspect the application to ensure it achieves a "Premium Design" with glassmorphism and animations.
- We will check if the chat integration stream works seamlessly with Anthropic endpoints.
