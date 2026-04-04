from __future__ import annotations

from collections import Counter

from ai_app.agents.base import AgentBase
from ai_app.agents.hypothesis_agent import HypothesisAgent
from ai_app.domain.enums import InsightType
from ai_app.schemas.research import Entity, Insight, Relationship, ResearchSession


class InsightGenerationAgent(AgentBase):
    name = "insight_generation_agent"

    def __init__(self, hypothesis_agent: HypothesisAgent) -> None:
        self.hypothesis_agent = hypothesis_agent

    async def run(self, session: ResearchSession) -> ResearchSession:
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
        session.follow_up_questions.extend(await self.hypothesis_agent.run(session))
        return session

