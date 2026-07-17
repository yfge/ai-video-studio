import { useState, type MutableRefObject } from "react";
import type {
  ProductionCanvasBriefOverrides,
  ProductionCanvasProductionContext,
  ProductionCanvasResolvedContext,
} from "@/utils/api/types";
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
  briefOverrides,
  clarificationAnswers,
  executeScript,
  isCurrent,
  onDomainContextResolved,
  onIdentityChange,
  onNodesCreated,
  onRunCreated,
  onProductionContext,
  prompt,
  publish,
  replaceContext,
  setExecutingNodeId,
}: {
  captureIdentity: () => ProductionCanvasStateIdentity;
  contextRef: MutableRefObject<ProductionCanvasContextDraft>;
  draft: ProductionCanvasSingleVideoDraft;
  briefOverrides: ProductionCanvasBriefOverrides;
  clarificationAnswers: Record<string, string>;
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
  onProductionContext: (
    context: ProductionCanvasProductionContext | null,
  ) => void;
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
  const plan = await createProductionCanvasPlan(
    prompt,
    contextRef.current,
    "single_video",
    {
      briefOverrides: {
        ...briefOverrides,
        title: draft.title.trim() || briefOverrides.title,
      },
      clarificationAnswers,
    },
  );
  if (!isCurrent(identity)) return;
  onProductionContext(plan.production_context || null);
  if (plan.run_id) {
    onRunCreated?.(plan.run_id);
    identity = captureIdentity();
    onIdentityChange(identity);
  }
  const resolvedContext = plan.resolved_context || {};
  replaceContext(resolvedContext);
  onDomainContextResolved?.(resolvedContext, true);
  const contextOutputs = productionCanvasContextOutputs(resolvedContext);
  const nodes = plan.nodes.map((node) =>
    productionCanvasPlanNodeToCanvasNode(node, plan, contextOutputs),
  );
  onNodesCreated(nodes, resolvedContext);
  if (!plan.production_context?.brief.ready_for_execution) return;

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
