Plan: Comparative / Debate Mode
Context
User story: As a user, I want to input two competing positions and get a balanced evidence comparison so that I can make an informed decision.

Input: Two claims or positions (e.g., "Remote work is more productive" vs. "In-office work is more productive")
Output: Structured pro/con evidence table with a "weight of evidence" assessment
Constraint: Same citation and confidence mechanics as standard mode

What exists: ResearchSession already has debate_mode, position_a, position_b fields (unused). The Contradiction model, ContradictionCheckerAgent, and credibility scoring pipeline all work and can be reused. The LangGraph pipeline is linear: planner -> retriever -> analysis -> insight -> reporter.

Approach: Add DEBATE to RunMode, thread position fields from UI -> API -> coordinator -> session, then add debate-conditional branches inside existing agents. No new graph nodes, no new schema types beyond one field on Claim.


Files to Modify (9 files)
1. src/ai_app/domain/enums.py — Add DEBATE enum value
Add DEBATE = "debate" to RunMode.

class RunMode(str, Enum):

    SINGLE = "single"

    BATCH = "batch"

    DEBATE = "debate"       # <-- add this


2. src/ai_app/schemas/research.py — Schema changes
2a. ResearchRequest (line 196): Add position fields
Add after run_mode:

position_a: str = ""

position_b: str = ""
2b. ResearchRequest.validate_request (line 208): Add debate validation
Add after the batch validation block:

if self.run_mode == RunMode.DEBATE:

    if not self.position_a.strip() or not self.position_b.strip():

        raise ValueError("position_a and position_b are required when run_mode=debate.")

    if not self.query.strip():

        self.query = f"{self.position_a.strip()} vs. {self.position_b.strip()}"
2c. Claim model (line 51): Add debate_position field
debate_position: str = ""   # "position_a", "position_b", or "" (neutral/both)


3. src/ai_app/orchestration/coordinator.py — Wire debate fields to session
In create_session() (line 160), add debate handling:

debate_mode = request.run_mode == RunMode.DEBATE

position_a = request.position_a.strip() if request.position_a else ""

position_b = request.position_b.strip() if request.position_b else ""

if debate_mode:

    query = f"Debate: {position_a} vs. {position_b}"

In the ResearchSession(...) constructor call, add:

debate_mode=debate_mode,

position_a=position_a if debate_mode else None,

position_b=position_b if debate_mode else None,


4. src/ai_app/api/research.py — Accept position fields from API
In _parse_request() multipart branch (line 41), extract:

position_a = str(form.get("position_a", ""))

position_b = str(form.get("position_b", ""))

Pass to ResearchRequest() constructor:

position_a=position_a,

position_b=position_b,

JSON branch needs no change — Pydantic auto-validates from payload.


5. src/ai_app/agents/planner_agent.py — Debate question generation
Add debate branch in run() after batch mode check. When session.debate_mode:

LLM path — new method _debate_questions_llm():

async def _debate_questions_llm(self, session: ResearchSession) -> list[str]:

    prompt = (

        f"Two competing positions are being debated:\n"

        f"Position A: {session.position_a}\n"

        f"Position B: {session.position_b}\n\n"

        f"Generate balanced research sub-questions. Include:\n"

        f"- 2-3 questions seeking evidence FOR Position A\n"

        f"- 2-3 questions seeking evidence FOR Position B\n"

        f"- 1-2 questions about shared context, methodology, or definitions\n"

        f"Depth: {session.depth.value}\n"

        "Prefix each question with [A], [B], or [SHARED].\n"

        "Return each sub-question on a new line."

    )

    completion = await self.llm_client.complete(

        "You are a research planning agent specializing in balanced debate analysis.",

        prompt,

    )

    parts = [line.lstrip("-0123456789. ").strip()

             for line in completion.splitlines() if line.strip()]

    return parts if parts else []

Heuristic fallback — new method _heuristic_debate_questions():

def _heuristic_debate_questions(self, position_a: str, position_b: str, depth: Depth) -> list[str]:

    questions = [

        f"[A] What evidence supports the position: {position_a}?",

        f"[A] What are the strongest arguments and data for: {position_a}?",

        f"[B] What evidence supports the position: {position_b}?",

        f"[B] What are the strongest arguments and data for: {position_b}?",

        f"[SHARED] What are the key definitions, metrics, and context for comparing these positions?",

        f"[SHARED] What do meta-analyses or systematic reviews say about: {position_a} vs. {position_b}?",

    ]

    if depth == Depth.DEEP:

        questions.extend([

            f"[A] What are the limitations or counter-arguments against: {position_a}?",

            f"[B] What are the limitations or counter-arguments against: {position_b}?",

            f"[SHARED] What contextual factors (industry, geography, demographics) affect this comparison?",

        ])

    return questions[:self._max_questions(depth)]

Key design: The [A], [B], [SHARED] prefixes in sub-questions flow through to finding.sub_question and are used by CriticalAnalysisAgent to tag claims by position.


