"use client";

import type { Episode, Script } from "@/utils/api";
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
  onTabChange: (tab: "overview" | "script" | "timeline" | "storyboard" | "characters") => void;
  onNavigateBack: () => void;
  onGenerateScript?: () => void;
  onGenerateTimeline?: () => void;
  onGenerateStoryboard?: () => void;
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
  onGenerateStoryboard,
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
      color: "blue" as const,
    },
    {
      key: "timeline",
      label: "时间轴",
      description: "生成对白音轨和时间轴数据",
      status: workflowStatus.timeline,
      actionLabel:
        workflowStatus.timeline === "ready" ? "查看时间轴" : "生成时间轴",
      onAction: () => {
        if (workflowStatus.timeline === "ready") {
          onTabChange("timeline");
        } else {
          onGenerateTimeline?.();
        }
      },
      color: "indigo" as const,
    },
    {
      key: "storyboard",
      label: "分镜",
      description: "管理分镜帧、生成图像和视频",
      status: workflowStatus.storyboard,
      actionLabel:
        workflowStatus.storyboard === "ready" ? "查看分镜" : "生成分镜",
      onAction: () => {
        if (workflowStatus.storyboard === "ready") {
          onTabChange("storyboard");
        } else {
          onGenerateStoryboard?.();
        }
      },
      color: "purple" as const,
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
      {/* Header Row */}
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={onNavigateBack}
            className="text-sm text-gray-500 hover:text-gray-700 mb-1"
          >
            ← 返回故事
          </button>
          <h1 className="text-2xl font-bold text-gray-900">
            第{episode.episode_number}集: {episode.title}
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            {episode.duration_minutes}分钟 · 剧集工作台
          </p>
        </div>
        <EpisodeWorkflowSteps steps={workflowSteps} compact />
      </div>

      {/* Workflow Steps (Full) */}
      <EpisodeWorkflowSteps steps={workflowSteps} />

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex gap-4">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => onTabChange(tab.key)}
              className={`py-2 px-1 border-b-2 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
    </div>
  );
}
