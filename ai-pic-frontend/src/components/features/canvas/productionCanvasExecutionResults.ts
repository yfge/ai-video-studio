import type {
  ProductionCanvasNodeExecutionResponse,
  ProductionCanvasSkillExecuteResponse,
} from "@/utils/api/types";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import {
  productionCanvasSkillResultToNode,
  productionCanvasSkillResultToTaskNode,
} from "./productionCanvasSkillNodes";

export type ProductionCanvasExecutionPublication = {
  sourceNode: ProductionCanvasNode;
  resultNodes: ProductionCanvasNode[];
};

export function productionCanvasExecutionPublications(
  response: ProductionCanvasSkillExecuteResponse,
  requestedNode: ProductionCanvasNode,
  nodes: ProductionCanvasNode[],
): ProductionCanvasExecutionPublication[] {
  const executions: ProductionCanvasNodeExecutionResponse[] = response
    .executions?.length
    ? response.executions
    : [response];
  return executions.map((execution) => {
    const sourceNode =
      nodes.find((node) => node.id === execution.node_id) || requestedNode;
    const skillNode = productionCanvasSkillResultToNode(
      sourceNode,
      execution.skill_result,
    );
    const taskNode = productionCanvasSkillResultToTaskNode(
      sourceNode,
      execution.skill_result,
      execution,
    );
    return {
      sourceNode,
      resultNodes: taskNode ? [skillNode, taskNode] : [skillNode],
    };
  });
}
