export type ScriptTabId = "overview" | "scenes" | "traffic";

export const SCRIPT_TABS: Array<{ id: ScriptTabId; name: string; description: string }> = [
  { id: "overview", name: "概览", description: "剧本文本与统计" },
  { id: "scenes", name: "场景", description: "按场景查看对白与指令" },
  { id: "traffic", name: "投流/评分", description: "爽点评分与素材清单" },
];
