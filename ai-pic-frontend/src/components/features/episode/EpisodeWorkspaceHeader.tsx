"use client";

import type {
  Episode,
  Script,
  TimelineResolvedVideoListResponse,
} from "@/utils/api/types";
import {
  buildEpisodeProductionState,
  type ProductionActionKind,
  type WorkflowStatus,
} from "./EpisodeWorkspaceProductionState";
import { EpisodeWorkspaceTimelineHeader } from "./EpisodeWorkspaceTimelineHeader";
import type { TabKey } from "@/hooks/episode/useEpisodeWorkspaceController";

export type { WorkflowStatus } from "./EpisodeWorkspaceProductionState";

interface EpisodeWorkspaceHeaderProps {
  episode: Episode;
  script?: Script | null;
  scripts: Script[];
  selectedScriptId: number | null;
  workflowStatus: WorkflowStatus;
  resolvedVideos?: TimelineResolvedVideoListResponse | null;
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
  onNavigateBack: () => void;
  onGenerateScript?: () => void;
  onGenerateTimeline?: () => void;
  onSelectScript: (scriptId: number | null) => void;
  storyboardActionLabel?: string;
  onOpenStoryboard?: () => void;
  singleVideoProject?: boolean;
}

export function EpisodeWorkspaceHeader({
  episode,
  script,
  scripts,
  selectedScriptId,
  workflowStatus,
  resolvedVideos,
  activeTab,
  onTabChange,
  onNavigateBack,
  onGenerateScript,
  onGenerateTimeline,
  onSelectScript,
  storyboardActionLabel = "打开分镜辅助",
  onOpenStoryboard,
  singleVideoProject = false,
}: EpisodeWorkspaceHeaderProps) {
  const productionState = buildEpisodeProductionState({
    activeTab,
    script,
    workflowStatus,
    storyboardActionLabel,
    resolvedVideos,
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
    <EpisodeWorkspaceTimelineHeader
      episode={episode}
      scripts={scripts}
      selectedScriptId={selectedScriptId}
      productionState={productionState}
      onTabChange={onTabChange}
      onNavigateBack={onNavigateBack}
      onSelectScript={onSelectScript}
      onPrimaryAction={runPrimaryAction}
      singleVideoProject={singleVideoProject}
    />
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
