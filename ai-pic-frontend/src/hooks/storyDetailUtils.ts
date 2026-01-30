import type { Episode } from "@/utils/api";

const asRecord = (value: unknown): Record<string, unknown> | null =>
  value && typeof value === "object"
    ? (value as Record<string, unknown>)
    : null;

export type EpisodeScene = Record<string, unknown>;

export const extractEpisodeScenes = (
  episode: Episode | null,
): EpisodeScene[] => {
  if (!episode) return [];
  const meta =
    asRecord(episode.extra_metadata) ?? asRecord(episode.metadata) ?? {};
  const scenes = (meta as Record<string, unknown>).scenes;
  if (Array.isArray(scenes)) {
    return scenes.filter(
      (scene): scene is EpisodeScene =>
        Boolean(scene) && typeof scene === "object",
    );
  }
  return [];
};

export const getEpisodeSceneCount = (
  episode: Episode | null,
): number | undefined => {
  if (!episode) return undefined;
  const scenes = extractEpisodeScenes(episode);
  const fallback = scenes.length > 0 ? scenes.length : undefined;
  return episode.scene_count ?? fallback;
};
