import { OperatorPanel } from "@/components/shared";
import { ProductionCanvasEdgeControls } from "./ProductionCanvasEdgeControls";
import { ProductionCanvasCandidateReview } from "./ProductionCanvasCandidateReview";
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
  onRemoveNode,
  onSelectNode,
  onUpdateNode,
  onUpdateNodeOutputs,
  onCanvasStateUpdated,
  refreshError,
  refreshingTasks,
  runId,
}: {
  edges: ProductionCanvasEdge[];
  node?: ProductionCanvasNode;
  nodes: ProductionCanvasNode[];
  onAddEdge: (edge: ProductionCanvasEdge) => void;
  onDuplicateNote: (nodeId: string) => void;
  onReturnFocus?: () => void;
  onRefreshTasks?: (nodes: ProductionCanvasNode[]) => void;
  onRemoveEdge: (edge: ProductionCanvasEdge) => void;
  onRemoveNode: (nodeId: string) => void;
  onSelectNode: (nodeId: string) => void;
  onUpdateNode: (nodeId: string, patch: Partial<ProductionCanvasNode>) => void;
  onUpdateNodeOutputs: (nodeId: string, patch: OutputPatch) => void;
  onCanvasStateUpdated: Parameters<
    typeof ProductionCanvasCandidateReview
  >[0]["onCanvasStateUpdated"];
  refreshError?: string | null;
  refreshingTasks?: boolean;
  runId: string;
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
      <ProductionCanvasCandidateReview
        node={node}
        onCanvasStateUpdated={onCanvasStateUpdated}
        runId={runId}
      />
      <ProductionCanvasNoteControls
        node={node}
        onDuplicateNote={onDuplicateNote}
        onRemoveNode={onRemoveNode}
        onUpdateNode={onUpdateNode}
      />
    </OperatorPanel>
  );
}
