import type { ComponentProps } from "react";
import { OperatorPanel } from "@/components/shared";
import { CanvasInspector } from "./ProductionCanvasElements";
import { ProductionCanvasNodeTools } from "./ProductionCanvasNodeTools";
import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";

type NodeToolsProps = ComponentProps<typeof ProductionCanvasNodeTools>;

export function ProductionCanvasSidePanel({
  edges,
  executionError,
  executingNodeId,
  node,
  nodes,
  onAddEdge,
  onDuplicateNote,
  onExecuteNode,
  onExecuteDownstream,
  onRefreshTaskNode,
  onRefreshTasks,
  onRemoveEdge,
  onRemoveNode,
  onReturnFocus,
  onSelectNode,
  onUpdateNode,
  onUpdateNodeOutputs,
  refreshError,
  refreshingTasks,
  taskSyncError,
  taskSyncingNodeId,
}: {
  edges: ProductionCanvasEdge[];
  executionError?: string | null;
  executingNodeId?: string | null;
  node?: ProductionCanvasNode;
  nodes: ProductionCanvasNode[];
  onAddEdge: (edge: ProductionCanvasEdge) => void;
  onDuplicateNote: (nodeId: string) => void;
  onExecuteNode: (node: ProductionCanvasNode) => void;
  onExecuteDownstream: (node: ProductionCanvasNode) => void;
  onRefreshTaskNode: (node: ProductionCanvasNode) => void;
  onRefreshTasks: (nodes: ProductionCanvasNode[]) => void;
  onRemoveEdge: (edge: ProductionCanvasEdge) => void;
  onRemoveNode: (nodeId: string) => void;
  onReturnFocus: () => void;
  onSelectNode: (nodeId: string) => void;
  onUpdateNode: (nodeId: string, patch: Partial<ProductionCanvasNode>) => void;
  onUpdateNodeOutputs: NodeToolsProps["onUpdateNodeOutputs"];
  refreshError?: string | null;
  refreshingTasks?: boolean;
  taskSyncError?: string | null;
  taskSyncingNodeId?: string | null;
}) {
  return (
    <div className="space-y-3">
      <CanvasInspector
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
        edges={edges}
        node={node}
        nodes={nodes}
        onAddEdge={onAddEdge}
        onDuplicateNote={onDuplicateNote}
        onReturnFocus={onReturnFocus}
        onRefreshTasks={onRefreshTasks}
        onRemoveEdge={onRemoveEdge}
        onRemoveNode={onRemoveNode}
        onSelectNode={onSelectNode}
        onUpdateNode={onUpdateNode}
        onUpdateNodeOutputs={onUpdateNodeOutputs}
        refreshError={refreshError}
        refreshingTasks={refreshingTasks}
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
