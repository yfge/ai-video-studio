import { useEffect, useRef, useState } from "react";
import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";
import {
  initialProductionCanvasRevealedNodeIds,
  productionCanvasExecutionRevealedNodeIds,
} from "./productionCanvasProgressiveReveal";

export function useProductionCanvasProgressiveReveal(
  activeRunId?: string | null,
) {
  const edgesRef = useRef<ProductionCanvasEdge[]>([]);
  const progressiveRef = useRef(false);
  const progressiveRunIdRef = useRef<string | null>(null);
  const [revealedNodeIds, setRevealedNodeIds] = useState<Set<string> | null>(
    null,
  );
  const revealNodeIds = (nodeIds: Iterable<string>) => {
    if (!progressiveRef.current) return;
    setRevealedNodeIds((current) => {
      const next = new Set(current || []);
      for (const nodeId of nodeIds) next.add(nodeId);
      return next;
    });
  };
  const revealExecutionNodes = (nodes: ProductionCanvasNode[]) =>
    revealNodeIds(
      productionCanvasExecutionRevealedNodeIds(nodes, edgesRef.current),
    );
  const begin = (
    nodes: ProductionCanvasNode[],
    edges: ProductionCanvasEdge[],
    runId?: string | null,
  ) => {
    if (!edges.length) {
      disable();
      return;
    }
    edgesRef.current = edges;
    progressiveRef.current = true;
    progressiveRunIdRef.current = runId?.trim() || null;
    setRevealedNodeIds(initialProductionCanvasRevealedNodeIds(nodes, edges));
  };
  const disable = () => {
    progressiveRef.current = false;
    progressiveRunIdRef.current = null;
    setRevealedNodeIds(null);
  };

  useEffect(() => {
    if (
      progressiveRef.current &&
      progressiveRunIdRef.current &&
      progressiveRunIdRef.current !== (activeRunId || null)
    ) {
      disable();
    }
  }, [activeRunId]);

  return {
    begin,
    disable,
    revealExecutionNodes,
    revealNode: (node: ProductionCanvasNode) => revealNodeIds([node.id]),
    revealedNodeIds,
  };
}
