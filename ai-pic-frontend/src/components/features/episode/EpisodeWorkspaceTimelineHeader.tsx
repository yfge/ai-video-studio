"use client";

import type { Episode, Script } from "@/utils/api/types";
import { operatorButtonClass, operatorSelectClass } from "@/components/shared";
import {
  productionStatusLabel,
  scriptOptionLabel,
  type ProductionStep,
  type ProductionState,
  type WorkflowStepStatus,
} from "./EpisodeWorkspaceProductionState";
import type { TabKey } from "@/hooks/episode/useEpisodeWorkspaceController";
import { SupportViewMenu } from "./EpisodeWorkspaceTimelineHeaderSupportMenu";

export function EpisodeWorkspaceTimelineHeader({
  episode,
  scripts,
  selectedScriptId,
  productionState,
  onTabChange,
  onNavigateBack,
  onSelectScript,
  onPrimaryAction,
  singleVideoProject = false,
}: {
  episode: Episode;
  scripts: Script[];
  selectedScriptId: number | null;
  productionState: ProductionState;
  onTabChange: (tab: TabKey) => void;
  onNavigateBack: () => void;
  onSelectScript: (scriptId: number | null) => void;
  onPrimaryAction: () => void;
  singleVideoProject?: boolean;
}) {
  const primaryActionVariant =
    productionState.primaryAction.kind === "open-clip" ? "ghost" : "primary";
  const primaryActionClass =
    productionState.primaryAction.kind === "open-clip"
      ? "!h-6 gap-1 whitespace-nowrap px-1 text-[11px] font-semibold text-amber-700 hover:text-amber-900 min-[760px]:!h-8 min-[760px]:gap-1.5 min-[760px]:px-1.5 min-[760px]:text-xs"
      : "!h-6 px-1.5 text-[11px] min-[760px]:!h-8 min-[760px]:px-3 min-[760px]:text-xs";
  const isMissingClipsAction =
    productionState.primaryAction.kind === "open-clip";

  return (
    <section
      data-episode-workspace-timeline-header="compact"
      className="border-b border-gray-200 px-1 pb-0.5"
    >
      <div
        data-episode-workspace-timeline-header-layout="responsive-workbar"
        className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-1.5 gap-y-0.5 min-[760px]:grid-cols-[minmax(76px,auto)_minmax(16rem,26rem)_minmax(10rem,1fr)_auto] min-[760px]:gap-x-2 min-[760px]:gap-y-1"
      >
        <div className="order-1 min-w-0 min-[760px]:order-none">
          <h1 className="truncate text-[13px] font-semibold leading-6 text-gray-950 min-[760px]:text-sm min-[760px]:leading-8">
            {singleVideoProject
              ? `单条视频：${episode.title}`
              : `第${episode.episode_number}集: ${episode.title}`}
          </h1>
        </div>
        <label
          data-workspace-script-select-slot="compact"
          className="order-3 min-w-0 min-[760px]:order-none"
        >
          <span className="sr-only">当前剧本</span>
          <select
            aria-label="当前剧本"
            value={selectedScriptId ?? ""}
            onChange={(event) => {
              const next = Number(event.target.value);
              onSelectScript(Number.isFinite(next) ? next : null);
            }}
            disabled={scripts.length === 0}
            className={operatorSelectClass(
              "!h-6 w-full min-w-0 bg-gray-50 px-1.5 text-[11px] min-[760px]:!h-8 min-[760px]:px-2 min-[760px]:text-xs",
            )}
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
        <div
          data-production-step-rail="compact"
          data-production-step-rail-layout="segments"
          aria-label="生产主线"
          className="order-4 flex min-w-0 items-center overflow-hidden text-[11px] min-[760px]:order-none min-[760px]:text-xs"
        >
          <span className="sr-only shrink-0 font-semibold text-gray-600">
            生产主线
          </span>
          <ProductionStepRail steps={productionState.steps} />
        </div>
        <div className="order-2 flex items-center justify-end gap-1.5 min-[760px]:order-none">
          <button
            type="button"
            onClick={onPrimaryAction}
            disabled={productionState.primaryAction.disabled}
            aria-label={productionState.primaryAction.label}
            title={productionState.primaryAction.label}
            data-workspace-primary-action={productionState.primaryAction.kind}
            data-workspace-primary-action-emphasis={
              isMissingClipsAction ? "inline-warning" : "primary-button"
            }
            className={operatorButtonClass(
              primaryActionVariant,
              primaryActionClass,
            )}
          >
            {isMissingClipsAction ? (
              <>
                <MissingClipsIcon />
                <span
                  data-workspace-primary-action-label="desktop-full"
                  className="hidden min-[760px]:inline"
                >
                  {productionState.primaryAction.label}
                </span>
                <span
                  aria-hidden="true"
                  data-workspace-primary-action-label="mobile-short"
                  className="min-[760px]:hidden"
                >
                  缺片段
                </span>
              </>
            ) : (
              productionState.primaryAction.label
            )}
          </button>
          <SupportViewMenu
            onNavigateBack={onNavigateBack}
            onTabChange={onTabChange}
          />
        </div>
      </div>
    </section>
  );
}

function MissingClipsIcon() {
  return (
    <svg
      aria-hidden="true"
      data-missing-clips-icon="warning"
      className="h-3 w-3 shrink-0 min-[760px]:h-3.5 min-[760px]:w-3.5"
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.8"
      viewBox="0 0 16 16"
    >
      <path d="M8 2.5 14 13H2L8 2.5Z" />
      <path d="M8 6v3.2" />
      <path d="M8 11.6h.01" />
    </svg>
  );
}

function ProductionStepRail({ steps }: { steps: ProductionStep[] }) {
  return (
    <div
      data-production-step-pills="compact"
      className="flex min-w-0 items-center gap-0.5 overflow-hidden whitespace-nowrap"
    >
      {steps.map((step) => (
        <span
          key={step.key}
          aria-label={`${step.label} ${productionStatusLabel(step.status)}`}
          title={`${step.label} · ${productionStatusLabel(step.status)}`}
          data-production-step-pill={step.key}
          data-production-step-status={step.status}
          data-production-step-compact="segment"
          className={`inline-flex h-1.5 w-4 shrink-0 rounded-full min-[760px]:w-5 ${productionStepPillClass(
            step.status,
          )}`}
        />
      ))}
    </div>
  );
}

function productionStepPillClass(status: WorkflowStepStatus) {
  if (status === "ready") {
    return "bg-emerald-500";
  }
  if (status === "generating") {
    return "bg-amber-500";
  }
  return "bg-slate-200";
}
