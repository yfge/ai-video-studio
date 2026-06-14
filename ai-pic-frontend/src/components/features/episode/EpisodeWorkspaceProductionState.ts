"use client";

import type { Script } from "@/utils/api/types";
import type { TimelineResolvedVideoListResponse } from "@/utils/api/types";
import type { TabKey } from "@/hooks/episode/useEpisodeWorkspaceController";

export type WorkflowStepStatus = "pending" | "ready" | "generating";

export interface WorkflowStatus {
  script: WorkflowStepStatus;
  timeline: WorkflowStepStatus;
  storyboard: WorkflowStepStatus;
}

export type ProductionActionKind =
  | "generate-script"
  | "generate-timeline"
  | "open-clip"
  | "open-storyboard"
  | "open-timeline";

export type ProductionStep = {
  key: "script" | "timeline" | "clip-video" | "render-export";
  label: string;
  status: WorkflowStepStatus;
};

export type ProductionState = {
  steps: ProductionStep[];
  primaryAction: {
    kind: ProductionActionKind;
    label: string;
    disabled?: boolean;
  };
};

export function buildEpisodeProductionState({
  activeTab,
  script,
  workflowStatus,
  storyboardActionLabel,
  resolvedVideos,
}: {
  activeTab: TabKey;
  script?: Script | null;
  workflowStatus: WorkflowStatus;
  storyboardActionLabel?: string;
  resolvedVideos?: TimelineResolvedVideoListResponse | null;
}): ProductionState {
  const scriptReady = Boolean(script) || workflowStatus.script === "ready";
  const hasTimelineClipEntry = storyboardActionLabel === "进入片段分镜";
  const timelineReady =
    workflowStatus.timeline === "ready" && hasTimelineClipEntry;
  const clipVideoStatus = clipVideoStepStatus(
    timelineReady,
    workflowStatus,
    resolvedVideos,
  );

  const steps: ProductionStep[] = [
    { key: "script", label: "剧本", status: scriptReady ? "ready" : "pending" },
    {
      key: "timeline",
      label: "时间轴",
      status: timelineReady ? "ready" : "pending",
    },
    {
      key: "clip-video",
      label: "片段视频",
      status: clipVideoStatus,
    },
    { key: "render-export", label: "渲染/导出", status: "pending" },
  ];

  if (!scriptReady) {
    return {
      steps,
      primaryAction: { kind: "generate-script", label: "生成剧本" },
    };
  }

  if (!timelineReady) {
    return {
      steps,
      primaryAction: { kind: "generate-timeline", label: "生成 Timeline" },
    };
  }

  if (hasTimelineClipEntry) {
    if (resolvedVideos?.ready) {
      return {
        steps,
        primaryAction: { kind: "open-timeline", label: "渲染/导出" },
      };
    }
    if (resolvedVideos && resolvedVideos.missing_clip_count > 0) {
      return {
        steps,
        primaryAction: { kind: "open-clip", label: "处理缺失片段" },
      };
    }
    return {
      steps,
      primaryAction: { kind: "open-clip", label: "处理片段视频" },
    };
  }

  if (activeTab !== "timeline") {
    return {
      steps,
      primaryAction: { kind: "open-timeline", label: "回到时间轴" },
    };
  }

  return {
    steps,
    primaryAction: { kind: "open-storyboard", label: "查看分镜参考" },
  };
}

function clipVideoStepStatus(
  timelineReady: boolean,
  workflowStatus: WorkflowStatus,
  resolvedVideos?: TimelineResolvedVideoListResponse | null,
): WorkflowStepStatus {
  if (!timelineReady) return "pending";
  if (resolvedVideos) {
    if (resolvedVideos.ready) return "ready";
    if (resolvedVideos.generating_clip_count > 0) return "generating";
    return "pending";
  }
  return workflowStatus.storyboard === "ready" ? "ready" : "pending";
}

export function productionStatusLabel(status: WorkflowStepStatus) {
  if (status === "ready") return "已就绪";
  if (status === "generating") return "生成中";
  return "待处理";
}

export function productionStatusTone(
  status: WorkflowStepStatus,
): "green" | "amber" | "gray" {
  if (status === "ready") return "green";
  if (status === "generating") return "amber";
  return "gray";
}

export function scriptOptionLabel(script: Script) {
  const hasVersionInTitle = /\(v[\d.]+\)$/.test(script.title || "");
  const versionSuffix =
    script.version && !hasVersionInTitle ? ` (v${script.version})` : "";
  return `${script.title}${versionSuffix}`;
}
