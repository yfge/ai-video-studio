import { useState, type MutableRefObject } from "react";
import { storyAPI } from "@/utils/api/endpoints";
import type { ProductionCanvasResolvedContext } from "@/utils/api/types";
import { singleVideoProjectTitle } from "@/utils/singleVideoProject";
import {
  productionCanvasContextOutputs,
  productionCanvasRequestContext,
  type ProductionCanvasContextDraft,
} from "./productionCanvasContext";
import {
  initialProductionCanvasSingleVideoDraft,
  type ProductionCanvasCreationMode,
  type ProductionCanvasSingleVideoDraft,
} from "./productionCanvasCreation";
import type { ProductionCanvasExecutionPublication } from "./productionCanvasExecutionResults";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { createProductionCanvasPlan } from "./productionCanvasSkillExecution";
import { productionCanvasPlanNodeToCanvasNode } from "./productionCanvasSkillNodes";
import type { ProductionCanvasStateIdentity } from "./productionCanvasStateIdentity";

type ResolveContext = (
  context: ProductionCanvasResolvedContext,
  replace?: boolean,
) => void;

export function useProductionCanvasSingleVideoMode({
  contextRef,
  onDomainContextResolved,
  replaceContext,
  resetAutoExecution,
  running,
}: {
  contextRef: MutableRefObject<ProductionCanvasContextDraft>;
  onDomainContextResolved?: ResolveContext;
  replaceContext: (context: ProductionCanvasResolvedContext) => void;
  resetAutoExecution: () => void;
  running: boolean;
}) {
  const [creationMode, setCreationModeState] =
    useState<ProductionCanvasCreationMode>("series");
  const [singleVideoDraft, setSingleVideoDraft] =
    useState<ProductionCanvasSingleVideoDraft>(
      initialProductionCanvasSingleVideoDraft,
    );
  const setCreationMode = (nextMode: ProductionCanvasCreationMode) => {
    if (nextMode === creationMode || running) return;
    setCreationModeState(nextMode);
    resetAutoExecution();
    const current = productionCanvasRequestContext(contextRef.current);
    const assetContext: ProductionCanvasResolvedContext = {
      virtual_ip_id: current.virtual_ip_id,
      environment_id: current.environment_id,
    };
    replaceContext(assetContext);
    onDomainContextResolved?.(assetContext, true);
  };
  return {
    creationMode,
    setCreationMode,
    singleVideoDraft,
    updateSingleVideoDraft: (
      patch: Partial<ProductionCanvasSingleVideoDraft>,
    ) => setSingleVideoDraft((current) => ({ ...current, ...patch })),
  };
}

export async function runSingleVideoCanvasCreation({
  captureIdentity,
  contextRef,
  draft,
  executeScript,
  isCurrent,
  onDomainContextResolved,
  onIdentityChange,
  onNodesCreated,
  onRunCreated,
  prompt,
  publish,
  replaceContext,
  setExecutingNodeId,
}: {
  captureIdentity: () => ProductionCanvasStateIdentity;
  contextRef: MutableRefObject<ProductionCanvasContextDraft>;
  draft: ProductionCanvasSingleVideoDraft;
  executeScript: (
    node: ProductionCanvasNode,
    nodes: ProductionCanvasNode[],
    runId?: string | null,
  ) => Promise<ProductionCanvasExecutionPublication[] | null>;
  isCurrent: (identity: ProductionCanvasStateIdentity) => boolean;
  onDomainContextResolved?: ResolveContext;
  onIdentityChange: (identity: ProductionCanvasStateIdentity) => void;
  onNodesCreated: (
    nodes: ProductionCanvasNode[],
    context?: ProductionCanvasResolvedContext,
  ) => void;
  onRunCreated?: (runId: string) => void;
  prompt: string;
  publish: (
    publication: ProductionCanvasExecutionPublication,
    runId: string | null | undefined,
    identity: ProductionCanvasStateIdentity,
  ) => void;
  replaceContext: (context: ProductionCanvasResolvedContext) => void;
  setExecutingNodeId: (nodeId: string | null) => void;
}) {
  let identity = captureIdentity();
  const selectedAssets = productionCanvasRequestContext(contextRef.current);
  const project = await storyAPI.createSingleVideoProject({
    title: singleVideoProjectTitle(draft.title, prompt),
    prompt,
    duration_minutes: draft.durationMinutes,
    aspect_ratio: draft.aspectRatio,
    style: draft.style.trim() || undefined,
    virtual_ip_id: selectedAssets.virtual_ip_id ?? undefined,
    environment_id: selectedAssets.environment_id ?? undefined,
    start_generation: false,
  });
  if (!project.success || !project.data) {
    throw new Error(project.error || "单条视频项目创建失败");
  }
  if (!isCurrent(identity)) return;
  replaceContext(project.data.context);
  onDomainContextResolved?.(project.data.context, true);

  const plan = await createProductionCanvasPlan(
    prompt,
    contextRef.current,
    "single_video",
  );
  if (!isCurrent(identity)) return;
  if (plan.run_id) {
    onRunCreated?.(plan.run_id);
    identity = captureIdentity();
    onIdentityChange(identity);
  }
  const resolvedContext = plan.resolved_context || project.data.context;
  replaceContext(resolvedContext);
  onDomainContextResolved?.(resolvedContext, true);
  const contextOutputs = productionCanvasContextOutputs(resolvedContext);
  const nodes = plan.nodes.map((node) =>
    productionCanvasPlanNodeToCanvasNode(node, plan, contextOutputs),
  );
  onNodesCreated(nodes, resolvedContext);

  const scriptNode = nodes.find((node) => node.skill === "script.generate");
  if (!scriptNode || scriptNode.status !== "ready") {
    throw new Error("单条视频项目缺少可执行的剧本生成节点");
  }
  setExecutingNodeId(scriptNode.id);
  const publications = await executeScript(scriptNode, nodes, plan.run_id);
  if (!publications || !isCurrent(identity)) return;
  publications.forEach((publication) =>
    publish(publication, plan.run_id, identity),
  );
}
