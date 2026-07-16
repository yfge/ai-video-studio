import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { OperatorPanel, operatorButtonClass } from "@/components/shared";
import type {
  ProductionCanvasContextDraft,
  ProductionCanvasContextKey,
} from "./productionCanvasContext";
import { afterProductionCanvasPaint } from "./productionCanvasBusyPaint";
import {
  findHierarchyAncestors,
  hierarchyContextPatch,
} from "./productionCanvasHierarchyModel";
import { visibleEnvironmentReferenceEdges } from "./productionCanvasHierarchyReferences";
import { ProductionCanvasHierarchySidebar } from "./ProductionCanvasHierarchySidebar";
import { ProductionCanvasHierarchyControls } from "./ProductionCanvasHierarchyControls";
import {
  ProductionCanvasHierarchySurface,
  type ProductionCanvasHierarchySurfaceHandle,
} from "./ProductionCanvasHierarchySurface";
import { useProductionCanvasHierarchy } from "./useProductionCanvasHierarchy";
import type { ProductionCanvasHierarchySyncRequest } from "./productionCanvasHierarchyReveal";

export function ProductionCanvasHierarchyView({
  context,
  isActive = true,
  onContextChange,
  syncRequest,
}: {
  context: ProductionCanvasContextDraft;
  isActive?: boolean;
  onContextChange: (key: ProductionCanvasContextKey, value: string) => void;
  syncRequest?: ProductionCanvasHierarchySyncRequest;
}) {
  const hierarchy = useProductionCanvasHierarchy();
  const { cancelPendingReveal, refreshAndReveal } = hierarchy;
  const surfaceRef = useRef<ProductionCanvasHierarchySurfaceHandle | null>(
    null,
  );
  const [selectedNodeId, setSelectedNodeId] = useState("");
  const [showReferences, setShowReferences] = useState(false);
  const appliedRevision = useRef(0);
  const selectionRevision = useRef(0);
  const pendingFocusNodeId = useRef("");
  const projection = useMemo(
    () => ({
      ...hierarchy.projection,
      edges: showReferences
        ? [
            ...hierarchy.projection.edges,
            ...visibleEnvironmentReferenceEdges(
              hierarchy.graph,
              hierarchy.projection,
            ),
          ]
        : hierarchy.projection.edges,
    }),
    [hierarchy.graph, hierarchy.projection, showReferences],
  );
  const selectedNode = hierarchy.graph.nodes.find(
    (node) => node.id === selectedNodeId,
  );

  useEffect(() => {
    if (!syncRequest || syncRequest.revision <= appliedRevision.current) return;
    const revision = syncRequest.revision;
    const currentSelectionRevision = selectionRevision.current;
    appliedRevision.current = revision;
    pendingFocusNodeId.current = "";
    setSelectedNodeId("");
    void refreshAndReveal(syncRequest.context).then((targetNodeId) => {
      if (
        !targetNodeId ||
        appliedRevision.current !== revision ||
        selectionRevision.current !== currentSelectionRevision
      )
        return;
      pendingFocusNodeId.current = targetNodeId;
      setSelectedNodeId(targetNodeId);
    });
  }, [refreshAndReveal, syncRequest]);

  useEffect(() => {
    const targetNodeId = pendingFocusNodeId.current;
    if (
      !isActive ||
      !targetNodeId ||
      selectedNodeId !== targetNodeId ||
      !hierarchy.projection.nodes.some((node) => node.id === targetNodeId)
    ) {
      return;
    }
    pendingFocusNodeId.current = "";
    afterProductionCanvasPaint(
      () => surfaceRef.current?.focusNode(targetNodeId),
    );
  }, [hierarchy.projection.nodes, isActive, selectedNodeId]);

  useEffect(() => {
    if (
      !hierarchy.graph.nodes.length ||
      hierarchy.graph.nodes.some((node) => node.id === selectedNodeId)
    ) {
      return;
    }
    const preferredId = context.virtual_ip_id
      ? `ip:${context.virtual_ip_id}`
      : "";
    const root =
      hierarchy.graph.nodes.find((node) => node.id === preferredId) ||
      hierarchy.graph.nodes.find((node) => node.entityType === "ip");
    if (root) setSelectedNodeId(root.id);
  }, [context.virtual_ip_id, hierarchy.graph.nodes, selectedNodeId]);

  const syncExecutionContext = useCallback(
    (nodeId: string, preferredVirtualIpId?: number) => {
      const node = hierarchy.graph.nodes.find((item) => item.id === nodeId);
      if (!node || node.empty) return;
      const patch = hierarchyContextPatch(
        hierarchy.graph,
        nodeId,
        preferredVirtualIpId || Number(context.virtual_ip_id) || undefined,
      );
      const setValue = (key: ProductionCanvasContextKey, value: string) => {
        onContextChange(key, value);
      };
      const nextVirtualIpId = patch.virtual_ip_id
        ? String(patch.virtual_ip_id)
        : "";
      const keepEnvironment =
        node.entityType !== "environment" &&
        nextVirtualIpId !== "" &&
        nextVirtualIpId === context.virtual_ip_id;
      const nextEnvironmentId = patch.environment_id
        ? String(patch.environment_id)
        : keepEnvironment
        ? context.environment_id
        : "";
      setValue("virtual_ip_id", nextVirtualIpId);
      setValue("environment_id", nextEnvironmentId);
      for (const key of [
        "story_id",
        "episode_id",
        "script_id",
        "timeline_id",
        "timeline_version",
        "clip_id",
      ] as const) {
        const value = patch[key];
        setValue(key, value === undefined ? "" : String(value));
      }
    },
    [context, hierarchy.graph, onContextChange],
  );

  const selectNode = useCallback(
    (nodeId: string, focus: boolean, preferredVirtualIpId?: number) => {
      selectionRevision.current += 1;
      cancelPendingReveal();
      setSelectedNodeId(nodeId);
      syncExecutionContext(nodeId, preferredVirtualIpId);
      if (focus) {
        afterProductionCanvasPaint(() => surfaceRef.current?.focusNode(nodeId));
      }
    },
    [cancelPendingReveal, syncExecutionContext],
  );

  const toggleNode = useCallback(
    (nodeId: string) => {
      if (
        hierarchy.expandedIds.has(nodeId) &&
        selectedNodeId &&
        selectedNodeId !== nodeId &&
        findHierarchyAncestors(hierarchy.graph, selectedNodeId).some(
          (ancestor) => ancestor.id === nodeId,
        )
      ) {
        selectNode(nodeId, false);
      }
      hierarchy.toggleNode(nodeId);
    },
    [hierarchy, selectNode, selectedNodeId],
  );

  if (hierarchy.rootLoading && !hierarchy.graph.nodes.length) {
    return (
      <OperatorPanel className="flex h-[560px] items-center justify-center text-sm text-slate-500">
        正在加载 IP 业务层级…
      </OperatorPanel>
    );
  }

  if (hierarchy.rootError && !hierarchy.graph.nodes.length) {
    return (
      <OperatorPanel className="flex h-[360px] flex-col items-center justify-center gap-3 p-6 text-center">
        <div className="text-sm font-semibold text-red-700">
          业务层级加载失败
        </div>
        <p className="text-xs text-slate-500" role="alert">
          {hierarchy.rootError}
        </p>
        <button
          className={operatorButtonClass("secondary")}
          type="button"
          onClick={hierarchy.refresh}
        >
          重新加载
        </button>
      </OperatorPanel>
    );
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
      <OperatorPanel className="overflow-hidden">
        <ProductionCanvasHierarchyControls
          onRefresh={hierarchy.refresh}
          onShowReferencesChange={setShowReferences}
          showReferences={showReferences}
        />
        <ProductionCanvasHierarchySurface
          ref={surfaceRef}
          errors={hierarchy.errors}
          expandedIds={hierarchy.expandedIds}
          loadingIds={hierarchy.loadingIds}
          projection={projection}
          selectedNodeId={selectedNodeId}
          onSelectNode={(nodeId) => selectNode(nodeId, false)}
          onToggleNode={toggleNode}
        />
      </OperatorPanel>
      <ProductionCanvasHierarchySidebar
        expandedIds={hierarchy.expandedIds}
        loadingIds={hierarchy.loadingIds}
        projection={projection}
        selectedNode={selectedNode}
        selectedNodeId={selectedNodeId}
        warning={hierarchy.warning}
        onSelect={(nodeId, preferredVirtualIpId) =>
          selectNode(nodeId, true, preferredVirtualIpId)
        }
        onToggle={toggleNode}
      />
    </div>
  );
}
