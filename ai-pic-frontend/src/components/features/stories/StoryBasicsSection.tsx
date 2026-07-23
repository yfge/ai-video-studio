"use client";

import type { Dispatch, SetStateAction } from "react";
import type { StoryGenerationForm, StoryFormat } from "@/utils/storyOptions";
import { STORY_FORMATS, STORY_GENRES } from "@/utils/storyOptions";

interface StoryBasicsSectionProps {
  generateForm: StoryGenerationForm;
  setGenerateForm: Dispatch<SetStateAction<StoryGenerationForm>>;
}

export function StoryBasicsSection({
  generateForm,
  setGenerateForm,
}: StoryBasicsSectionProps) {
  return (
    <section className="space-y-4" aria-labelledby="story-seed-basics">
      <div>
        <h2
          id="story-seed-basics"
          className="text-sm font-semibold text-gray-900"
        >
          Story Seed 初始条件
        </h2>
        <p className="mt-1 text-xs text-gray-500">
          这里只建立故事初始条件；分集节奏、投流钩子和拍摄检查在下游完成。
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <label className="text-sm font-medium text-gray-700">
          故事标题 *
          <input
            type="text"
            value={generateForm.title}
            onChange={(event) =>
              setGenerateForm((prev) => ({
                ...prev,
                title: event.target.value,
              }))
            }
            placeholder="输入故事标题"
            className="mt-2 w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500"
          />
        </label>
        <label className="text-sm font-medium text-gray-700">
          故事类型
          <select
            value={generateForm.genre}
            onChange={(event) =>
              setGenerateForm((prev) => ({
                ...prev,
                genre: event.target.value,
              }))
            }
            className="mt-2 w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500"
          >
            {STORY_GENRES.map((genre) => (
              <option key={genre.value} value={genre.value}>
                {genre.label}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm font-medium text-gray-700">
          故事形态
          <select
            value={generateForm.story_format}
            onChange={(event) =>
              setGenerateForm((prev) => ({
                ...prev,
                story_format: event.target.value as StoryFormat,
              }))
            }
            className="mt-2 w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500"
          >
            {STORY_FORMATS.map((format) => (
              <option key={format.value} value={format.value}>
                {format.label}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm font-medium text-gray-700">
          目标受众
          <input
            type="text"
            value={generateForm.target_audience}
            onChange={(event) =>
              setGenerateForm((prev) => ({
                ...prev,
                target_audience: event.target.value,
              }))
            }
            placeholder="例如：都市女性、青少年"
            className="mt-2 w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500"
          />
        </label>
      </div>
      <label className="block text-sm font-medium text-gray-700">
        一句话创作 Brief *
        <textarea
          value={generateForm.additional_requirements}
          onChange={(event) =>
            setGenerateForm((prev) => ({
              ...prev,
              additional_requirements: event.target.value,
            }))
          }
          placeholder="谁在什么处境下，为何必须做什么，以及主要阻力是什么"
          rows={3}
          className="mt-2 w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500"
        />
      </label>
    </section>
  );
}
