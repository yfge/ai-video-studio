"use client";

import { useState } from "react";
import type { Story } from "@/utils/api";

interface StorySummarySectionProps {
  story: Story;
}

export function StorySummarySection({ story }: StorySummarySectionProps) {
  const [showPrompt, setShowPrompt] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h2 className="text-xl font-semibold mb-3">故事概要</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <p className="text-gray-700 whitespace-pre-wrap">
            {story.synopsis || story.premise || "暂无概要"}
          </p>
          {story.main_conflict && (
            <p className="text-gray-700 mt-3 whitespace-pre-wrap">
              <span className="font-medium">主要冲突：</span>
              {story.main_conflict}
            </p>
          )}
          {story.resolution && (
            <p className="text-gray-700 mt-2 whitespace-pre-wrap">
              <span className="font-medium">结局趋势：</span>
              {story.resolution}
            </p>
          )}
        </div>
        <div>
          <div className="text-sm text-gray-600">
            {story.setting_time && <div>时间设定：{story.setting_time}</div>}
            {story.setting_location && <div>地点设定：{story.setting_location}</div>}
            {story.world_building && (
              <div className="mt-2">
                <div className="font-medium text-gray-800">世界观</div>
                <div className="whitespace-pre-wrap">{story.world_building}</div>
              </div>
            )}
          </div>
        </div>
      </div>
      {story.generation_prompt && (
        <div className="mt-4">
          <button
            onClick={() => setShowPrompt(!showPrompt)}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            {showPrompt ? "收起生成提示词" : "查看生成提示词"}
          </button>
          {showPrompt && (
            <div className="mt-2 bg-gray-50 p-3 rounded text-sm text-gray-700 whitespace-pre-wrap">
              {story.generation_prompt}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
