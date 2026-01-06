"use client";

import type { Dispatch, SetStateAction } from "react";
import type { StoryGenerationRequest } from "@/utils/api";
import { AIModelType } from "@/utils/api";
import { MarketingFields, MultiModelSelector } from "@/components/shared";
import { STORY_GENRES } from "@/utils/storyOptions";

interface StoryBasicsSectionProps {
  generateForm: StoryGenerationRequest;
  setGenerateForm: Dispatch<SetStateAction<StoryGenerationRequest>>;
}

export function StoryBasicsSection({
  generateForm,
  setGenerateForm,
}: StoryBasicsSectionProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            故事标题 *
          </label>
          <input
            type="text"
            value={generateForm.title}
            onChange={(e) =>
              setGenerateForm((prev) => ({ ...prev, title: e.target.value }))
            }
            placeholder="输入故事标题"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            故事类型
          </label>
          <select
            value={generateForm.genre}
            onChange={(e) =>
              setGenerateForm((prev) => ({ ...prev, genre: e.target.value }))
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {STORY_GENRES.map((genre) => (
              <option key={genre.value} value={genre.value}>
                {genre.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            故事主题
          </label>
          <input
            type="text"
            value={generateForm.theme}
            onChange={(e) =>
              setGenerateForm((prev) => ({ ...prev, theme: e.target.value }))
            }
            placeholder="例如：友情、成长、冒险"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            目标受众
          </label>
          <input
            type="text"
            value={generateForm.target_audience}
            onChange={(e) =>
              setGenerateForm((prev) => ({
                ...prev,
                target_audience: e.target.value,
              }))
            }
            placeholder="例如：青少年、成人、女性向"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <MarketingFields
        form={generateForm}
        setForm={setGenerateForm}
        title="市场/微类型/节奏模板"
        idPrefix="story"
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            预计总时长（分钟）
          </label>
          <input
            type="number"
            value={generateForm.duration_minutes}
            onChange={(e) =>
              setGenerateForm((prev) => ({
                ...prev,
                duration_minutes: parseInt(e.target.value) || 30,
              }))
            }
            min="1"
            max="300"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <MultiModelSelector
          label="选择模型"
          value={generateForm.model ? [generateForm.model] : []}
          onChange={(ids) =>
            setGenerateForm((prev) => ({ ...prev, model: ids[0] || "" }))
          }
          modelType={AIModelType.Text}
          multiple={false}
          helperText="为空将由后端自动挑选最佳提供商与模型（故事生成推荐使用支持 JSON Schema 的模型）"
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            温度（0.0 - 1.5）
          </label>
          <input
            type="range"
            min="0"
            max="1.5"
            step="0.1"
            value={generateForm.temperature ?? 0.7}
            onChange={(e) =>
              setGenerateForm((prev) => ({
                ...prev,
                temperature: parseFloat(e.target.value),
              }))
            }
            className="w-full"
          />
          <div className="text-sm text-gray-600">
            当前温度：{generateForm.temperature?.toFixed(1)}
          </div>
        </div>
      </div>
    </div>
  );
}
