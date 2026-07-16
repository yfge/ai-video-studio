"use client";

import { operatorButtonClass } from "@/components/shared";
import { ClipProductionActionIcon } from "./ClipProductionActionIcon";
import { ClipProductionActionShell } from "./ClipProductionActionShell";
import { TimelineClipTaskStatusLine } from "./TimelineClipTaskStatusLine";
import type { TrackedClipGenerationTask } from "./useTimelineClipGenerationTaskTracker";

export function TimelineClipKeyframeCard({
  generating,
  canGenerate,
  keyframeStatus,
  keyframesTask,
  currentClipId,
  onGenerate,
}: {
  generating: boolean;
  canGenerate: boolean;
  keyframeStatus: { startReady: boolean; endReady: boolean; label: string };
  keyframesTask?: TrackedClipGenerationTask;
  currentClipId?: string | null;
  onGenerate: () => void;
}) {
  return (
    <ClipProductionActionShell kind="keyframes" step="2" title="首尾帧">
      <div
        data-clip-action-group="keyframes"
        className="inline-flex w-full min-w-0 items-center"
      >
        <button
          type="button"
          aria-label="生成首尾帧"
          disabled={!canGenerate}
          className={operatorButtonClass(
            "secondary",
            "!h-8 w-full min-w-0 gap-1.5 whitespace-nowrap rounded-md border border-slate-200 bg-white px-2.5 text-slate-700 shadow-none hover:bg-slate-50",
          )}
          onClick={onGenerate}
        >
          <ClipProductionActionIcon kind="keyframes" />
          <span>{generating ? "提交中..." : "生成首尾帧"}</span>
        </button>
      </div>
      <div className="mt-2 rounded-md bg-slate-50 px-2 py-1.5 text-[11px] text-slate-600">
        <span>{keyframeStatus.label}</span>
        <span> · 推荐作为视频生成的首尾帧控制</span>
      </div>
      <TimelineClipTaskStatusLine
        kind="keyframes"
        task={keyframesTask}
        currentClipId={currentClipId ?? null}
      />
    </ClipProductionActionShell>
  );
}
