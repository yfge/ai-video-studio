import { productionCanvasAPI } from "@/utils/api/endpoints";
import {
  productionCanvasRequestContext,
  type ProductionCanvasContextDraft,
} from "./productionCanvasContext";
import type { ProductionCanvasBriefOverrides } from "@/utils/api/types";
import { productionCanvasExecutionPublications } from "./productionCanvasExecutionResults";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { productionCanvasSkillExecuteRequest } from "./productionCanvasSkillRequest";

export async function createProductionCanvasPlan(
  prompt: string,
  context: ProductionCanvasContextDraft,
  planningMode: "series" | "single_video" = "series",
  options: {
    briefOverrides?: ProductionCanvasBriefOverrides;
    clarificationAnswers?: Record<string, string>;
  } = {},
) {
  const response = await productionCanvasAPI.createPlan({
    prompt,
    ...(planningMode === "single_video" ? { planning_mode: planningMode } : {}),
    brief_overrides: options.briefOverrides,
    clarification_answers: options.clarificationAnswers,
    ...productionCanvasRequestContext(context),
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || "整体创建失败");
  }
  return response.data;
}

export async function executeProductionCanvasSkill({
  context,
  currentRunId,
  executionScope,
  fallbackPrompt,
  node,
  nodes,
  prompt,
  targetRunId,
}: {
  context: ProductionCanvasContextDraft;
  currentRunId?: string | null;
  executionScope: "node" | "downstream";
  fallbackPrompt?: string;
  node: ProductionCanvasNode;
  nodes: ProductionCanvasNode[];
  prompt: string;
  targetRunId?: string | null;
}) {
  const response = await productionCanvasAPI.executeSkill(
    productionCanvasSkillExecuteRequest({
      context,
      currentRunId,
      executionScope,
      fallbackPrompt,
      node,
      prompt,
      targetRunId,
    }),
  );
  if (!response.success || !response.data) {
    throw new Error(response.error || "Skill 执行失败");
  }
  return productionCanvasExecutionPublications(response.data, node, nodes);
}
