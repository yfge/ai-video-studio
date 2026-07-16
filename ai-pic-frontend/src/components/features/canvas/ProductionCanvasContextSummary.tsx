import type { ProductionCanvasContextDraft } from "./productionCanvasContext";
import type { ProductionCanvasSingleVideoDraft } from "./productionCanvasCreation";
import type { ProductionCanvasChatBarAssetOptions } from "./ProductionCanvasChatBarFields";

function optionName(
  options: Array<{ id: number; name: string }> | undefined,
  value: string,
  fallback = "可选",
) {
  if (!value) return fallback;
  return (
    options?.find((option) => String(option.id) === value)?.name || `#${value}`
  );
}

export function ProductionCanvasContextSummary({
  assetOptions,
  context,
  singleVideo,
  singleVideoDraft,
}: {
  assetOptions: ProductionCanvasChatBarAssetOptions;
  context: ProductionCanvasContextDraft;
  singleVideo: boolean;
  singleVideoDraft: ProductionCanvasSingleVideoDraft;
}) {
  const items = singleVideo
    ? [
        ["IP", optionName(assetOptions.virtualIPs, context.virtual_ip_id)],
        ["风格", singleVideoDraft.style || "可选"],
        ["时长", `${singleVideoDraft.durationMinutes} 分钟`],
        ["画幅", singleVideoDraft.aspectRatio],
        ["环境", optionName(assetOptions.environments, context.environment_id)],
      ]
    : [
        ["IP", optionName(assetOptions.virtualIPs, context.virtual_ip_id)],
        ["环境", optionName(assetOptions.environments, context.environment_id)],
        [
          "剧集",
          optionName(assetOptions.episodes, context.episode_id, "待选择"),
        ],
        ["剧本", optionName(assetOptions.scripts, context.script_id)],
        ["任务", context.task_id ? `#${context.task_id}` : "报告证据"],
      ];

  return (
    <span className="flex min-w-0 flex-1 flex-wrap items-center gap-x-5 gap-y-2">
      {items.map(([label, value]) => (
        <span
          key={label}
          className="inline-flex min-w-0 items-center gap-1.5 text-[13px] text-slate-500"
        >
          <span className="font-medium text-slate-600">{label}</span>
          <span className="max-w-36 truncate text-slate-700">{value}</span>
        </span>
      ))}
    </span>
  );
}
