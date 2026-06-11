"use client";

import type { Episode, Script } from "@/utils/api/types";
import {
  OperatorPanel,
  StatusPill,
  operatorButtonClass,
  operatorSelectClass,
} from "@/components/shared";
import {
  buildEpisodeProductionState,
  productionStatusLabel,
  productionStatusTone,
  scriptOptionLabel,
  type ProductionActionKind,
  type WorkflowStatus,
} from "./EpisodeWorkspaceProductionState";
import type { TabKey } from "@/hooks/episode/useEpisodeWorkspaceController";

export type { WorkflowStatus } from "./EpisodeWorkspaceProductionState";

interface EpisodeWorkspaceHeaderProps {
  episode: Episode;
  script?: Script | null;
  scripts: Script[];
  selectedScriptId: number | null;
  workflowStatus: WorkflowStatus;
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
  onNavigateBack: () => void;
  onGenerateScript?: () => void;
  onGenerateTimeline?: () => void;
  onSelectScript: (scriptId: number | null) => void;
  storyboardActionLabel?: string;
  onOpenStoryboard?: () => void;
}

export function EpisodeWorkspaceHeader({
  episode,
  script,
  scripts,
  selectedScriptId,
  workflowStatus,
  activeTab,
  onTabChange,
  onNavigateBack,
  onGenerateScript,
  onGenerateTimeline,
  onSelectScript,
  storyboardActionLabel = "打开分镜辅助",
  onOpenStoryboard,
}: EpisodeWorkspaceHeaderProps) {
  const productionState = buildEpisodeProductionState({
    activeTab,
    script,
    workflowStatus,
    storyboardActionLabel,
  });

  const runPrimaryAction = () => {
    runProductionAction(productionState.primaryAction.kind, {
      onGenerateScript,
      onGenerateTimeline,
      onOpenStoryboard,
      onTabChange,
    });
  };

  return (
    <OperatorPanel className="p-4">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0">
          <div className="text-xs font-medium text-gray-500">IP 剧集工作台</div>
          <h1 className="mt-1 truncate text-lg font-semibold text-gray-950">
            第{episode.episode_number}集: {episode.title}
          </h1>
          <p className="mt-1 truncate text-sm text-gray-600">
            {episode.duration_minutes || "-"}分钟 · Timeline-first 生产控制台
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={onNavigateBack}
            className={operatorButtonClass("ghost")}
          >
            返回故事
          </button>
          <button
            type="button"
            onClick={runPrimaryAction}
            disabled={productionState.primaryAction.disabled}
            className={operatorButtonClass("primary")}
          >
            {productionState.primaryAction.label}
          </button>
        </div>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-[minmax(260px,360px)_minmax(0,1fr)]">
        <label className="min-w-0 text-xs font-medium text-gray-600">
          当前剧本
          <select
            aria-label="当前剧本"
            value={selectedScriptId ?? ""}
            onChange={(event) => {
              const next = Number(event.target.value);
              onSelectScript(Number.isFinite(next) ? next : null);
            }}
            disabled={scripts.length === 0}
            className={operatorSelectClass("mt-1 w-full")}
          >
            {scripts.length === 0 ? (
              <option value="">未生成剧本</option>
            ) : (
              scripts.map((item) => (
                <option key={item.id} value={item.id}>
                  {scriptOptionLabel(item)}
                </option>
              ))
            )}
          </select>
        </label>

        <div className="min-w-0 rounded-md border border-gray-100 bg-gray-50 px-3 py-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-gray-600">
              生产主线
            </span>
            {productionState.steps.map((step) => (
              <span key={step.key} className="inline-flex items-center gap-1">
                <span className="text-xs font-medium text-gray-800">
                  {step.label}
                </span>
                <StatusPill tone={productionStatusTone(step.status)}>
                  {productionStatusLabel(step.status)}
                </StatusPill>
              </span>
            ))}
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => onTabChange("script")}
              className={operatorButtonClass(
                activeTab === "script" ? "secondary" : "ghost",
              )}
            >
              剧本设置
            </button>
            <button
              type="button"
              onClick={() => onTabChange("storyboard")}
              className={operatorButtonClass(
                activeTab === "storyboard" ? "secondary" : "ghost",
              )}
            >
              分镜参考
            </button>
            <button
              type="button"
              onClick={() => onTabChange("characters")}
              className={operatorButtonClass(
                activeTab === "characters" ? "secondary" : "ghost",
              )}
            >
              临时角色/IP 绑定
            </button>
          </div>
        </div>
      </div>
    </OperatorPanel>
  );
}

function runProductionAction(
  kind: ProductionActionKind,
  handlers: {
    onGenerateScript?: () => void;
    onGenerateTimeline?: () => void;
    onOpenStoryboard?: () => void;
    onTabChange: (tab: TabKey) => void;
  },
) {
  if (kind === "generate-script") {
    handlers.onGenerateScript?.();
    return;
  }
  if (kind === "generate-timeline") {
    handlers.onGenerateTimeline?.();
    return;
  }
  if (kind === "open-clip") {
    handlers.onOpenStoryboard?.();
    return;
  }
  if (kind === "open-storyboard") {
    handlers.onTabChange("storyboard");
    return;
  }
  handlers.onTabChange("timeline");
}
