from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from ai_app.agents.base import AgentBase
from ai_app.agents.hypothesis_agent import HypothesisAgent
from ai_app.agents.llm_contracts import InsightOutput
from ai_app.domain.enums import InsightType
from ai_app.llms.client import OpenRouterClient
from ai_app.llms.prompts import load_prompt
from ai_app.llms.structured_output import parse_model
from ai_app.schemas.research import Entity, FollowUpQuestion, Insight, Relationship, ResearchSession


class InsightGenerationAgent(AgentBase):
    name = "insight_generation_agent"

    def __init__(self, llm_client: OpenRouterClient, hypothesis_agent: HypothesisAgent) -> None:
        self.llm_client = llm_client
        self.hypothesis_agent = hypothesis_agent
        self.system_prompt = load_prompt("system", "insight_generation")

    async def run(self, session: ResearchSession) -> ResearchSession:
        llm_populated = await self._run_llm(session)
        if not llm_populated:
            self._heuristic_populate(session)
        session.follow_up_questions.extend(await self.hypothesis_agent.run(session))
        return session

    async def _run_llm(self, session: ResearchSession) -> bool:
        if not self.llm_client.enabled or not session.claims:
            return False
        payload = {
            "query": session.query,
            "claims": [
                {
                    "id": claim.id,
                    "statement": claim.statement,
                    "supporting_source_ids": claim.supporting_source_ids[:5],
                    "contradicting_source_ids": claim.contradicting_source_ids[:5],
                    "confidence_pct": claim.confidence_pct,
                    "trust_score": claim.trust_score,
                    "consensus_pct": claim.consensus_pct,
                    "debate_position": claim.debate_position or "neutral",
                }
                for claim in session.claims[:14]
            ],
            "contradictions": [
                {
                    "id": contradiction.id,
                    "claim_a": contradiction.claim_a,
                    "claim_b": contradiction.claim_b,
                    "analysis": contradiction.analysis,
                    "credibility_lean": contradiction.credibility_lean,
                }
                for contradiction in session.contradictions[:10]
            ],
        }
        raw_output = await self.llm_client.complete_json(
            self.system_prompt,
            "Produce higher-order insights, graph entities, relationships, and follow-up questions as JSON.\n"
            f"payload={payload}",
        )
        parsed = parse_model(self._normalize_llm_output(raw_output), InsightOutput)
        if not parsed:
            return False

        for insight in parsed.insights[:8]:
            try:
                insight_type = InsightType(insight.insight_type)
            except ValueError:
                insight_type = InsightType.TREND
            session.insights.append(
                Insight(
                    content=insight.content,
                    evidence_chain=insight.evidence_chain,
                    insight_type=insight_type,
                    label=insight.label,
                )
            )

        entity_map: dict[str, Entity] = {entity.name.lower(): entity for entity in session.entities}
        for item in parsed.entities[:14]:
            key = item.name.lower()
            if key in entity_map:
                continue
            entity = Entity(
                name=item.name,
                entity_type=item.entity_type,
                description=item.description or None,
                source_ids=item.source_ids,
            )
            session.entities.append(entity)
            entity_map[key] = entity

        for relation in parsed.relationships[:20]:
            source_entity = entity_map.get(relation.source_entity_name.lower())
            target_entity = entity_map.get(relation.target_entity_name.lower())
            if not source_entity or not target_entity:
                continue
            session.relationships.append(
                Relationship(
                    source_entity_id=source_entity.id,
                    target_entity_id=target_entity.id,
                    relationship_type=relation.relationship_type,
                    description=relation.description or None,
                )
            )

        for follow_up in parsed.follow_up_questions[:6]:
            session.follow_up_questions.append(
                FollowUpQuestion(question=follow_up.question, rationale=follow_up.rationale)
            )
        return bool(parsed.insights or parsed.entities or parsed.relationships or parsed.follow_up_questions)

    def _heuristic_populate(self, session: ResearchSession) -> None:
        if session.claims:
            top_claim = session.claims[0]
            session.insights.append(
                Insight(
                    content=f"The evidence suggests the main pattern is concentrated around: {top_claim.statement}",
                    evidence_chain=top_claim.supporting_source_ids[:3],
                    insight_type=InsightType.TREND,
                    label="Emerging pattern",
                )
            )
        words = Counter()
        for claim in session.claims:
            for word in claim.statement.split():
                clean = word.strip(".,()").title()
                if len(clean) > 4:
                    words[clean] += 1
        entities = []
        for name, _ in words.most_common(6):
            entities.append(Entity(name=name, entity_type="concept", source_ids=[]))
        session.entities.extend(entities)
        for left, right in zip(entities, entities[1:]):
            session.relationships.append(Relationship(source_entity_id=left.id, target_entity_id=right.id, relationship_type="related_to"))

    def _normalize_llm_output(self, data: dict) -> dict:
        if not isinstance(data, dict):
            return {}
        normalized = dict(data)
        normalized["insights"] = [self._normalize_insight(item) for item in self._as_list(data.get("insights"))]
        normalized["entities"] = [self._normalize_entity(item) for item in self._as_list(data.get("entities"))]
        normalized["relationships"] = [self._normalize_relationship(item) for item in self._as_list(data.get("relationships"))]
        normalized["follow_up_questions"] = [self._normalize_follow_up(item) for item in self._as_list(data.get("follow_up_questions"))]
        return normalized

    def _normalize_insight(self, item) -> dict:
        if isinstance(item, str):
            return {
                "label": item[:80] or "Insight",
                "content": item,
                "insight_type": "trend",
                "evidence_chain": [],
            }
        if not isinstance(item, dict):
            return {"label": "Insight", "content": "", "insight_type": "trend", "evidence_chain": []}
        return {
            "label": item.get("label") or item.get("title") or item.get("statement") or "Insight",
            "content": item.get("content") or item.get("statement") or item.get("summary") or item.get("description") or "",
            "insight_type": item.get("insight_type") or item.get("type") or "trend",
            "evidence_chain": self._string_list(item.get("evidence_chain") or item.get("evidence") or item.get("source_ids")),
        }

    def _normalize_entity(self, item) -> dict:
        if isinstance(item, str):
            return {"name": item, "entity_type": "concept", "description": "", "source_ids": []}
        if not isinstance(item, dict):
            return {"name": "Unknown entity", "entity_type": "concept", "description": "", "source_ids": []}
        return {
            "name": item.get("name") or item.get("entity") or item.get("label") or "Unknown entity",
            "entity_type": item.get("entity_type") or item.get("type") or "concept",
            "description": item.get("description") or item.get("summary") or "",
            "source_ids": self._string_list(item.get("source_ids") or item.get("sources")),
        }

    def _normalize_relationship(self, item) -> dict:
        if not isinstance(item, dict):
            return {
                "source_entity_name": "",
                "target_entity_name": "",
                "relationship_type": "related_to",
                "description": "",
            }
        return {
            "source_entity_name": item.get("source_entity_name") or item.get("source") or item.get("from") or "",
            "target_entity_name": item.get("target_entity_name") or item.get("target") or item.get("to") or "",
            "relationship_type": item.get("relationship_type") or item.get("type") or "related_to",
            "description": item.get("description") or item.get("summary") or "",
        }

    def _normalize_follow_up(self, item) -> dict:
        if isinstance(item, str):
            return {"question": item, "rationale": ""}
        if not isinstance(item, dict):
            return {"question": "", "rationale": ""}
        return {
            "question": item.get("question") or item.get("prompt") or item.get("text") or "",
            "rationale": item.get("rationale") or item.get("reason") or item.get("why") or "",
        }

    def _string_list(self, value) -> list[str]:
        return [str(item).strip() for item in self._as_list(value) if str(item).strip()]

    def _as_list(self, value) -> list:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict)):
            return list(value)
        return [value]
