"use client";

import type { Story } from "@/utils/api";
import { resolveCreatorLabel } from "@/utils/creator";

interface StoryDetailHeaderProps {
  story: Story;
  onBack: () => void;
}

export function StoryDetailHeader({ story, onBack }: StoryDetailHeaderProps) {
  return (
    <div className="mb-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{story.title}</h1>
          <div className="mt-2 flex items-center gap-2 text-sm">
            <span className="inline-block bg-purple-100 text-purple-800 px-2 py-1 rounded">
              {story.genre}
            </span>
            {story.theme && (
              <span className="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded">
                {story.theme}
              </span>
            )}
            <span className="text-gray-500">
              创建者：{resolveCreatorLabel(story.creator)} · 创建于{" "}
              {new Date(story.created_at).toLocaleString()}
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onBack}
            className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
          >
            返回列表
          </button>
        </div>
      </div>
    </div>
  );
}
