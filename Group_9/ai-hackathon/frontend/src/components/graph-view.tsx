import { useMemo } from "react";
import ReactFlow, { Background, Controls, MiniMap, type Edge, type Node, type Viewport } from "reactflow";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Entity, Relationship } from "@/lib/types";

interface GraphViewProps {
  entities: Entity[];
  relationships: Relationship[];
  selectedNodeId: string | null;
  viewport: Viewport | null;
  onSelectNode: (nodeId: string | null) => void;
  onViewportChange: (viewport: Viewport) => void;
}

export function GraphView({ entities, relationships, selectedNodeId, viewport, onSelectNode, onViewportChange }: GraphViewProps) {
  const { nodes, edges } = useMemo(() => {
    const nodes: Node[] = entities.map((entity, index) => ({
      id: entity.id,
      position: {
        x: 120 + (index % 4) * 220,
        y: 60 + Math.floor(index / 4) * 160,
      },
      data: {
        label: (
          <div className="rounded-xl border border-primary/15 bg-white/90 px-3 py-2 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">{entity.entity_type}</p>
            <p className="font-heading text-sm text-foreground">{entity.name}</p>
          </div>
        ),
      },
      type: "default",
    }));

    const edges: Edge[] = relationships.map((relationship, index) => ({
      id: `${relationship.source_entity_id}-${relationship.target_entity_id}-${index}`,
      source: relationship.source_entity_id,
      target: relationship.target_entity_id,
      label: relationship.relationship_type,
      animated: true,
      style: { stroke: "#b86139" },
      labelStyle: { fill: "#485364", fontSize: 11, fontWeight: 600 },
    }));
    return { nodes, edges };
  }, [entities, relationships]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Knowledge graph</CardTitle>
      </CardHeader>
      <CardContent>
        {nodes.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-border bg-white/60 p-8 text-sm text-muted-foreground">
            No graph nodes yet. Deep runs will progressively populate entity relationships as the investigation advances.
          </div>
        ) : (
          <div className="h-[560px] overflow-hidden rounded-2xl border border-border bg-white/70">
            <ReactFlow
              nodes={nodes.map((node) => ({
                ...node,
                style: node.id === selectedNodeId ? { border: "2px solid #b86139", borderRadius: "1rem" } : node.style,
              }))}
              edges={edges}
              fitView={!viewport}
              defaultViewport={viewport ?? undefined}
              onNodeClick={(_, node) => onSelectNode(node.id)}
              onMoveEnd={(_, nextViewport) => onViewportChange(nextViewport)}
            >
              <MiniMap pannable zoomable />
              <Controls />
              <Background gap={24} size={1} color="#d4c7ba" />
            </ReactFlow>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