6. src/ai_app/agents/critical_analysis_agent.py — Tag claims by position
Add static helper method:

@staticmethod

def _infer_debate_position(finding_sub_question: str) -> str:

    sq_lower = finding_sub_question.lower().lstrip()

    if sq_lower.startswith("[a]"):

        return "position_a"

    if sq_lower.startswith("[b]"):

        return "position_b"

    return ""

In the claim-building loop, after constructing each Claim, add:

if session.debate_mode:

    claim.debate_position = self._infer_debate_position(finding.sub_question)

No changes to confidence scoring — same credibility pipeline applies equally to both sides, ensuring apples-to-apples comparison.


7. src/ai_app/agents/insight_generation_agent.py — Weight-of-evidence insight
At the top of run(), after the existing if session.claims: block, add debate insights:

if session.debate_mode and session.position_a and session.position_b:

    a_claims = [c for c in session.claims if c.debate_position == "position_a"]

    b_claims = [c for c in session.claims if c.debate_position == "position_b"]

    a_avg = sum(c.confidence_pct for c in a_claims) / max(1, len(a_claims))

    b_avg = sum(c.confidence_pct for c in b_claims) / max(1, len(b_claims))

    a_trust = sum(c.trust_score for c in a_claims) / max(1, len(a_claims))

    b_trust = sum(c.trust_score for c in b_claims) / max(1, len(b_claims))

    if abs(a_avg - b_avg) < 5:

        verdict = "The evidence is roughly balanced between both positions."

    elif a_avg > b_avg:

        verdict = f'Position A ("{session.position_a}") has stronger overall evidence (avg confidence {a_avg:.0f}% vs {b_avg:.0f}%).'

    else:

        verdict = f'Position B ("{session.position_b}") has stronger overall evidence (avg confidence {b_avg:.0f}% vs {a_avg:.0f}%).'

    session.insights.append(Insight(

        content=verdict,

        evidence_chain=(

            [c.supporting_source_ids[0] for c in a_claims if c.supporting_source_ids][:2]

            + [c.supporting_source_ids[0] for c in b_claims if c.supporting_source_ids][:2]

        ),

        insight_type=InsightType.CROSS_DOMAIN,

        label="Weight of Evidence Assessment",

    ))

    session.insights.append(Insight(

        content=f"Position A has {len(a_claims)} claims (avg trust {a_trust:.0f}%), Position B has {len(b_claims)} claims (avg trust {b_trust:.0f}%).",

        evidence_chain=[],

        insight_type=InsightType.GAP,

        label="Evidence Distribution",

    ))


8. src/ai_app/agents/report_builder_agent.py — Comparison table + verdict sections
When session.debate_mode, insert two new ReportSections after "Source Strategy" and override the executive summary.
8a. Build the comparison table
if session.debate_mode and session.position_a and session.position_b:

    a_claims = [c for c in session.claims if c.debate_position == "position_a"]

    b_claims = [c for c in session.claims if c.debate_position == "position_b"]

    neutral_claims = [c for c in session.claims if c.debate_position == ""]

    # Markdown comparison table

    table_rows = [

        f"| Aspect | Position A: {session.position_a} | Position B: {session.position_b} |",

        "|---|---|---|",

        f"| Number of claims | {len(a_claims)} | {len(b_claims)} |",

    ]

    a_avg_conf = sum(c.confidence_pct for c in a_claims) / max(1, len(a_claims))

    b_avg_conf = sum(c.confidence_pct for c in b_claims) / max(1, len(b_claims))

    table_rows.append(f"| Avg confidence | {a_avg_conf:.0f}% | {b_avg_conf:.0f}% |")

    a_avg_trust = sum(c.trust_score for c in a_claims) / max(1, len(a_claims))

    b_avg_trust = sum(c.trust_score for c in b_claims) / max(1, len(b_claims))

    table_rows.append(f"| Avg trust score | {a_avg_trust:.0f}% | {b_avg_trust:.0f}% |")

    a_high = sum(1 for c in a_claims if c.confidence == ConfidenceLabel.HIGH)

    b_high = sum(1 for c in b_claims if c.confidence == ConfidenceLabel.HIGH)

    table_rows.append(f"| High-confidence claims | {a_high} | {b_high} |")

    a_contested = sum(1 for c in a_claims if c.contested)

    b_contested = sum(1 for c in b_claims if c.contested)

    table_rows.append(f"| Contested claims | {a_contested} | {b_contested} |")

    a_weak = sum(1 for c in a_claims if c.weak_evidence)

    b_weak = sum(1 for c in b_claims if c.weak_evidence)

    table_rows.append(f"| Weak-evidence claims | {a_weak} | {b_weak} |")

    debate_comparison = "\n".join(table_rows)

    # Itemized claims per position

    a_detail = "\n".join(

        f"- {c.statement} (confidence: {c.confidence_pct}%, trust: {c.trust_score}%)"

        for c in a_claims[:8]

    ) or "- No claims found for this position."

    b_detail = "\n".join(

        f"- {c.statement} (confidence: {c.confidence_pct}%, trust: {c.trust_score}%)"

        for c in b_claims[:8]

    ) or "- No claims found for this position."

    debate_comparison += f"\n\n### Evidence for Position A: {session.position_a}\n{a_detail}"

    debate_comparison += f"\n\n### Evidence for Position B: {session.position_b}\n{b_detail}"

    if neutral_claims:

        neutral_detail = "\n".join(

            f"- {c.statement} (confidence: {c.confidence_pct}%)" for c in neutral_claims[:5]

        )

        debate_comparison += f"\n\n### Shared / Neutral Evidence\n{neutral_detail}"
