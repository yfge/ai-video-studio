import { operatorButtonClass } from "@/components/shared";
import {
  type ProductionCanvasContextDraft,
  type ProductionCanvasContextKey,
} from "./productionCanvasContext";
import {
  initialProductionCanvasSingleVideoDraft,
  type ProductionCanvasCreationMode,
  type ProductionCanvasSingleVideoDraft,
} from "./productionCanvasCreation";
import { useProductionCanvasAssetOptions } from "./useProductionCanvasAssetOptions";
import {
  ProductionCanvasSeriesFields,
  ProductionCanvasSingleVideoFields,
  type ProductionCanvasChatBarAssetOptions,
} from "./ProductionCanvasChatBarFields";

export function ProductionCanvasChatBar({
  assetOptions: providedAssetOptions,
  creationMode = "series",
  context,
  error,
  onCreate,
  onContextChange,
  onCreationModeChange = () => undefined,
  onPromptChange,
  onSingleVideoDraftChange = () => undefined,
  prompt,
  running,
  singleVideoDraft = initialProductionCanvasSingleVideoDraft,
}: {
  assetOptions?: ProductionCanvasChatBarAssetOptions;
  creationMode?: ProductionCanvasCreationMode;
  context: ProductionCanvasContextDraft;
  error?: string | null;
  onCreate: () => void;
  onContextChange: (key: ProductionCanvasContextKey, value: string) => void;
  onCreationModeChange?: (mode: ProductionCanvasCreationMode) => void;
  onPromptChange: (value: string) => void;
  onSingleVideoDraftChange?: (
    patch: Partial<ProductionCanvasSingleVideoDraft>,
  ) => void;
  prompt: string;
  running: boolean;
  singleVideoDraft?: ProductionCanvasSingleVideoDraft;
}) {
  const loadedAssetOptions = useProductionCanvasAssetOptions(
    providedAssetOptions === undefined,
  );
  const assetOptions = providedAssetOptions || loadedAssetOptions;
  const singleVideo = creationMode === "single_video";

  return (
    <div className="border-b border-gray-200 bg-white px-4 py-3">
      <div
        className="mb-3 inline-flex rounded-md border border-gray-200 bg-gray-50 p-0.5"
        aria-label="创建模式"
        role="group"
      >
        {(
          [
            ["single_video", "单条视频"],
            ["series", "系列制作"],
          ] as const
        ).map(([mode, label]) => (
          <button
            key={mode}
            type="button"
            aria-pressed={creationMode === mode}
            disabled={running}
            className={`h-7 rounded px-3 text-xs font-medium ${
              creationMode === mode
                ? "bg-white text-blue-700 shadow-sm"
                : "text-gray-500 hover:text-gray-900"
            }`}
            onClick={() => onCreationModeChange(mode)}
          >
            {label}
          </button>
        ))}
      </div>
      <div className="flex flex-col gap-2 lg:flex-row lg:items-end">
        <label className="min-w-0 flex-1">
          <span className="text-xs font-semibold text-gray-700">
            {singleVideo ? "视频目标" : "生产目标"}
          </span>
          <textarea
            aria-label={singleVideo ? "视频目标" : "生产目标"}
            value={prompt}
            onChange={(event) => onPromptChange(event.target.value)}
            onInput={(event) => onPromptChange(event.currentTarget.value)}
            placeholder={
              singleVideo
                ? "例如：用轻快科技感介绍一款桌面机器人，包含开场钩子、三项卖点和结尾行动号召"
                : "例如：基于林妹妹做第 4 集，办公室轻喜剧，生成完整短剧链路"
            }
            className="mt-1 min-h-16 w-full resize-none rounded-md border border-gray-200 bg-white px-3 py-2 text-xs leading-5 text-gray-800 placeholder:text-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
          />
        </label>
        <button
          type="button"
          aria-busy={running || undefined}
          className={operatorButtonClass("primary", "lg:mb-0.5")}
          disabled={running || !prompt.trim()}
          onClick={onCreate}
        >
          {running ? "执行中" : singleVideo ? "创建并生成" : "整体创建"}
        </button>
      </div>
      {singleVideo ? (
        <ProductionCanvasSingleVideoFields
          assetOptions={assetOptions}
          context={context}
          draft={singleVideoDraft}
          onContextChange={onContextChange}
          onDraftChange={onSingleVideoDraftChange}
        />
      ) : (
        <ProductionCanvasSeriesFields
          assetOptions={assetOptions}
          context={context}
          onContextChange={onContextChange}
        />
      )}
      {error || assetOptions.error ? (
        <div className="mt-2 text-xs text-red-600" role="alert">
          {error || assetOptions.error}
        </div>
      ) : null}
    </div>
  );
}
