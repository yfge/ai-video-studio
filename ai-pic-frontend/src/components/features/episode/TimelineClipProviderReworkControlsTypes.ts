import type { TimelineItem } from "@/components/features";
import type { Environment, EpisodeCharacter } from "@/utils/api/types";
import type {
  StoryboardCharacterImageOptions,
  StoryboardReferenceImageOption,
} from "./TimelineClipStoryboardReferenceImagesModel";

export type NotifyVariant = "success" | "error" | "warning" | "info";

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
  onQueued?: () => void | Promise<void>;
  onNotify?: (message: string, variant: NotifyVariant) => void;
};
