## Info about the mock statements:
Here are three months of realistic test data. The statements are designed to give the agents interesting patterns to work with:
The fictional user earns $6,400/month from a regular payroll split across two deposits, with a one-off $850 freelance payment appearing in March — good for testing how the savings agent handles variable income.
There are three distinct debt streams to stress-test the payoff optimizer: a Chase Visa ($85/month minimum), a Discover Card ($65/month), and a Capital One card ($55/month), plus a $287/month student loan. None of them show principal paydown from minimums alone, which should trigger the avalanche vs. snowball comparison nicely.
Spending has some deliberate variance across the months — February spikes on dining (Valentine's dinner at Cheesecake Factory, florist), March has a splurge at Nobu and a bigger Amazon haul — so the budget coach has something concrete to call out rather than flat, boring numbers.
The balance grows month-over-month (Jan ends at $7,467 → Mar ends at $14,365), which gives the savings agent a clear opportunity to recommend accelerating debt payoff rather than letting cash sit idle.

## additional helpful code:
import { parseMultipleStatements } from "./csvParser.js";
import { buildPrompt, DEBT_ANALYZER_PROMPT } from "./agentPrompts.js";

// from a file input with 3 CSVs selected
const files = Array.from(fileInput.files);
const financialJson = await parseMultipleStatements(files);

// pass to any agent
const prompt = buildPrompt(DEBT_ANALYZER_PROMPT, financialJson);

## how to use the dashboard

Here's the full dashboard — click "Use demo data" to load it up. Here's what's in each tab:
Overview — monthly cash flow bar chart, spending breakdown donut, and four summary stat cards showing income, spend, surplus, and net balance change across the 3 months.
Debt — all four debt accounts with balance bars, APR, and urgency flags. The red alert banners call out that every account is on minimum payments only.
Budget — the real/recommended spend comparison bars per category, the three specific overspend findings from the budget agent (named merchants, real numbers), and the ranked action items with estimated monthly savings.
Savings — emergency fund progress bar, gap analysis, and the three prioritized savings goals with timelines.
Payoff — toggle between avalanche and snowball strategies, see the payoff order with month numbers, and a side-by-side interest comparison bar chart. The recommendation banner tells the user which to pick and why.
Chat — a working chat interface that sends messages to Claude with the full financial context injected into the system prompt. The three suggestion pills pre-populate common questions to make the demo feel instant.
The next wiring step is replacing the hardcoded DEMO_AGENTS object with real responses from the four agent calls you built earlier, and hooking up the CSV upload button to parseMultipleStatements. Want me to write that integration layer?