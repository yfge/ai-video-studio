"use client";

import type { ReactNode } from "react";
import {
  StatusPill,
  operatorButtonClass,
  operatorSelectClass,
} from "@/components/shared";
import type { Environment, NormalizedScene } from "@/utils/api/types";

export function ClipEnvironmentSection({
  scene,
  environments,
  selectedEnvironmentId,
  environmentSaving,
  actionSlot,
  onEnvironmentChange,
  onSaveEnvironment,
}: {
  scene: NormalizedScene | null;
  environments: Environment[];
  selectedEnvironmentId: number | null;
  environmentSaving: boolean;
  actionSlot?: ReactNode;
  onEnvironmentChange: (value: number | null) => void;
  onSaveEnvironment: () => void;
}) {
  const hasScene = Boolean(scene);
  const sceneEnvironmentId =
    typeof scene?.environment_id === "number" ? scene.environment_id : null;
  const effectiveEnvironmentId = selectedEnvironmentId ?? sceneEnvironmentId;
  const canSaveEnvironment = hasScene && effectiveEnvironmentId !== null;
  const showSaveEnvironment = canSaveEnvironment || environmentSaving;
  const saveButtonVariant =
    canSaveEnvironment || environmentSaving ? "primary" : "secondary";
  const selectedEnvironment = environments.find(
    (environment) => environment.id === effectiveEnvironmentId,
  );
  const environmentSummary = selectedEnvironment
    ? selectedEnvironment.name
    : effectiveEnvironmentId !== null
    ? `环境 ${effectiveEnvironmentId}`
    : "未设置";
  const environmentActionLabel = environments.length ? "更换" : "无可选";
  const sceneSlugLabel = scene ? cleanSceneSlugLine(scene.slug_line) : "";
  const sceneLabel = scene
    ? `场景 ${scene.scene_number} · ${sceneSlugLabel}`
    : "未匹配规范化场景，当前环境仅用于片段生成参考。";

  return (
    <section className="px-0 pb-0 pt-0">
      <details
        open={showSaveEnvironment ? true : undefined}
        data-clip-environment-row="true"
        data-clip-environment-layout="context-ribbon"
        className="group bg-transparent px-0 py-0 text-xs"
      >
        <summary
          data-clip-environment-summary="compact"
          className="flex min-h-6 cursor-pointer list-none items-center gap-1 overflow-hidden marker:hidden [&::-webkit-details-marker]:hidden"
        >
          <span data-clip-environment-label="sr-only" className="sr-only">
            场景环境
          </span>
          <span
            data-clip-environment-kind="visible"
            className="inline-flex shrink-0 text-[11px] font-semibold text-slate-700"
          >
            环境
          </span>
          <span aria-hidden="true" className="text-[11px] text-slate-300">
            ·
          </span>
          <span
            data-clip-environment-scene="inline"
            title={sceneLabel}
            className="inline-flex min-w-0 max-w-[18rem] items-center text-[11px] font-medium text-slate-500"
          >
            {hasScene ? <span className="sr-only">{sceneLabel}</span> : null}
            <span
              aria-hidden={hasScene ? "true" : undefined}
              className="truncate"
            >
              {hasScene ? sceneSlugLabel : sceneLabel}
            </span>
          </span>
          <span
            data-clip-environment-choice="summary"
            className="inline-flex h-6 min-w-0 max-w-[10rem] items-center gap-1 rounded border border-transparent bg-transparent px-1 text-[11px] font-semibold text-slate-600 group-open:bg-blue-50/60 group-open:text-blue-700 hover:bg-slate-50"
          >
            <span className="truncate">{environmentSummary}</span>
            <span
              data-clip-environment-action="inline"
              className="shrink-0 text-blue-700"
            >
              {environmentActionLabel}
            </span>
          </span>
        </summary>
        {!hasScene ? <StatusPill tone="gray">片段生成参考</StatusPill> : null}
        <div
          data-clip-environment-controls="expanded"
          className="mt-1 grid grid-cols-1 items-center gap-2 min-[860px]:grid-cols-[minmax(14rem,24rem)_auto]"
        >
          <select
            aria-label="片段环境"
            value={effectiveEnvironmentId ?? ""}
            onChange={(event) =>
              onEnvironmentChange(
                event.target.value ? Number(event.target.value) : null,
              )
            }
            className={operatorSelectClass("w-full")}
          >
            <option value="" disabled>
              {environments.length ? "选择场景环境" : "暂无可选环境"}
            </option>
            {effectiveEnvironmentId !== null && !selectedEnvironment ? (
              <option value={effectiveEnvironmentId}>
                环境 {effectiveEnvironmentId}
              </option>
            ) : null}
            {environments.map((env) => (
              <option key={env.id} value={env.id}>
                {env.name}
                {(env.linked_virtual_ip_count || 0) > 0 ? " · IP资产" : ""}
              </option>
            ))}
          </select>
          {hasScene || actionSlot ? (
            <div className="flex min-w-0 items-center justify-end gap-1">
              {showSaveEnvironment ? (
                <button
                  type="button"
                  onClick={onSaveEnvironment}
                  disabled={environmentSaving || !canSaveEnvironment}
                  className={operatorButtonClass(
                    saveButtonVariant,
                    "w-full px-2 min-[860px]:w-16",
                  )}
                >
                  {environmentSaving ? (
                    "保存中..."
                  ) : (
                    <>
                      保存<span className="sr-only">场景环境</span>
                    </>
                  )}
                </button>
              ) : null}
              {actionSlot}
            </div>
          ) : null}
        </div>
      </details>
    </section>
  );
}

function cleanSceneSlugLine(value?: string | null) {
  const label = (value || "").trim();
  return label.replace(/^SCENE\s+\d+\s*[-:：]\s*/i, "") || label;
}
