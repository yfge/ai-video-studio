import { productionCanvasAPI } from "@/utils/api/endpoints";
import {
  productionCanvasRequestContext,
  type ProductionCanvasContextDraft,
} from "./productionCanvasContext";
import { productionCanvasExecutionPublications } from "./productionCanvasExecutionResults";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { productionCanvasSkillExecuteRequest } from "./productionCanvasSkillRequest";

export async function createProductionCanvasPlan(
  prompt: string,
  context: ProductionCanvasContextDraft,
) {
  const response = await productionCanvasAPI.createPlan({
    prompt,
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
