"use client";

import { ModelSelector, operatorInputClass } from "@/components/shared";
import type { StorySeed } from "@/utils/api/types";
import { storySeedOutlineText } from "./StorySeedFields";

export function StorySeedPlanningInputs({
  chapterCount,
  model,
  disabled,
  onChapterCount,
  onModel,
}: {
  chapterCount: number;
  model: string;
  disabled: boolean;
  onChapterCount: (value: number) => void;
  onModel: (value: string) => void;
}) {
  return (
    <div className="grid gap-3 rounded-md border border-blue-100 bg-blue-50 p-3 md:grid-cols-2">
      <label className="text-xs font-medium text-gray-700">
        结构化章节数
        <input
          aria-label="结构化章节数"
          type="number"
          min={1}
          step={1}
          value={chapterCount}
          disabled={disabled}
          onChange={(event) =>
            onChapterCount(Math.max(1, Math.trunc(Number(event.target.value))))
          }
          className={operatorInputClass("mt-1 w-full")}
        />
      </label>
      <ModelSelector
        value={model}
        onChange={onModel}
        label="结构化规划模型"
        helperText="只用于把文字大纲转换为指定章数的结构化章节。"
        autoLabel="使用故事默认模型"
        modelType="text"
        disabled={disabled}
        cacheKey="story-seed-structure-models"
      />
    </div>
  );
}

export function suggestedStructureChapterCount(seed: StorySeed) {
  if (seed.schema === "story_seed_v2") {
    return (
      seed.structured_outline.requested_chapter_count ||
      seed.structured_outline.chapters.length
    );
  }
  const range = storySeedOutlineText(seed).match(
    /第\s*1\s*章\s*(?:至|到|-|—|~|～)\s*第?\s*(\d+)\s*章/,
  );
  return Math.max(1, Number(range?.[1] || 12));
}

export function suggestedStructureModel(seed: StorySeed, fallback?: string) {
  return seed.schema === "story_seed_v2"
    ? seed.structured_outline.planning_model || fallback || ""
    : fallback || "";
}
