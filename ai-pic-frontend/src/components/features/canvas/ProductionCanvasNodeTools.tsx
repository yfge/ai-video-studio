import { OperatorPanel } from "@/components/shared";
import { ProductionCanvasEdgeControls } from "./ProductionCanvasEdgeControls";
import { ProductionCanvasMediaControls } from "./ProductionCanvasMediaControls";
import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";

type OutputPatch = Record<string, string | number | boolean | number[] | undefined>;

export function ProductionCanvasNodeTools({
  edges,
  node,
  nodes,
  onAddEdge,
  onRemoveEdge,
  onUpdateNodeOutputs,
}: {
  edges: ProductionCanvasEdge[];
  node?: ProductionCanvasNode;
  nodes: ProductionCanvasNode[];
  onAddEdge: (from: string, to: string) => void;
  onRemoveEdge: (from: string, to: string) => void;
  onUpdateNodeOutputs: (nodeId: string, patch: OutputPatch) => void;
}) {
  return (
    <OperatorPanel className="space-y-3 p-4">
      <ProductionCanvasEdgeControls
        edges={edges}
        node={node}
        nodes={nodes}
        onAddEdge={onAddEdge}
        onRemoveEdge={onRemoveEdge}
      />
      <ProductionCanvasMediaControls
        node={node}
        onUpdateNodeOutputs={onUpdateNodeOutputs}
      />
    </OperatorPanel>
  );
}
