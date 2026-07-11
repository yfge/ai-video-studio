import type { ComponentProps } from "react";
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
  refreshError,
  refreshingTasks,
  retryingNodeId,
  runId,
  taskSyncError,
  taskSyncingNodeId,
}: {
  accessRole: ProductionCanvasAccessRole | null;
  capabilities: ProductionCanvasCapabilities;
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
  refreshError?: string | null;
  refreshingTasks?: boolean;
  retryingNodeId?: string | null;
  runId: string;
  taskSyncError?: string | null;
  taskSyncingNodeId?: string | null;
}) {
  return (
    <div className="space-y-3">
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
        refreshError={refreshError}
        refreshingTasks={refreshingTasks}
        retryingNode={retryingNodeId === node?.id}
        runId={runId}
      />
      <ProductionCanvasCollaborationPanel
        accessRole={accessRole}
        edges={edges}
        node={node}
        nodes={nodes}
        runId={runId}
        sections={sections}
      />
      <OperatorPanel className="p-4">
        <div className="text-xs font-semibold text-gray-950">画布操作</div>
        <div className="mt-2 space-y-1 text-xs leading-5 text-gray-500">
          <p>拖拽节点调整链路位置。</p>
          <p>拖拽空白区域移动画布。</p>
          <p>滚轮或工具栏缩放视图。</p>
        </div>
      </OperatorPanel>
    </div>
  );
}
