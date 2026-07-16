import { OperatorPanel } from "@/components/shared";
import { ProductionCanvasEdgeControls } from "./ProductionCanvasEdgeControls";
import { ProductionCanvasCandidateReview } from "./ProductionCanvasCandidateReview";
import { ProductionCanvasMediaControls } from "./ProductionCanvasMediaControls";
import { ProductionCanvasNoteControls } from "./ProductionCanvasNoteControls";
import { ProductionCanvasTaskSummary } from "./ProductionCanvasTaskSummary";
import { ProductionCanvasRetryControls } from "./ProductionCanvasRetryControls";
import { ProductionCanvasVideoTaskStatus } from "./ProductionCanvasVideoTaskStatus";
import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";

type OutputPatch = Record<
  string,
  string | number | boolean | number[] | undefined
>;

export function ProductionCanvasNodeTools({
  canApprove = true,
  canEdit = true,
  canExecute = true,
  captureCanvasStateIdentity,
  edges,
  node,
  nodes,
  onAddEdge,
  onDuplicateNote,
  onReturnFocus,
  onRefreshTasks,
  onRetryNode,
  onRemoveEdge,
  onRemoveNode,
  onSelectNode,
  onUpdateNode,
  onUpdateNodeOutputs,
  onCanvasStateUpdated,
  onDomainContextResolved,
  refreshError,
  refreshingTasks,
  retryingNode,
  runId,
}: {
  canApprove?: boolean;
  canEdit?: boolean;
  canExecute?: boolean;
  captureCanvasStateIdentity: Parameters<
    typeof ProductionCanvasCandidateReview
  >[0]["captureCanvasStateIdentity"];
  edges: ProductionCanvasEdge[];
  node?: ProductionCanvasNode;
  nodes: ProductionCanvasNode[];
  onAddEdge: (edge: ProductionCanvasEdge) => void;
  onDuplicateNote: (nodeId: string) => void;
  onReturnFocus?: () => void;
  onRefreshTasks?: (nodes: ProductionCanvasNode[]) => void;
  onRetryNode?: Parameters<typeof ProductionCanvasRetryControls>[0]["onRetry"];
  onRemoveEdge: (edge: ProductionCanvasEdge) => void;
  onRemoveNode: (nodeId: string) => void;
  onSelectNode: (nodeId: string) => void;
  onUpdateNode: (nodeId: string, patch: Partial<ProductionCanvasNode>) => void;
  onUpdateNodeOutputs: (nodeId: string, patch: OutputPatch) => void;
  onCanvasStateUpdated: Parameters<
    typeof ProductionCanvasCandidateReview
  >[0]["onCanvasStateUpdated"];
  onDomainContextResolved?: Parameters<
    typeof ProductionCanvasCandidateReview
  >[0]["onDomainContextResolved"];
  refreshError?: string | null;
  refreshingTasks?: boolean;
  retryingNode?: boolean;
  runId: string;
}) {
  return (
    <OperatorPanel className="space-y-3 p-4">
      <ProductionCanvasTaskSummary
        nodes={nodes}
        onReturnFocus={onReturnFocus}
        onRefreshTasks={canExecute ? onRefreshTasks : undefined}
        onSelectNode={onSelectNode}
        refreshError={refreshError}
        refreshingTasks={refreshingTasks}
      />
      {canEdit ? (
        <>
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
        </>
      ) : null}
      <ProductionCanvasVideoTaskStatus node={node} />
      <ProductionCanvasRetryControls
        node={node}
        onRetry={canExecute ? onRetryNode : undefined}
        retrying={retryingNode}
        runId={runId}
      />
      <ProductionCanvasCandidateReview
        canApprove={canApprove}
        canBranch={canExecute}
        captureCanvasStateIdentity={captureCanvasStateIdentity}
        node={node}
        onCanvasStateUpdated={onCanvasStateUpdated}
        onDomainContextResolved={onDomainContextResolved}
        runId={runId}
      />
      {canEdit ? (
        <ProductionCanvasNoteControls
          node={node}
          onDuplicateNote={onDuplicateNote}
          onRemoveNode={onRemoveNode}
          onUpdateNode={onUpdateNode}
        />
      ) : null}
    </OperatorPanel>
  );
}
