"use client";

import Link from "next/link";
import StoryboardEditor from "@/components/features/storyboard/StoryboardEditor";
import {
  OperatorPanel,
  OperatorSectionHeader,
  operatorButtonClass,
} from "@/components/shared";
import { episodeWorkspaceHref } from "@/utils/routes";

interface WorkspaceStoryboardTabContentProps {
  episodeKey?: string;
  selectedScriptId?: number | null;
  hasStoryboard?: boolean;
}

export function WorkspaceStoryboardTabContent({
  episodeKey = "",
  selectedScriptId,
  hasStoryboard,
}: WorkspaceStoryboardTabContentProps) {
  const timelineHref = episodeWorkspaceHref(episodeKey, {
    tab: "timeline",
    scriptId: selectedScriptId,
  });

  return (
    <div className="space-y-4">
      <OperatorPanel>
        <OperatorSectionHeader
          title="分镜辅助工作区"
          subtitle="分镜按时间轴 beat 对齐，用于图像和视频生成"
          action={
            <Link
              href={timelineHref}
              className={operatorButtonClass("secondary")}
            >
              返回时间轴
            </Link>
          }
        />
        <div className="mt-4 grid gap-3 text-xs text-gray-600 sm:grid-cols-3">
          <ContextCell label="时间轴来源" value="当前剧本 beat" />
          <ContextCell
            label="分镜状态"
            value={hasStoryboard ? "已有占位" : "待生成占位"}
          />
          <ContextCell label="建议操作" value="先校验对齐，再生成图像/视频" />
        </div>
      </OperatorPanel>
      <OperatorPanel className="max-h-[calc(100vh-260px)] overflow-y-auto p-4">
        <StoryboardEditor />
      </OperatorPanel>
    </div>
  );
}

function ContextCell({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-gray-200 bg-white px-3 py-2">
      <div className="text-gray-500">{label}</div>
      <div className="mt-1 font-medium text-gray-800">{value}</div>
    </div>
  );
}
