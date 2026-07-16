import type { ProductionCanvasResolvedContext } from "@/utils/api/types";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import type { ProductionCanvasStateIdentity } from "./productionCanvasStateIdentity";

export type ProductionCanvasSkillPlannerProps = {
  currentRunId?: string | null;
  captureStateIdentity?: () => ProductionCanvasStateIdentity;
  getCurrentRunId?: () => string | null | undefined;
  nodes: ProductionCanvasNode[];
  onDomainContextResolved?: (
    context: ProductionCanvasResolvedContext,
    replace?: boolean,
  ) => void;
  onNodesCreated: (
    nodes: ProductionCanvasNode[],
    resolvedContext?: ProductionCanvasResolvedContext,
  ) => void;
  onRunCreated?: (runId: string) => void;
  operationBlocked?: boolean;
  taskMaxPollMs?: number;
  taskPollIntervalMs?: number;
};
