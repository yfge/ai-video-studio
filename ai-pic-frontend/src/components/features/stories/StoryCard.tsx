"use client";

import type { Story } from "@/utils/api";
import { resolveCreatorLabel } from "@/utils/creator";
import { GENRES } from "@/hooks/useStories";

interface StoryCardProps {
  story: Story;
  onViewDetails: (businessId: string) => void;
  onDelete: (businessId: string) => void;
}

export function StoryCard({ story, onViewDetails, onDelete }: StoryCardProps) {
  const getStatusStyle = (status: string) => {
    switch (status) {
      case "published":
        return "bg-green-100 text-green-800";
      case "approved":
        return "bg-blue-100 text-blue-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "published":
        return "已发布";
      case "approved":
        return "已批准";
      default:
        return "草稿";
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
      <div className="p-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900 truncate">
            {story.title}
          </h3>
          <span
            className={`px-2 py-1 text-xs rounded-full ${getStatusStyle(
              story.status,
            )}`}
          >
            {getStatusLabel(story.status)}
          </span>
        </div>

        <div className="mb-3">
          <span className="inline-block bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded-full">
            {GENRES.find((g) => g.value === story.genre)?.label || story.genre}
          </span>
          {story.theme && (
            <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full ml-2">
              {story.theme}
            </span>
          )}
        </div>

        <p className="text-gray-600 text-sm mb-4 line-clamp-3">
          {story.synopsis || story.premise || "暂无概要"}
        </p>

        <div className="text-sm text-gray-500 mb-4 space-y-1">
          <div className="flex items-center justify-between">
            <span>时长: {story.duration_minutes || "--"}分钟</span>
            <span>{new Date(story.created_at).toLocaleDateString()}</span>
          </div>
          <div className="text-xs">
            创建者：{resolveCreatorLabel(story.creator)}
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => onViewDetails(story.business_id)}
            className="flex-1 bg-blue-600 text-white px-3 py-2 rounded text-sm hover:bg-blue-700"
          >
            查看详情
          </button>
          <button
            onClick={() => onDelete(story.business_id)}
            className="bg-red-600 text-white px-3 py-2 rounded text-sm hover:bg-red-700"
          >
            删除
          </button>
        </div>
      </div>
    </div>
  );
}
