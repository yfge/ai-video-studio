"use client";

import type { Episode, Script } from "@/utils/api/types";
import {
  OperatorEntityHeader,
  OperatorTabs,
  OperatorToolbar,
  operatorButtonClass,
} from "@/components/shared";
import {
  EpisodeWorkflowSteps,
  type WorkflowStepStatus,
} from "./EpisodeWorkflowSteps";

export interface WorkflowStatus {
  script: WorkflowStepStatus;
  timeline: WorkflowStepStatus;
  storyboard: WorkflowStepStatus;
}

interface EpisodeWorkspaceHeaderProps {
  episode: Episode;
  script?: Script | null;
  workflowStatus: WorkflowStatus;
  activeTab: "overview" | "script" | "timeline" | "storyboard" | "characters";
  onTabChange: (
    tab: "overview" | "script" | "timeline" | "storyboard" | "characters",
  ) => void;
  onNavigateBack: () => void;
  onGenerateScript?: () => void;
  onGenerateTimeline?: () => void;
  storyboardActionLabel?: string;
  onOpenStoryboard?: () => void;
}

export function EpisodeWorkspaceHeader({
  episode,
  script,
  workflowStatus,
  activeTab,
  onTabChange,
  onNavigateBack,
  onGenerateScript,
  onGenerateTimeline,
  storyboardActionLabel = "打开分镜辅助",
  onOpenStoryboard,
}: EpisodeWorkspaceHeaderProps) {
  const workflowSteps = [
    {
      key: "script",
      label: "剧本",
      description: "查看和编辑剧本内容、场景对白",
      status: workflowStatus.script,
      actionLabel: script ? "查看剧本" : "生成剧本",
      onAction: () => {
        if (script) {
          onTabChange("script");
        } else {
          onGenerateScript?.();
        }
      },
    },
    {
      key: "timeline",
      label: "时间轴",
      description: "生成对白音轨和时间轴数据",
      status: workflowStatus.timeline,
      actionLabel:
        workflowStatus.timeline === "ready" ? "进入时间轴" : "生成时间轴",
      onAction: () => {
        if (workflowStatus.timeline === "ready") {
          onTabChange("timeline");
        } else {
          onGenerateTimeline?.();
        }
      },
    },
    {
      key: "storyboard",
      label: "分镜",
      description:
        storyboardActionLabel === "进入片段分镜"
          ? "按视频片段生成分镜、首尾帧和视频"
          : "按时间轴辅助查看分镜占位",
      status: workflowStatus.storyboard,
      actionLabel: storyboardActionLabel,
      onAction: () => {
        if (onOpenStoryboard) {
          onOpenStoryboard();
        } else {
          onTabChange("storyboard");
        }
      },
    },
  ];

  const tabs = [
    { key: "overview" as const, label: "剧集概要" },
    { key: "script" as const, label: "剧本" },
    { key: "timeline" as const, label: "时间轴" },
    { key: "storyboard" as const, label: "分镜" },
    { key: "characters" as const, label: "临时角色" },
  ];

  return (
    <div className="space-y-4">
      <OperatorEntityHeader
        eyebrow="IP 剧集工作台"
        title={`第${episode.episode_number}集: ${episode.title}`}
        subtitle={`${episode.duration_minutes}分钟 · Timeline-first 生产路径`}
        meta={<EpisodeWorkflowSteps steps={workflowSteps} compact />}
        action={
          <button
            type="button"
            onClick={onNavigateBack}
            className={operatorButtonClass("ghost")}
          >
            返回故事
          </button>
        }
      />

      <EpisodeWorkflowSteps steps={workflowSteps} />

      <OperatorToolbar>
        <OperatorTabs tabs={tabs} active={activeTab} onChange={onTabChange} />
      </OperatorToolbar>
    </div>
  );
}