8b. Build the weight-of-evidence verdict
    if abs(a_avg_conf - b_avg_conf) < 5:

        verdict_text = "The collected evidence does not clearly favor either position."

    elif a_avg_conf > b_avg_conf:

        verdict_text = f'The weight of evidence leans toward Position A ("{session.position_a}").'

    else:

        verdict_text = f'The weight of evidence leans toward Position B ("{session.position_b}").'

    debate_verdict = (

        f"{verdict_text}\n\n"

        f"- Position A avg confidence: {a_avg_conf:.0f}%, avg trust: {a_avg_trust:.0f}%, claims: {len(a_claims)}\n"

        f"- Position B avg confidence: {b_avg_conf:.0f}%, avg trust: {b_avg_trust:.0f}%, claims: {len(b_claims)}\n\n"

        "Note: This assessment is based solely on the evidence retrieved during this session. "

        "It reflects the weight of available evidence, not absolute truth."

    )
8c. Build report sections
When debate mode: override summary, insert debate_comparison (order 4) and debate_verdict (order 5), bump remaining sections by +2.

When not debate mode: existing 12 sections unchanged.


9. ui/gradio/deep_researcher.py — Debate UI inputs
9a. Add position input fields (after batch_topics Textbox)
position_a = gr.Textbox(

    label="Position A", lines=2,

    placeholder='e.g., "Remote work is more productive"',

    visible=False,

)

position_b = gr.Textbox(

    label="Position B", lines=2,

    placeholder='e.g., "In-office work is more productive"',

    visible=False,

)
9b. Toggle visibility based on run_mode
def toggle_mode_inputs(mode):

    is_batch = mode == RunMode.BATCH.value

    is_debate = mode == RunMode.DEBATE.value

    return (

        gr.update(visible=is_batch),   # batch_topics

        gr.update(visible=is_debate),  # position_a

        gr.update(visible=is_debate),  # position_b

    )

run_mode.change(

    fn=toggle_mode_inputs,

    inputs=run_mode,

    outputs=[batch_topics, position_a, position_b],

)
9c. Update run_research signature
Add position_a_val, position_b_val params. Pass position_a=position_a_val or "", position_b=position_b_val or "" to ResearchRequest.
9d. Update start.click inputs
Add position_a, position_b to the inputs list.

RunMode radio choices auto-update via the existing enum comprehension.


Files NOT Modified
File
Reason
orchestration/graph.py
Linear pipeline unchanged
orchestration/state.py
GraphState unchanged
agents/contextual_retriever_agent.py
Iterates sub_questions as-is; [A]/[B] prefixes guide search naturally
agents/contradiction_checker_agent.py
Works on all claims; cross-position contradictions are expected
agents/source_verifier_agent.py
Credibility scoring is position-agnostic
agents/hypothesis_agent.py
Follow-up templates work with debate query
ui/components/*
Report viewer renders all ReportSections generically



Implementation Order
1. enums.py                      (foundation)

2. schemas/research.py           (fields + validation)

3. coordinator.py                (wire to session)

4. api/research.py               (accept from API)

5. planner_agent.py              (debate sub-questions)      ─┐

6. critical_analysis_agent.py    (position tagging)           │ independent

7. insight_generation_agent.py   (weight-of-evidence)         │ of each other

8. report_builder_agent.py       (comparison table + verdict) ─┘

9. ui/gradio/deep_researcher.py  (UI inputs)


Verification
Compile check: PYTHONPATH="src;." python -m compileall src/ ui/
Import check: PYTHONPATH="src;." python -c "from ai_app.main import app; print('OK')"
Start server: PYTHONPATH="src;." python -m uvicorn ai_app.main:app --port 8000
UI test: Open http://localhost:8000 -> select "Debate" mode -> verify position fields appear, batch_topics hides
End-to-end: Enter two positions, run research -> verify:
Sub-questions have [A]/[B]/[SHARED] prefixes
Report contains "Position Comparison" table and "Weight of Evidence Assessment"
Claims show debate_position values
Existing Single/Batch modes still work unchanged

