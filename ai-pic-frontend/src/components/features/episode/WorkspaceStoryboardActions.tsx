"use client";

import Link from "next/link";
import { useState } from "react";
import { operatorButtonClass } from "@/components/shared";
import { generateStoryboardFromAudioTimelineAsync } from "@/utils/api/endpoints";

type ShowAlert = (options: {
  message: string;
  variant: "info" | "success" | "warning" | "error";
}) => void;

interface WorkspaceStoryboardActionsProps {
  selectedScriptId?: number | null;
  selectedAudioTimeline?: Record<string, unknown> | null;
  timelineHref: string;
  clipStoryboardHref?: string | null;
  showAlert?: ShowAlert;
}

export function WorkspaceStoryboardActions({
  selectedScriptId,
  selectedAudioTimeline,
  timelineHref,
  clipStoryboardHref,
  showAlert,
}: WorkspaceStoryboardActionsProps) {
  const [syncingAudioStoryboard, setSyncingAudioStoryboard] = useState(false);
  const hasClipStoryboardEntry = Boolean(clipStoryboardHref);
  const showAudioStoryboardSync =
    !hasClipStoryboardEntry || Boolean(selectedAudioTimeline);
  const canSyncAudioTimelineStoryboard = Boolean(
    selectedAudioTimeline && selectedScriptId && !syncingAudioStoryboard,
  );

  const handleSyncAudioTimelineStoryboard = async () => {
    if (!selectedScriptId) {
      showAlert?.({ message: "请先选择一个剧本", variant: "warning" });
      return;
    }
    if (!selectedAudioTimeline) {
      showAlert?.({
        message: "请先生成时间轴，再同步分镜占位",
        variant: "warning",
      });
      return;
    }

    setSyncingAudioStoryboard(true);
    try {
      const res = await generateStoryboardFromAudioTimelineAsync(
        selectedScriptId,
        {
          overwrite_existing: false,
          min_pause_seconds: 1.5,
        },
      );
      if (!res.success || !res.data) {
        showAlert?.({
          message: res.error || "分镜占位任务提交失败",
          variant: "error",
        });
        return;
      }
      showAlert?.({
        message: `分镜占位任务已提交 #${res.data.task_id}`,
        variant: "success",
      });
    } catch (error) {
      showAlert?.({
        message:
          error instanceof Error
            ? `分镜占位任务提交失败：${error.message}`
            : "分镜占位任务提交失败",
        variant: "error",
      });
    } finally {
      setSyncingAudioStoryboard(false);
    }
  };

  return (
    <div className="flex flex-wrap justify-end gap-2">
      {clipStoryboardHref ? (
        <Link
          href={clipStoryboardHref}
          className={operatorButtonClass("primary")}
        >
          进入第一个片段分镜
        </Link>
      ) : null}
      {showAudioStoryboardSync ? (
        <button
          type="button"
          disabled={!canSyncAudioTimelineStoryboard}
          className={operatorButtonClass(
            hasClipStoryboardEntry ? "ghost" : "primary",
          )}
          onClick={handleSyncAudioTimelineStoryboard}
        >
          {syncingAudioStoryboard ? "提交中..." : "同步分镜占位"}
        </button>
      ) : null}
      {!clipStoryboardHref ? (
        <Link href={timelineHref} className={operatorButtonClass("secondary")}>
          进入时间轴
        </Link>
      ) : null}
    </div>
  );
}
