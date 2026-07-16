import { useState, type ComponentProps } from "react";
import { OperatorPanel } from "@/components/shared";
import { CanvasInspector } from "./ProductionCanvasElements";
import { ProductionCanvasNodeTools } from "./ProductionCanvasNodeTools";
import { ProductionCanvasCollaborationPanel } from "./ProductionCanvasCollaborationPanel";
import type { ProductionCanvasAccessRole } from "@/utils/api/types";
import type { ProductionCanvasCapabilities } from "./productionCanvasAccess";
import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";
import type { ProductionCanvasSection } from "./productionCanvasSectionModel";

type NodeToolsProps = ComponentProps<typeof ProductionCanvasNodeTools>;

export function ProductionCanvasSidePanel({
  accessRole,
  capabilities,
  captureCanvasStateIdentity,
  edges,
  executionError,
  executingNodeId,
  node,
  nodes,
  sections,
  onAddEdge,
  onDuplicateNote,
  onExecuteNode,
  onExecuteDownstream,
  onRefreshTaskNode,
  onRefreshTasks,
  onRetryNode,
  onRemoveEdge,
  onRemoveNode,
  onReturnFocus,
  onSelectNode,
  onUpdateNode,
  onUpdateNodeOutputs,
  onCanvasStateUpdated,
  onDomainContextResolved,
  refreshError,
  refreshingTasks,
  retryingNodeId,
  runId,
  taskSyncError,
  taskSyncingNodeId,
}: {
  accessRole: ProductionCanvasAccessRole | null;
  capabilities: ProductionCanvasCapabilities;
  captureCanvasStateIdentity: NodeToolsProps["captureCanvasStateIdentity"];
  edges: ProductionCanvasEdge[];
  executionError?: string | null;
  executingNodeId?: string | null;
  node?: ProductionCanvasNode;
  nodes: ProductionCanvasNode[];
  sections: ProductionCanvasSection[];
  onAddEdge: (edge: ProductionCanvasEdge) => void;
  onDuplicateNote: (nodeId: string) => void;
  onExecuteNode: (node: ProductionCanvasNode) => void;
  onExecuteDownstream: (node: ProductionCanvasNode) => void;
  onRefreshTaskNode: (node: ProductionCanvasNode) => void;
  onRefreshTasks: (nodes: ProductionCanvasNode[]) => void;
  onRetryNode: NodeToolsProps["onRetryNode"];
  onRemoveEdge: (edge: ProductionCanvasEdge) => void;
  onRemoveNode: (nodeId: string) => void;
  onReturnFocus: () => void;
  onSelectNode: (nodeId: string) => void;
  onUpdateNode: (nodeId: string, patch: Partial<ProductionCanvasNode>) => void;
  onUpdateNodeOutputs: NodeToolsProps["onUpdateNodeOutputs"];
  onCanvasStateUpdated: NodeToolsProps["onCanvasStateUpdated"];
  onDomainContextResolved?: NodeToolsProps["onDomainContextResolved"];
  refreshError?: string | null;
  refreshingTasks?: boolean;
  retryingNodeId?: string | null;
  runId: string;
  taskSyncError?: string | null;
  taskSyncingNodeId?: string | null;
}) {
  const [showCollaboration, setShowCollaboration] = useState(false);
  return (
    <OperatorPanel className="h-[clamp(560px,calc(100vh-330px),760px)] overflow-y-auto xl:sticky xl:top-[72px]">
      <div className="divide-y divide-slate-100 [&>section]:rounded-none [&>section]:border-0">
        <CanvasInspector
          canExecute={capabilities.execute}
          node={node}
          executingNodeId={executingNodeId}
          executionError={executionError}
          onExecuteNode={onExecuteNode}
          onExecuteDownstream={onExecuteDownstream}
          onRefreshTaskNode={onRefreshTaskNode}
          taskSyncError={taskSyncError}
          taskSyncingNodeId={taskSyncingNodeId}
        />
        <ProductionCanvasNodeTools
          canApprove={capabilities.approve}
          canEdit={capabilities.edit}
          canExecute={capabilities.execute}
          captureCanvasStateIdentity={captureCanvasStateIdentity}
          edges={edges}
          node={node}
          nodes={nodes}
          onAddEdge={onAddEdge}
          onDuplicateNote={onDuplicateNote}
          onReturnFocus={onReturnFocus}
          onRefreshTasks={onRefreshTasks}
          onRetryNode={onRetryNode}
          onRemoveEdge={onRemoveEdge}
          onRemoveNode={onRemoveNode}
          onSelectNode={onSelectNode}
          onUpdateNode={onUpdateNode}
          onUpdateNodeOutputs={onUpdateNodeOutputs}
          onCanvasStateUpdated={onCanvasStateUpdated}
          onDomainContextResolved={onDomainContextResolved}
          refreshError={refreshError}
          refreshingTasks={refreshingTasks}
          retryingNode={retryingNodeId === node?.id}
          runId={runId}
        />
      </div>
      {runId ? (
        <div className="border-t border-slate-100 p-4">
          <button
            type="button"
            aria-expanded={showCollaboration}
            className="flex w-full items-center justify-between text-left text-[13px] font-semibold text-slate-700"
            onClick={() => setShowCollaboration((value) => !value)}
          >
            协作与版本
            <span className="font-normal text-slate-400">
              {showCollaboration ? "收起" : "展开"}
            </span>
          </button>
          {showCollaboration ? (
            <div className="mt-3 [&>section]:rounded-none [&>section]:border-0">
              <ProductionCanvasCollaborationPanel
                accessRole={accessRole}
                edges={edges}
                node={node}
                nodes={nodes}
                runId={runId}
                sections={sections}
              />
            </div>
          ) : null}
        </div>
      ) : null}
    </OperatorPanel>
  );
}
