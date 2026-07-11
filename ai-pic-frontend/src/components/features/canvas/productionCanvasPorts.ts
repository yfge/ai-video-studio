import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
  ProductionCanvasPort,
} from "./productionCanvasModel";

type PortContract = {
  inputs?: ProductionCanvasPort[];
  outputs?: ProductionCanvasPort[];
};

const port = (
  id: string,
  label: string,
  type: ProductionCanvasPort["type"],
  required = false,
): ProductionCanvasPort => ({ id, label, type, required });

const skillContracts: Record<string, PortContract> = {
  "brief.compose": { outputs: [port("production_brief", "生产简报", "text")] },
  "asset.select": {
    inputs: [port("production_brief", "生产简报", "text")],
    outputs: [port("selected_assets", "选中资产", "entity_ref")],
  },
  "virtual_ip.image": {
    inputs: [port("virtual_ip", "角色资产", "entity_ref", true)],
    outputs: [port("character_image", "角色图片", "image")],
  },
  "environment.image": {
    inputs: [port("environment", "环境资产", "entity_ref", true)],
    outputs: [port("environment_image", "环境图片", "image")],
  },
  "script.generate": {
    inputs: [port("production_brief", "生产简报", "text", true)],
    outputs: [port("script", "剧本", "entity_ref")],
  },
  "timeline.assemble": {
    inputs: [port("script", "剧本", "entity_ref", true)],
    outputs: [port("timeline", "时间线", "entity_ref")],
  },
  "storyboard.plan": {
    inputs: [port("script", "剧本", "entity_ref", true)],
    outputs: [port("storyboard_frame", "分镜帧", "image")],
  },
  "image.candidates": {
    inputs: [port("script", "剧本", "entity_ref", true)],
    outputs: [port("approved_image", "选用图片", "image")],
  },
  "video.candidates": {
    inputs: [port("start_frame", "起始帧", "image", true)],
    outputs: [port("approved_video", "选用视频", "video")],
  },
  "timeline.render": {
    inputs: [port("timeline", "时间线", "entity_ref", true)],
    outputs: [port("rendered_video", "渲染视频", "video")],
  },
  "timeline.export": {
    inputs: [port("rendered_video", "渲染视频", "video", true)],
    outputs: [port("exported_video", "导出成片", "video")],
  },
  "report.summarize": {
    inputs: [port("execution", "执行证据", "execution_ref", true)],
    outputs: [port("report", "汇总报告", "execution_ref")],
  },
};

const genericContract: PortContract = {
  inputs: [port("input", "输入", "text")],
  outputs: [port("output", "输出", "text")],
};

export function productionCanvasPortContract(node: ProductionCanvasNode) {
  if (node.kind === "note") return {};
  const contract =
    (node.skill && skillContracts[node.skill]) || genericContract;
  const hasExplicitPorts =
    node.inputPorts !== undefined || node.outputPorts !== undefined;
  return {
    definitionVersion: node.definitionVersion || 1,
    inputPorts: hasExplicitPorts
      ? node.inputPorts || []
      : contract.inputs || [],
    outputPorts: hasExplicitPorts
      ? node.outputPorts || []
      : contract.outputs || [],
  };
}

export function withProductionCanvasPortContract(
  node: ProductionCanvasNode,
): ProductionCanvasNode {
  return { ...node, ...productionCanvasPortContract(node) };
}

export function compatibleProductionCanvasEdges(
  source: ProductionCanvasNode,
  target: ProductionCanvasNode,
  edges: ProductionCanvasEdge[],
) {
  if (
    source.id === target.id ||
    source.kind === "note" ||
    target.kind === "note"
  ) {
    return [];
  }
  if (
    edges.some(
      (edge) =>
        edge.from === source.id && edge.to === target.id && !edge.fromPort,
    )
  ) {
    return [];
  }
  const sourcePorts = productionCanvasPortContract(source).outputPorts || [];
  const targetPorts = productionCanvasPortContract(target).inputPorts || [];
  const candidates: ProductionCanvasEdge[] = [];
  for (const sourcePort of sourcePorts) {
    for (const targetPort of targetPorts) {
      if (sourcePort.type !== targetPort.type) continue;
      const existing = edges.filter(
        (edge) => edge.to === target.id && edge.toPort === targetPort.id,
      );
      if (!targetPort.multiple && existing.length) continue;
      if (
        edges.some(
          (edge) =>
            edge.from === source.id &&
            edge.fromPort === sourcePort.id &&
            edge.to === target.id &&
            edge.toPort === targetPort.id,
        )
      )
        continue;
      candidates.push({
        edgeId: `${source.id}-${sourcePort.id}-to-${target.id}-${targetPort.id}`,
        from: source.id,
        fromPort: sourcePort.id,
        to: target.id,
        toPort: targetPort.id,
        bindingType: sourcePort.id.startsWith("approved_")
          ? "selected_output"
          : "value",
        required: Boolean(targetPort.required),
        ...(targetPort.multiple ? { bindingOrder: existing.length } : {}),
      });
    }
  }
  return candidates;
}

export function isTypedProductionCanvasEdge(edge: ProductionCanvasEdge) {
  return Boolean(
    edge.edgeId && edge.fromPort && edge.toPort && edge.bindingType,
  );
}
