import type {
  NormalizedScene,
  TimelineResolvedVideoListResponse,
  TimelineResponse,
} from "@/utils/api/types";

export interface EpisodeTimelineWorkspaceProps {
  episodeId?: number | string | null;
  selectedScriptId: number | null;
  selectedTimelineSpec: TimelineResponse | null;
  onTimelineUpdated?: (timeline: TimelineResponse) => void;
  resolvedVideos?: TimelineResolvedVideoListResponse | null;
  resolvedVideosError?: string | null;
  reloadResolvedVideos?: () => void | Promise<void>;
  onSelectedClipIdChange?: (clipId: string | null) => void;
  initialSelectedClipId?: string | null;
  selectedAudioTimeline: Record<string, unknown> | null;
  selectedStoryboard: Record<string, unknown> | null;
  normalizedScenes: NormalizedScene[];
  pipelineBusy?: boolean;
  timingModel: string;
  setTimingModel: (value: string) => void;
  useDurationControl: boolean;
  setUseDurationControl: (value: boolean) => void;
  onGenerateTimelinePipeline?: () => void;
  pipelineTask?: {
    taskId: number;
    phase: string;
    error: string | null;
  } | null;
  onNavigateToTasks: () => void;
  onNavigateToScript: () => void;
  onNavigateToStoryboard: () => void;
  onNavigateToCharacters: () => void;
}
