"use client";

import type { Episode } from "@/utils/api/types";
import { getSceneCount } from "@/hooks/useEpisodeDetail";

interface EpisodeHeaderProps {
  episode: Episode;
  onNavigateToStory: () => void;
  onNavigateToStoryboard: () => void;
  onShowGenerateForm: () => void;
}

export function EpisodeHeader({
  episode,
  onNavigateToStory,
  onNavigateToStoryboard,
  onShowGenerateForm,
}: EpisodeHeaderProps) {
  return (
    <div className="mb-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            第{episode.episode_number}集: {episode.title}
          </h1>
          <p className="mt-2 text-gray-600">
            {episode.duration_minutes}分钟 • {getSceneCount(episode) || "未知"}
            个场景
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onNavigateToStory}
            className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
          >
            返回故事
          </button>
          <button
            onClick={onNavigateToStoryboard}
            className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
          >
            分镜管理
          </button>
          <button
            onClick={onShowGenerateForm}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
          >
            生成剧本
          </button>
        </div>
      </div>
    </div>
  );
}
