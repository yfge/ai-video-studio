import Link from "next/link";
import { StatusPill, operatorButtonClass } from "@/components/shared";
import type { Story, StoryCharacter } from "@/utils/api/types";
import { episodeWorkspaceHref } from "@/utils/routes";
import {
  isSingleVideoProject,
  singleVideoProjectEpisodeId,
  singleVideoProjectTaskId,
} from "@/utils/singleVideoProject";
import { storyDisplayText } from "./StoryProductionModel";
import { storyCharacterDisplayName } from "./StoryProductionDetailParts";

export function StoryProjectCard({
  story,
  onDelete,
}: {
  story: Story;
  onDelete: (businessId: string) => void;
}) {
  const storyKey = story.business_id || String(story.id);
  const linkedCharacters = story.story_characters || story.characters || [];
  const singleVideo = isSingleVideoProject(story);
  const episodeId = singleVideoProjectEpisodeId(story);
  const taskId = singleVideoProjectTaskId(story);
  const singleVideoHref = episodeId
    ? episodeWorkspaceHref(episodeId, {
        tab: "script",
        extraParams: taskId ? { taskId } : undefined,
      })
    : `/stories/${storyKey}`;

  return (
    <article className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate text-sm font-semibold text-gray-950">
            {story.title}
          </h3>
          <p className="mt-1 text-xs text-gray-500">
            {singleVideo
              ? `单条视频 · ${story.duration_minutes || 3} 分钟 · ${
                  story.default_aspect_ratio || "9:16"
                }`
              : `${story.genre || "未分类"}${
                  story.theme ? ` · ${story.theme}` : ""
                }`}
          </p>
        </div>
        <StatusPill
          tone={
            singleVideo
              ? "blue"
              : story.status === "published"
              ? "green"
              : "gray"
          }
        >
          {singleVideo ? "单条视频" : story.status || "draft"}
        </StatusPill>
      </div>

      <p className="mt-4 line-clamp-3 text-sm leading-6 text-gray-600">
        {storyDisplayText(story.synopsis, story.premise)}
      </p>
      <StoryCharacterChips
        characters={linkedCharacters}
        emptyLabel={singleVideo ? "无需预先配置 IP" : undefined}
      />

      <div className="mt-4 flex items-center justify-between border-t border-gray-100 pt-3">
        <span className="text-xs text-gray-500">
          更新 {new Date(story.updated_at).toLocaleDateString("zh-CN")}
        </span>
        <div className="flex gap-2">
          {singleVideo ? (
            <Link
              href={singleVideoHref}
              className={operatorButtonClass("primary", "whitespace-nowrap")}
            >
              打开视频
            </Link>
          ) : (
            <>
              <Link
                href={`/stories/${storyKey}?generate=episodes#episode-generation`}
                className={operatorButtonClass("primary", "whitespace-nowrap")}
              >
                生成剧集
              </Link>
              <Link
                href={`/stories/${storyKey}`}
                className={operatorButtonClass("ghost", "whitespace-nowrap")}
              >
                详情
              </Link>
            </>
          )}
          <button
            type="button"
            onClick={() => onDelete(storyKey)}
            className="h-8 whitespace-nowrap rounded-md px-2 text-xs font-medium text-red-600 hover:bg-red-50"
          >
            删除
          </button>
        </div>
      </div>
    </article>
  );
}

function StoryCharacterChips({
  characters,
  emptyLabel = "暂未关联 IP",
}: {
  characters: StoryCharacter[];
  emptyLabel?: string;
}) {
  if (!characters.length) {
    return (
      <div className="mt-4">
        <span className="rounded-md border border-amber-200 bg-amber-50 px-2 py-1 text-xs text-amber-700">
          {emptyLabel}
        </span>
      </div>
    );
  }

  return (
    <div className="mt-4 flex flex-wrap gap-2">
      {characters.slice(0, 3).map((character) => (
        <span
          key={character.id}
          className="rounded-md border border-gray-200 bg-gray-50 px-2 py-1 text-xs text-gray-600"
        >
          IP: {storyCharacterDisplayName(character)}
        </span>
      ))}
      {characters.length > 3 ? (
        <span className="rounded-md border border-gray-200 bg-gray-50 px-2 py-1 text-xs text-gray-600">
          +{characters.length - 3}
        </span>
      ) : null}
    </div>
  );
}
