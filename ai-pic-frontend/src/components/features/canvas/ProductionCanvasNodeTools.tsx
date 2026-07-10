import { OperatorPanel } from "@/components/shared";
import { ProductionCanvasEdgeControls } from "./ProductionCanvasEdgeControls";
import { ProductionCanvasMediaControls } from "./ProductionCanvasMediaControls";
import { ProductionCanvasNoteControls } from "./ProductionCanvasNoteControls";
import { ProductionCanvasTaskSummary } from "./ProductionCanvasTaskSummary";
import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";

type OutputPatch = Record<
  string,
  string | number | boolean | number[] | undefined
>;

export function ProductionCanvasNodeTools({
  edges,
  node,
  nodes,
  onAddEdge,
  onDuplicateNote,
  onReturnFocus,
  onRefreshTasks,
  onRemoveEdge,
  onSelectNode,
  onUpdateNode,
  onUpdateNodeOutputs,
  refreshError,
  refreshingTasks,
}: {
  edges: ProductionCanvasEdge[];
  node?: ProductionCanvasNode;
  nodes: ProductionCanvasNode[];
  onAddEdge: (from: string, to: string) => void;
  onDuplicateNote: (nodeId: string) => void;
  onReturnFocus?: () => void;
  onRefreshTasks?: (nodes: ProductionCanvasNode[]) => void;
  onRemoveEdge: (from: string, to: string) => void;
  onSelectNode?: (nodeId: string) => void;
  onUpdateNode: (nodeId: string, patch: Partial<ProductionCanvasNode>) => void;
  onUpdateNodeOutputs: (nodeId: string, patch: OutputPatch) => void;
  refreshError?: string | null;
  refreshingTasks?: boolean;
}) {
  return (
    <OperatorPanel className="space-y-3 p-4">
      <ProductionCanvasTaskSummary
        nodes={nodes}
        onReturnFocus={onReturnFocus}
        onRefreshTasks={onRefreshTasks}
        onSelectNode={onSelectNode}
        refreshError={refreshError}
        refreshingTasks={refreshingTasks}
      />
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
      <ProductionCanvasNoteControls
        node={node}
        onDuplicateNote={onDuplicateNote}
        onUpdateNode={onUpdateNode}
      />
    </OperatorPanel>
  );
}
