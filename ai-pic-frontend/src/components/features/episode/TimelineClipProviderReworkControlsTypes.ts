import type { TimelineItem } from "@/components/features";
import type { Environment, EpisodeCharacter } from "@/utils/api/types";
import type {
  StoryboardCharacterImageOptions,
  StoryboardReferenceImageOption,
} from "./TimelineClipStoryboardReferenceImagesModel";

import type { NotifyVariant } from "@/components/shared/notifications";

export type { NotifyVariant };

export type VideoModelOption = {
  id?: string;
  model_id?: string;
  name?: string;
  provider?: string;
};

export type TimelineClipProviderReworkControlsProps = {
  timelineId?: number | string | null;
  timelineVersion?: number | null;
  clipId?: string | null;
  item: TimelineItem | null;
  episodeId?: number | string | null;
  episodeCharacters?: EpisodeCharacter[];
  episodeCharactersLoading?: boolean;
  episodeCharactersError?: string | null;
  environments?: Environment[];
  selectedEnvironmentId?: number | null;
  storyboardCharacterImageOptions?: StoryboardCharacterImageOptions;
  storyboardEnvironmentImageOptions?: StoryboardReferenceImageOption[];
  videoModels?: VideoModelOption[];
  videoModelsLoading?: boolean;
  onNavigateToCharacters?: () => void;
  onQueued?: () => void | Promise<void>;
  onGenerationCompleted?: () => void | Promise<void>;
  onNotify?: (message: string, variant: NotifyVariant) => void;
};
