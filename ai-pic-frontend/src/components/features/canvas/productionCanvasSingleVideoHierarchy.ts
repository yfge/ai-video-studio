import type { Episode, Story } from "@/utils/api/types";
import { isSingleVideoProject } from "@/utils/singleVideoProject";
import type { HierarchyGraph } from "./productionCanvasHierarchyTypes";

export function storyHierarchyDetail(story: Story) {
  return isSingleVideoProject(story)
    ? `单条视频 · ${story.duration_minutes || 3} 分钟 · ${
        story.default_aspect_ratio || "9:16"
      }`
    : story.premise || story.genre;
}

export function storyHierarchyTypeLabel(story: Story) {
  return isSingleVideoProject(story) ? "视频项目" : undefined;
}

export function episodeHierarchyDetail(episode: Episode) {
  return isSingleVideoProject(episode)
    ? `${episode.duration_minutes || 3} 分钟 · ${
        episode.aspect_ratio || "9:16"
      } · ${episode.status}`
    : `第 ${episode.episode_number} 集 · ${episode.status}`;
}

export function episodeHierarchyTypeLabel(episode: Episode) {
  return isSingleVideoProject(episode) ? "主视频" : undefined;
}

export function buildStoryHierarchyRoot(story: Story): HierarchyGraph {
  return {
    nodes: [
      {
        id: `story:${story.id}`,
        entityType: "story",
        entityId: story.id,
        businessId: story.business_id,
        displayTypeLabel: storyHierarchyTypeLabel(story),
        title: story.title,
        detail: storyHierarchyDetail(story),
        status: "ready",
        parentIds: [],
        expandable: true,
        laneOrder: 0,
      },
    ],
    edges: [],
  };
}
