import type { ReactNode } from "react";
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
import { ProductionCanvasContextSummary } from "./ProductionCanvasContextSummary";
import { ProductionCanvasClarifications } from "./ProductionCanvasClarifications";
import { ProductionCanvasPlanningSettingsFields } from "./ProductionCanvasPlanningSettingsFields";
import type { ProductionCanvasPlanningSettings } from "./productionCanvasPlanningSettings";
import type { ProductionCanvasProductionContext } from "@/utils/api/types";

export function ProductionCanvasChatBar({
  advancedControls,
  assetOptions: providedAssetOptions,
  creationMode = "series",
  context,
  error,
  onCreate,
  onContextChange,
  onCreationModeChange = () => undefined,
  onPromptChange,
  onClarificationAnswer = () => undefined,
  onPlanningSettingsChange = () => undefined,
  onSingleVideoDraftChange = () => undefined,
  planningSettings,
  productionContext,
  clarificationAnswers = {},
  prompt,
  running,
  singleVideoDraft = initialProductionCanvasSingleVideoDraft,
}: {
  advancedControls?: ReactNode;
  assetOptions?: ProductionCanvasChatBarAssetOptions;
  creationMode?: ProductionCanvasCreationMode;
  context: ProductionCanvasContextDraft;
  error?: string | null;
  onCreate: () => void;
  onContextChange: (key: ProductionCanvasContextKey, value: string) => void;
  onCreationModeChange?: (mode: ProductionCanvasCreationMode) => void;
  onPromptChange: (value: string) => void;
  onClarificationAnswer?: (id: string, value: string) => void;
  onPlanningSettingsChange?: (
    patch: Partial<ProductionCanvasPlanningSettings>,
  ) => void;
  onSingleVideoDraftChange?: (
    patch: Partial<ProductionCanvasSingleVideoDraft>,
  ) => void;
  prompt: string;
  planningSettings: ProductionCanvasPlanningSettings;
  productionContext?: ProductionCanvasProductionContext | null;
  clarificationAnswers?: Record<string, string>;
  running: boolean;
  singleVideoDraft?: ProductionCanvasSingleVideoDraft;
}) {
  const loadedAssetOptions = useProductionCanvasAssetOptions(
    providedAssetOptions === undefined,
  );
  const assetOptions = providedAssetOptions || loadedAssetOptions;
  const singleVideo = creationMode === "single_video";
  const pendingQuestions =
    productionContext?.brief.clarifications.filter(
      (item) => item.required && !item.answer,
    ) || [];
  const answersComplete = pendingQuestions.every(
    (item) => clarificationAnswers[item.id]?.trim(),
  );

  return (
    <div className="bg-white p-4 sm:p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div
          className="inline-flex rounded-md bg-slate-100 p-0.5"
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
              className={`h-8 rounded px-3 text-[13px] font-medium transition ${
                creationMode === mode
                  ? "bg-white text-blue-700 shadow-sm"
                  : "text-slate-500 hover:text-slate-900"
              }`}
              onClick={() => onCreationModeChange(mode)}
            >
              {label}
            </button>
          ))}
        </div>
        {advancedControls}
      </div>
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end">
        <label className="min-w-0 flex-1">
          <span className="text-[13px] font-semibold text-slate-700">
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
            className="mt-1.5 min-h-[72px] w-full resize-none rounded-lg border border-slate-200 bg-white px-3.5 py-3 text-sm leading-6 text-slate-800 placeholder:text-slate-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
          />
        </label>
        <button
          type="button"
          aria-busy={running || undefined}
          className={operatorButtonClass(
            "primary",
            "h-11 px-5 text-sm lg:mb-0.5 lg:min-w-32",
          )}
          disabled={
            running ||
            !prompt.trim() ||
            (pendingQuestions.length > 0 && !answersComplete)
          }
          onClick={onCreate}
        >
          {running
            ? "执行中"
            : pendingQuestions.length
            ? "补充并重新规划"
            : singleVideo
            ? "创建并生成"
            : "整体创建"}
        </button>
      </div>
      <details
        className="group mt-3 border-t border-slate-100 pt-3"
        name="production-canvas-popover"
      >
        <summary
          aria-label="更多生产参数"
          className="flex cursor-pointer list-none items-center gap-4 rounded-md py-1 focus:outline-none focus:ring-2 focus:ring-blue-100 [&::-webkit-details-marker]:hidden"
        >
          <ProductionCanvasContextSummary
            assetOptions={assetOptions}
            context={context}
            singleVideo={singleVideo}
            settings={planningSettings}
          />
          <span className="shrink-0 text-[13px] font-medium text-slate-600 group-open:text-blue-700">
            <span className="group-open:hidden">更多</span>
            <span className="hidden group-open:inline">收起</span>
          </span>
        </summary>
        <div className="mt-3 border-t border-slate-100 pt-3">
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
          <ProductionCanvasPlanningSettingsFields
            mode={creationMode}
            settings={planningSettings}
            onChange={onPlanningSettingsChange}
          />
        </div>
      </details>
      <ProductionCanvasClarifications
        answers={clarificationAnswers}
        context={productionContext}
        onAnswer={onClarificationAnswer}
      />
      {error || assetOptions.error ? (
        <div className="mt-3 text-sm text-red-600" role="alert">
          {error || assetOptions.error}
        </div>
      ) : null}
    </div>
  );
}
