import { useEffect, useRef, type MutableRefObject } from "react";
import type { ProductionCanvasResolvedContext } from "@/utils/api/types";
import { executeProductionCanvasReadyNodes } from "./productionCanvasAutoExecution";
import type { ProductionCanvasContextDraft } from "./productionCanvasContext";
import type { ProductionCanvasExecutionPublication } from "./productionCanvasExecutionResults";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { executeProductionCanvasSkill } from "./productionCanvasSkillExecution";
import type { ProductionCanvasStateIdentity } from "./productionCanvasStateIdentity";

type AutoContinuation = {
  prompt: string;
  runId?: string | null;
};

type RunGuard = {
  capture: () => ProductionCanvasStateIdentity;
  isCurrent: (identity: ProductionCanvasStateIdentity) => boolean;
};

type PublishExecutionNodes = (
  sourceNode: ProductionCanvasNode,
  resultNodes: ProductionCanvasNode[],
  runId: string | null | undefined,
  operationEpoch: number,
  resolvedContext: ProductionCanvasResolvedContext,
) => void;

export function useProductionCanvasExecutionActions({
  autoContinuationPendingRef,
  autoContinuationRef,
  autoExecutionActiveRef,
  contextRef,
  executingNodeId,
  nodes,
  operationBlocked,
  onAutoExecutingNode,
  prompt,
  publishExecutionNodes,
  runGuard,
  setError,
  setExecutingNodeId,
  setExecutionError,
}: {
  autoContinuationPendingRef: MutableRefObject<boolean>;
  autoContinuationRef: MutableRefObject<AutoContinuation | null>;
  autoExecutionActiveRef: MutableRefObject<boolean>;
  contextRef: MutableRefObject<ProductionCanvasContextDraft>;
  executingNodeId: string | null;
  nodes: ProductionCanvasNode[];
  operationBlocked: boolean;
  onAutoExecutingNode?: (node: ProductionCanvasNode) => void;
  prompt: string;
  publishExecutionNodes: PublishExecutionNodes;
  runGuard: RunGuard;
  setError: (message: string | null) => void;
  setExecutingNodeId: (nodeId: string | null) => void;
  setExecutionError: (
    error: { message: string; nodeId: string } | null,
  ) => void;
}) {
  const nodesRef = useRef(nodes);
  nodesRef.current = nodes;
  const continueAutoExecutionRef = useRef<() => void>(() => undefined);

  const executeSkillRequest = async (
    node: ProductionCanvasNode,
    fallbackPrompt?: string,
    executionScope: "node" | "downstream" = "node",
    targetRunId?: string | null,
    executionNodes: ProductionCanvasNode[] = nodesRef.current,
  ): Promise<ProductionCanvasExecutionPublication[] | null> => {
    const identity = runGuard.capture();
    try {
      const publications = await executeProductionCanvasSkill({
        context: contextRef.current,
        currentRunId: identity.runId,
        executionScope,
        fallbackPrompt,
        node,
        nodes: executionNodes,
        prompt,
        targetRunId,
      });
      return runGuard.isCurrent(identity) ? publications : null;
    } catch (error) {
      if (!runGuard.isCurrent(identity)) return null;
      throw error;
    }
  };

  const continueAutoExecution = async (initialNodes = nodesRef.current) => {
    const continuation = autoContinuationRef.current;
    if (!continuation || autoExecutionActiveRef.current || operationBlocked)
      return;
    autoExecutionActiveRef.current = true;
    try {
      await executeProductionCanvasReadyNodes({
        initialNodes,
        onExecuting: (node) => {
          setExecutingNodeId(node.id);
          onAutoExecutingNode?.(node);
        },
        execute: (node) =>
          executeSkillRequest(
            node,
            continuation.prompt,
            "node",
            continuation.runId,
          ),
        publish: (publication) => {
          const identity = runGuard.capture();
          publishExecutionNodes(
            publication.sourceNode,
            publication.resultNodes,
            continuation.runId,
            identity.epoch,
            publication.resolvedContext,
          );
        },
      });
    } catch (error) {
      setError(error instanceof Error ? error.message : String(error));
    } finally {
      autoExecutionActiveRef.current = false;
      setExecutingNodeId(null);
    }
  };
  continueAutoExecutionRef.current = () => void continueAutoExecution();
  useEffect(() => {
    if (!autoContinuationPendingRef.current) return;
    autoContinuationPendingRef.current = false;
    continueAutoExecutionRef.current();
  });

  const executeSkillNode = async (
    node: ProductionCanvasNode,
    executionScope: "node" | "downstream" = "node",
  ) => {
    if (!node.skill || executingNodeId || operationBlocked) return;
    const identity = runGuard.capture();
    setExecutingNodeId(node.id);
    setExecutionError(null);
    try {
      const publications = await executeSkillRequest(
        node,
        undefined,
        executionScope,
      );
      if (!publications) return;
      publications.forEach((publication) =>
        publishExecutionNodes(
          publication.sourceNode,
          publication.resultNodes,
          identity.runId,
          identity.epoch,
          publication.resolvedContext,
        ),
      );
    } catch (error) {
      if (runGuard.isCurrent(identity)) {
        setExecutionError({
          message: error instanceof Error ? error.message : String(error),
          nodeId: node.id,
        });
      }
    } finally {
      if (runGuard.isCurrent(identity)) setExecutingNodeId(null);
    }
  };

  return { continueAutoExecution, executeSkillNode, executeSkillRequest };
}
